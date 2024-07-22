import sys
import os
import shutil
import time
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton,
                             QStackedWidget, QMessageBox, QDialog, QFormLayout, QDialogButtonBox)
from PyQt5.QtCore import QTimer

# Folder Counter Logic
MAX_DEPTH = 2

def create_numbered_folders(root_folder):
    folder_counter = {"G": 1, "D": 1}

    for parent_dir, _, files in os.walk(root_folder):
        depth = parent_dir[len(root_folder):].count(os.path.sep)
        if depth > MAX_DEPTH or depth != 2:
            continue

        folder_type = parent_dir.split()[-1][0]
        existing_folders = [folder for folder in os.listdir(parent_dir) if folder.startswith((folder_type))]
        existing_numbers = [int(folder[1:]) for folder in existing_folders if folder[1:].isdigit()]
        max_existing_number = max(existing_numbers) if existing_numbers else 0
        current_counter = max(folder_counter.get(folder_type, 1), max_existing_number + 1)

        folder_prefix = "G" if folder_type == "G" else "D"
        new_folder_name = f"{folder_prefix}{current_counter:02d}"
        new_folder_path = os.path.join(parent_dir, new_folder_name)

        if os.path.exists(new_folder_path):
            shutil.rmtree(new_folder_path)

        os.makedirs(new_folder_path)
        folder_counter[folder_type] = current_counter + 1

# QC Server Logic
def find_completed_parent_folder(incoming_path, completed_path, prefix):
    for root, dirs, files in os.walk(incoming_path):
        if prefix in dirs:
            relative_path = os.path.relpath(root, incoming_path)
            return os.path.join(completed_path, relative_path)
    return None

def copy_images_to_completed(source, destination):
    for file in os.listdir(source):
        if file.lower().endswith(".jpg"):
            source_file = os.path.join(source, file)
            destination_file = os.path.join(destination, file)
            shutil.copy2(source_file, destination_file)

def move_folders_and_copy_images(incoming_path, completed_path, processed_path, done_path):
    error_path = os.path.join(processed_path, "_Error")
    for processed_folder in os.listdir(processed_path):
        processed_folder_path = os.path.join(processed_path, processed_folder)
        if os.path.isdir(processed_folder_path):
            if processed_folder == "_Error":
                continue

            words = processed_folder.split()[:1]
            prefix = ' '.join(words)
            completed_parent_folder = find_completed_parent_folder(incoming_path, completed_path, prefix)

            if not completed_parent_folder:
                words = processed_folder.split()[:2]
                prefix = ' '.join(words)
                completed_parent_folder = find_completed_parent_folder(incoming_path, completed_path, prefix)

            if completed_parent_folder:
                copy_images_to_completed(processed_folder_path, completed_parent_folder)
                try:
                    shutil.move(processed_folder_path, done_path)
                    shutil.rmtree(os.path.join(completed_parent_folder, processed_folder), ignore_errors=True)
                    print("Program Executed Successfully...")
                except Exception as e:
                    os.makedirs(error_path, exist_ok=True)
                    shutil.move(processed_folder_path, error_path)
                    print(f"An error occurred: {e}")
            else:
                try:
                    os.makedirs(error_path, exist_ok=True)
                    shutil.move(processed_folder_path, error_path)
                    print(f"Warning: {processed_folder} diskip, Folder tidak ada di incoming!.")
                except Exception as e:
                    print(f"An error occurred: {e}")

class LoginPage(QWidget):
    def __init__(self, parent=None):
        super(LoginPage, self).__init__(parent)
        self.parent_widget = parent

        layout = QVBoxLayout()
        self.id_label = QLineEdit(self)
        self.id_label.setPlaceholderText("ID Admin")
        layout.addWidget(self.id_label)

        self.password_label = QLineEdit(self)
        self.password_label.setPlaceholderText("Password Admin")
        self.password_label.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_label)

        self.login_button = QPushButton("Login", self)
        self.login_button.clicked.connect(self.login)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def login(self):
        if self.id_label.text() == "admin" and self.password_label.text() == "admin":
            self.parent_widget.switch_to_path_dialog()
        else:
            self.show_error_message()

    def show_error_message(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Coba lagi")
        msg.setWindowTitle("Login Failed")
        msg.exec_()

class PathDialog(QWidget):
    def __init__(self, parent=None):
        super(PathDialog, self).__init__(parent)
        self.setWindowTitle("Edit QC Server Paths")
        layout = QFormLayout()

        self.incoming_path_edit = QLineEdit("")
        layout.addRow("Incoming Path:", self.incoming_path_edit)

        self.completed_path_edit = QLineEdit("")
        layout.addRow("Completed Path:", self.completed_path_edit)

        self.processed_path_edit = QLineEdit("")
        layout.addRow("Processed Path:", self.processed_path_edit)

        self.done_path_edit = QLineEdit("")
        layout.addRow("Done Path:", self.done_path_edit)

        self.start_qc_server_button = QPushButton("Start QC Server")
        self.start_qc_server_button.clicked.connect(self.start_qc_server)
        layout.addRow(self.start_qc_server_button)

        self.setLayout(layout)

    def start_qc_server(self):
        incoming_path = self.incoming_path_edit.text()
        completed_path = self.completed_path_edit.text()
        processed_path = self.processed_path_edit.text()
        done_path = self.done_path_edit.text()

        move_folders_and_copy_images(incoming_path, completed_path, processed_path, done_path)
        print("QC Server started.")

class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.stacked_widget = QStackedWidget(self)
        self.login_page = LoginPage(self)
        self.path_dialog = PathDialog(self)
        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.path_dialog)

        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

        self.login_page.login_button.clicked.connect(self.handle_login)

    def handle_login(self):
        if self.login_page.id_label.text() == "admin" and self.login_page.password_label.text() == "admin":
            self.switch_to_path_dialog()
        else:
            self.login_page.show_error_message()

    def switch_to_path_dialog(self):
        self.stacked_widget.setCurrentWidget(self.path_dialog)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
