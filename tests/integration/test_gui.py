# tests/integration/test_gui.py

import unittest
from PyQt6.QtWidgets import QApplication
from app.gui.main_window import FileOrganizerGUI

class TestFileOrganizerGUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])

    def setUp(self):
        self.window = FileOrganizerGUI()

    def test_initial_ui_elements(self):
        self.assertIsNotNone(self.window.tabs)
        self.assertIsNotNone(self.window.directory_button)
        self.assertIsNotNone(self.window.recursive_checkbox)
        self.assertIsNotNone(self.window.dry_run_checkbox)
        self.assertIsNotNone(self.window.organize_button)
        self.assertIsNotNone(self.window.undo_button)
        self.assertIsNotNone(self.window.progress_bar)
        self.assertIsNotNone(self.window.log_text)

    def test_select_directory(self):
        # Simulate selecting a directory
        with unittest.mock.patch('PyQt6.QtWidgets.QFileDialog.getExistingDirectory', return_value='test_dir'):
            self.window.select_directory()
            self.assertEqual(self.window.selected_directory, 'test_dir')
            self.assertEqual(self.window.directory_button.text(), 'Selected: test_dir')

    # Add more GUI integration tests as needed

    @classmethod
    def tearDownClass(cls):
        cls.app.quit()

if __name__ == '__main__':
    unittest.main()
