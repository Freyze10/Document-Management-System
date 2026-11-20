from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar


class LoadingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Syncing...")
        self.setModal(True)  # blocks interaction with main window
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)  # disable close button
        self.setFixedSize(200, 100)

        layout = QVBoxLayout(self)
        self.label = QLabel("Please wait, syncing...")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate (infinite loading)
        self.progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress)