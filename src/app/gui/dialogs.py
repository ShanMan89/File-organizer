# src/app/gui/dialogs.py

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, QPushButton, QFileDialog
from PyQt6.QtCore import Qt
from typing import List, Dict
import os
from app.models.rule import Rule
from app.logic.organizer import Organizer
from PyQt6.QtGui import QPixmap

class FilePreviewDialog(QDialog):
    def __init__(self, directory: str, rules: List[Rule], recursive: bool):
        super().__init__()
        self.directory = directory
        self.rules = rules
        self.recursive = recursive
        self.organizer = Organizer(self.directory, self.rules, self.recursive, dry_run=True)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Organization Preview')
        self.setGeometry(100, 100, 600, 400)
        layout = QVBoxLayout()

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['Current Location', 'New Location'])
        layout.addWidget(self.tree)

        export_button = QPushButton('Export Preview')
        export_button.clicked.connect(self.exportPreview)
        layout.addWidget(export_button)

        self.setLayout(layout)
        self.loadPreview()

    def loadPreview(self):
        preview_data = self.organizer.get_preview()
        self.populateTree(preview_data)

    def populateTree(self, data: Dict[str, str]):
        self.tree.clear()
        for current_path, new_path in data.items():
            item = QTreeWidgetItem(self.tree)
            item.setText(0, current_path)
            item.setText(1, new_path)

    def exportPreview(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Preview", "", "Text Files (*.txt)")
        if file_name:
            try:
                with open(file_name, 'w') as f:
                    for i in range(self.tree.topLevelItemCount()):
                        item = self.tree.topLevelItem(i)
                        f.write(f"Current: {item.text(0)}\nNew: {item.text(1)}\n\n")
                QLabel(self).setText("Preview exported successfully!")
            except Exception as e:
                QLabel(self).setText(f"Error exporting preview: {str(e)}")


class SingleFilePreviewDialog(QDialog):
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self.initUI()

    def initUI(self):
        self.setWindowTitle('File Preview')
        layout = QVBoxLayout()

        self.preview_label = QLabel()
        layout.addWidget(self.preview_label)

        self.setLayout(layout)
        self.loadPreview()

    def loadPreview(self):
        if self.file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            pixmap = QPixmap(self.file_path)
            self.preview_label.setPixmap(pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    content = f.read(1000)  # Read first 1000 characters
                self.preview_label.setText(content)
            except Exception as e:
                self.preview_label.setText(f"Cannot preview this file type.\nError: {str(e)}")

