# src/app/threads/schedule_thread.py

from PyQt6.QtCore import QThread, pyqtSignal
import schedule
import time

class ScheduleThread(QThread):
    schedule_status = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._running = True

    def run(self):
        while self._running:
            schedule.run_pending()
            time.sleep(1)

    def stop(self):
        self._running = False
