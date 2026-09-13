"""Build small, auditable examples directly from ERCOT's public XLSX archives.

Uses Python's standard library and curl for downloads. Run from the repository root:
python3 scripts/build_historical_cases.py
The downloaded archives are held in memory; private training files are not used.
"""

import csv
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
SOURCES = {
    2023: "https://www.ercot.com/files/docs/2023/02/09/Native_Load_2023.zip",
    2021: "https://www.ercot.com/files/docs/2021/11/12/Native_Load_2021.zip",
}
ARCHIVE_CHECKSUMS = {
    2023: '34e7067d3273f56be42ce469e23747cff0db736d668519070ad63674c3ddecd4',
    2021: '63d77e711fbcf838aff1666df475cd86a1fa939ad8aecd60a1bfe5039c4e5b91',
}
CASES = [
    ("summer-2023", 2023, "2023-08-09", "Summer load · August 2023", 80000,
     "A high-load summer window. Compare a fixed capacity assumption with a proportional load reduction."),
    ("spring-2023", 2023, "2023-04-10", "Spring load · April 2023", 45000,
     "A spring comparison window. The same planning rule can behave differently across seasons."),
    ("winter-2021", 2021, "2021-02-14", "Winter storm · February 2021", 60000,
     "Recorded load during the winter storm includes the effects of outages and load shedding. It does not measure unconstrained demand."),
]


def read_archive(blob):
    outer = zipfile.ZipFile(io.BytesIO(blob))
    files = [name for name in outer.namelist() if name.endswith(".xlsx")]
    if len(files) != 1:
        raise ValueError("Expected exactly one XLSX workbook")
    workbook = zipfile.ZipFile(io.BytesIO(outer.read(files[0])))
    strings = ["".join(item.itertext()) for item in ET.fromstring(workbook.read("xl/sharedStrings.xml"))]
    records = []
    for row in ET.fromstring(workbook.read("xl/worksheets/sheet1.xml")).findall("m:sheetData/m:row", NS):
        cells = {}
        for cell in row:
            value = cell.find("m:v", NS)
            if value is not None:
                cells[''.join(filter(str.isalpha, cell.attrib['r']))] = strings[int(value.text)] if cell.attrib.get("t") == "s" else value.text
        records.append(cells)
    if records[0].get("A") != "Hour Ending" or records[0].get("J") != "ERCOT":
        raise ValueError("ERCOT workbook schema changed; inspect before proceeding")
    return records[1:]


def build():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-dir', type=Path, help='Use already downloaded gert-native-load-YEAR.zip files')
    args = parser.parse_args()
    archives = {}
    for year, url in SOURCES.items():
        if args.archive_dir:
            blob = (args.archive_dir / f'gert-native-load-{year}.zip').read_bytes()
        else:
            blob = subprocess.check_output(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '40', url])
        if hashlib.sha256(blob).hexdigest() != ARCHIVE_CHECKSUMS[year]:
            raise ValueError(f'{year}: source archive changed; inspect and version explicitly')
        archives[year] = (read_archive(blob), hashlib.sha256(blob).hexdigest())
    cases = []
    for case_id, year, start_date, title, capacity, note in CASES:
        records, archive_sha = archives[year]
        first = datetime.fromisoformat(start_date)
        end = first + timedelta(days=3)
        hours = []
        for row in records:
            label = row.get("A", "")
            # Select by market date first. These windows avoid DST transitions.
            if not label or label[:10] not in [(first + timedelta(days=i)).strftime("%m/%d/%Y") for i in range(3)]:
                continue
            day, clock = label.split()
            hour = int(clock.split(":")[0])
            ending = datetime.strptime(day, "%m/%d/%Y") + timedelta(hours=hour)
            starting = (ending - timedelta(hours=1)).replace(tzinfo=ZoneInfo("America/Chicago"))
            load = float(row["J"])
            if not math.isfinite(load) or load <= 0:
                raise ValueError("Invalid recorded load")
            hours.append({"timestamp": starting.isoformat(), "load_mw": round(load, 3)})
        if len(hours) != 72 or len({row["timestamp"] for row in hours}) != 72:
            raise ValueError(f"{case_id}: expected 72 unique hourly records, got {len(hours)}")
        times = [datetime.fromisoformat(row["timestamp"]) for row in hours]
        if any(b - a != timedelta(hours=1) for a, b in zip(times, times[1:])):
            raise ValueError("Non-contiguous series")
        cases.append({
            "id": case_id, "title": title, "note": note, "default_capacity_mw": capacity,
            "start_date": start_date, "end_date_exclusive": end.date().isoformat(),
            "source_url": SOURCES[year], "source_archive_sha256": archive_sha,
            "hours": hours,
        })
    bundle = {
        "version": "ercot-native-load-cases-v1",
        "source": "ERCOT Hourly Load Data Archives",
        "source_index_url": "https://www.ercot.com/gridinfo/load/load_hist",
        "timezone": "America/Chicago",
        "timestamp_convention": "Interval start, converted from ERCOT market-local Hour Ending labels; each row spans one hour.",
        "load_definition": "ERCOT published hourly native load. This series differs from the forecast-zone load data used by the probabilistic research candidate.",
        "scope": "Observed historical load with user-defined counterfactual assumptions. No live data or probabilistic forecast is produced.",
        "cases": cases,
    }
    destination = ROOT / "public" / "data"
    destination.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(bundle, indent=2, ensure_ascii=False) + "\n").encode()
    (destination / "historical-cases.json").write_bytes(data)
    sha = hashlib.sha256(data).hexdigest()
    (destination / "historical-cases.sha256").write_text(f"{sha}  historical-cases.json\n")
    with (destination / "historical-load.csv").open("w", newline="") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(["case_id", "interval_start", "recorded_load_mw", "source_archive_sha256"])
        for case in cases:
            for hour in case["hours"]:
                writer.writerow([case["id"], hour["timestamp"], hour["load_mw"], case["source_archive_sha256"]])
    print(f"Built {len(cases)} cases / {sum(len(c['hours']) for c in cases)} hours; SHA256 {sha}")


if __name__ == "__main__":
    build()
