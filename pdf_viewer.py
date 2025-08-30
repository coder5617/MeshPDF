from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea,  
                            QMessageBox, QInputDialog, QMenu)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QImage, QCursor, QFont, QMouseEvent, QColor
import fitz  # PyMuPDF
import traceback

class DraggableLabel(QLabel):
    """A QLabel that can be dragged, edited, and deleted"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.draggable = True
        self.dragging = False
        self.offset = QPoint()
        self.setMouseTracking(True)
        
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.draggable:
            self.dragging = True
            self.offset = event.pos()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            self.raise_()  # Bring to front when clicked
            event.accept()
            
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging and self.draggable:
            new_pos = event.globalPosition().toPoint() - self.offset
            parent_widget = self.parent()
            if parent_widget:
                new_pos = parent_widget.mapFromGlobal(new_pos)
                # Constrain to parent bounds
                new_pos.setX(max(0, min(new_pos.x(), parent_widget.width() - self.width())))
                new_pos.setY(max(0, min(new_pos.y(), parent_widget.height() - self.height())))
                self.move(new_pos)
            event.accept()
            
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.draggable:
            self.dragging = False
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            event.accept()
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double-click for editing"""
        if hasattr(self, 'modification_info'):
            mod_info = self.modification_info
            if mod_info['type'] == 'text':
                # Edit text
                text, ok = QInputDialog.getText(
                    self, "Edit Text", "Edit your text:", 
                    text=self.text()
                )
                if ok and text:
                    self.setText(text)
                    self.adjustSize()
                    print(f"Text edited: {text[:30]}...")
            elif mod_info['type'] == 'signature':
                # Re-open signature pad for editing
                reply = QMessageBox.question(
                    self, "Edit Signature",
                    "Do you want to redraw your signature?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    from signature_pad import SignaturePad
                    sig_pad = SignaturePad(self.window())
                    if sig_pad.exec():
                        new_sig = sig_pad.get_signature()
                        # Store the original pixmap
                        self.original_pixmap = new_sig
                        # Scale to current size
                        scaled_sig = new_sig.scaled(
                            self.size(), 
                            Qt.AspectRatioMode.KeepAspectRatio, 
                            Qt.TransformationMode.SmoothTransformation
                        )
                        self.setPixmap(scaled_sig)
                        print("Signature updated")
        event.accept()
    
    def contextMenuEvent(self, event):
        """Right-click context menu for delete and other options"""
        if hasattr(self, 'modification_info'):
            context_menu = QMenu(self)
            
            # Delete action
            delete_action = QAction("🗑️ Delete", self)
            delete_action.triggered.connect(self.delete_overlay)
            context_menu.addAction(delete_action)
            
            # Edit action
            edit_action = QAction("✏️ Edit", self)
            edit_action.triggered.connect(lambda: self.mouseDoubleClickEvent(event))
            context_menu.addAction(edit_action)
            
            # Show menu
            context_menu.exec(event.globalPos())
    
    def delete_overlay(self):
        """Delete this overlay"""
        print(f"Deleting {self.modification_info['type']} overlay")
        self.deleteLater()
            
    def enterEvent(self, event):
        if self.draggable:
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            
    def leaveEvent(self, event):
        if self.draggable:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

class ClickableLabel(QLabel):
    """A QLabel that handles click events for the PDF pages"""
    def __init__(self, viewer, page_num=0):
        super().__init__()
        self.viewer = viewer
        self.page_num = page_num
        self.setMouseTracking(True)
        
    def mousePressEvent(self, event):
        # Pass the event to the viewer's click handler
        self.viewer.handle_click(event, self.page_num)

class PDFViewer(QScrollArea):
    zoom_changed = pyqtSignal(float)  # Signal for zoom level changes
    
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.container = QWidget()
        self.setWidget(self.container)
        self.layout = QVBoxLayout(self.container)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        
        # Initialize properties
        self.current_doc = None
        self.current_file = None
        self.pages = []
        self.page_labels = []
        self.text_mode = False
        self.signature_mode = False
        self.current_signature = None
        self.scale_factor = 2  # PDF rendering scale (200% for better quality)
        self.zoom_level = 1.0  # Current zoom level
        self.overlays = []  # Store overlay information for persistence across zoom
        
        # Set scrollbar policies for better navigation
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
    
    def collect_overlays(self):
        """Collect all overlay information before clearing pages"""
        overlays = []
        for page_num, page_label in enumerate(self.page_labels):
            for child in page_label.children():
                if isinstance(child, DraggableLabel) and hasattr(child, 'modification_info'):
                    mod_info = child.modification_info
                    overlay_data = {
                        'type': mod_info['type'],
                        'page': page_num,
                        'position': child.pos(),
                        'size': child.size(),
                        'original_zoom': mod_info.get('original_zoom', self.zoom_level)  # Use stored original zoom
                    }
                    
                    if mod_info['type'] == 'signature':
                        # Store the original signature pixmap if available, otherwise use current
                        overlay_data['pixmap'] = getattr(child, 'original_pixmap', child.pixmap())
                    elif mod_info['type'] == 'text':
                        overlay_data['text'] = child.text()
                        overlay_data['font_size'] = child.font().pointSize()
                    
                    overlays.append(overlay_data)
                    print(f"Collected {mod_info['type']} overlay from page {page_num}")
        
        return overlays
    
    def restore_overlays(self, overlays):
        """Restore overlays after page recreation with proper scaling"""
        for overlay in overlays:
            page_num = overlay['page']
            if page_num >= len(self.page_labels):
                continue  # Skip if page doesn't exist
                
            page_label = self.page_labels[page_num]
            
            # Calculate position and size scaling
            zoom_ratio = self.zoom_level / overlay['original_zoom']
            scaled_pos = QPoint(
                int(overlay['position'].x() * zoom_ratio),
                int(overlay['position'].y() * zoom_ratio)
            )
            
            if overlay['type'] == 'signature':
                # Create signature overlay
                sig_label = DraggableLabel(page_label)
                
                # Always scale from the original pixmap to prevent quality degradation
                original_pixmap = overlay['pixmap']
                
                # Calculate target size based on current zoom
                base_width = int(200 * self.zoom_level)
                base_height = int(100 * self.zoom_level)
                scaled_pixmap = original_pixmap.scaled(
                    base_width, base_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                sig_label.setPixmap(scaled_pixmap)
                # Preserve the original pixmap for future scaling
                sig_label.original_pixmap = original_pixmap
                sig_label.move(scaled_pos)
                sig_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
                sig_label.setStyleSheet("background: transparent;")
                sig_label.show()
                
                sig_label.modification_info = {
                    'type': 'signature',
                    'page': page_num,
                    'original_zoom': self.zoom_level  # Update to current zoom after restoration
                }
                
            elif overlay['type'] == 'text':
                # Create text overlay
                text_label = DraggableLabel(page_label)
                text_label.setText(overlay['text'])
                
                # Scale font size appropriately
                font = QFont()
                scaled_font_size = int(overlay['font_size'] * zoom_ratio)
                font.setPointSize(max(8, scaled_font_size))  # Minimum font size
                text_label.setFont(font)
                
                text_label.setStyleSheet("""
                    color: black; 
                    background-color: rgba(255, 255, 255, 200);
                    padding: 2px;
                    border: 1px solid rgba(0, 0, 0, 50);
                """)
                
                text_label.adjustSize()
                text_label.move(scaled_pos)
                text_label.show()
                
                text_label.modification_info = {
                    'type': 'text',
                    'page': page_num,
                    'original_zoom': self.zoom_level  # Update to current zoom after restoration
                }
            
            print(f"Restored {overlay['type']} overlay on page {page_num} at zoom {self.zoom_level:.2f}")
        
    def load_pdf(self, file_path, preserve_overlays=True):
        """Load and display a PDF file"""
        try:
            # Store current file path
            self.current_file = file_path
            
            # Collect existing overlays before clearing if preserving
            collected_overlays = []
            if preserve_overlays and self.page_labels:
                collected_overlays = self.collect_overlays()
                print(f"Collected {len(collected_overlays)} overlays to preserve")
            
            # Clear existing pages
            self.clear_pages()
            
            # Open the PDF document
            self.current_doc = fitz.open(file_path)
            print(f"Opened PDF with {len(self.current_doc)} pages")
            
            # Render each page
            for page_num in range(len(self.current_doc)):
                page = self.current_doc[page_num]
                
                # Render page at scale_factor zoom
                render_scale = self.scale_factor * self.zoom_level
                pix = page.get_pixmap(matrix=fitz.Matrix(render_scale, render_scale))
                
                # Convert to QPixmap
                img = QPixmap.fromImage(QImage(pix.samples, 
                                               pix.width, 
                                               pix.height, 
                                               pix.stride, 
                                               QImage.Format.Format_RGB888))
                
                # Create container for the page
                page_container = QWidget()
                page_container.setFixedSize(img.width(), img.height())
                
                # Create clickable label for the page
                label = ClickableLabel(self, page_num)
                label.setPixmap(img)
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setParent(page_container)
                label.setGeometry(0, 0, img.width(), img.height())
                
                # Add to lists
                self.pages.append(page_container)
                self.page_labels.append(label)
                self.layout.addWidget(page_container)
                
                # Add spacing between pages
                if page_num < len(self.current_doc) - 1:
                    spacer = QWidget()
                    spacer.setFixedHeight(20)
                    self.layout.addWidget(spacer)
                    
            print(f"Successfully loaded {len(self.pages)} pages at zoom {self.zoom_level:.2f}")
            
            # Restore overlays if any were collected
            if collected_overlays:
                self.restore_overlays(collected_overlays)
                print(f"Restored {len(collected_overlays)} overlays")
            
        except Exception as e:
            self.clear_pages()
            error_msg = f"Error loading PDF: {str(e)}\n\n{traceback.format_exc()}"
            QMessageBox.critical(self, "Error", error_msg)
            print(error_msg)
            raise
    
    def zoom(self, factor):
        """Zoom in or out by the given factor"""
        new_zoom = self.zoom_level * factor
        # Clamp zoom between 25% and 400%
        new_zoom = max(0.25, min(new_zoom, 4.0))
        
        if new_zoom != self.zoom_level:
            # Store scroll position
            v_scroll = self.verticalScrollBar().value()
            h_scroll = self.horizontalScrollBar().value()
            v_max = self.verticalScrollBar().maximum()
            h_max = self.horizontalScrollBar().maximum()
            
            # Calculate relative position
            v_relative = v_scroll / v_max if v_max > 0 else 0
            h_relative = h_scroll / h_max if h_max > 0 else 0
            
            self.zoom_level = new_zoom
            self.zoom_changed.emit(self.zoom_level)
            
            if self.current_file:
                # Reload at new zoom
                self.load_pdf(self.current_file)
                
                # Restore approximate scroll position
                QApplication.processEvents()  # Let layout update
                new_v_max = self.verticalScrollBar().maximum()
                new_h_max = self.horizontalScrollBar().maximum()
                self.verticalScrollBar().setValue(int(v_relative * new_v_max))
                self.horizontalScrollBar().setValue(int(h_relative * new_h_max))
            
            print(f"Zoom level: {self.zoom_level:.2f}x ({int(self.zoom_level * 100)}%)")
    
    def reset_zoom(self):
        """Reset zoom to 100%"""
        if self.zoom_level != 1.0:
            self.zoom_level = 1.0
            self.zoom_changed.emit(self.zoom_level)
            if self.current_file:
                self.load_pdf(self.current_file)
            print("Zoom reset to 100%")
            
    def clear_pages(self):
        """Clear all pages from the viewer"""
        # Remove all widgets from layout
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # Clear lists
        self.pages.clear()
        self.page_labels.clear()
        
        # Close document if open
        if self.current_doc:
            self.current_doc.close()
            self.current_doc = None
            
    def enable_signature_mode(self, signature_image):
        """Enable signature placement mode"""
        self.signature_mode = True
        self.text_mode = False
        self.current_signature = signature_image
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        QMessageBox.information(self, "Add Signature", 
                              "Click where you want to place the signature.\n"
                              "• Drag to reposition\n"
                              "• Right-click to delete\n"
                              "• Double-click to edit")
        
    def enable_text_mode(self):
        """Enable text placement mode"""
        self.text_mode = True
        self.signature_mode = False
        self.setCursor(QCursor(Qt.CursorShape.IBeamCursor))
        QMessageBox.information(self, "Add Text", 
                              "Click where you want to add text.\n"
                              "• Drag to reposition\n"
                              "• Right-click to delete\n"
                              "• Double-click to edit")
        
    def handle_click(self, event, page_num):
        """Handle clicks on PDF pages"""
        if self.signature_mode and self.current_signature:
            # Add signature at click position
            pos = event.pos()
            parent_widget = self.page_labels[page_num]
            
            # Create draggable signature label
            sig_label = DraggableLabel(parent_widget)
            
            # Scale signature based on zoom level
            base_width = int(200 * self.zoom_level)
            base_height = int(100 * self.zoom_level)
            scaled_signature = self.current_signature.scaled(
                base_width, base_height,
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            sig_label.setPixmap(scaled_signature)
            # Store the original unscaled signature for quality preservation
            sig_label.original_pixmap = self.current_signature
            
            # Position signature centered on click point
            sig_label.move(pos.x() - scaled_signature.width() // 2, 
                          pos.y() - scaled_signature.height() // 2)
            
            # Make background transparent
            sig_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            sig_label.setStyleSheet("background: transparent;")
            sig_label.show()
            
            # Store modification info
            sig_label.modification_info = {
                'type': 'signature',
                'page': page_num,
                'original_zoom': self.zoom_level
            }
            
            print(f"Added signature to page {page_num} at position ({pos.x()}, {pos.y()})")
            
            # Reset mode
            self.signature_mode = False
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            
        elif self.text_mode:
            # Get text from user
            text, ok = QInputDialog.getText(self, "Add Text", "Enter your text:")
            if ok and text:
                pos = event.pos()
                parent_widget = self.page_labels[page_num]
                
                # Create draggable text label
                text_label = DraggableLabel(parent_widget)
                text_label.setText(text)
                
                # Set font scaled by zoom
                font = QFont()
                font.setPointSize(int(14 * self.zoom_level))
                text_label.setFont(font)
                
                # Set style with semi-transparent background
                text_label.setStyleSheet("""
                    color: black; 
                    background-color: rgba(255, 255, 255, 200);
                    padding: 2px;
                    border: 1px solid rgba(0, 0, 0, 50);
                """)
                
                # Adjust size to fit text
                text_label.adjustSize()
                
                # Position at click point
                text_label.move(pos.x(), pos.y())
                text_label.show()
                
                # Store modification info
                text_label.modification_info = {
                    'type': 'text',
                    'page': page_num,
                    'original_zoom': self.zoom_level
                }
                
                print(f"Added text to page {page_num} at position ({pos.x()}, {pos.y()})")
                
                # Reset mode
                self.text_mode = False
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def print_pdf(self):
        """Print the PDF with modifications properly composited"""
        if not self.current_doc:
            QMessageBox.warning(self, "Print Error", "Please open a PDF file first.")
            return

        try:
            from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
            from PyQt6.QtGui import QPageSize, QPageLayout
            
            # Create printer
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            
            # Detect and set page size from first page
            if len(self.current_doc) > 0:
                page_rect = self.current_doc[0].rect
                width_pt = page_rect.width
                height_pt = page_rect.height
                
                # Set custom page size based on PDF
                page_size = QPageSize(QPageSize.PageSizeId.A4)  # Default
                if abs(width_pt - 612) < 10 and abs(height_pt - 792) < 10:
                    page_size = QPageSize(QPageSize.PageSizeId.Letter)
                elif abs(width_pt - 595) < 10 and abs(height_pt - 842) < 10:
                    page_size = QPageSize(QPageSize.PageSizeId.A4)
                    
                printer.setPageSize(page_size)
            
            printer.setColorMode(QPrinter.ColorMode.Color)
            printer.setPageOrientation(QPageLayout.Orientation.Portrait)

            # Show print dialog
            dialog = QPrintDialog(printer, self)
            dialog.setWindowTitle("Print PDF")

            if dialog.exec() != QPrintDialog.DialogCode.Accepted:
                return

            # Show progress
            progress_dialog = QMessageBox(QMessageBox.Icon.Information, 
                                          "Printing", 
                                          "Preparing document for printing...",
                                          QMessageBox.StandardButton.NoButton, self)
            progress_dialog.show()

            # Start painting
            painter = QPainter()
            if not painter.begin(printer):
                raise Exception("Failed to initialize printer")

            try:
                printer_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
                
                # Print each page with composited overlays
                for page_num, page_label in enumerate(self.page_labels):
                    if page_num > 0:
                        printer.newPage()

                    # Get base page pixmap
                    base_pixmap = page_label.pixmap()
                    if base_pixmap is None:
                        continue

                    # Create a composite pixmap with all overlays
                    composite = QPixmap(base_pixmap.size())
                    composite.fill(Qt.GlobalColor.transparent)
                    
                    # Create painter for composite
                    composite_painter = QPainter(composite)
                    composite_painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                    composite_painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
                    
                    # Draw base PDF page
                    composite_painter.drawPixmap(0, 0, base_pixmap)
                    
                    # Draw all overlays (signatures and text) onto composite
                    for child in page_label.children():
                        if isinstance(child, DraggableLabel) and hasattr(child, 'modification_info'):
                            mod_info = child.modification_info
                            
                            if mod_info['type'] == 'signature':
                                # Draw signature with transparency
                                sig_pixmap = child.pixmap()
                                if sig_pixmap:
                                    composite_painter.setCompositionMode(
                                        QPainter.CompositionMode.CompositionMode_SourceOver
                                    )
                                    composite_painter.drawPixmap(child.pos(), sig_pixmap)
                                    
                            elif mod_info['type'] == 'text':
                                # Draw text
                                composite_painter.setPen(Qt.GlobalColor.black)
                                composite_painter.setFont(child.font())
                                
                                # Draw text background if needed
                                text_rect = child.rect().translated(child.pos())
                                composite_painter.fillRect(text_rect, 
                                                          QColor(255, 255, 255, 200))
                                
                                # Draw text
                                composite_painter.drawText(text_rect, 
                                                          Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                                                          child.text())
                    
                    composite_painter.end()
                    
                    # Now scale and print the composite image
                    scaled_composite = composite.scaled(
                        int(printer_rect.width()),
                        int(printer_rect.height()),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    
                    # Center on page
                    x = (printer_rect.width() - scaled_composite.width()) / 2
                    y = (printer_rect.height() - scaled_composite.height()) / 2
                    
                    # Draw the composite to printer
                    painter.drawPixmap(int(x), int(y), scaled_composite)
                                
            finally:
                painter.end()
                progress_dialog.close()

            QMessageBox.information(self, "Success", "Document sent to printer successfully!")
            print("PDF printed successfully with all overlays")

        except Exception as e:
            error_msg = f"Printing error: {str(e)}\n\n{traceback.format_exc()}"
            QMessageBox.critical(self, "Print Error", error_msg)
            print(error_msg)

# Import QApplication for zoom
from PyQt6.QtWidgets import QApplication

# Export classes
__all__ = ['PDFViewer', 'DraggableLabel']