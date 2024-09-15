# tests/mocks/mock_filesystem.py

import os
from unittest.mock import MagicMock

def mock_os_walk(directory):
    # Define your mock directory structure here
    return [
        (directory, ('subdir',), ('file1.jpg', 'file2.pdf', 'file3.unknown')),
        (os.path.join(directory, 'subdir'), (), ('file4.png',)),
    ]
