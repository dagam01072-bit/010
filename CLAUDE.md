# CLAUDE.md — 010 부재중 수집기

전역 규칙(`C:\Users\pc\.claude\CLAUDE.md`)과 루트 `giant\CLAUDE.md`를 상속한다.

## 파일 역할

| 파일 | 역할 |
|---|---|
| `server.py` | Flask 수신 서버 (포트 5010) |
| `scheduler.py` | 08:30 / 20:30 구글 시트 업로드 |
| `db.py` | SQLite CRUD + 중복 체크 |
| `sheets.py` | 구글 시트 연동 (ARS 시트 업로드) |
| `service.py` | Windows 서비스 등록 |
| `missed_calls.db` | 수집된 번호 저장소 |

## 핵심 설정값

- 서버 포트: `5010`
- 중복 체크 기준: 5분 이내 같은 번호 재수신 무시 (`db.py` `DEDUP_MINUTES`)
- 업로드 시각: 08:30 / 20:30 (`scheduler.py`)
- 업로드 대상 시트: ARS
- 중복 체크 시트: 메인PC, 서브PC, 거인PC, ARS 4개 전체
- Service Account 키: `../DB/service_account.json`
- 스프레드시트 ID: `1xIgkPE2rMWW6SH1lkDZqMGfVmEbpX-ScCnBMgg0ZzqM`

## 서비스 관리 (관리자 PowerShell)

```powershell
# 시작 / 중지 / 재시작
Start-Service MissedCallServer
Stop-Service MissedCallServer
Restart-Service MissedCallServer

# 상태 확인
Get-Service MissedCallServer
```

## 할 수 있는 것

- `server.py`, `scheduler.py`, `db.py`, `sheets.py` 수정
- `missed_calls.db` 조회 (테스트 목적 초기화는 확인 후)

## 할 수 없는 것

- `../DB/service_account.json` 수정·삭제
- 명시적 요청 없이 커밋·배포
