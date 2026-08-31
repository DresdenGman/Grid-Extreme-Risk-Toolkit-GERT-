"""ERCOT data adapter with an authenticated Public API load client.

The Public API endpoint used here is ERCOT report NP6-346-CD, "Actual
System Load by Forecast Zone".  It supplies the system ``total`` in MW.
Authentication follows ERCOT's documented ROPC flow: the returned ``id_token``
is supplied as a Bearer token alongside the subscription key.
"""

from __future__ import annotations

import asyncio
import math
import os
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from data.base import GridDataAdapter, GridLoadData, WeatherData
from services.region import (
    ERCOT_SYSTEM_WEATHER_POINTS,
    ERCOT_SYSTEM_WEATHER_WEIGHTS,
    REGION_COORDS,
)


class ERCOTAdapter(GridDataAdapter):
    """Retrieve ERCOT load from the official authenticated Public API.

    Missing credentials or a failed upstream request deliberately return the
    clearly labelled estimated fallback.  They never masquerade as live data.
    """

    TOKEN_URL = (
        "https://ercotb2c.b2clogin.com/ercotb2c.onmicrosoft.com/"
        "B2C_1_PUBAPI-ROPC-FLOW/oauth2/v2.0/token"
    )
    CLIENT_ID = "fec253ea-0d06-4272-a5e6-b478baeecd70"
    LOAD_URL = "https://api.ercot.com/api/public-reports/np6-346-cd/act_sys_load_by_fzn"
    ADEQUACY_URL = "https://api.ercot.com/api/public-reports/np3-763-cd/st_sys_adequacy"
    TOKEN_REFRESH_SKEW_SECONDS = 60
    _shared_id_token: str | None = None
    _shared_token_expires_at: datetime | None = None
    _shared_token_lock: asyncio.Lock | None = None
    MARKET_TIMEZONE = ZoneInfo("America/Chicago")

    def __init__(self) -> None:
        self._username = os.getenv("ERCOT_API_USERNAME", "").strip()
        self._password = os.getenv("ERCOT_API_PASSWORD", "")
        self._subscription_key = os.getenv("ERCOT_API_SUBSCRIPTION_KEY", "").strip()

    @property
    def official_api_configured(self) -> bool:
        """Whether all credentials necessary for an official ERCOT request exist."""
        return bool(self._username and self._password and self._subscription_key)

    async def _get_id_token(self, client: httpx.AsyncClient) -> str:
        now = datetime.now().astimezone()
        if (
            self.__class__._shared_id_token
            and self.__class__._shared_token_expires_at
            and now < self.__class__._shared_token_expires_at
        ):
            return self.__class__._shared_id_token

        if self.__class__._shared_token_lock is None:
            self.__class__._shared_token_lock = asyncio.Lock()
        async with self.__class__._shared_token_lock:
            now = datetime.now().astimezone()
            if (
                self.__class__._shared_id_token
                and self.__class__._shared_token_expires_at
                and now < self.__class__._shared_token_expires_at
            ):
                return self.__class__._shared_id_token

            response = await client.post(
                self.TOKEN_URL,
                data={
                    "username": self._username,
                    "password": self._password,
                    "grant_type": "password",
                    "scope": f"openid {self.CLIENT_ID} offline_access",
                    "client_id": self.CLIENT_ID,
                    "response_type": "id_token",
                },
            )
            response.raise_for_status()
            payload = response.json()
            token = payload.get("id_token")
            if not isinstance(token, str) or not token:
                raise ValueError("ERCOT token response did not contain id_token")

            expires_in = int(payload.get("expires_in", 3600))
            self.__class__._shared_id_token = token
            self.__class__._shared_token_expires_at = now + timedelta(
                seconds=max(1, expires_in - self.TOKEN_REFRESH_SKEW_SECONDS)
            )
            return token

    @staticmethod
    def _records(payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Normalize ERCOT report rows from object or field/value response forms."""
        data = payload.get("data", [])
        if isinstance(data, dict):
            for key in ("rows", "items", "data"):
                if isinstance(data.get(key), list):
                    data = data[key]
                    break
            else:
                data = [data]
        if not isinstance(data, list):
            return []

        fields = payload.get("fields", [])
        field_names = [field.get("name") for field in fields if isinstance(field, dict)]
        records: list[dict[str, Any]] = []
        for row in data:
            if isinstance(row, dict):
                records.append(row)
            elif isinstance(row, list) and len(field_names) == len(row):
                records.append(dict(zip(field_names, row)))
        return records

    @staticmethod
    def _normalized_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "".join(character for character in str(key).lower() if character.isalnum()): value
            for key, value in row.items()
        }

    @classmethod
    def _historical_totals(
        cls, payload: dict[str, Any]
    ) -> list[tuple[datetime, float]]:
        """Convert NP6-346 rows to ordered UTC hourly system totals.

        ERCOT publishes market-day/hour-ending fields in Central time.  Rows
        are grouped by operating day and converted by sequential UTC interval,
        matching the offline archive extractor and preserving DST day length.
        """
        grouped: dict[date, list[tuple[float, str, float]]] = {}
        for raw in cls._records(payload):
            row = cls._normalized_row(raw)
            day_value = row.get("operday") or row.get("operatingday")
            hour_value = row.get("hourending") or row.get("hourend")
            total_value = row.get("total") or row.get("totalload")
            try:
                text_day = str(day_value).strip()
                try:
                    operating_day = datetime.strptime(text_day, "%m/%d/%Y").date()
                except ValueError:
                    operating_day = date.fromisoformat(text_day[:10])
                hour_text = str(hour_value).strip().split(":", 1)[0]
                hour_ending = float(hour_text)
                total_mw = float(total_value)
            except (TypeError, ValueError):
                continue
            if total_mw <= 0 or not math.isfinite(total_mw):
                continue
            dst_flag = str(row.get("dstflag", ""))
            grouped.setdefault(operating_day, []).append(
                (hour_ending, dst_flag, total_mw)
            )

        result: list[tuple[datetime, float]] = []
        for operating_day in sorted(grouped):
            day_rows = sorted(grouped[operating_day], key=lambda item: (item[0], item[1]))
            start_utc = datetime.combine(
                operating_day, time.min, tzinfo=cls.MARKET_TIMEZONE
            ).astimezone(timezone.utc)
            result.extend(
                (start_utc + timedelta(hours=index), total_mw)
                for index, (_, _, total_mw) in enumerate(day_rows)
            )
        return result

    @staticmethod
    def operational_features_from_series(
        series: list[tuple[datetime, float]], target_time: datetime
    ) -> tuple[dict[str, float], datetime]:
        """Build causal v1.3 features for the hour after the latest observation."""
        if target_time.tzinfo is None:
            target_time = target_time.replace(tzinfo=timezone.utc)
        target_time = target_time.astimezone(timezone.utc)
        ordered = sorted(series, key=lambda item: item[0])
        if len(ordered) < 168:
            raise ValueError("At least 168 official hourly load observations are required")
        window = ordered[-168:]
        if any(
            later[0] - earlier[0] != timedelta(hours=1)
            for earlier, later in zip(window, window[1:])
        ):
            raise ValueError("Official load history is not contiguous for 168 hours")
        latest_time = window[-1][0].astimezone(timezone.utc)
        forecast_origin_gap = target_time - (latest_time + timedelta(hours=1))
        if abs(forecast_origin_gap.total_seconds()) > 3 * 3600:
            raise ValueError("Official load history is too stale for a one-hour forecast")

        values = [float(value) for _, value in window]
        prior_24 = values[-24:]
        mean_24 = sum(prior_24) / 24
        mean_168 = sum(values) / 168
        std_24 = (sum((value - mean_24) ** 2 for value in prior_24) / 24) ** 0.5
        std_168 = (sum((value - mean_168) ** 2 for value in values) / 168) ** 0.5
        return (
            {
                "lag_load_1h": values[-1],
                "lag_load_24h": values[-24],
                "lag_load_168h": values[0],
                "rolling_load_mean_24h": mean_24,
                "rolling_load_std_24h": std_24,
                "rolling_load_mean_168h": mean_168,
                "rolling_load_std_168h": std_168,
            },
            latest_time,
        )

    @classmethod
    def _latest_total_mw(cls, payload: dict[str, Any]) -> float:
        """Extract a positive system total from an NP6-346-CD response."""
        records = cls._records(payload)
        if not records:
            raise ValueError("ERCOT load response contained no records")

        # API sorting is requested newest-first.  Still walk every row so an
        # incomplete newest record cannot suppress a valid official reading.
        for row in records:
            normalized = {str(key).lower().replace("_", ""): value for key, value in row.items()}
            value = normalized.get("total") or normalized.get("totalload")
            try:
                total_mw = float(value)
            except (TypeError, ValueError):
                continue
            if total_mw > 0:
                return total_mw
        raise ValueError("ERCOT load response did not contain a positive total MW value")

    @classmethod
    def _latest_available_generation_mw(cls, payload: dict[str, Any]) -> float:
        """Extract ERCOT's available generation capacity from NP3-763-CD."""
        records = cls._records(payload)
        if not records:
            raise ValueError("ERCOT adequacy response contained no records")

        for row in records:
            normalized = {str(key).lower().replace("_", ""): value for key, value in row.items()}
            value = normalized.get("availcapgen")
            try:
                available_mw = float(value)
            except (TypeError, ValueError):
                continue
            if available_mw > 0:
                return available_mw
        raise ValueError("ERCOT adequacy response did not contain positive available generation MW")

    @staticmethod
    def _aggregate_system_weather(payload: Any, target_key: str) -> dict[str, float]:
        if not isinstance(payload, list) or len(payload) != len(ERCOT_SYSTEM_WEATHER_POINTS):
            raise ValueError("Open-Meteo did not return all ERCOT weather points")
        values = {"temperature_2m": 0.0, "wind_speed_10m": 0.0, "shortwave_radiation": 0.0}
        for (zone, _, _), location in zip(ERCOT_SYSTEM_WEATHER_POINTS, payload):
            hourly = location["hourly"]
            index = hourly["time"].index(target_key)
            weight = ERCOT_SYSTEM_WEATHER_WEIGHTS[zone]
            for name in values:
                values[name] += float(hourly[name][index]) * weight
        return values

    async def _fetch_official_context(self) -> tuple[float, float | None]:
        if not self.official_api_configured:
            raise RuntimeError("ERCOT Public API credentials are not fully configured")

        today = datetime.now().date()
        load_params = {
            "operatingDayFrom": (today - timedelta(days=1)).isoformat(),
            "operatingDayTo": today.isoformat(),
            "page": 1,
            "size": 100,
            "sort": "operatingDay",
            "dir": "DESC",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            token = await self._get_id_token(client)
            headers = {
                "Authorization": f"Bearer {token}",
                "Ocp-Apim-Subscription-Key": self._subscription_key,
            }
            response = await client.get(
                self.LOAD_URL,
                params=load_params,
                headers=headers,
            )
            response.raise_for_status()
            load_mw = self._latest_total_mw(response.json())

            # The adequacy product is an hourly planning/operating input.  A
            # failure here must not discard a valid official load observation.
            try:
                adequacy_response = await client.get(
                    self.ADEQUACY_URL,
                    params={
                        "deliveryDateFrom": (today - timedelta(days=1)).isoformat(),
                        "deliveryDateTo": today.isoformat(),
                        "page": 1,
                        "size": 100,
                        "sort": "postedDatetime",
                        "dir": "DESC",
                    },
                    headers=headers,
                )
                adequacy_response.raise_for_status()
                return load_mw, self._latest_available_generation_mw(adequacy_response.json())
            except Exception:
                return load_mw, None

    async def fetch_operational_features(
        self, target_time: datetime
    ) -> tuple[dict[str, float], datetime]:
        """Fetch recent official load history and build server-owned v1.3 features."""
        if not self.official_api_configured:
            raise RuntimeError("ERCOT Public API credentials are not fully configured")
        today = datetime.now(self.MARKET_TIMEZONE).date()
        async with httpx.AsyncClient(timeout=20.0) as client:
            token = await self._get_id_token(client)
            response = await client.get(
                self.LOAD_URL,
                params={
                    "operatingDayFrom": (today - timedelta(days=9)).isoformat(),
                    "operatingDayTo": today.isoformat(),
                    "page": 1,
                    "size": 500,
                    "sort": "operatingDay",
                    "dir": "ASC",
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Ocp-Apim-Subscription-Key": self._subscription_key,
                },
            )
            response.raise_for_status()
        return self.operational_features_from_series(
            self._historical_totals(response.json()), target_time
        )

    def _estimated_load(self, region: str) -> GridLoadData:
        hour = datetime.now().hour
        estimated_load = 45000 + 15000 * math.sin((hour - 6) * math.pi / 12)
        return GridLoadData(
            current_load_mw=estimated_load,
            capacity_mw=self.get_region_capacity(region),
            timestamp=datetime.now(),
            region=region,
            source="estimated_fallback",
            capacity_source="configured_reference",
            capacity_basis="configured regional reference",
        )

    async def fetch_current_load(self, region: str) -> GridLoadData:
        try:
            load_mw, available_capacity_mw = await self._fetch_official_context()
            return GridLoadData(
                current_load_mw=load_mw,
                capacity_mw=available_capacity_mw or self.get_region_capacity(region),
                timestamp=datetime.now(),
                region=region,
                source="official_live",
                capacity_source=(
                    "official_adequacy" if available_capacity_mw else "configured_reference"
                ),
                capacity_basis=(
                    "ERCOT available generation capacity (NP3-763-CD)"
                    if available_capacity_mw
                    else "configured regional reference"
                ),
            )
        except Exception:
            return self._estimated_load(region)

    async def fetch_historical_load(
        self, region: str, start_time: datetime, end_time: datetime
    ) -> list[GridLoadData]:
        """Historical retrieval is deliberately deferred pending paging semantics."""
        return []

    async def fetch_weather(self, region: str) -> WeatherData:
        """Retrieve target-hour weather from Open-Meteo for the ERCOT system."""
        coords = REGION_COORDS.get(region) or REGION_COORDS["ERCOT_NORTH"]
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                if region in {"ERCOT_SYSTEM", "ERCOT_NORTH"}:
                    response = await client.get(
                        "https://api.open-meteo.com/v1/forecast",
                        params={
                            "latitude": ",".join(str(item[1]) for item in ERCOT_SYSTEM_WEATHER_POINTS),
                            "longitude": ",".join(str(item[2]) for item in ERCOT_SYSTEM_WEATHER_POINTS),
                            "hourly": ["temperature_2m", "wind_speed_10m", "shortwave_radiation"],
                            "forecast_hours": 3,
                            "timezone": "UTC",
                            "wind_speed_unit": "ms",
                        },
                    )
                    response.raise_for_status()
                    payload = response.json()
                    target = (datetime.now(timezone.utc) + timedelta(hours=1)).replace(
                        minute=0, second=0, microsecond=0
                    )
                    target_key = target.strftime("%Y-%m-%dT%H:00")
                    values = self._aggregate_system_weather(payload, target_key)
                    return WeatherData(
                        temperature=values["temperature_2m"],
                        wind_speed=values["wind_speed_10m"],
                        solar_irradiance=values["shortwave_radiation"],
                        timestamp=target,
                        source="external_forecast",
                    )
                response = await client.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": coords["lat"],
                        "longitude": coords["long"],
                        "current": [
                            "temperature_2m",
                            "wind_speed_10m",
                            "shortwave_radiation",
                        ],
                        "wind_speed_unit": "ms",
                    },
                )
                response.raise_for_status()
                current = response.json().get("current", {})
                return WeatherData(
                    temperature=current.get("temperature_2m", 25.0),
                    wind_speed=current.get("wind_speed_10m", 5.0),
                    solar_irradiance=current.get("shortwave_radiation", 500.0),
                    timestamp=datetime.now(),
                    source="external_forecast",
                )
        except Exception:
            return WeatherData(
                temperature=25.0,
                wind_speed=10.0,
                solar_irradiance=600.0,
                timestamp=datetime.now(),
                source="estimated_fallback",
            )
