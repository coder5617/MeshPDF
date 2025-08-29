from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QBrush

class SignaturePad(QDialog):
    """Dialog for drawing signatures with transparent background"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sign Here")
        self.setFixedSize(400, 300)
        self.setModal(True)  # Make it modal
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Add instructions
        instructions = QLabel("Draw your signature below using your mouse or touch screen")
        instructions.setWordWrap(True)
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instructions)
        
        # Create signature area with checkered background to show transparency
        self.signature_label = QLabel()
        self.signature_label.setFixedSize(380, 200)
        
        # Create a checkered background to visualize transparency
        self.signature_label.setStyleSheet("""
            QLabel {
                border: 2px solid #cccccc;
                border-radius: 5px;
                background-color: #ffffff;
                background-image: 
                    repeating-linear-gradient(
                        45deg,
                        #f0f0f0,
                        #f0f0f0 10px,
                        #ffffff 10px,
                        #ffffff 20px
                    );
            }
        """)
        
        # Initialize signature pixmap with TRANSPARENT background
        self.signature_pixmap = QPixmap(380, 200)
        self.signature_pixmap.fill(Qt.GlobalColor.transparent)  # Transparent background
        
        # Create display pixmap with checkered pattern
        self.update_display()
        
        layout.addWidget(self.signature_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Add buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Clear button
        clear_button = QPushButton("Clear")
        clear_button.setFixedHeight(35)
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: black;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px 15px;
                font-weight: normal;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        clear_button.clicked.connect(self.clear_signature)
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedHeight(35)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: black;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px 15px;
                font-weight: normal;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        
        # Done button
        done_button = QPushButton("Done")
        done_button.setFixedHeight(35)
        done_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        done_button.clicked.connect(self.validate_and_accept)
        done_button.setDefault(True)  # Make it the default button
        
        button_layout.addWidget(clear_button)
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(done_button)
        layout.addLayout(button_layout)
        
        # Initialize drawing variables
        self.last_point = QPoint()
        self.drawing = False
        self.has_signature = False  # Track if user has drawn anything
        
    def create_checkered_background(self):
        """Create a checkered pattern background to show transparency"""
        background = QPixmap(380, 200)
        background.fill(Qt.GlobalColor.white)
        
        painter = QPainter(background)
        brush = QBrush(QColor(240, 240, 240))
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Draw checkered pattern
        square_size = 10
        for i in range(0, 380, square_size * 2):
            for j in range(0, 200, square_size * 2):
                painter.drawRect(i, j, square_size, square_size)
                painter.drawRect(i + square_size, j + square_size, square_size, square_size)
        
        painter.end()
        return background
        
    def update_display(self):
        """Update the display with signature over checkered background"""
        # Create checkered background
        display_pixmap = self.create_checkered_background()
        
        # Draw signature on top
        painter = QPainter(display_pixmap)
        painter.drawPixmap(0, 0, self.signature_pixmap)
        painter.end()
        
        self.signature_label.setPixmap(display_pixmap)
        
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if click is within signature area
            label_pos = self.signature_label.pos()
            label_rect = self.signature_label.rect().translated(label_pos)
            
            if label_rect.contains(event.pos()):
                self.drawing = True
                self.last_point = event.pos() - label_pos
                self.has_signature = True
            
    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        if self.drawing and event.buttons() & Qt.MouseButton.LeftButton:
            # Calculate current point relative to signature label
            label_pos = self.signature_label.pos()
            current_point = event.pos() - label_pos
            
            # Check if current point is within bounds
            if (0 <= current_point.x() < self.signature_pixmap.width() and 
                0 <= current_point.y() < self.signature_pixmap.height()):
                
                # Draw line on the transparent signature pixmap
                painter = QPainter(self.signature_pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                
                # Use a nice pen for smooth signature (dark blue/black)
                pen = QPen(QColor(0, 0, 100), 2.5, Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                
                # Draw the line
                painter.drawLine(self.last_point, current_point)
                painter.end()
                
                # Update the display with checkered background
                self.update_display()
                
                # Update last point
                self.last_point = current_point
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = False
            
    def clear_signature(self):
        """Clear the signature pad"""
        self.signature_pixmap.fill(Qt.GlobalColor.transparent)  # Clear to transparent
        self.update_display()
        self.has_signature = False
        print("Signature cleared")
        
    def validate_and_accept(self):
        """Check if signature exists before accepting"""
        if not self.has_signature:
            # Show a message that signature is required
            QMessageBox.warning(self, "No Signature", 
                               "Please draw your signature before clicking Done.")
            return
        self.accept()
        
    def get_signature(self):
        """Get the signature pixmap with transparent background"""
        return self.signature_pixmap

# Export class
__all__ = ['SignaturePad']