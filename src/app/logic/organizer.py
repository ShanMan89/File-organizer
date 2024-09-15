# src/app/logic/organizer.py

import shutil
import logging
from typing import List, Callable, Dict, Tuple
from pathlib import Path
from app.models.rule import Rule

class Organizer:
    def __init__(self, directory: str, rules: List[Rule], recursive: bool = False, dry_run: bool = False):
        """
        Initialize the Organizer.

        :param directory: The directory to organize
        :param rules: List of organization rules
        :param recursive: Whether to organize subdirectories
        :param dry_run: If True, don't actually move files
        """
        self.directory = Path(directory)
        self.rules = rules
        self.recursive = recursive
        self.dry_run = dry_run
        self.undo_actions: List[Tuple[Path, Path]] = []
        self.logger = logging.getLogger(__name__)

    def validate(self) -> bool:
        """
        Validate the directory and rules.

        :return: True if valid, False otherwise
        """
        if not self.directory.is_dir():
            self.logger.error(f"Invalid directory: {self.directory}")
            return False
        if not self.rules:
            self.logger.error("No rules provided")
            return False
        return True

    def get_unique_filename(self, destination: Path, filename: str) -> str:
        """
        Get a unique filename for the destination.

        :param destination: Destination directory
        :param filename: Original filename
        :return: Unique filename
        """
        base, extension = filename.rsplit('.', 1)
        counter = 1
        while (destination / filename).exists():
            filename = f"{base}_{counter}.{extension}"
            counter += 1
        return filename

    def organize_files(self, update_progress: Callable[[int], None], update_log: Callable[[str], None], update_stats: Callable[[Dict[str, int]], None]) -> None:
        """
        Organize files based on the given rules.

        :param update_progress: Callback to update progress
        :param update_log: Callback to update log
        :param update_stats: Callback to update stats
        """
        if not self.validate():
            update_log("Validation failed. Please check your directory and rules.")
            return

        stats = {rule.name: 0 for rule in self.rules}
        stats['Unorganized'] = 0

        total_files = sum(1 for _ in self.directory.rglob('*') if _.is_file())
        processed_files = 0

        for file_path in self.directory.rglob('*'):
            if file_path.is_file():
                try:
                    relative_path = file_path.relative_to(self.directory)
                    
                    if not self.recursive and file_path.parent != self.directory:
                        continue

                    file_ext = file_path.suffix.lower()
                    for rule in self.rules:
                        if file_ext in rule.extensions:
                            destination_folder = self.directory / rule.name
                            destination = destination_folder / relative_path
                            destination.parent.mkdir(parents=True, exist_ok=True)
                            
                            unique_filename = self.get_unique_filename(destination.parent, destination.name)
                            destination = destination.parent / unique_filename
                            
                            if not self.dry_run:
                                shutil.move(str(file_path), str(destination))
                                self.undo_actions.append((destination, file_path))
                                update_log(f"Moved {relative_path} to {destination.relative_to(self.directory)}")
                            else:
                                update_log(f"Would move {relative_path} to {destination.relative_to(self.directory)}")
                            stats[rule.name] += 1
                            break
                    else:
                        update_log(f"Unrecognized file type: {relative_path}")
                        stats['Unorganized'] += 1
                except Exception as e:
                    self.logger.error(f"Error processing {file_path}: {str(e)}")
                    update_log(f"Error processing {file_path}: {str(e)}")

                processed_files += 1
                progress = int(processed_files / total_files * 100)
                update_progress(progress)

        if not self.dry_run:
            update_log("Organization complete!")
        else:
            update_log("Dry run complete. No files were actually moved.")

        update_stats(stats)

    def undo(self) -> None:
        """
        Undo the last organization action.
        """
        if not self.undo_actions:
            self.logger.info("No actions to undo")
            return

        for new_path, original_path in reversed(self.undo_actions):
            try:
                shutil.move(str(new_path), str(original_path))
                self.logger.info(f"Moved {new_path} back to {original_path}")
            except Exception as e:
                self.logger.error(f"Error undoing move from {new_path} to {original_path}: {str(e)}")

        self.undo_actions.clear()

    def get_preview(self) -> Dict[str, str]:
        """
        Get a preview of how files would be organized.

        :return: A dictionary with current file paths as keys and new file paths as values
        """
        preview = {}
        if not self.validate():
            self.logger.error("Validation failed. Please check your directory and rules.")
            return preview

        for file_path in self.directory.rglob('*'):
            if file_path.is_file():
                try:
                    relative_path = file_path.relative_to(self.directory)
                    
                    if not self.recursive and file_path.parent != self.directory:
                        continue

                    file_ext = file_path.suffix.lower()
                    for rule in self.rules:
                        if file_ext in rule.extensions:
                            destination_folder = self.directory / rule.name
                            destination = destination_folder / relative_path
                            
                            unique_filename = self.get_unique_filename(destination.parent, destination.name)
                            destination = destination.parent / unique_filename
                            
                            preview[str(file_path)] = str(destination)
                            break
                    else:
                        preview[str(file_path)] = "Unorganized"
                except Exception as e:
                    self.logger.error(f"Error processing {file_path}: {str(e)}")

        return preview
