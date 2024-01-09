import sys
import os
import warnings  # Add this line

# Suppress DeprecationWarnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from PyQt5.QtCore import QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices, QColor
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QWidget,
    QCheckBox,
    QDialog,
    QLabel,
    QLineEdit,
    QFormLayout,
    QComboBox,
)


class StyledButton(QPushButton):
    def __init__(self, text, color, parent=None):
        super(StyledButton, self).__init__(text, parent)
        self.setStyleSheet(f"QPushButton {{ background-color: {color}; color: white; }}")

class DuplicateScannerThread(QThread):
    scan_complete = pyqtSignal(list)

    def __init__(self, folder, file_types, size_threshold, include_hidden):
        super().__init__()
        self.folder = folder
        self.file_types = file_types
        self.size_threshold = size_threshold
        self.include_hidden = include_hidden

    def run(self):
        files = self.list_files(self.folder)
        duplicates = self.find_duplicates(files)
        self.scan_complete.emit(duplicates)

    def list_files(self, folder):
        files = []
        for root, _, filenames in os.walk(folder):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                # Skip hidden files if include_hidden is False
                if not self.include_hidden and filename.startswith("."):
                    continue
                # Skip files with unsupported extensions
                if self.file_types and not any(file_path.lower().endswith(ext) for ext in self.file_types):
                    continue
                files.append(file_path)
        return files

    def find_duplicates(self, files):
        seen = {}
        duplicates = []
        for file in files:
            try:
                file_size = os.path.getsize(file)
            except OSError as e:
                print(f"Error accessing file {file}: {e}")
                continue

            if file_size in seen:
                seen[file_size].append(file)
            else:
                seen[file_size] = [file]

        for size, file_list in seen.items():
            if len(file_list) > 1:
                duplicates.append(file_list)
        return duplicates


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("Advanced Options")

        layout = QFormLayout()

        self.file_types_label = QLabel("File Types:")
        self.file_types_combobox = QComboBox()
        self.file_types_combobox.setEditable(True)
        self.file_types_combobox.addItems(["", "txt", "pdf", "jpg", "png", "docx", "xlsx"])  # Add commonly used file types
        layout.addRow(self.file_types_label, self.file_types_combobox)

        self.size_threshold_label = QLabel("Size Threshold (in bytes):")
        self.size_threshold_edit = QLineEdit()
        layout.addRow(self.size_threshold_label, self.size_threshold_edit)

        self.include_hidden_label = QLabel("Include Hidden Files:")
        self.include_hidden_checkbox = QCheckBox()
        layout.addRow(self.include_hidden_label, self.include_hidden_checkbox)

        self.ok_button = StyledButton("OK", "#4CAF50")  # Green color
        self.ok_button.clicked.connect(self.accept)

        self.cancel_button = StyledButton("Cancel", "#e53935")  # Red color
        self.cancel_button.clicked.connect(self.reject)

        layout.addRow(self.ok_button, self.cancel_button)

        self.setLayout(layout)


class DuplicateFinderApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Duplicate Finder App")

        # Create a layout
        layout = QVBoxLayout()

        # Create a button for folder selection
        folder_button = StyledButton("Select Folders", "#2196F3")  # Blue color
        folder_button.clicked.connect(self.select_folders)
        layout.addWidget(folder_button)

        # Create a button for starting the scan
        scan_button = StyledButton("Start Scan", "#4CAF50")  # Green color
        scan_button.clicked.connect(self.start_scan)
        layout.addWidget(scan_button)

        # Create a list widget for displaying results
        self.result_list = QListWidget()
        layout.addWidget(self.result_list)

        # Create a sorting combo box
        self.sorting_combobox = QComboBox()
        self.sorting_combobox.addItems(["No Sorting", "File Name", "File Size", "Modification Date"])
        layout.addWidget(self.sorting_combobox)

        # Create a button for deleting duplicates
        delete_button = StyledButton("Delete Selected Duplicates", "#e53935")  # Red color
        delete_button.clicked.connect(self.delete_duplicates)
        layout.addWidget(delete_button)

        # Create a button for file preview
        preview_button = StyledButton("Preview Selected File", "#FFC107")  # Yellow color
        preview_button.clicked.connect(self.preview_file)
        layout.addWidget(preview_button)

        # Create a button for advanced options
        settings_button = StyledButton("Advanced Options", "#795548")  # Brown color
        settings_button.clicked.connect(self.show_advanced_options)
        layout.addWidget(settings_button)

        # Set the central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # List to store duplicate files and their corresponding items and checkboxes
        self.duplicate_files = []

        # Thread for scanning duplicates
        self.scan_thread = None

        # Default settings
        self.file_types = []
        self.size_threshold = None
        self.include_hidden = False

        # List to store selected folders
        self.selected_folders = []

    def select_folders(self):
        folders = QFileDialog.getExistingDirectory(self, "Select Folders", ".", QFileDialog.ShowDirsOnly | QFileDialog.ReadOnly)
        if folders:
            self.selected_folders = folders.split(";")
            print(f"Selected Folders: {self.selected_folders}")
        else:
            print("Folder selection canceled.")
            self.result_list.clear()
            self.result_list.addItem("Folder selection canceled. Please select folders.")

    def start_scan(self):
        if self.selected_folders:
            self.result_list.clear()
            self.duplicate_files.clear()

            for folder in self.selected_folders:
                # Create and start the scanning thread with advanced options
                self.scan_thread = DuplicateScannerThread(
                    folder=folder,
                    file_types=self.file_types,
                    size_threshold=self.size_threshold,
                    include_hidden=self.include_hidden
                )
                self.scan_thread.scan_complete.connect(self.display_duplicates)
                self.scan_thread.start()
        else:
            self.result_list.clear()
            self.result_list.addItem("Please select folders first.")

    def display_duplicates(self, duplicates):
        if duplicates:
            # Sort the duplicates based on the selected criterion
            sorting_criterion = self.sorting_combobox.currentText()
            duplicates = self.sort_duplicates(duplicates, sorting_criterion)

            for index, duplicate_set in enumerate(duplicates):
                self.result_list.addItem(f"Set {index + 1}:")

                for file in duplicate_set:
                    item = QListWidgetItem(f" - {file}")
                    checkbox = QCheckBox()  # Checkbox for selecting files
                    self.result_list.addItem(item)
                    self.result_list.setItemWidget(item, checkbox)
                    self.duplicate_files.append((item, file, checkbox))
        else:
            self.result_list.addItem("No duplicate files found.")

    def sort_duplicates(self, duplicates, criterion):
        if criterion == "File Name":
            return sorted(duplicates, key=lambda x: os.path.basename(x[0]))
        elif criterion == "File Size":
            return sorted(duplicates, key=lambda x: os.path.getsize(x[0]))
        elif criterion == "Modification Date":
            return sorted(duplicates, key=lambda x: os.path.getmtime(x[0]))
        else:
            return duplicates

    def delete_duplicates(self):
        selected_items = self.get_selected_items()
        if selected_items:
            # Display the confirmation dialog
            confirm_dialog = self.create_delete_confirmation_dialog(selected_items)
            result = confirm_dialog.exec_()

            if result == QMessageBox.Yes:
                # User confirmed deletion
                for item, file_path, checkbox in selected_items:
                    try:
                        os.remove(file_path)
                    except OSError as e:
                        print(f"Error deleting file {file_path}: {e}")

                self.result_list.clear()
                self.start_scan()  # Re-scan the folder after deletion
                self.result_list.addItem("Selected duplicates deleted.")
            else:
                self.result_list.addItem("Deletion canceled.")
        else:
            self.result_list.addItem("Please select a duplicate to delete.")

    def create_delete_confirmation_dialog(self, selected_items):
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Warning)
        dialog.setWindowTitle("Confirmation Dialog")
        dialog.setText("Are you sure you want to delete the selected duplicates?")

        # Display a summary of selected duplicates
        summary_text = "Selected Duplicates:\n"
        for _, file_path, _ in selected_items:
            summary_text += f"\n- {file_path}"

        dialog.setDetailedText(summary_text)

        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dialog.setDefaultButton(QMessageBox.No)

        return dialog

    def get_selected_items(self):
        selected_items = []
        for index in range(self.result_list.count()):
            item = self.result_list.item(index)
            file_path = item.text()[3:]  # Remove the leading " - " from the file path
            checkbox = self.result_list.itemWidget(item)
            if checkbox is not None and checkbox.isChecked():
                selected_items.append((item, file_path, checkbox))
        return selected_items

    def preview_file(self):
        selected_items = self.get_selected_items()
        if selected_items:
            _, file_path, _ = selected_items[0]  # Preview the first selected file
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        else:
            self.result_list.addItem("Please select a file to preview.")

    def show_advanced_options(self):
        # Show the advanced options dialog
        dialog = SettingsDialog(self)
        result = dialog.exec_()

        # If the user clicks OK, update the settings
        if result == QDialog.Accepted:
            self.file_types = [ext.strip() for ext in dialog.file_types_combobox.currentText().split(",")]
            self.size_threshold = int(dialog.size_threshold_edit.text()) if dialog.size_threshold_edit.text() else None
            self.include_hidden = dialog.include_hidden_checkbox.isChecked()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DuplicateFinderApp()
    window.show()
    sys.exit(app.exec_())