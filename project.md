# project.md — 010 부재중 수집기

## 목표

Tasker(Android)로 부재중 전화번호를 실시간 수집하여 구글 시트 ARS 탭에 자동 업로드한다.

## 전체 흐름

```
핸드폰 부재중 수신
  → Tasker (Missed Call 이벤트)
  → HTTP POST → Flask 서버 (192.168.0.20:5010)
  → SQLite 저장 (중복 체크 5분)
  → 08:30 / 20:30 스케줄러 실행
  → 4개 시트 중복 체크 (메인PC, 서브PC, 거인PC, ARS)
  → ARS 시트 B열에 010-NNNN-NNNN 형식으로 append
```

## 연결된 핸드폰 (device_id)

| device_id | 담당 |
|---|---|
| `main` | 메인PC |
| `sub` | 서브PC |
| `geoin` | 거인PC |
| `ars` | ARS |

## 구글 시트

- 스프레드시트 ID: `1xIgkPE2rMWW6SH1lkDZqMGfVmEbpX-ScCnBMgg0ZzqM`
- 업로드 시트: ARS (B열)
- 중복 체크 시트: 메인PC, 서브PC, 거인PC, ARS

## 환경

- PC: 메인PC (`192.168.0.20`)
- Python 3.14
- Windows 서비스: `MissedCallServer` (Automatic)
- 방화벽: 5010 포트 인바운드 허용
