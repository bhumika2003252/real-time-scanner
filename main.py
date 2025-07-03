import sys
import cv2
import pytesseract
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QWidget,
    QFileDialog, QTextEdit, QTabWidget, QMessageBox, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QPixmap, QImage, QFont, QColor, QPalette, QBrush, QLinearGradient
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QByteArray, QEasingCurve
import numpy as np
from deep_translator import GoogleTranslator
import PyPDF2

class AnimatedTabWidget(QTabWidget):
    """Tab widget with fade-in animation on tab change."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.currentChanged.connect(self.animate_tab)
        self.opacity = 1.0

    def animate_tab(self, index):
        widget = self.widget(index)
        self.anim = QPropertyAnimation(widget, b"windowOpacity")
        self.anim.setDuration(400)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        widget.setWindowOpacity(0.0)
        self.anim.start()

class TranslationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🗣️ Language Translator Deluxe")
        self.setGeometry(100, 100, 900, 650)
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8ffae, stop:1 #43cea2
                );
            }
        """)
        self.setup_ui()
        self.translator = GoogleTranslator(source='auto', target='en')
        self.camera = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_camera)
        self.current_image = None

    def setup_ui(self):
        main_layout = QVBoxLayout()
        self.tabs = AnimatedTabWidget()
        self.camera_tab = QWidget()
        self.file_tab = QWidget()
        self.tabs.addTab(self.camera_tab, "📷 Camera Input")
        self.tabs.addTab(self.file_tab, "📁 File Input")
        self.setup_camera_tab()
        self.setup_file_tab()

        # Output Area
        output_layout = QVBoxLayout()
        output_label = QLabel("📝 Translated Text (English):")
        output_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        output_label.setStyleSheet("color: #2d3436; margin-bottom: 4px;")
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 11))
        self.output_text.setStyleSheet("""
            QTextEdit {
                background: #f5f6fa;
                border-radius: 10px;
                border: 2px solid #00b894;
                padding: 8px;
                color: #222f3e;
            }
        """)
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_text)

        main_layout.addWidget(self.tabs, 3)
        main_layout.addLayout(output_layout, 2)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def setup_camera_tab(self):
        layout = QVBoxLayout()
        # Camera preview
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setText("Camera preview will appear here")
        self.camera_label.setMinimumHeight(300)
        self.camera_label.setFont(QFont("Segoe UI", 11, QFont.StyleItalic))
        self.camera_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #e0c3fc, stop:1 #8ec5fc
                );
                border: 2px solid #6c5ce7;
                border-radius: 18px;
                color: #636e72;
            }
        """)
        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(76, 201, 240, 120))
        shadow.setOffset(0, 4)
        self.camera_label.setGraphicsEffect(shadow)

        # Camera controls
        camera_controls = QHBoxLayout()
        self.start_camera_btn = QPushButton("▶ Start Camera")
        self.capture_btn = QPushButton("📸 Capture Image")
        self.translate_camera_btn = QPushButton("🌐 Translate")

        for btn in [self.start_camera_btn, self.capture_btn, self.translate_camera_btn]:
            btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 #43cea2, stop:1 #185a9d
                    );
                    color: white;
                    border-radius: 13px;
                    padding: 10px 24px;
                    border: none;
                    transition: all 0.2s;
                }
                QPushButton:hover {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 #ffaf7b, stop:1 #d76d77
                    );
                    color: #fffde7;
                    font-size: 13.5px;
                }
            """)
        self.capture_btn.setEnabled(False)
        self.translate_camera_btn.setEnabled(False)
        self.start_camera_btn.clicked.connect(self.start_camera)
        self.capture_btn.clicked.connect(self.capture_image)
        self.translate_camera_btn.clicked.connect(self.translate_camera_image)
        camera_controls.addWidget(self.start_camera_btn)
        camera_controls.addWidget(self.capture_btn)
        camera_controls.addWidget(self.translate_camera_btn)

        layout.addWidget(self.camera_label)
        layout.addLayout(camera_controls)
        self.camera_tab.setLayout(layout)

    def setup_file_tab(self):
        layout = QVBoxLayout()
        self.file_preview = QLabel()
        self.file_preview.setAlignment(Qt.AlignCenter)
        self.file_preview.setText("File preview will appear here")
        self.file_preview.setMinimumHeight(300)
        self.file_preview.setFont(QFont("Segoe UI", 11, QFont.StyleItalic))
        self.file_preview.setStyleSheet("""
            QLabel {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f7971e, stop:1 #ffd200
                );
                border: 2px solid #fdcb6e;
                border-radius: 18px;
                color: #636e72;
            }
        """)
        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(253, 203, 110, 120))
        shadow.setOffset(0, 4)
        self.file_preview.setGraphicsEffect(shadow)

        file_controls = QHBoxLayout()
        self.select_file_btn = QPushButton("🗂 Select File")
        self.translate_file_btn = QPushButton("🌐 Translate")
        for btn in [self.select_file_btn, self.translate_file_btn]:
            btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 #ff9966, stop:1 #ff5e62
                    );
                    color: white;
                    border-radius: 13px;
                    padding: 10px 24px;
                    border: none;
                    transition: all 0.2s;
                }
                QPushButton:hover {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 #43cea2, stop:1 #185a9d
                    );
                    color: #fffde7;
                    font-size: 13.5px;
                }
            """)
        self.translate_file_btn.setEnabled(False)
        self.select_file_btn.clicked.connect(self.select_file)
        self.translate_file_btn.clicked.connect(self.translate_file)
        file_controls.addWidget(self.select_file_btn)
        file_controls.addWidget(self.translate_file_btn)
        layout.addWidget(self.file_preview)
        layout.addLayout(file_controls)
        self.file_tab.setLayout(layout)

    def start_camera(self):
        if self.timer.isActive():
            self.timer.stop()
            if self.camera:
                self.camera.release()
                self.camera = None
            self.start_camera_btn.setText("▶ Start Camera")
            self.capture_btn.setEnabled(False)
        else:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                QMessageBox.critical(self, "Error", "Could not open camera.")
                return
            self.timer.start(30)
            self.start_camera_btn.setText("⏹ Stop Camera")
            self.capture_btn.setEnabled(True)

    def update_camera(self):
        ret, frame = self.camera.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            q_img = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.camera_label.setPixmap(QPixmap.fromImage(q_img).scaled(
                self.camera_label.width(), self.camera_label.height(), Qt.KeepAspectRatio))
            self.current_frame = frame

    def capture_image(self):
        if hasattr(self, 'current_frame'):
            self.current_image = self.current_frame.copy()
            self.translate_camera_btn.setEnabled(True)
            QMessageBox.information(self, "Success", "Image captured successfully!")

    def select_file(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Select File", "", "Images (*.png *.jpg *.jpeg);;PDF Files (*.pdf);;All Files (*)"
        )
        if file_path:
            self.file_path = file_path
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                pixmap = QPixmap(file_path)
                self.file_preview.setPixmap(pixmap.scaled(
                    self.file_preview.width(), self.file_preview.height(), Qt.KeepAspectRatio))
                self.current_image = cv2.imread(file_path)
            elif file_path.lower().endswith('.pdf'):
                self.file_preview.setText("PDF File Selected: " + file_path.split('/')[-1])
                self.current_image = None
            self.translate_file_btn.setEnabled(True)

    def extract_text_from_image(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        text = pytesseract.image_to_string(gray)
        return text

    def extract_text_from_pdf(self, pdf_path):
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    text += reader.pages[page_num].extract_text()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to extract text from PDF: {str(e)}")
        return text

    def translate_text(self, text):
        if not text.strip():
            return "No text detected to translate."
        try:
            translation = self.translator.translate(text)
            result = f"Original text:\n{text}\n\nTranslated text:\n{translation}"
            return result
        except Exception as e:
            return f"Translation error: {str(e)}"

    def translate_camera_image(self):
        if self.current_image is not None:
            text = self.extract_text_from_image(self.current_image)
            translated_text = self.translate_text(text)
            self.output_text.setText(translated_text)
        else:
            QMessageBox.warning(self, "Warning", "No image captured yet.")

    def translate_file(self):
        if hasattr(self, 'file_path'):
            if self.file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                if self.current_image is not None:
                    text = self.extract_text_from_image(self.current_image)
                    translated_text = self.translate_text(text)
                    self.output_text.setText(translated_text)
            elif self.file_path.lower().endswith('.pdf'):
                text = self.extract_text_from_pdf(self.file_path)
                translated_text = self.translate_text(text)
                self.output_text.setText(translated_text)
        else:
            QMessageBox.warning(self, "Warning", "No file selected.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TranslationApp()
    window.show()
    sys.exit(app.exec_())
