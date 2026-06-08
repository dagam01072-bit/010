"""
Windows 서비스로 Flask 서버 + 스케줄러를 동시에 실행한다.
서비스 등록:   py service.py install
서비스 시작:   py service.py start
서비스 중지:   py service.py stop
서비스 제거:   py service.py remove
"""
import sys
import os
import threading
import servicemanager
import win32event
import win32service
import win32serviceutil

# 현재 파일 기준 경로를 sys.path에 추가 (server, scheduler 임포트용)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


class MissedCallService(win32serviceutil.ServiceFramework):
    _svc_name_ = "MissedCallServer"
    _svc_display_name_ = "Missed Call Flask Server"
    _svc_description_ = "010 부재중 번호 수집 서버 (Flask + 스케줄러)"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.flask_thread = None
        self.scheduler_thread = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, "")
        )
        self._run()

    def _run(self):
        # Flask 서버를 별도 스레드로 실행
        self.flask_thread = threading.Thread(target=self._run_flask, daemon=True)
        self.flask_thread.start()

        # 스케줄러를 별도 스레드로 실행
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()

        # 서비스 중지 신호 대기
        win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)

    def _run_flask(self):
        from server import app
        app.run(host="0.0.0.0", port=5010, debug=False, use_reloader=False)

    def _run_scheduler(self):
        import schedule
        import time
        from scheduler import upload_job

        schedule.every().day.at("08:30").do(upload_job)
        schedule.every().day.at("20:30").do(upload_job)

        while True:
            schedule.run_pending()
            time.sleep(30)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # 인자 없이 실행하면 서비스 매니저로 진입
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(MissedCallService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(MissedCallService)
