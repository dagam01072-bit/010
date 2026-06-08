import gspread
from pathlib import Path

SERVICE_ACCOUNT_FILE = Path(__file__).parent.parent / "DB" / "service_account.json"
SPREADSHEET_ID = "1xIgkPE2rMWW6SH1lkDZqMGfVmEbpX-ScCnBMgg0ZzqM"

# 중복 체크 대상 시트 4개
CHECK_SHEETS = ["메인PC", "서브PC", "거인PC", "ARS"]
UPLOAD_SHEET = "ARS"


def normalize_phone(number: str) -> str:
    """01012345678 → 010-1234-5678"""
    digits = "".join(filter(str.isdigit, number))
    if len(digits) == 11 and digits.startswith("010"):
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    return number


def get_all_existing_phones(sh) -> set:
    """4개 시트 B열에서 번호 전체 수집"""
    existing = set()
    for sheet_name in CHECK_SHEETS:
        try:
            ws = sh.worksheet(sheet_name)
            values = ws.col_values(2)  # B열 전체
            for v in values[1:]:       # 헤더 제외
                v = v.strip()
                if v:
                    existing.add(v)
        except gspread.exceptions.WorksheetNotFound:
            print(f"  [없음] {sheet_name} 시트 없음 — 건너뜀")
    return existing


def upload_numbers(numbers: list[tuple]) -> dict:
    """
    numbers: [(id, number, device_id, received_at), ...]
    4개 시트 중복 체크 후 ARS 시트 B열에 신규 번호만 추가
    반환: {"uploaded_ids": [...], "total": N, "duplicates": N, "registered": N}
    """
    gc = gspread.service_account(filename=str(SERVICE_ACCOUNT_FILE))
    sh = gc.open_by_key(SPREADSHEET_ID)

    existing_phones = get_all_existing_phones(sh)

    new_rows = []
    uploaded_ids = []
    duplicate_count = 0
    seen = set(existing_phones)

    for call_id, number, device_id, received_at in numbers:
        normalized = normalize_phone(number)
        if normalized in seen:
            duplicate_count += 1
            continue
        seen.add(normalized)
        new_rows.append([None, normalized])
        uploaded_ids.append(call_id)

    if new_rows:
        ars_ws = sh.worksheet(UPLOAD_SHEET)
        ars_ws.append_rows(new_rows, value_input_option="RAW")

    return {
        "uploaded_ids": uploaded_ids,
        "total": len(numbers),
        "duplicates": duplicate_count,
        "registered": len(new_rows),
    }
