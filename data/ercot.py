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
from datetime import datetime, timedelta
from typing import Any

import httpx

from data.base import GridDataAdapter, GridLoadData, WeatherData
from services.region import REGION_COORDS


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
    TOKEN_REFRESH_SKEW_SECONDS = 60

    def __init__(self) -> None:
        self._username = os.getenv("ERCOT_API_USERNAME", "").strip()
        self._password = os.getenv("ERCOT_API_PASSWORD", "")
        self._subscription_key = os.getenv("ERCOT_API_SUBSCRIPTION_KEY", "").strip()
        self._id_token: str | None = None
        self._token_expires_at: datetime | None = None
        self._token_lock = asyncio.Lock()

    @property
    def official_api_configured(self) -> bool:
        """Whether all credentials necessary for an official ERCOT request exist."""
        return bool(self._username and self._password and self._subscription_key)

    async def _get_id_token(self, client: httpx.AsyncClient) -> str:
        now = datetime.utcnow()
        if self._id_token and self._token_expires_at and now < self._token_expires_at:
            return self._id_token

        async with self._token_lock:
            now = datetime.utcnow()
            if self._id_token and self._token_expires_at and now < self._token_expires_at:
                return self._id_token

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
            self._id_token = token
            self._token_expires_at = now + timedelta(
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

    async def _fetch_official_load(self) -> float:
        if not self.official_api_configured:
            raise RuntimeError("ERCOT Public API credentials are not fully configured")

        today = datetime.now().date()
        params = {
            "operatingDayFrom": (today - timedelta(days=1)).isoformat(),
            "operatingDayTo": today.isoformat(),
            "page": 1,
            "size": 100,
            "sort": "operatingDay",
            "dir": "DESC",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            token = await self._get_id_token(client)
            response = await client.get(
                self.LOAD_URL,
                params=params,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Ocp-Apim-Subscription-Key": self._subscription_key,
                },
            )
            response.raise_for_status()
            return self._latest_total_mw(response.json())

    def _estimated_load(self, region: str) -> GridLoadData:
        hour = datetime.now().hour
        estimated_load = 45000 + 15000 * math.sin((hour - 6) * math.pi / 12)
        return GridLoadData(
            current_load_mw=estimated_load,
            capacity_mw=self.get_region_capacity(region),
            timestamp=datetime.now(),
            region=region,
            source="estimated_fallback",
        )

    async def fetch_current_load(self, region: str) -> GridLoadData:
        try:
            load_mw = await self._fetch_official_load()
            return GridLoadData(
                current_load_mw=load_mw,
                capacity_mw=self.get_region_capacity(region),
                timestamp=datetime.now(),
                region=region,
                source="official_live",
            )
        except Exception:
            return self._estimated_load(region)

    async def fetch_historical_load(
        self, region: str, start_time: datetime, end_time: datetime
    ) -> list[GridLoadData]:
        """Historical retrieval is deliberately deferred pending paging semantics."""
        return []

    async def fetch_weather(self, region: str) -> WeatherData:
        """Retrieve current weather from Open-Meteo for the requested ERCOT region."""
        coords = REGION_COORDS.get(region) or REGION_COORDS["ERCOT_NORTH"]
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": coords["lat"],
                        "longitude": coords["long"],
                        "current": [
                            "temperature_2m",
                            "wind_speed_10m",
                            "direct_normal_irradiance",
                        ],
                        "wind_speed_unit": "ms",
                    },
                )
                response.raise_for_status()
                current = response.json().get("current", {})
                return WeatherData(
                    temperature=current.get("temperature_2m", 25.0),
                    wind_speed=current.get("wind_speed_10m", 5.0),
                    solar_irradiance=current.get("direct_normal_irradiance", 500.0),
                    timestamp=datetime.now(),
                    source="official_live",
                )
        except Exception:
            return WeatherData(
                temperature=25.0,
                wind_speed=10.0,
                solar_irradiance=600.0,
                timestamp=datetime.now(),
                source="estimated_fallback",
            )
