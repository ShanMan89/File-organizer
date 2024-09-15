# src/app/threads/organizer_thread.py

from PyQt6.QtCore import QThread, pyqtSignal
from app.logic.organizer import Organizer

class FileOrganizerThread(QThread):
    update_progress = pyqtSignal(int)
    update_log = pyqtSignal(str)
    update_stats = pyqtSignal(dict)

    def __init__(self, directory, recursive, dry_run, rules):
        super().__init__()
        self.organizer = Organizer(directory, rules, recursive, dry_run)

    def run(self):
        self.organizer.organize_files(self.emit_progress, self.emit_log, self.emit_stats)

    def emit_progress(self, value):
        self.update_progress.emit(value)

    def emit_log(self, message):
        self.update_log.emit(message)

    def emit_stats(self, stats):
        self.update_stats.emit(stats)

    def undo(self):
        self.organizer.undo()
        self.update_log.emit("Undo completed.")
