"""
08:30, 20:30 두 번 실행되는 업로드 스케줄러
"""
import schedule
import time
import logging
import urllib.request
import urllib.parse
from datetime import datetime
from db import get_pending_calls, mark_uploaded
from sheets import upload_numbers
from export_excel import export

# 텔레그램 설정 (DB 폴더 .env 와 동일한 값)
TELEGRAM_TOKEN = "8600709357:AAFA0mzVgRZFY9dx81fJBTJv1T8Wr9mzCFo"
TELEGRAM_CHAT_ID = "8451577758"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("scheduler.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)


def send_telegram(message: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        }).encode("utf-8")
        urllib.request.urlopen(url, data=data, timeout=10)
    except Exception as e:
        logging.error(f"텔레그램 전송 실패: {e}")


def upload_job():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"=== 업로드 작업 시작: {now} ===")

    rows = get_pending_calls()
    if not rows:
        logging.info("업로드할 번호 없음")
        return

    logging.info(f"총 {len(rows)}건 처리 예정")

    try:
        result = upload_numbers(rows)
        uploaded_ids = result["uploaded_ids"]

        if uploaded_ids:
            mark_uploaded(uploaded_ids)

        logging.info(f"총 {result['total']}건 / 중복 {result['duplicates']}건 / 등록 {result['registered']}건")

        # device_id → 표시 이름 매핑
        device_label = {
            "main": "메인PC",
            "sub": "서브PC",
            "geoin": "거인PC",
            "ars": "ARS",
        }
        device_lines = ""
        for dev_id, count in result["device_counts"].items():
            label = device_label.get(dev_id, dev_id)
            device_lines += f"{label} : {count}건\n"

        msg = (
            f"회신 정상등록\n"
            f"─────────────\n"
            f"{device_lines}"
            f"─────────────\n"
            f"총 갯수 : {result['total']}\n"
            f"중복 제거 : {result['duplicates']}\n"
            f"등록 갯수 : {result['registered']}"
        )
        send_telegram(msg)

    except Exception as e:
        logging.error(f"업로드 실패: {e}")
        send_telegram(f"메인PC 업로드 실패\n오류: {e}")

    # 업로드 완료 후 엑셀 내보내기
    try:
        export()
        logging.info("엑셀 내보내기 완료")
    except Exception as e:
        logging.error(f"엑셀 내보내기 실패: {e}")

    logging.info("=== 업로드 작업 완료 ===")


def run_scheduler():
    schedule.every().day.at("08:30").do(upload_job)
    schedule.every().day.at("20:30").do(upload_job)

    logging.info("스케줄러 시작 — 08:30 / 20:30 실행 대기 중")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    run_scheduler()
