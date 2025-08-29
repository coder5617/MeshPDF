from PyQt6.QtCore import QPointF, QPoint, Qt
from PyQt6.QtGui import QPixmap, QImage
import fitz  # PyMuPDF
import os
import io
from PIL import Image
import numpy as np
import traceback
import tempfile
import shutil

class PDFEditor:
    """Backend class for PDF modifications with proper transparency handling and zoom support"""
    def __init__(self):
        self.modifications = []
        self.current_pdf = None
        self.scale_factor = 2  # Default scale factor
        
    def set_current_pdf(self, pdf_path, scale_factor=2):
        """Set the current PDF being edited with scale factor"""
        self.current_pdf = pdf_path
        self.scale_factor = scale_factor
        print(f"PDF Editor initialized with scale factor: {self.scale_factor}")
        
    def add_signature(self, signature_pixmap, page_num, position, size, zoom_level=1.0):
        """Add a signature to the PDF with proper transparency, scaling, and zoom adjustment"""
        if signature_pixmap is None:
            print("Warning: signature_pixmap is None")
            return
        try:
            # Scale the pixmap to the widget's current size if needed
            if signature_pixmap.size() != size:
                signature_pixmap = signature_pixmap.scaled(
                    size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )

            # Convert QPixmap to QImage in ARGB32 format (widely supported)
            image = signature_pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)

            # Convert QImage to numpy array, handling stride correctly
            width = image.width()
            height = image.height()
            ptr = image.bits()
            ptr.setsize(image.sizeInBytes())
            arr = np.frombuffer(ptr, np.uint8).reshape((height, image.bytesPerLine() // 4, 4))
            arr = arr[:, :width, :]

            # Convert BGRA to RGBA for PIL
            arr = arr[..., [2, 1, 0, 3]]

            # Create PIL Image with RGBA (preserving transparency)
            pil_image = Image.fromarray(arr, 'RGBA')

            # Store modification with zoom level
            self.modifications.append({
                'type': 'signature',
                'image': pil_image,
                'page': page_num,
                'position': position if isinstance(position, QPoint) else QPoint(position),
                'size': size,
                'pixmap': signature_pixmap,  # Keep original pixmap for reference
                'zoom_level': zoom_level  # Store zoom level
            })

            print(f"Added signature modification: page {page_num}, pos ({position.x()}, {position.y()}), "
                  f"size ({size.width()}, {size.height()}), zoom {zoom_level:.2f}")

        except Exception as e:
            print(f"Error preparing signature: {str(e)}")
            traceback.print_exc()
        
    def add_text(self, text, page_num, position, font_size=14, zoom_level=1.0):
        """Add text to the PDF with zoom adjustment"""
        if not text:
            print("Warning: empty text")
            return
            
        # Store modification with zoom level
        self.modifications.append({
            'type': 'text',
            'text': text,
            'page': page_num,
            'position': position if isinstance(position, QPoint) else QPoint(position),
            'font_size': font_size,
            'zoom_level': zoom_level  # Store zoom level
        })
        
        print(f"Added text modification: page {page_num}, text '{text[:30]}...', "
              f"pos ({position.x()}, {position.y()}), zoom {zoom_level:.2f}")
    
    def merge_pdfs(self, pdf_paths):
        """Merge multiple PDFs into one temporary PDF and return its path"""
        if not pdf_paths:
            return None

        temp_path = None
        try:
            merged_doc = fitz.open()  # New empty PDF
            total_pages = 0
            skipped_files = []
            successful_files = []

            for path in pdf_paths:
                try:
                    doc = fitz.open(path)
                    # Check if document is encrypted
                    if doc.is_encrypted:
                        print(f"Skipping encrypted PDF {path}")
                        skipped_files.append(os.path.basename(path))
                        doc.close()
                        continue

                    merged_doc.insert_pdf(doc)
                    page_count = len(doc)
                    total_pages += page_count
                    successful_files.append(os.path.basename(path))
                    print(f"Added {page_count} pages from {os.path.basename(path)}")
                    doc.close()

                except Exception as e:
                    print(f"Skipping invalid PDF {path}: {str(e)}")
                    skipped_files.append(os.path.basename(path))
                    # Continue with others

            if total_pages == 0:
                print("No valid pages to merge")
                return None

            # Save to temp file (Windows-safe)
            fd, temp_path = tempfile.mkstemp(suffix='.pdf', prefix='meshpdf_merged_')
            try:
                os.close(fd)  # Close the file descriptor so PyMuPDF can write to it
            except:
                pass
            
            merged_doc.save(temp_path)
            merged_doc.close()

            print(f"Merged PDF created at: {temp_path}")
            print(f"Successfully merged: {', '.join(successful_files)}")
            print(f"Total pages: {total_pages}")
            
            if skipped_files:
                print(f"Skipped files: {', '.join(skipped_files)}")

            return temp_path

        except Exception as e:
            print(f"Merge error: {str(e)}")
            traceback.print_exc()
            # Clean up temp file if created but merge failed
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            return None
    
    def save_pdf(self, output_path):
        """Save the PDF with all modifications and proper transparency, accounting for zoom"""
        if not self.current_pdf:
            print("Error: No current PDF set")
            return False
            
        if not self.modifications:
            # If no modifications, just copy the original
            print("No modifications to apply, copying original PDF")
            try:
                shutil.copy2(self.current_pdf, output_path)
                return True
            except Exception as e:
                print(f"Error copying PDF: {str(e)}")
                return False
            
        temp_files = []
        try:
            print(f"Saving PDF with {len(self.modifications)} modifications")
            
            # Open the PDF with PyMuPDF
            doc = fitz.open(self.current_pdf)
            
            # Process each modification
            for i, mod in enumerate(self.modifications):
                try:
                    page = doc[mod['page']]
                    page_rect = page.rect
                    
                    # Account for scale factor and zoom level in position calculations
                    zoom_level = mod.get('zoom_level', 1.0)
                    scale_adjustment = 1.0 / (self.scale_factor * zoom_level)
                    
                    if mod['type'] == 'signature':
                        # Save signature to temporary PNG file with transparency
                        temp_path = f'temp_signature_{i}_{os.getpid()}.png'
                        temp_files.append(temp_path)
                        
                        # Save with transparency preserved
                        mod['image'].save(temp_path, format='PNG', compress_level=0)
                        
                        # Calculate position and size in PDF coordinates
                        x = mod['position'].x() * scale_adjustment
                        y = mod['position'].y() * scale_adjustment
                        width = mod['size'].width() * scale_adjustment
                        height = mod['size'].height() * scale_adjustment
                        
                        # Create rectangle for image insertion
                        rect = fitz.Rect(
                            x,
                            y,
                            x + width,
                            y + height
                        )
                        
                        # Verify the temp file exists and has content
                        if not os.path.exists(temp_path):
                            print(f"Warning: Temp file {temp_path} not found")
                            continue
                            
                        file_size = os.path.getsize(temp_path)
                        print(f"Temp signature file size: {file_size} bytes")
                        
                        # Insert image into PDF with transparency overlay
                        try:
                            # Use overlay=True to preserve transparency
                            page.insert_image(
                                rect,
                                filename=temp_path,
                                keep_proportion=True,
                                overlay=True,  # Important for transparency
                                rotate=0
                            )
                            print(f"Successfully inserted signature at rect: {rect}")
                        except Exception as img_error:
                            print(f"Error inserting image: {str(img_error)}")
                            # Try alternative method
                            img_doc = fitz.open(temp_path)
                            pix = img_doc[0].get_pixmap(alpha=True)
                            page.insert_image(rect, pixmap=pix, overlay=True)
                            img_doc.close()
                        
                    elif mod['type'] == 'text':
                        # Calculate position in PDF coordinates
                        x = mod['position'].x() * scale_adjustment
                        y = mod['position'].y() * scale_adjustment
                        
                        # Adjust font size for zoom
                        actual_font_size = mod['font_size'] / zoom_level
                        
                        # Adjust y coordinate for text baseline
                        y += actual_font_size  # Text baseline adjustment
                        
                        # Insert text into PDF
                        point = fitz.Point(x, y)
                        
                        # Create text insertion with proper font
                        text_dict = {
                            "text": mod['text'],
                            "fontsize": actual_font_size,
                            "color": (0, 0, 0),  # Black color
                            "fontname": "helv",  # Helvetica font
                            "render_mode": 0  # Fill mode
                        }
                        
                        page.insert_text(
                            point=point,
                            **text_dict
                        )
                        
                        print(f"Inserted text at ({x:.1f}, {y:.1f}) with size {actual_font_size:.1f}")
                        
                except Exception as e:
                    print(f"Error processing modification {i}: {str(e)}")
                    traceback.print_exc()
                    # Continue with other modifications even if one fails
                    
            # Save the modified PDF with compression
            doc.save(output_path, garbage=4, deflate=True, clean=True)
            doc.close()
            
            print(f"PDF saved successfully to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error saving PDF: {str(e)}")
            traceback.print_exc()
            return False
            
        finally:
            # Clean up all temp files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                        print(f"Removed temp file: {temp_file}")
                    except Exception as e:
                        print(f"Warning: Could not remove temp file {temp_file}: {str(e)}")
                    
            # Clear modifications after saving
            self.modifications.clear()

# Export class
__all__ = ['PDFEditor']