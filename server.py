from flask import Flask, request, jsonify
from db import save_call
import logging

app = Flask(__name__)

# 로그를 파일과 콘솔 둘 다 출력
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("server.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)


@app.route("/call", methods=["POST"])
def receive_call():
    """
    Tasker가 보내는 형식:
    {
        "device_id": "main",
        "number": "01012345678",
        "timestamp": "2026-06-08 14:23:00"
    }
    """
    data = request.get_json(silent=True)

    # 필수 필드 검사
    if not data:
        return jsonify({"status": "error", "message": "JSON 없음"}), 400

    number = data.get("number", "").strip()
    device_id = data.get("device_id", "main").strip()
    timestamp = data.get("timestamp", "").strip()

    if not number or not timestamp:
        return jsonify({"status": "error", "message": "number 또는 timestamp 누락"}), 400

    # 010 번호만 처리 (Tasker에서 이미 필터했지만 서버에서도 한 번 더)
    if not number.startswith("010"):
        logging.info(f"[무시] 010 아님: {number}")
        return jsonify({"status": "ignored", "message": "010 아님"}), 200

    # SQLite 저장 (중복 체크 포함)
    saved = save_call(number=number, device_id=device_id, received_at=timestamp)

    if saved:
        logging.info(f"[저장] {number} | {device_id} | {timestamp}")
        return jsonify({"status": "ok", "message": "저장 완료"}), 200
    else:
        logging.info(f"[중복] {number} | {timestamp} — 5분 이내 중복, 무시")
        return jsonify({"status": "duplicate", "message": "중복 무시"}), 200


@app.route("/health", methods=["GET"])
def health():
    """서버 살아있는지 확인용"""
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    # Tasker와 같은 Wi-Fi에 있으면 0.0.0.0으로 열어야 핸드폰에서 접근 가능
    app.run(host="0.0.0.0", port=5010, debug=False)
