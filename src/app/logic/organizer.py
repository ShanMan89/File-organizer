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

    def _get_file_destination(self, file_path: Path) -> Tuple[str, Path | None]:
        """
        Determines the destination path for a given file based on organization rules.
        This method does not perform any file system operations (like creating directories).

        :param file_path: The path to the file.
        :return: A tuple containing the rule name (or "Unorganized") and the destination Path (or None).
        """
        relative_path = file_path.relative_to(self.directory)
        file_ext = file_path.suffix.lower()

        for rule in self.rules:
            if file_ext in rule.extensions:
                destination_folder = self.directory / rule.name
                # Preserve subdirectory structure within the rule folder
                destination_path = destination_folder / relative_path
                
                unique_filename = self.get_unique_filename(destination_path.parent, destination_path.name)
                unique_destination_path = destination_path.parent / unique_filename
                return rule.name, unique_destination_path
        
        return "Unorganized", None

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

        :param destination: Destination directory (parent of the file)
        :param filename: Original filename
        :return: Unique filename
        """
        # Ensure filename is just the name, not part of the path
        filename_only = Path(filename).name
        base, extension = filename_only.rsplit('.', 1) if '.' in filename_only else (filename_only, '')
        
        counter = 1
        # Construct the full path for checking existence
        current_filename_to_check = filename_only
        while (destination / current_filename_to_check).exists():
            if extension:
                current_filename_to_check = f"{base}_{counter}.{extension}"
            else:
                current_filename_to_check = f"{base}_{counter}"
            counter += 1
        return current_filename_to_check

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

        files_to_process = [f for f in self.directory.rglob('*') if f.is_file()]
        total_files = len(files_to_process)
        processed_files_count = 0

        for file_path in files_to_process:
            try:
                if not self.recursive and file_path.parent != self.directory:
                    # This file is in a subdirectory but recursive is off.
                    # We still count it as "processed" for progress bar accuracy.
                    # But it won't be organized or marked as "Unorganized" by rule matching logic.
                    # If it needs to be counted as Unorganized, that logic would need adjustment.
                    # For now, it's just skipped from organization.
                    pass # Will be handled by processed_files_count increment in finally
                else:
                    rule_name, destination = self._get_file_destination(file_path)
                    original_relative_path = file_path.relative_to(self.directory)

                    if destination:
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        relative_dest_path = destination.relative_to(self.directory)

                        if not self.dry_run:
                            try:
                                shutil.move(str(file_path), str(destination))
                                self.undo_actions.append((destination, file_path))
                                update_log(f"Moved {original_relative_path} to {relative_dest_path}")
                                stats[rule_name] += 1
                            except FileNotFoundError:
                                self.logger.error(f"Error: File not found {file_path} when trying to move to {destination}. Skipping.")
                                update_log(f"Error: File not found {original_relative_path}. Skipping.")
                                stats['Unorganized'] += 1
                            except PermissionError:
                                self.logger.error(f"Error: Permission denied for {file_path} or when moving to {destination}. Skipping.")
                                update_log(f"Error: Permission denied for {original_relative_path}. Skipping.")
                                stats['Unorganized'] += 1
                            except OSError as e:
                                self.logger.error(f"Error moving file {file_path} to {destination}: {e}. Skipping.")
                                update_log(f"Error moving file {original_relative_path}: {e}. Skipping.")
                                stats['Unorganized'] += 1
                        else: # dry_run
                            update_log(f"Would move {original_relative_path} to {relative_dest_path}")
                            stats[rule_name] += 1
                    else: # rule_name is "Unorganized", destination is None
                        update_log(f"Unrecognized file type: {original_relative_path}")
                        stats[rule_name] += 1 # This will be stats['Unorganized']
            
            except Exception as e:
                self.logger.error(f"An unexpected error occurred while processing {file_path}: {str(e)}")
                update_log(f"An unexpected error occurred while processing {file_path.name}: {str(e)}. Skipping.")
                if 'Unorganized' not in stats: stats['Unorganized'] = 0 # Ensure key exists
                stats['Unorganized'] += 1
            finally:
                processed_files_count += 1
                if total_files > 0:
                    progress = int(processed_files_count / total_files * 100)
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
                # Ensure parent directory of original path exists before moving back
                original_path.parent.mkdir(parents=True, exist_ok=True)
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

        files_to_preview = [f for f in self.directory.rglob('*') if f.is_file()]

        for file_path in files_to_preview:
            try:
                if not self.recursive and file_path.parent != self.directory:
                    # Skip files in subdirectories if not recursive
                    # These files won't appear in the preview as neither organized nor unorganized by rule.
                    # Or, they could be explicitly marked as "Skipped (not recursive)".
                    # For now, just skipping them from preview.
                    continue 

                _, destination = self._get_file_destination(file_path) 

                if destination:
                    preview[str(file_path)] = str(destination)
                else:
                    preview[str(file_path)] = "Unorganized"
            except Exception as e:
                self.logger.error(f"Error generating preview for {file_path}: {str(e)}")
                preview[str(file_path)] = f"Error processing: {e}"

        return preview
