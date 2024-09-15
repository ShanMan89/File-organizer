# src/app/gui/main_window.py

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QCheckBox,
    QPushButton, QTextEdit, QProgressBar, QComboBox, QLabel,
    QTableWidget, QTableWidgetItem, QDialog, QFileDialog, QListWidget,
    QLineEdit, QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt, QTranslator, QCoreApplication
from PyQt6.QtGui import QColor, QPalette
from typing import List, Dict
from app.threads.organizer_thread import FileOrganizerThread
from app.threads.schedule_thread import ScheduleThread
from app.utils.settings import load_settings, save_settings
from app.models.rule import Rule
from app.gui.dialogs import FilePreviewDialog
import json
import schedule

class FileOrganizerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.rules: List[Rule] = self.load_initial_rules()
        self.selected_directory: str = ""
        self.translator: QTranslator = QTranslator()
        self.initUI()
        self.loadSettings()
        self.retranslateUi()

    def load_initial_rules(self) -> List[Rule]:
        """Load initial set of organization rules."""
        return [
            Rule(name='Images', extensions=['.jpg', '.jpeg', '.png', '.gif', '.bmp']),
            Rule(name='Documents', extensions=['.pdf', '.doc', '.docx', '.txt', '.rtf']),
            Rule(name='Videos', extensions=['.mp4', '.avi', '.mov', '.wmv']),
            Rule(name='Audio', extensions=['.mp3', '.wav', '.flac', '.m4a']),
        ]

    def initUI(self) -> None:
        """Initialize the user interface."""
        self.setWindowTitle('File Organizer')
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.createOrganizeTab(), "Organize")
        self.tabs.addTab(self.createRulesTab(), "Rules")
        self.tabs.addTab(self.createScheduleTab(), "Schedule")
        self.tabs.addTab(self.createStatsTab(), "Statistics")
        main_layout.addWidget(self.tabs)

        # Dark Mode Toggle
        self.dark_mode_checkbox = QCheckBox('Dark Mode')
        self.dark_mode_checkbox.stateChanged.connect(self.toggleDarkMode)
        main_layout.addWidget(self.dark_mode_checkbox)

        # Language Selector
        self.language_selector = QComboBox()
        self.language_selector.addItems(['English', 'Español', 'Français', '日本語'])
        self.language_selector.currentIndexChanged.connect(self.changeLanguage)
        main_layout.addWidget(self.language_selector)

        central_widget.setLayout(main_layout)

    def createOrganizeTab(self) -> QWidget:
        """Create the Organize tab."""
        tab = QWidget()
        layout = QVBoxLayout()

        self.directory_button = QPushButton('Select Directory', self)
        self.directory_button.clicked.connect(self.select_directory)
        layout.addWidget(self.directory_button)

        self.recursive_checkbox = QCheckBox('Recursive', self)
        layout.addWidget(self.recursive_checkbox)

        self.dry_run_checkbox = QCheckBox('Dry Run', self)
        layout.addWidget(self.dry_run_checkbox)

        self.organize_button = QPushButton('Organize Files', self)
        self.organize_button.clicked.connect(self.start_organizing)
        layout.addWidget(self.organize_button)

        self.undo_button = QPushButton('Undo Last Organization', self)
        self.undo_button.clicked.connect(self.undo_organization)
        layout.addWidget(self.undo_button)

        self.preview_button = QPushButton('Preview Organization', self)
        self.preview_button.clicked.connect(self.preview_organization)
        layout.addWidget(self.preview_button)

        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)

        self.log_text = QTextEdit(self)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        tab.setLayout(layout)
        return tab

    def createRulesTab(self) -> QWidget:
        """Create the Rules tab."""
        tab = QWidget()
        layout = QVBoxLayout()

        self.rules_list = QListWidget()
        self.updateRulesList()
        layout.addWidget(self.rules_list)

        add_rule_button = QPushButton('Add Rule')
        add_rule_button.clicked.connect(self.addRule)
        layout.addWidget(add_rule_button)

        remove_rule_button = QPushButton('Remove Rule')
        remove_rule_button.clicked.connect(self.removeRule)
        layout.addWidget(remove_rule_button)

        export_rules_button = QPushButton('Export Rules')
        export_rules_button.clicked.connect(self.exportRules)
        layout.addWidget(export_rules_button)

        import_rules_button = QPushButton('Import Rules')
        import_rules_button.clicked.connect(self.importRules)
        layout.addWidget(import_rules_button)

        tab.setLayout(layout)
        return tab

    def createScheduleTab(self) -> QWidget:
        """Create the Schedule tab."""
        tab = QWidget()
        layout = QVBoxLayout()

        self.schedule_input = QLineEdit()
        self.schedule_input.setPlaceholderText("Enter schedule (e.g., 'daily at 09:00')")
        layout.addWidget(self.schedule_input)

        schedule_button = QPushButton('Set Schedule')
        schedule_button.clicked.connect(self.setSchedule)
        layout.addWidget(schedule_button)

        self.schedule_status = QLabel("No schedule set")
        layout.addWidget(self.schedule_status)

        tab.setLayout(layout)
        return tab

    def createStatsTab(self) -> QWidget:
        """Create the Statistics tab."""
        tab = QWidget()
        layout = QVBoxLayout()

        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(['Category', 'Files Organized'])
        layout.addWidget(self.stats_table)

        tab.setLayout(layout)
        return tab

    def select_directory(self) -> None:
        """Open a dialog to select a directory for organization."""
        self.selected_directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if self.selected_directory:
            self.directory_button.setText(f"Selected: {self.selected_directory}")

    def start_organizing(self) -> None:
        """Start the file organization process."""
        if not self.selected_directory:
            QMessageBox.warning(self, "Warning", "Please select a directory first.")
            return

        self.progress_bar.setValue(0)
        self.log_text.clear()

        try:
            self.organize_thread = FileOrganizerThread(
                self.selected_directory,
                self.recursive_checkbox.isChecked(),
                self.dry_run_checkbox.isChecked(),
                self.rules
            )
            self.organize_thread.update_progress.connect(self.update_progress)
            self.organize_thread.update_log.connect(self.update_log)
            self.organize_thread.update_stats.connect(self.update_stats)
            self.organize_thread.finished.connect(self.organization_finished)
            self.organize_thread.start()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def undo_organization(self) -> None:
        """Undo the last organization action."""
        if hasattr(self, 'organize_thread'):
            try:
                self.organize_thread.undo()
                self.log_text.append("Undo operation completed.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred during undo: {str(e)}")
        else:
            QMessageBox.warning(self, "Warning", "No organization action to undo.")

    def preview_organization(self) -> None:
        """Preview the organization without actually moving files."""
        if not self.selected_directory:
            QMessageBox.warning(self, "Warning", "Please select a directory first.")
            return

        try:
            preview_dialog = FilePreviewDialog(self.selected_directory, self.rules, self.recursive_checkbox.isChecked())
            preview_dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during preview: {str(e)}")

    def update_progress(self, value: int) -> None:
        """Update the progress bar."""
        self.progress_bar.setValue(value)

    def update_log(self, message: str) -> None:
        """Update the log with a new message."""
        self.log_text.append(message)

    def update_stats(self, stats: Dict[str, int]) -> None:
        """Update the statistics table."""
        self.stats_table.setRowCount(len(stats))
        for row, (category, count) in enumerate(stats.items()):
            self.stats_table.setItem(row, 0, QTableWidgetItem(category))
            self.stats_table.setItem(row, 1, QTableWidgetItem(str(count)))

    def organization_finished(self) -> None:
        """Handle the completion of the organization process."""
        QMessageBox.information(self, "Complete", "File organization completed successfully.")

    def addRule(self) -> None:
        """Open a dialog to add a new organization rule."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Rule")
        layout = QVBoxLayout()

        name_input = QLineEdit()
        name_input.setPlaceholderText("Rule Name")
        layout.addWidget(name_input)

        extensions_input = QLineEdit()
        extensions_input.setPlaceholderText("Extensions (comma-separated)")
        layout.addWidget(extensions_input)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = name_input.text()
            extensions = [ext.strip() for ext in extensions_input.text().split(',')]
            self.rules.append(Rule(name=name, extensions=extensions))
            self.updateRulesList()

    def removeRule(self) -> None:
        """Remove the selected rule from the list."""
        current_item = self.rules_list.currentItem()
        if current_item:
            rule_name = current_item.text().split(':')[0]
            self.rules = [rule for rule in self.rules if rule.name != rule_name]
            self.updateRulesList()
        else:
            QMessageBox.warning(self, "Warning", "Please select a rule to remove.")

    def updateRulesList(self) -> None:
        """Update the displayed list of rules."""
        self.rules_list.clear()
        for rule in self.rules:
            self.rules_list.addItem(f"{rule.name}: {', '.join(rule.extensions)}")

    def exportRules(self) -> None:
        """Export the current rules to a JSON file."""
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Rules", "", "JSON Files (*.json)")
        if file_name:
            try:
                with open(file_name, 'w') as f:
                    json.dump([rule.__dict__ for rule in self.rules], f)
                QMessageBox.information(self, "Success", "Rules exported successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while exporting rules: {str(e)}")

    def importRules(self) -> None:
        """Import rules from a JSON file."""
        file_name, _ = QFileDialog.getOpenFileName(self, "Import Rules", "", "JSON Files (*.json)")
        if file_name:
            try:
                with open(file_name, 'r') as f:
                    imported_rules = json.load(f)
                self.rules = [Rule(**rule) for rule in imported_rules]
                self.updateRulesList()
                QMessageBox.information(self, "Success", "Rules imported successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while importing rules: {str(e)}")

    def setSchedule(self) -> None:
        """Set a schedule for automatic organization."""
        schedule_str = self.schedule_input.text()
        try:
            schedule.clear()
            schedule.every().day.at(schedule_str).do(self.scheduled_organization)
            self.schedule_status.setText(f"Schedule set: {schedule_str}")

            # Start the scheduling in a separate thread
            self.schedule_thread = ScheduleThread()
            self.schedule_thread.start()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Invalid schedule: {str(e)}")

    def scheduled_organization(self) -> None:
        """Run the organization process on schedule."""
        if self.selected_directory:
            self.start_organizing()

    def toggleDarkMode(self, state: Qt.CheckState) -> None:
        """Toggle between light and dark mode."""
        if state == Qt.CheckState.Checked:
            self.setDarkTheme()
        else:
            self.setLightTheme()

    def setDarkTheme(self) -> None:
        """Apply dark theme to the application."""
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        self.setPalette(dark_palette)

    def setLightTheme(self) -> None:
        """Apply light theme to the application."""
        self.setPalette(self.style().standardPalette())

    def changeLanguage(self, index: int) -> None:
        """Change the application language."""
        languages = ['en', 'es', 'fr', 'ja']
        locale = languages[index]
        if self.translator.load(f"../translations/translations_{locale}.qm"):
            QCoreApplication.instance().installTranslator(self.translator)
            self.retranslateUi()
        else:
            QMessageBox.warning(self, "Warning", "Translation not available.")

    def retranslateUi(self) -> None:
        """Update all text elements with translations."""
        self.setWindowTitle(self.tr('File Organizer'))
        self.directory_button.setText(self.tr('Select Directory'))
        self.recursive_checkbox.setText(self.tr('Recursive'))
        self.dry_run_checkbox.setText(self.tr('Dry Run'))
        self.organize_button.setText(self.tr('Organize Files'))
        self.undo_button.setText(self.tr('Undo Last Organization'))
        self.preview_button.setText(self.tr('Preview Organization'))
        self.dark_mode_checkbox.setText(self.tr('Dark Mode'))
        # ... add more translations as needed

    def loadSettings(self) -> None:
        """Load application settings."""
        settings = load_settings()
        self.rules = [Rule(**rule) for rule in settings.get('rules', [])]
        self.updateRulesList()

    def saveSettings(self) -> None:
        """Save application settings."""
        settings = {
            'rules': [rule.__dict__ for rule in self.rules]
        }
        save_settings(settings)

    def closeEvent(self, event) -> None:
        """Handle the window close event."""
        self.saveSettings()
        event.accept()
