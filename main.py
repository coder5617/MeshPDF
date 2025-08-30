import sys
import tempfile
import os

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QFileDialog,
                            QMessageBox)
from PyQt6.QtCore import Qt
from pdf_viewer import PDFViewer, DraggableLabel
from pdf_editor import PDFEditor
from signature_pad import SignaturePad

class MeshPDFApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MeshPDF")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create toolbar
        toolbar = QHBoxLayout()
        
        # Create buttons with smaller height to fit more buttons
        self.import_btn = QPushButton("📂 Open")
        self.import_btn.setFixedHeight(35)
        self.import_btn.setToolTip("Open a PDF file for editing")
        self.import_btn.clicked.connect(self.import_pdf)
        
        self.save_btn = QPushButton("💾 Save")
        self.save_btn.setFixedHeight(35)
        self.save_btn.setToolTip("Save the modified PDF")
        self.save_btn.clicked.connect(self.save_pdf)
        self.save_btn.setEnabled(False)
        
        self.print_btn = QPushButton("🖨️ Print")
        self.print_btn.setFixedHeight(35)
        self.print_btn.setToolTip("Print the PDF with modifications")
        self.print_btn.clicked.connect(self.print_pdf)
        self.print_btn.setEnabled(False)
        
        self.sign_btn = QPushButton("✍️ Sign")
        self.sign_btn.setFixedHeight(35)
        self.sign_btn.setToolTip("Draw and add your signature")
        self.sign_btn.clicked.connect(self.add_signature)
        self.sign_btn.setEnabled(False)
        
        self.text_btn = QPushButton("📝 Text")
        self.text_btn.setFixedHeight(35)
        self.text_btn.setToolTip("Add text annotation")
        self.text_btn.clicked.connect(self.add_text)
        self.text_btn.setEnabled(False)
        
        self.combine_btn = QPushButton("📑 Combine")
        self.combine_btn.setFixedHeight(35)
        self.combine_btn.setToolTip("Combine multiple PDFs into one (files merged in selection order)")
        self.combine_btn.clicked.connect(self.combine_pdfs)
        
        self.zoom_in_btn = QPushButton("🔍+")
        self.zoom_in_btn.setFixedHeight(35)
        self.zoom_in_btn.setToolTip("Zoom in (25%)")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_in_btn.setEnabled(False)
        
        self.zoom_out_btn = QPushButton("🔍-")
        self.zoom_out_btn.setFixedHeight(35)
        self.zoom_out_btn.setToolTip("Zoom out (20%)")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.zoom_out_btn.setEnabled(False)
        
        self.zoom_reset_btn = QPushButton("🔍↺")
        self.zoom_reset_btn.setFixedHeight(35)
        self.zoom_reset_btn.setToolTip("Reset zoom to 100%")
        self.zoom_reset_btn.clicked.connect(self.zoom_reset)
        self.zoom_reset_btn.setEnabled(False)
        
        # Add zoom label
        self.zoom_label = QLabel("100%")
        self.zoom_label.setFixedHeight(35)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_label.setStyleSheet("QLabel { padding: 0 10px; font-weight: bold; }")
        
        # Add buttons to toolbar
        toolbar.addWidget(self.import_btn)
        toolbar.addWidget(self.save_btn)
        toolbar.addWidget(self.print_btn)
        toolbar.addWidget(self.sign_btn)
        toolbar.addWidget(self.text_btn)
        toolbar.addWidget(self.combine_btn)
        toolbar.addStretch()  # Add space before zoom controls
        toolbar.addWidget(self.zoom_out_btn)
        toolbar.addWidget(self.zoom_reset_btn)
        toolbar.addWidget(self.zoom_in_btn)
        toolbar.addWidget(self.zoom_label)
        
        # Add toolbar to main layout
        layout.addLayout(toolbar)
        
        # Create PDF viewer
        self.pdf_viewer = PDFViewer()
        self.pdf_viewer.zoom_changed.connect(self.update_zoom_label)
        self.pdf_editor = PDFEditor()
        layout.addWidget(self.pdf_viewer)
        
        # Initialize current file path and temp files list
        self.current_file = None
        self.temp_files = []
        
    def update_zoom_label(self, zoom_level):
        """Update the zoom percentage label"""
        self.zoom_label.setText(f"{int(zoom_level * 100)}%")
        
    def import_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF File", "", "PDF Files (*.pdf)")
        if file_path:
            try:
                # Clean up temp files
                self.cleanup_temp_files()
                
                self.current_file = file_path
                # Pass scale factor to editor
                self.pdf_editor.set_current_pdf(file_path, scale_factor=self.pdf_viewer.scale_factor)
                self.pdf_viewer.load_pdf(file_path, preserve_overlays=False)  # No overlays to preserve on initial load
                
                # Enable buttons after successful load
                self.enable_editing_buttons(True)
                
                print(f"Successfully loaded PDF: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open PDF: {str(e)}")
                print(f"Error loading PDF: {str(e)}")
    
    def enable_editing_buttons(self, enabled):
        """Enable or disable editing buttons"""
        self.save_btn.setEnabled(enabled)
        self.print_btn.setEnabled(enabled)
        self.sign_btn.setEnabled(enabled)
        self.text_btn.setEnabled(enabled)
        self.zoom_in_btn.setEnabled(enabled)
        self.zoom_out_btn.setEnabled(enabled)
        self.zoom_reset_btn.setEnabled(enabled)
            
    def save_pdf(self):
        if not self.current_file:
            QMessageBox.warning(self, "No PDF", "Please open a PDF file first.")
            return
            
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF File", "", "PDF Files (*.pdf)")
        if save_path:
            try:
                print("Collecting modifications...")
                # Collect all modifications
                modifications = []
                for page_num, page_label in enumerate(self.pdf_viewer.page_labels):
                    for child in page_label.children():
                        if isinstance(child, DraggableLabel) and hasattr(child, 'modification_info'):
                            mod_info = child.modification_info
                            
                            # Create modification entry with actual widget data
                            modification = {
                                'type': mod_info['type'],
                                'page': mod_info['page'],
                                'position': child.pos(),
                            }
                            
                            if mod_info['type'] == 'signature':
                                modification['size'] = child.size()
                                modification['image'] = child.pixmap()
                            elif mod_info['type'] == 'text':
                                modification['text'] = child.text()
                                modification['font_size'] = child.font().pointSize()
                            
                            modifications.append(modification)
                            print(f"Added {mod_info['type']} modification on page {mod_info['page']}")
                
                # If no modifications, offer to save as copy
                if not modifications:
                    reply = QMessageBox.question(
                        self, "No Modifications",
                        "No modifications found. Do you want to save a copy of the original PDF?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        # Save copy of original
                        import shutil
                        shutil.copy2(self.current_file, save_path)
                        QMessageBox.information(self, "Success", "PDF copy saved successfully!")
                    return
                
                print(f"Total modifications to apply: {len(modifications)}")
                
                # Clear previous modifications in editor
                self.pdf_editor.modifications = []
                
                # Apply modifications accounting for zoom
                for mod in modifications:
                    if mod['type'] == 'signature':
                        self.pdf_editor.add_signature(
                            mod['image'], 
                            mod['page'], 
                            mod['position'], 
                            mod['size'],
                            zoom_level=self.pdf_viewer.zoom_level
                        )
                    elif mod['type'] == 'text':
                        self.pdf_editor.add_text(
                            mod['text'], 
                            mod['page'], 
                            mod['position'], 
                            mod.get('font_size', 14),
                            zoom_level=self.pdf_viewer.zoom_level
                        )
                
                # Save the PDF
                success = self.pdf_editor.save_pdf(save_path)
                if success:
                    QMessageBox.information(self, "Success", "PDF saved successfully!")
                    print(f"PDF saved successfully to: {save_path}")
                else:
                    QMessageBox.critical(self, "Error", "Failed to save PDF. Please check console for details.")
                    
            except Exception as e:
                error_msg = f"Error saving PDF: {str(e)}"
                QMessageBox.critical(self, "Error", error_msg)
                print(error_msg)
                import traceback
                traceback.print_exc()
            
    def print_pdf(self):
        if self.current_file:
            self.pdf_viewer.print_pdf()
        else:
            QMessageBox.warning(self, "No PDF", "Please open a PDF file first.")
            
    def add_signature(self):
        if not self.current_file:
            QMessageBox.warning(self, "No PDF", "Please open a PDF file first.")
            return
            
        signature_pad = SignaturePad(self)
        if signature_pad.exec():
            signature_image = signature_pad.get_signature()
            self.pdf_viewer.enable_signature_mode(signature_image)
            
    def add_text(self):
        if not self.current_file:
            QMessageBox.warning(self, "No PDF", "Please open a PDF file first.")
            return
            
        self.pdf_viewer.enable_text_mode()
    
    def zoom_in(self):
        """Zoom in by 25%"""
        self.pdf_viewer.zoom(1.25)
    
    def zoom_out(self):
        """Zoom out by 20%"""
        self.pdf_viewer.zoom(0.8)
    
    def zoom_reset(self):
        """Reset zoom to 100%"""
        self.pdf_viewer.reset_zoom()
    
    def combine_pdfs(self):
        """Combine multiple PDFs into one"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select PDFs to Combine", "", "PDF Files (*.pdf)"
        )
        if not files:
            return
        
        # Check for unsaved changes
        has_mods = any(
            isinstance(child, DraggableLabel) and hasattr(child, 'modification_info')
            for page_label in self.pdf_viewer.page_labels
            for child in page_label.children()
        )
        if has_mods:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "Current PDF has unsaved modifications. Combining will discard them. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        try:
            # Clean up previous temp files
            self.cleanup_temp_files()
            
            merged_path = self.pdf_editor.merge_pdfs(files)
            if merged_path:
                self.current_file = merged_path
                self.temp_files.append(merged_path)  # Track temp file
                self.pdf_editor.set_current_pdf(merged_path, scale_factor=self.pdf_viewer.scale_factor)
                self.pdf_viewer.load_pdf(merged_path, preserve_overlays=False)  # No overlays to preserve for merged PDF
                
                # Enable buttons
                self.enable_editing_buttons(True)
                
                QMessageBox.information(self, "Success", 
                    f"Combined {len(files)} PDFs successfully!\nYou can now edit, save, or print the combined PDF.")
            else:
                raise Exception("Merge failed - no valid PDFs could be combined")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to combine PDFs: {str(e)}")
            print(f"Combine error: {str(e)}")
    
    def cleanup_temp_files(self):
        """Clean up all temporary files"""
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    print(f"Cleaned up temp file: {temp_file}")
                except:
                    pass
        self.temp_files.clear()
    
    def closeEvent(self, event):
        """Clean up temporary files on close"""
        self.cleanup_temp_files()
        super().closeEvent(event)

# Import QLabel for zoom label
from PyQt6.QtWidgets import QLabel

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MeshPDFApp()
    window.show()
    sys.exit(app.exec())