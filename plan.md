# plan.md — 010 부재중 수집기

## 완료

- [x] Flask 수신 서버 (server.py) — POST /call, 010 필터, 중복 체크
- [x] SQLite DB (db.py) — 저장, 중복 체크, uploaded 관리
- [x] 스케줄러 (scheduler.py) — 08:30 / 20:30 자동 업로드
- [x] 구글 시트 연동 (sheets.py) — ARS 시트 B열 append, 4개 시트 중복 체크
- [x] Windows 서비스 등록 (MissedCallServer, Automatic)
- [x] 방화벽 5010 포트 인바운드 허용
- [x] Tasker 설정 — Missed Call 이벤트 → HTTP POST

## 다음 작업

- [ ] 서브PC, 거인PC, ARS 핸드폰 Tasker 설정 (device_id 각각 다르게)
- [ ] 실 운영 후 이상 없는지 모니터링 (scheduler.log, server.log)
