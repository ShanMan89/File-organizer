# tests/unit/test_organizer.py

import unittest
from unittest.mock import patch, MagicMock, call, ANY
from pathlib import Path
from app.logic.organizer import Organizer
from app.models.rule import Rule

class TestOrganizer(unittest.TestCase):

    def setUp(self):
        self.rules = [
            Rule(name='Images', extensions=['.jpg', '.jpeg', '.png']),
            Rule(name='Documents', extensions=['.pdf', '.docx', '.txt']),
        ]
        # Mock callbacks
        self.mock_update_progress = MagicMock()
        self.mock_update_log = MagicMock()
        self.mock_update_stats = MagicMock()

    # Test __init__ and validate
    def test_init_organizer(self):
        organizer = Organizer(directory='test_dir', rules=self.rules, recursive=False, dry_run=False)
        self.assertEqual(organizer.directory, Path('test_dir'))
        self.assertEqual(organizer.rules, self.rules)
        self.assertFalse(organizer.recursive)
        self.assertFalse(organizer.dry_run)
        self.assertEqual(organizer.undo_actions, [])

    @patch('pathlib.Path.is_dir')
    def test_validate_valid_directory_and_rules(self, mock_is_dir):
        mock_is_dir.return_value = True
        organizer = Organizer(directory='valid_dir', rules=self.rules)
        self.assertTrue(organizer.validate())

    @patch('pathlib.Path.is_dir')
    def test_validate_invalid_directory(self, mock_is_dir):
        mock_is_dir.return_value = False
        organizer = Organizer(directory='invalid_dir', rules=self.rules)
        self.assertFalse(organizer.validate())
        organizer.logger.error.assert_called_with("Invalid directory: invalid_dir")

    def test_validate_no_rules(self):
        organizer = Organizer(directory='some_dir', rules=[])
        # Assuming is_dir is True for this test part, or mock it if validation order matters
        with patch('pathlib.Path.is_dir', return_value=True):
            self.assertFalse(organizer.validate())
        organizer.logger.error.assert_called_with("No rules provided")

    # Test get_unique_filename
    @patch('pathlib.Path.exists')
    def test_get_unique_filename_no_collision(self, mock_exists):
        mock_exists.return_value = False
        organizer = Organizer(directory='test_dir', rules=self.rules)
        unique_name = organizer.get_unique_filename(Path('test_dir/Images'), 'file.jpg')
        self.assertEqual(unique_name, 'file.jpg')
        mock_exists.assert_called_once_with(Path('test_dir/Images/file.jpg'))

    @patch('pathlib.Path.exists')
    def test_get_unique_filename_one_collision(self, mock_exists):
        mock_exists.side_effect = [True, False]
        organizer = Organizer(directory='test_dir', rules=self.rules)
        unique_name = organizer.get_unique_filename(Path('test_dir/Images'), 'file.jpg')
        self.assertEqual(unique_name, 'file_1.jpg')
        self.assertEqual(mock_exists.call_count, 2)
        mock_exists.assert_any_call(Path('test_dir/Images/file.jpg'))
        mock_exists.assert_any_call(Path('test_dir/Images/file_1.jpg'))

    @patch('pathlib.Path.exists')
    def test_get_unique_filename_multiple_collisions(self, mock_exists):
        mock_exists.side_effect = [True, True, True, False]
        organizer = Organizer(directory='test_dir', rules=self.rules)
        unique_name = organizer.get_unique_filename(Path('test_dir/Images'), 'file.jpg')
        self.assertEqual(unique_name, 'file_3.jpg')
        self.assertEqual(mock_exists.call_count, 4)

    @patch('pathlib.Path.exists')
    def test_get_unique_filename_multiple_dots_in_name(self, mock_exists):
        mock_exists.side_effect = [True, False]
        organizer = Organizer(directory='test_dir', rules=self.rules)
        unique_name = organizer.get_unique_filename(Path('test_dir/Archives'), 'archive.tar.gz')
        self.assertEqual(unique_name, 'archive.tar_1.gz')

    @patch('pathlib.Path.exists')
    def test_get_unique_filename_no_extension(self, mock_exists):
        mock_exists.side_effect = [True, False] # README exists, README_1 does not
        organizer = Organizer(directory='test_dir', rules=self.rules)
        unique_name = organizer.get_unique_filename(Path('test_dir/Misc'), 'README')
        self.assertEqual(unique_name, 'README_1')
    
    @patch('pathlib.Path.exists')
    def test_get_unique_filename_no_extension_no_collision(self, mock_exists):
        mock_exists.return_value = False
        organizer = Organizer(directory='test_dir', rules=self.rules)
        unique_name = organizer.get_unique_filename(Path('test_dir/Misc'), 'LICENSE')
        self.assertEqual(unique_name, 'LICENSE')


    # Tests for organize_files
    @patch('shutil.move')
    @patch('pathlib.Path')
    def test_organize_files_basic_success(self, MockPath, mock_shutil_move):
        # Setup mock Path object and its methods
        mock_base_dir = MagicMock(spec=Path)
        mock_base_dir.is_dir.return_value = True # For validate()
        
        file1_path = MagicMock(spec=Path)
        file1_path.is_file.return_value = True
        file1_path.suffix = '.jpg'
        file1_path.name = 'image1.jpg'
        file1_path.parent = mock_base_dir
        file1_path.relative_to.return_value = Path('image1.jpg')

        file2_path = MagicMock(spec=Path)
        file2_path.is_file.return_value = True
        file2_path.suffix = '.txt'
        file2_path.name = 'doc1.txt'
        file2_path.parent = mock_base_dir
        file2_path.relative_to.return_value = Path('doc1.txt')

        mock_base_dir.rglob.return_value = [file1_path, file2_path]
        
        # Configure MockPath to return our mock_base_dir when instantiated for the directory
        # And also handle destination path creations
        def path_side_effect(path_arg):
            if str(path_arg) == 'test_dir':
                return mock_base_dir
            # For destination paths, return new mocks that can be configured for `exists`, `mkdir`
            new_mock_path = MagicMock(spec=Path)
            new_mock_path.name = Path(path_arg).name
            new_mock_path.parent = MagicMock(spec=Path) # Parent for mkdir
            new_mock_path.exists.return_value = False # No collisions for simplicity here
            new_mock_path.relative_to.return_value = Path(path_arg).relative_to(mock_base_dir) # simplify
            return new_mock_path

        MockPath.side_effect = path_side_effect
        
        # Mock destination path `exists` for get_unique_filename
        # This requires that when Path('test_dir/Images/image1.jpg') is created, its `exists` is False.
        # The side_effect for MockPath above handles this by returning new mocks with exists=False.

        organizer = Organizer(directory='test_dir', rules=self.rules, recursive=False, dry_run=False)
        organizer.organize_files(self.mock_update_progress, self.mock_update_log, self.mock_update_stats)

        expected_dest1 = Path('test_dir/Images/image1.jpg')
        expected_dest2 = Path('test_dir/Documents/doc1.txt')
        
        mock_shutil_move.assert_any_call(str(file1_path), str(expected_dest1))
        mock_shutil_move.assert_any_call(str(file2_path), str(expected_dest2))
        
        self.mock_update_log.assert_any_call(f"Moved {Path('image1.jpg')} to {Path('Images/image1.jpg')}")
        self.mock_update_log.assert_any_call(f"Moved {Path('doc1.txt')} to {Path('Documents/doc1.txt')}")
        self.mock_update_stats.assert_called_with({'Images': 1, 'Documents': 1, 'Unorganized': 0})
        self.assertEqual(len(organizer.undo_actions), 2)
        self.assertIn((expected_dest1, file1_path), organizer.undo_actions)


    @patch('shutil.move')
    @patch('pathlib.Path')
    def test_organize_files_dry_run(self, MockPath, mock_shutil_move):
        mock_base_dir = MagicMock(spec=Path)
        mock_base_dir.is_dir.return_value = True
        
        file1_path = MagicMock(spec=Path, name="file1_path_mock") # Add name for easier debugging
        file1_path.is_file.return_value = True
        file1_path.suffix = '.png'
        file1_path.name = 'photo.png'
        file1_path.parent = mock_base_dir
        file1_path.relative_to.return_value = Path('photo.png')

        mock_base_dir.rglob.return_value = [file1_path]

        def path_side_effect(path_arg):
            if str(path_arg) == 'test_dir_dry':
                return mock_base_dir
            new_mock_path = MagicMock(spec=Path)
            new_mock_path.name = Path(path_arg).name
            new_mock_path.parent = MagicMock(spec=Path)
            new_mock_path.exists.return_value = False
            # Make relative_to simpler for dry run log check
            if 'Images' in str(path_arg):
                 new_mock_path.relative_to.return_value = Path('Images/photo.png')
            else:
                 new_mock_path.relative_to.return_value = Path(path_arg) # Fallback
            return new_mock_path
            
        MockPath.side_effect = path_side_effect

        organizer = Organizer(directory='test_dir_dry', rules=self.rules, recursive=False, dry_run=True)
        organizer.organize_files(self.mock_update_progress, self.mock_update_log, self.mock_update_stats)

        mock_shutil_move.assert_not_called()
        self.mock_update_log.assert_any_call(f"Would move {Path('photo.png')} to {Path('Images/photo.png')}")
        self.mock_update_stats.assert_called_with({'Images': 1, 'Documents': 0, 'Unorganized': 0})
        self.assertEqual(len(organizer.undo_actions), 0)

    @patch('shutil.move')
    @patch('pathlib.Path')
    def test_organize_files_recursive(self, MockPath, mock_shutil_move):
        mock_base_dir = MagicMock(spec=Path, name="base_dir_mock")
        mock_base_dir.is_dir.return_value = True
        
        mock_subdir = MagicMock(spec=Path, name="subdir_mock")
        # No need for mock_subdir.is_dir(), rglob handles traversal.
        
        file1_path = MagicMock(spec=Path, name="file1_path_mock")
        file1_path.is_file.return_value = True
        file1_path.suffix = '.jpg'
        file1_path.name = 'image_root.jpg'
        file1_path.parent = mock_base_dir # In root
        file1_path.relative_to.return_value = Path('image_root.jpg')

        file2_path = MagicMock(spec=Path, name="file2_path_mock")
        file2_path.is_file.return_value = True
        file2_path.suffix = '.pdf'
        file2_path.name = 'doc_sub.pdf'
        file2_path.parent = mock_subdir # In subdir
        file2_path.relative_to.return_value = Path('sub/doc_sub.pdf') # Relative to base_dir

        mock_base_dir.rglob.return_value = [file1_path, file2_path]

        # Path factory
        path_map = {
            'test_dir_rec': mock_base_dir,
            'test_dir_rec/sub': mock_subdir,
        }

        def path_side_effect(path_arg_str):
            path_arg = str(path_arg_str)
            if path_arg in path_map:
                return path_map[path_arg]
            
            # For destination paths
            new_mock_path = MagicMock(spec=Path, name=f"dest_path_mock_{path_arg}")
            new_mock_path.name = Path(path_arg).name
            # Parent needs to be a mock that can have mkdir called on it
            new_mock_path.parent = MagicMock(spec=Path, name=f"parent_mock_for_{path_arg}")
            new_mock_path.parent.mkdir = MagicMock()
            new_mock_path.exists.return_value = False # No collisions
            
            # Simplify relative_to for destination paths for logging checks
            if 'Images' in path_arg and 'image_root.jpg' in path_arg:
                new_mock_path.relative_to.return_value = Path('Images/image_root.jpg')
            elif 'Documents' in path_arg and 'sub/doc_sub.pdf' in path_arg:
                 new_mock_path.relative_to.return_value = Path('Documents/sub/doc_sub.pdf')
            else:
                 new_mock_path.relative_to.return_value = Path(path_arg) # Fallback
            return new_mock_path

        MockPath.side_effect = path_side_effect
        # Link mock_subdir.parent to mock_base_dir for relative_to calculations if they were more complex
        mock_subdir.parent = mock_base_dir 


        organizer = Organizer(directory='test_dir_rec', rules=self.rules, recursive=True, dry_run=False)
        organizer.organize_files(self.mock_update_progress, self.mock_update_log, self.mock_update_stats)
        
        expected_dest1 = Path('test_dir_rec/Images/image_root.jpg')
        expected_dest2 = Path('test_dir_rec/Documents/sub/doc_sub.pdf')

        mock_shutil_move.assert_any_call(str(file1_path), str(expected_dest1))
        mock_shutil_move.assert_any_call(str(file2_path), str(expected_dest2))
        
        self.mock_update_log.assert_any_call(f"Moved {Path('image_root.jpg')} to {Path('Images/image_root.jpg')}")
        self.mock_update_log.assert_any_call(f"Moved {Path('sub/doc_sub.pdf')} to {Path('Documents/sub/doc_sub.pdf')}")
        self.mock_update_stats.assert_called_with({'Images': 1, 'Documents': 1, 'Unorganized': 0})

    @patch('shutil.move')
    @patch('pathlib.Path')
    def test_organize_files_no_matching_rules(self, MockPath, mock_shutil_move):
        mock_base_dir = MagicMock(spec=Path)
        mock_base_dir.is_dir.return_value = True
        
        file1_path = MagicMock(spec=Path)
        file1_path.is_file.return_value = True
        file1_path.suffix = '.unknown'
        file1_path.name = 'other.unknown'
        file1_path.parent = mock_base_dir
        file1_path.relative_to.return_value = Path('other.unknown')

        mock_base_dir.rglob.return_value = [file1_path]
        
        MockPath.side_effect = lambda p: mock_base_dir if p == 'test_dir_unknown' else MagicMock(exists=False)

        organizer = Organizer(directory='test_dir_unknown', rules=self.rules, recursive=False, dry_run=False)
        organizer.organize_files(self.mock_update_progress, self.mock_update_log, self.mock_update_stats)

        mock_shutil_move.assert_not_called()
        self.mock_update_log.assert_any_call(f"Unrecognized file type: {Path('other.unknown')}")
        self.mock_update_stats.assert_called_with({'Images': 0, 'Documents': 0, 'Unorganized': 1})

    @patch('shutil.move')
    @patch('pathlib.Path')
    def test_organize_files_empty_directory(self, MockPath, mock_shutil_move):
        mock_base_dir = MagicMock(spec=Path)
        mock_base_dir.is_dir.return_value = True
        mock_base_dir.rglob.return_value = [] # Empty directory
        
        MockPath.return_value = mock_base_dir # All Path() calls return this

        organizer = Organizer(directory='test_dir_empty', rules=self.rules)
        organizer.organize_files(self.mock_update_progress, self.mock_update_log, self.mock_update_stats)

        mock_shutil_move.assert_not_called()
        self.mock_update_stats.assert_called_with({'Images': 0, 'Documents': 0, 'Unorganized': 0})
        self.mock_update_log.assert_any_call("Organization complete!") # Or Dry run complete!

    @patch('shutil.move')
    @patch('pathlib.Path')
    def test_organize_files_move_permission_error(self, MockPath, mock_shutil_move):
        mock_base_dir = MagicMock(spec=Path); mock_base_dir.is_dir.return_value = True
        file1_path = MagicMock(spec=Path); file1_path.is_file.return_value = True
        file1_path.suffix = '.jpg'; file1_path.name = 'img.jpg'; file1_path.parent = mock_base_dir
        file1_path.relative_to.return_value = Path('img.jpg')
        
        mock_base_dir.rglob.return_value = [file1_path]
        
        # Path factory for Path() calls
        path_map = {'test_dir_perm': mock_base_dir}
        def path_side_effect(p_str):
            s = str(p_str)
            if s in path_map: return path_map[s]
            # For destination paths
            m = MagicMock(spec=Path); m.name = Path(s).name; m.parent = MagicMock(spec=Path)
            m.exists.return_value = False
            m.relative_to.return_value = Path(s).relative_to(Path('test_dir_perm'))
            path_map[s] = m # cache for consistency if Path(str(dest)) is called multiple times
            return m
        MockPath.side_effect = path_side_effect

        mock_shutil_move.side_effect = PermissionError("Test permission error")

        organizer = Organizer(directory='test_dir_perm', rules=self.rules, dry_run=False)
        organizer.organize_files(self.mock_update_progress, self.mock_update_log, self.mock_update_stats)

        mock_shutil_move.assert_called_once() # It was attempted
        self.mock_update_log.assert_any_call(f"Error: Permission denied for {Path('img.jpg')}. Skipping.")
        self.mock_update_stats.assert_called_with({'Images': 0, 'Documents': 0, 'Unorganized': 1})
        self.assertEqual(len(organizer.undo_actions), 0) # Failed move not added to undo

    # Test get_preview
    @patch('pathlib.Path')
    def test_get_preview_basic(self, MockPath):
        mock_base_dir = MagicMock(spec=Path); mock_base_dir.is_dir.return_value = True
        
        file1 = MagicMock(spec=Path); file1.is_file.return_value = True; file1.suffix = '.png'
        file1.name = 'pic.png'; file1.parent = mock_base_dir
        file1.relative_to.return_value = Path('pic.png')

        file2 = MagicMock(spec=Path); file2.is_file.return_value = True; file2.suffix = '.dat'
        file2.name = 'data.dat'; file2.parent = mock_base_dir
        file2.relative_to.return_value = Path('data.dat')
        
        mock_base_dir.rglob.return_value = [file1, file2]

        path_map = {'test_dir_preview': mock_base_dir}
        def path_side_effect(p_str_arg):
            p_str = str(p_str_arg)
            if p_str in path_map: return path_map[p_str]
            
            m = MagicMock(spec=Path, name=f"DestMock_{Path(p_str).name}")
            m.name = Path(p_str).name
            m.parent = MagicMock(spec=Path)
            m.exists.return_value = False # For unique name generation
            path_map[p_str] = m # Cache for consistency
            return m
        MockPath.side_effect = path_side_effect
        
        organizer = Organizer(directory='test_dir_preview', rules=self.rules)
        preview = organizer.get_preview()

        expected_preview = {
            str(file1): str(Path('test_dir_preview/Images/pic.png')),
            str(file2): "Unorganized"
        }
        self.assertEqual(preview, expected_preview)

    # Test undo
    @patch('shutil.move')
    @patch('pathlib.Path.mkdir') # Mock mkdir for undo's parent.mkdir call
    def test_undo_multiple_actions(self, mock_mkdir, mock_shutil_move):
        organizer = Organizer(directory='any_dir', rules=self.rules) # Not used for undo logic itself
        
        # Mock Path objects for undo_actions
        mock_new_path1 = MagicMock(spec=Path, name="NewPath1")
        mock_new_path1.parent = MagicMock(spec=Path)
        mock_orig_path1 = MagicMock(spec=Path, name="OrigPath1")
        mock_orig_path1.parent = MagicMock(spec=Path)

        mock_new_path2 = MagicMock(spec=Path, name="NewPath2")
        mock_new_path2.parent = MagicMock(spec=Path)
        mock_orig_path2 = MagicMock(spec=Path, name="OrigPath2")
        mock_orig_path2.parent = MagicMock(spec=Path)

        organizer.undo_actions = [
            (mock_new_path1, mock_orig_path1), # new, original
            (mock_new_path2, mock_orig_path2)
        ]
        
        organizer.undo()

        mock_shutil_move.assert_has_calls([
            call(str(mock_new_path2), str(mock_orig_path2)), # Reverse order
            call(str(mock_new_path1), str(mock_orig_path1))
        ])
        # Check that original_path.parent.mkdir was called
        mock_orig_path2.parent.mkdir.assert_called_with(parents=True, exist_ok=True)
        mock_orig_path1.parent.mkdir.assert_called_with(parents=True, exist_ok=True)

        self.assertEqual(len(organizer.undo_actions), 0)

    @patch('shutil.move')
    def test_undo_empty_list(self, mock_shutil_move):
        organizer = Organizer(directory='any', rules=self.rules)
        organizer.undo_actions = []
        organizer.undo()
        mock_shutil_move.assert_not_called()

    @patch('shutil.move')
    @patch('pathlib.Path.mkdir')
    def test_undo_move_error(self, mock_mkdir, mock_shutil_move):
        organizer = Organizer(directory='any', rules=self.rules)
        
        mock_new_path1 = MagicMock(spec=Path); mock_new_path1.parent = MagicMock()
        mock_orig_path1 = MagicMock(spec=Path); mock_orig_path1.parent = MagicMock()
        
        organizer.undo_actions = [(mock_new_path1, mock_orig_path1)]
        mock_shutil_move.side_effect = OSError("Failed to move back")
        
        with patch.object(organizer.logger, 'error') as mock_logger_error:
            organizer.undo()
            mock_logger_error.assert_called_once_with(f"Error undoing move from {mock_new_path1} to {mock_orig_path1}: Failed to move back")
        
        self.assertEqual(len(organizer.undo_actions), 0) # Still clears list


if __name__ == '__main__':
    unittest.main()
