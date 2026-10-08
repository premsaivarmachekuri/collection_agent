"""Build 200 overdue accounts from UCI dataset 350, plus three demo accounts.

UCI rows are Taiwan credit-card bills in NT$. Indian names, DOBs, PAN last-4,
phones, and rupee amounts are synthetic. The mapping is recorded on each row.
"""

from __future__ import annotations

import csv
import io
import json
import random
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "accounts.json"
UCI_URLS = (
    "https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip",
)

FIRST = [
    "Asha", "Ravi", "Meera", "Arjun", "Kavita", "Imran", "Neha", "Sanjay",
    "Pooja", "Vikram", "Anjali", "Farhan", "Divya", "Kiran", "Lakshmi", "Naveen",
]
LAST = [
    "Iyer", "Sharma", "Nair", "Khan", "Das", "Reddy", "Menon", "Joshi",
    "Kapoor", "Banerjee", "Patel", "Singh", "Ghosh", "Kulkarni", "Pillai", "Rao",
]


def main() -> None:
    rows, source = _load_rows()
    random.seed(350)
    accounts = []
    for index, row in enumerate(rows[:200], start=1):
        uci_id = int(float(row.get("ID") or row.get("id") or index))
        age = int(float(row.get("AGE") or row.get("age") or 35))
        bill = abs(int(float(row.get("BILL_AMT1") or row.get("bill_amt1") or 20000)))
        paid = abs(int(float(row.get("PAY_AMT1") or row.get("pay_amt1") or 0)))
        # Synthetic scaler, not an FX rate. Keeps values in an EMI-like INR band.
        overdue = max(5000, min(80000, (bill - paid) // 10 or 8000))
        charges = 150 + (uci_id % 700)
        if charges >= overdue:
            charges = 200
        dob_month = (uci_id % 12) + 1
        dob_day = (uci_id % 27) + 1
        birth_year = 2026 - max(24, min(age, 62))
        accounts.append(
            {
                "account_id": f"HL{index:06d}",
                "borrower_name": f"{FIRST[index % len(FIRST)]} {LAST[uci_id % len(LAST)]}",
                "phone": f"+9198{index:08d}",
                "dob": f"{birth_year}-{dob_month:02d}-{dob_day:02d}",
                "pan_last4": f"{(uci_id * 7) % 10000:04d}",
                "overdue_inr": int(overdue),
                "charges_inr": int(charges),
                "dpd": (uci_id % 30) + 1,
                "last_payment_inr": 0,
                "last_payment_date": None,
                "language": "en",
                "source": source,
                "uci_id": uci_id,
            }
        )
    accounts.extend(_demo_accounts(source))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(accounts, indent=2), encoding="utf-8")
    print(f"wrote {len(accounts)} accounts to {OUT} source={source}")


def _demo_accounts(source: str) -> list[dict]:
    common = {
        "language": "en",
        "source": source,
        "uci_id": None,
        "last_payment_inr": 0,
        "last_payment_date": None,
    }
    return [
        {
            **common,
            "account_id": "HL-DEMO-PTP",
            "borrower_name": "Ravi Iyer",
            "phone": "+919800000001",
            "dob": "1982-03-14",
            "pan_last4": "1937",
            "overdue_inr": 18400,
            "charges_inr": 400,
            "dpd": 12,
        },
        {
            **common,
            "account_id": "HL-DEMO-PLAN",
            "borrower_name": "Meera Sharma",
            "phone": "+919800000002",
            "dob": "1990-07-02",
            "pan_last4": "4410",
            "overdue_inr": 20000,
            "charges_inr": 350,
            "dpd": 9,
        },
        {
            **common,
            "account_id": "HL-DEMO-FAMILY",
            "borrower_name": "Arjun Nair",
            "phone": "+919800000003",
            "dob": "1988-11-21",
            "pan_last4": "6628",
            "overdue_inr": 15600,
            "charges_inr": 275,
            "dpd": 6,
        },
    ]


def _load_rows() -> tuple[list[dict], str]:
    for url in UCI_URLS:
        try:
            rows = _rows_from_uci_zip(url)
            if len(rows) >= 200:
                return rows, "uci-350-pay0-eq-1-synthetic-inr"
        except Exception as exc:
            print(f"uci fetch failed for {url}: {exc}")
    return _fallback_rows(), "synthetic-fallback-uci-unavailable"


def _rows_from_uci_zip(url: str) -> list[dict]:
    import zipfile

    request = urllib.request.Request(url, headers={"User-Agent": "collection-agent-case-study"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    archive = zipfile.ZipFile(io.BytesIO(payload))
    name = next(item for item in archive.namelist() if item.lower().endswith(".xls"))
    # The UCI file is an Excel workbook. Libre/Windows may not have xlrd.
    # Convert via a tiny OLE-unaware path: use openpyxl only if the zip is xlsx.
    # This archive is .xls. Parse with the stdlib if we can; otherwise defer to xlrd
    # when installed. The adapter keeps a raw CSV cache when conversion works.
    raw = archive.read(name)
    cache = ROOT / "data" / "uci_default.xls"
    cache.write_bytes(raw)
    try:
        import xlrd
    except ImportError as exc:
        raise RuntimeError("xlrd is required to read the UCI .xls") from exc
    book = xlrd.open_workbook(file_contents=raw)
    sheet = book.sheet_by_index(0)
    headers = [str(sheet.cell_value(1, col)).strip() for col in range(sheet.ncols)]
    rows = []
    for index in range(2, sheet.nrows):
        row = {headers[col]: sheet.cell_value(index, col) for col in range(sheet.ncols)}
        lowered = {key.lower(): value for key, value in row.items()}
        pay0 = lowered.get("pay_0")
        if pay0 is None:
            continue
        if int(float(pay0)) == 1:
            rows.append(lowered)
    return rows


def _fallback_rows() -> list[dict]:
    random.seed(350)
    rows = []
    for index in range(1, 201):
        rows.append(
            {
                "id": str(index),
                "age": str(25 + (index % 35)),
                "bill_amt1": str(20000 + index * 137),
                "pay_amt1": str(index * 13),
                "pay_0": "1",
            }
        )
    return rows


if __name__ == "__main__":
    main()
