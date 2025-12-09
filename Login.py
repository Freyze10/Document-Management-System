import sys
import hashlib
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, \
    QPushButton, QLabel, QFormLayout, QStackedWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from db import db_con
from alert import window_alert
import Main
from utils import abs_path


class AuthWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Document Management System - Login")
        self.resize(600, 450)
        self.setWindowIcon(QIcon(abs_path.resource("img/icon.ico")))
        db_con.create_tables()
        db_dr.create_delivery_legacy_tables()

        # Main layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(30, 30, 30, 30)

        # Logo
        self.logo_label = QLabel()
        self.logo_label.setPixmap(QIcon(abs_path.resource("img/logo.png")).pixmap(120, 120))
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.logo_label)

        # Stacked widget for Login and Signup
        self.stacked_widget = QStackedWidget()

        # Login widget
        self.login_container = QWidget()
        self.login_container.setProperty("class", "form_container")
        self.login_layout = QVBoxLayout()
        self.login_layout.setSpacing(15)
        self.login_layout.setContentsMargins(20, 20, 20, 20)

        # Login label
        self.login_title = QLabel("Login")
        self.login_title.setProperty("class", "form_title")
        self.login_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.login_layout.addWidget(self.login_title)

        # Login form
        self.login_form_layout = QFormLayout()
        self.login_form_layout.setSpacing(10)
        self.login_username_input = QLineEdit()
        self.login_username_input.setPlaceholderText("Enter username")
        self.login_password_input = QLineEdit()
        self.login_password_input.setPlaceholderText("Enter password")
        self.login_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_form_layout.addRow(QLabel("Username:"), self.login_username_input)
        self.login_form_layout.addRow(QLabel("Password:"), self.login_password_input)

        # Connect returnPressed signal to handle_login for both inputs
        self.login_username_input.returnPressed.connect(self.handle_login)
        self.login_password_input.returnPressed.connect(self.handle_login)

        self.login_btn = QPushButton("Login")
        self.login_btn.setProperty("class", "auth_btn")
        self.login_btn.clicked.connect(self.handle_login)
        self.login_form_layout.addRow(self.login_btn)

        # Signup link (as button)
        self.signup_link = QPushButton("Don't have an account? Sign Up")
        self.signup_link.setProperty("class", "link_button")
        self.signup_link.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.login_form_layout.addRow(self.signup_link)

        self.login_layout.addLayout(self.login_form_layout)
        self.login_container.setLayout(self.login_layout)
        self.stacked_widget.addWidget(self.login_container)

        # Signup widget
        self.signup_container = QWidget()
        self.signup_container.setProperty("class", "form_container")
        self.signup_layout = QVBoxLayout()
        self.signup_layout.setSpacing(5)
        self.signup_layout.setContentsMargins(20, 20, 20, 20)

        # Signup label
        self.signup_title = QLabel("Signup")
        self.signup_title.setProperty("class", "form_title")
        self.signup_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.signup_layout.addWidget(self.signup_title)

        # Signup form
        self.signup_form_layout = QFormLayout()
        self.signup_form_layout.setSpacing(10)
        self.signup_username_input = QLineEdit()
        self.signup_username_input.setPlaceholderText("Enter username")
        self.signup_password_input = QLineEdit()
        self.signup_password_input.setPlaceholderText("Enter password")
        self.signup_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.signup_confirm_password_input = QLineEdit()
        self.signup_confirm_password_input.setPlaceholderText("Confirm password")
        self.signup_confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.signup_form_layout.addRow(QLabel("Username:"), self.signup_username_input)
        self.signup_form_layout.addRow(QLabel("Password:"), self.signup_password_input)
        self.signup_form_layout.addRow(QLabel("Confirm Password:"), self.signup_confirm_password_input)

        # Connect returnPressed signal to handle_signup for all signup inputs
        self.signup_username_input.returnPressed.connect(self.handle_signup)
        self.signup_password_input.returnPressed.connect(self.handle_signup)
        self.signup_confirm_password_input.returnPressed.connect(self.handle_signup)

        self.signup_btn = QPushButton("Sign Up")
        self.signup_btn.setProperty("class", "auth_btn")
        self.signup_btn.clicked.connect(self.handle_signup)
        self.signup_form_layout.addRow(self.signup_btn)

        # Back to Login button
        self.back_to_login_btn = QPushButton("Back to Login")
        self.back_to_login_btn.setProperty("class", "auth_btn")
        self.back_to_login_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.signup_form_layout.addRow(self.back_to_login_btn)

        self.signup_layout.addLayout(self.signup_form_layout)
        self.signup_container.setLayout(self.signup_layout)
        self.stacked_widget.addWidget(self.signup_container)

        # Add stacked widget to main layout
        self.main_layout.addWidget(self.stacked_widget)
        self.main_layout.addStretch()

        # Set central widget
        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

        # Apply styles
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e6f0fa, stop:1 #ffffff);
                border-radius: 8px;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
            }
            QWidget[class="form_container"] {
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                padding: 10px;
            }
            QLabel[class="form_title"] {
                font-size: 28px;
                font-weight: bold;
                color: #1a3c6c;
                padding: 10px 0;
            }
            QLineEdit {
                font-size: 14px;
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                background-color: #ffffff;
                min-height: 32px;
            }
            QLineEdit:focus {
                border: 1px solid #4a90e2;
                background-color: #f8fafc;
                box-shadow: 0 0 4px rgba(74, 144, 226, 0.3);
            }
            QLineEdit::placeholder {
                color: #6b7280;
                font-style: italic;
            }
            QLabel {
                font-size: 14px;
                color: #1a3c6c;
                font-weight: 500;
            }
            QPushButton[class="auth_btn"] {
                background-color: #4CAF50;
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                min-width: 100px;
                min-height: 36px;
            }
            QPushButton[class="auth_btn"]:hover {
                background-color: #45a049;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            QPushButton[class="auth_btn"]:pressed {
                background-color: #388e3c;
            }
            QPushButton[class="auth_btn"]:focus {
                outline: none;
                border: 2px solid #4a90e2;
            }
            QPushButton[class="link_button"] {
                background: none;
                color: #1a73e8;
                font-size: 14px;
                font-weight: 500;
                border: none;
                text-align: left;
                padding: 8px 0;
            }
            QPushButton[class="link_button"]:hover {
                text-decoration: underline;
                color: #005a9e;
            }
            QPushButton[class="link_button"]:pressed {
                color: #003087;
            }
        """)

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def handle_login(self):
        try:
            username = self.login_username_input.text().strip()
            password = self.login_password_input.text().strip()

            if not username or not password:
                window_alert.show_message(self, "Missing Input", "Please fill in all fields.", icon_type="warning")
                return

            hashed_password = self.hash_password(password)
            user = db_con.authenticate_user(username, hashed_password)

            if user:
                window_alert.show_message(self, "Success", "Login successful!", icon_type="info")
                self.close()
                self.main_window = Main.MainWindow(username=username)
                self.main_window.setWindowTitle("Document Management System")
                self.main_window.setWindowIcon(QIcon(abs_path.resource("img/icon.ico")))
                self.main_window.resize(1000, 800)
                self.main_window.showMaximized()
            else:
                window_alert.show_message(self, "Error", "Invalid username or password.", icon_type="critical")
        except Exception as e:
            window_alert.show_message(self, "Unexpected Error", f"An error occurred: {str(e)}", icon_type="critical")

    def handle_signup(self):
        try:
            username = self.signup_username_input.text().strip()
            password = self.signup_password_input.text().strip()
            confirm_password = self.signup_confirm_password_input.text().strip()

            if not all([username, password, confirm_password]):
                window_alert.show_message(self, "Missing Input", "Please fill in all fields.", icon_type="warning")
                return

            if password != confirm_password:
                window_alert.show_message(self, "Error", "Passwords do not match.", icon_type="warning")
                return

            hashed_password = self.hash_password(password)
            try:
                db_con.register_user(username, hashed_password)
                window_alert.show_message(self, "Success", "Sign up successful! Please log in.", icon_type="info")
                self.signup_username_input.clear()
                self.signup_password_input.clear()
                self.signup_confirm_password_input.clear()
                self.stacked_widget.setCurrentIndex(0)
                self.login_username_input.setFocus()
            except ValueError as e:
                window_alert.show_message(self, "Error", str(e), icon_type="critical")
            except Exception as e:
                window_alert.show_message(self, "Database Error", f"Failed to register: {str(e)}", icon_type="critical")
        except Exception as e:
            window_alert.show_message(self, "Unexpected Error", f"An error occurred: {str(e)}", icon_type="critical")


def main():
    app = QApplication(sys.argv)
    window = AuthWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
