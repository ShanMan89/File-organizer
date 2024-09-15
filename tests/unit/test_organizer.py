# tests/unit/test_organizer.py

import unittest
from app.logic.organizer import Organizer
from app.models.rule import Rule
from unittest.mock import patch, MagicMock

class TestOrganizer(unittest.TestCase):
    def setUp(self):
        self.rules = [
            Rule(name='Images', extensions=['.jpg', '.jpeg', '.png', '.gif', '.bmp']),
            Rule(name='Documents', extensions=['.pdf', '.doc', '.docx', '.txt', '.rtf']),
        ]
        self.organizer = Organizer(directory='test_dir', rules=self.rules, recursive=True, dry_run=True)

    @patch('app.logic.organizer.os')
    @patch('app.logic.organizer.shutil')
    def test_organize_files(self, mock_shutil, mock_os):
        # Setup mock behavior
        mock_os.walk.return_value = [
            ('test_dir', ('subdir',), ('file1.jpg', 'file2.pdf', 'file3.unknown')),
            ('test_dir/subdir', (), ('file4.png',)),
        ]
        self.organizer.organize_files(lambda x: None, lambda y: None, lambda z: None)

        # Assertions
        mock_shutil.move.assert_not_called()  # Because dry_run=True
        # Add more assertions as needed

    def test_get_unique_filename(self):
        with patch('os.path.exists') as mock_exists:
            mock_exists.side_effect = [True, True, False]
            unique_name = self.organizer.get_unique_filename('destination', 'file.txt')
            self.assertEqual(unique_name, 'file_2.txt')

    def test_undo(self):
        self.organizer.undo_actions = [("new_path1", "original_path1"), ("new_path2", "original_path2")]
        with patch('app.logic.organizer.shutil.move') as mock_move:
            self.organizer.undo()
            mock_move.assert_any_call("new_path2", "original_path2")
            mock_move.assert_any_call("new_path1", "original_path1")
            self.assertEqual(len(self.organizer.undo_actions), 0)

if __name__ == '__main__':
    unittest.main()
