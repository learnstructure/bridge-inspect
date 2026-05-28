from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtCore import Qt

class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.background_pixmap = QPixmap("assets/images/splash_image.png")
        if self.background_pixmap.isNull():
            print("Warning: Background image 'assets/images/splash_image.png' not found.")

        # A central layout to position the content frame
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        # A frame to act as a container for all the text content
        content_frame = QFrame(self)
        content_frame.setStyleSheet("background: transparent;") # Make frame invisible
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(15)
        content_layout.setAlignment(Qt.AlignCenter)

        # --- Title ---
        title = QLabel("AI Tools for Rapid Post-Earthquake Damage Assessment of Bridges")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #FFFFFF; background: transparent;")

        # --- Subtitle ---
        subtitle = QLabel("with Standard and Substandard Columns")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 24px; color: #E0E0E0; background: transparent;")
        
        # --- Description ---
        description = QLabel(
            "This application provides tools for the rapid assessment of bridge column damage "
            "following seismic events. Utilize the 'PDA Page' for automated image-based analysis "
            "and the 'DDA Page' for detailed structural pushover analysis."
        )
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setStyleSheet("font-size: 16px; color: #F0F0F0; background: transparent; max-width: 800px;")

        # --- Credits ---
        credits = QLabel(
            "Developed for the <b>Alaska Department of Transportation</b><br>"
            "by the team of Abinash Mandal, Prof. Mostafa Tazarv,<br>and Prof. Kwanghee Won"
        )
        credits.setAlignment(Qt.AlignCenter)
        credits.setStyleSheet("font-size: 12px; color: #CCCCCC; background: transparent;")
        
        # Add widgets to the content layout
        content_layout.addStretch()
        content_layout.addWidget(title)
        content_layout.addWidget(subtitle)
        content_layout.addSpacing(30)
        content_layout.addWidget(description)
        content_layout.addStretch()
        content_layout.addStretch()
        content_layout.addWidget(credits)

        # Add the content frame to the main layout
        main_layout.addWidget(content_frame)

    def paintEvent(self, event):
        """
        Override paintEvent to draw a scaled background image and a semi-transparent overlay.
        The child widgets will be drawn on top of this by Qt's paint system.
        """
        painter = QPainter(self)
        
        # If no image is found, just draw a dark background.
        if self.background_pixmap.isNull():
            painter.fillRect(self.rect(), QColor("#154360"))
            return

        # Scale image to cover the entire widget, cropping if necessary.
        scaled_pixmap = self.background_pixmap.scaled(
            self.size(), 
            Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
            Qt.TransformationMode.SmoothTransformation
        )
        # Center the image.
        x = (self.width() - scaled_pixmap.width()) / 2
        y = (self.height() - scaled_pixmap.height()) / 2
        painter.drawPixmap(int(x), int(y), scaled_pixmap)
        
        # Draw a semi-transparent black overlay on top of the image.
        overlay_color = QColor(0, 0, 0, 120) # Black with ~67% opacity
        painter.fillRect(self.rect(), overlay_color)
