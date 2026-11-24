"""The reader's error paths and mixed date columns (fixes found by the TypeScript port; ts/test/reader.test.ts checks
the same cases on plotkit-ts). Offline; files are written to a temporary folder."""
import datetime as dt
import math
from pathlib import Path

import pytest

from plotkit import charts, core
from plotkit.core import PlotkitError

INPUTS = Path(__file__).resolve().parent / "inputs"
TGA_SHEETS = ["1006R1-V normal", "1006R1-V acid", "1006R1-V 750C"]

# 10 cells, 9 of them dates in different forms: the column is a date column, and every date cell is read
MIXED_DATES = ["2026-03-01 08:00", "2026-03-02", "2026-03-03T09:30:15", "2026/03/04", "2026.3.5 7:05", "2026-02-30",
               "2026-03-07 23:59:59", "2026-3-8", "2026-03-09 12:00", "n/a"]
MIXED_WANT = [dt.datetime(2026, 3, 1, 8), dt.datetime(2026, 3, 2), dt.datetime(2026, 3, 3, 9, 30, 15), dt.datetime(2026, 3, 4),
              dt.datetime(2026, 3, 5, 7, 5), None, dt.datetime(2026, 3, 7, 23, 59, 59), dt.datetime(2026, 3, 8),
              dt.datetime(2026, 3, 9, 12), None]
CSV = "t,v\n" + "\n".join(f"{30 + 10 * i},{100 - i}" for i in range(12)) + "\n"


def err(fn, *a):
    with pytest.raises(PlotkitError) as e:
        fn(*a)
    return e.value.message, e.value.hint


def write(tmp_path, name, data):
    p = tmp_path / name
    p.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
    return str(p)


# ------------------------------------------------------------------- sheets
@pytest.mark.parametrize("sel", ["²", "٣", "1²"])
def test_sheet_names_of_other_digits_are_names(sel):
    assert err(core._select_sheets, TGA_SHEETS, sel, "dir/TGA.xlsx") == (
        f'sheet "{sel}" not found in TGA.xlsx', f"sheet names: {TGA_SHEETS}")


def test_sheet_numbers():
    assert core._select_sheets(TGA_SHEETS, " 2 ", "TGA.xlsx") == ["1006R1-V acid"]
    assert core._select_sheets(TGA_SHEETS, [3, "1", 2.7], "TGA.xlsx") == ["1006R1-V 750C", "1006R1-V normal", "1006R1-V acid"]
    for bad, shown in ((math.nan, "nan"), (math.inf, "inf"), (4, "4"), ("0", "0")):
        assert err(core._select_sheets, TGA_SHEETS, bad, "TGA.xlsx") == (
            f"sheet number {shown} does not exist in TGA.xlsx", f"it has 3 sheet(s): {TGA_SHEETS}")


def test_load_sheets_with_a_superscript_sheet():
    assert err(core.load_sheets, {"file": [str(INPUTS / "TGA.xlsx")], "sheets": "²", "read": {}}) == (
        'sheet "²" not found in TGA.xlsx', f"sheet names: {TGA_SHEETS}")


def test_load_frame_with_no_sheet():
    assert err(charts.load_frame, {"file": [str(INPUTS / "TGA.xlsx")], "sheets": [], "read": {}}) == (
        "no sheet to read", 'set "sheets" to a sheet name, a number from 1, or "all"')


# ------------------------------------------------------------------- dates
def test_mixed_date_forms_in_one_column(tmp_path):
    f = write(tmp_path, "mixed.csv", "d,v\n" + "\n".join(f"{d},{i}" for i, d in enumerate(MIXED_DATES)) + "\n")
    df = charts.load_frame({"file": [f], "sheets": None, "read": {}})
    assert df["d"].dtype.kind == "M"
    assert [None if v is None or v != v else v.to_pydatetime() for v in df["d"].tolist()] == MIXED_WANT
    pv = charts.preview(f)["sheets"][0]["columns"][0]
    assert (pv["type"], pv["min"], pv["max"]) == ("date", "2026-03-01", "2026-03-09")


def test_one_date_form_is_read_as_before(tmp_path):
    days = [f"2026-04-{d:02d}" for d in range(1, 11)]
    f = write(tmp_path, "days.csv", "d,v\n" + "\n".join(f"{d},{i}" for i, d in enumerate(days)) + "\nn/a,10\n")
    df = charts.load_frame({"file": [f], "sheets": None, "read": {}})
    assert [str(v.date()) if v == v else None for v in df["d"]] == days + [None]


def test_to_date():
    assert charts._to_date(" 2026-01-02 03:04:05.5 ") == dt.datetime(2026, 1, 2, 3, 4, 5, 500000)
    assert charts._to_date(dt.datetime(2026, 1, 2, 3)) == dt.datetime(2026, 1, 2, 3)
    for v in ("2026-13-01", "2026-01-01 24:00", "0000-01-01", "08:30", "2026-01", 45000, True, None, dt.time(8, 30)):
        assert charts._to_date(v) is None, v


