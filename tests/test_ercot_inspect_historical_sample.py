import io
import zipfile

from training.ercot.inspect_historical_sample import (
    csv_header,
    operational_time_summary,
    sample_csv_content,
)


def test_csv_header_supports_utf8_bom() -> None:
    assert csv_header("\ufeffOperating Day,Hour Ending,Total\n2025-01-01,1,1\n".encode()) == [
        "Operating Day",
        "Hour Ending",
        "Total",
    ]


def test_sample_csv_content_extracts_one_csv_from_zip() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("load.csv", "A,B\n1,2\n")

    source_format, content = sample_csv_content(buffer.getvalue())

    assert source_format == "zip"
    assert csv_header(content) == ["A", "B"]


def test_operational_time_summary_drops_load_values() -> None:
    summary = operational_time_summary(b"OperDay,HourEnding,TOTAL\n08/01/2025,1,100\n08/01/2025,2,200\n")

    assert summary == {
        "row_count": 2,
        "operating_day_min": "08/01/2025",
        "operating_day_max": "08/01/2025",
        "hour_endings": ["1", "2"],
    }
