# File Organizer

A powerful and user-friendly PyQt6-based File Organizer application designed to help you keep your files organized effortlessly.

## Features

- **Intelligent File Organization**: Automatically organize files based on customizable rules.
- **Flexible Rule Management**: Create, edit, and delete organization rules with ease.
- **Preview Functionality**: Preview how files will be organized before making any changes.
- **Recursive Organization**: Option to organize files in subdirectories.
- **Dry Run Mode**: Test your organization rules without actually moving files.
- **Undo Capability**: Easily undo the last organization action.
- **Scheduled Organization**: Set up automatic file organization on a schedule.
- **Dark Mode**: Toggle between light and dark themes for comfortable use in any lighting condition.
- **Multilingual Support**: Use the application in English, Spanish, French, or Japanese.
- **Export/Import Rules**: Share your organization rules or use them across different machines.
- **Detailed Logging**: Keep track of all file movements and actions taken.
- **Statistics**: View statistics on how many files were organized into each category.

## Installation

1. Ensure you have Python 3.9 or higher installed on your system.
2. Clone this repository:
   ```
   git clone https://github.com/yourusername/file-organizer.git
   cd file-organizer
   ```
3. Install the required dependencies:
   ```
   pip install poetry
   poetry install
   ```

## Getting Started

Follow these steps to quickly set up and run your first file organization task:

1. Launch the application:
   ```
   poetry run python src/main.py
   ```

2. In the main window, click on the "Rules" tab.

3. Click the "Add Rule" button to create your first organization rule:
   - Name the rule (e.g., "Images")
   - Add file extensions for this rule (e.g., .jpg, .png, .gif)
   - Click "OK" to save the rule

4. Switch to the "Organize" tab.

5. Click "Select Directory" and choose a folder you want to organize.

6. (Optional) Check the "Recursive" box if you want to include subdirectories.

7. Click "Preview Organization" to see how your files will be organized based on the rule you created.

8. If you're satisfied with the preview, click "Organize Files" to run the organization process.

9. Check the "Statistics" tab to see a summary of how many files were organized.

Congratulations! You've just organized your first set of files with File Organizer.

## Detailed Usage

1. Run the application:
   ```
   poetry run python src/main.py
   ```

2. Select the directory you want to organize using the "Select Directory" button.

3. Configure your organization rules in the "Rules" tab:
   - Click "Add Rule" to create a new rule.
   - Enter a name for the rule and specify file extensions (e.g., .jpg, .png for images).
   - Use "Remove Rule" to delete unwanted rules.

4. Optional: Set up a schedule for automatic organization in the "Schedule" tab.

5. In the "Organize" tab:
   - Check "Recursive" if you want to include subdirectories.
   - Check "Dry Run" to preview changes without moving files.
   - Click "Preview Organization" to see how files will be organized.
   - Click "Organize Files" to start the organization process.

6. Use the "Undo Last Organization" button if you need to revert the last organization action.

7. View statistics about organized files in the "Statistics" tab.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Testing

Before using the File Organizer in a production environment, it's recommended to thoroughly test all features to ensure they work as expected. Here are some suggested test scenarios:

1. Create multiple rules with different file extensions and test the organization process.
2. Test the recursive organization feature with nested directories.
3. Use the preview functionality and verify that it accurately represents the expected file movements.
4. Test the undo feature to ensure it correctly reverts the last organization action.
5. Try the dark mode and verify that all UI elements are visible and properly styled.
6. Test the application with different languages to ensure all text is properly translated.
7. Export and import rules to verify that this feature works correctly.
8. Set up a schedule and verify that the automatic organization runs as expected.
9. Test the dry run mode to ensure no files are actually moved.
10. Verify that the statistics are accurately updated after each organization process.

If you encounter any issues during testing, please report them in the GitHub issue tracker.