# ------------------------------------------------------------------- text files: encodings and separators
UHC = "온도,똠값\n1,2\n3,4\n".encode("cp949")                     # 똠: a cp949 (UHC) syllable that EUC-KR lacks


def test_encodings(tmp_path):
    f = write(tmp_path, "k.csv", UHC)
    assert core.read_tables(f)[0]["k"][0] == ["온도", "똠값"]
    assert core.read_tables(f, {"encoding": "cp949"})[0]["k"][0] == ["온도", "똠값"]
    hint = 'check read.encoding (e.g. "utf-8" or "cp949"), or leave it out to detect the encoding'
    assert err(core.read_tables, f, {"encoding": "utf-8"}) == ("k.csv is not utf-8 text", hint)
    assert err(core.read_tables, f, {"encoding": "EUC_KR"}) == ("k.csv is not EUC_KR text", hint)
    assert err(core.read_tables, f, {"encoding": "klingon"}) == (
        'unknown encoding "klingon"', 'use "utf-8", "cp949", "utf-16" or "latin-1", or leave read.encoding out')
    g = write(tmp_path, "ks.csv", "온도,값\n1,2\n".encode("euc-kr"))
    assert core.read_tables(g, {"encoding": "euc-kr"})[0]["ks"][0] == ["온도", "값"]


def test_undecodable_utf16_and_utf8_bom(tmp_path):
    hint = "set read.encoding, or save the file again as UTF-8"
    f = write(tmp_path, "u16.txt", b"\xff\xfe" + "a\tb\n".encode("utf-16-le") + b"\x00")       # odd length
    assert err(core.read_tables, f) == ("u16.txt looks like UTF-16 text but could not be decoded", hint)
    g = write(tmp_path, "u8.txt", b"\xef\xbb\xbfa,b\n\xff\xfe1,2\n")
    assert err(core.read_tables, g) == ("u8.txt looks like UTF-8 text but could not be decoded", hint)


@pytest.mark.parametrize("sep, shown", [("", "''"), (5, "5"), (["a"], "['a']"), (True, "True")])
def test_bad_separator(tmp_path, sep, shown):
    f = write(tmp_path, "t.csv", CSV)
    assert err(core.read_tables, f, {"sep": sep}) == (
        f'read.sep must be a separator like "," or "tab", not {shown}', 'use ",", ";", "tab" or "space", or leave it out')


# ------------------------------------------------------------------- row numbers
ROW_HINT = "rows count from 1 at the top of the sheet, e.g. 3"


@pytest.mark.parametrize("key, value, shown", [("header_row", "abc", "'abc'"), ("header_row", -2, "-2"),
                                               ("header_row", "0", "'0'"), ("data_start_row", True, "True"),
                                               ("data_start_row", "2.5", "'2.5'"), ("data_start_row", [3], "[3]")])
def test_bad_row_numbers(tmp_path, key, value, shown):
    f = write(tmp_path, "t.csv", CSV)
    want = (f't.csv / sheet "t": read.{key} must be a row number from 1, not {shown}', ROW_HINT)
    assert err(core.load_sheets, {"file": [f], "sheets": "all", "read": {key: value}}) == want
    assert err(charts.load_frame, {"file": [f], "sheets": None, "read": {key: value}}) == want


def test_header_row_after_the_end(tmp_path):
    f = write(tmp_path, "t.csv", CSV)
    want = ('t.csv / sheet "t": read.header_row 99 is after the end of the sheet (it has 13 rows)', "check read.header_row")
    assert err(core.load_sheets, {"file": [f], "sheets": "all", "read": {"header_row": 99, "data_start_row": 2}}) == want
    assert err(charts.load_frame, {"file": [f], "sheets": None, "read": {"header_row": 99}}) == want


def test_row_numbers_as_text_still_work(tmp_path):
    f = write(tmp_path, "t.csv", CSV)
    (_, _, t), = core.load_sheets({"file": [f], "sheets": "all", "read": {"header_row": "1", "data_start_row": " 2 "}})
    assert [c["name"] for c in t["columns"]] == ["t", "v"] and t["data_start_row"] == 2
    df = charts.load_frame({"file": [f], "sheets": None, "read": {"header_row": "1"}})
    assert list(df.columns) == ["t", "v"] and len(df) == 12


# ------------------------------------------------------------------- files
def test_not_an_xlsx(tmp_path):
    f = write(tmp_path, "bad.xlsx", "this is not a workbook")
    assert err(core.read_tables, f) == (
        "bad.xlsx could not be read as an .xlsx file",
        "check that it is an Excel workbook; open it in Excel and save it again as .xlsx")


def test_a_folder_is_not_a_file(tmp_path):
    (tmp_path / "data.csv").mkdir()
    msg, _ = err(core.read_tables, str(tmp_path / "data.csv"))
    assert msg == f"file not found: {tmp_path / 'data.csv'}"
