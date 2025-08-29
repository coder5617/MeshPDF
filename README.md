# 📄 MeshPDF - A Simple Easy To Use PDF Editor

A powerful yet simple PDF editor that lets you add signatures, text annotations, and combine multiple PDFs with ease.

## ✨ Features

- **📂 Open & View PDFs** - Load and display PDF files with high-quality rendering
- **✍️ Digital Signatures** - Draw signatures with your mouse/touchpad and place them anywhere
- **📝 Text Annotations** - Add text overlays to PDFs with drag-and-drop positioning
- **📑 Combine PDFs** - Merge multiple PDF files into one document
- **🔍 Zoom Controls** - Zoom in/out (25%-400%) for better viewing and editing
- **💾 Save Modified PDFs** - Export PDFs with all your annotations embedded
- **🖨️ Print Support** - Print PDFs with all modifications properly rendered
- **✏️ Edit/Delete Overlays** - Right-click to delete, double-click to edit annotations

## 🎯 What's New

### Interactive Editing
- **Right-click menu** on signatures/text for quick deletion
- **Double-click** signatures to redraw them
- **Double-click** text to edit content
- **Drag-and-drop** repositioning of all overlays

### Enhanced Zoom
- **🔍+ Zoom In** - Increases view by 25%
- **🔍- Zoom Out** - Decreases view by 20%
- **🔍↺ Reset** - Returns to 100% zoom
- Zoom range: 25% to 400%
- Maintains scroll position during zoom

### Improved UX
- Clear button visibility in signature pad
- Better temp file management
- Automatic page size detection for printing
- Warning prompts for unsaved changes

## 🛠️ Prerequisites

### Python Version
- Python 3.8 or higher

### Required Libraries
```bash
pip install PyQt6
pip install PyMuPDF
pip install Pillow
pip install numpy
```

Or install all at once:
```bash
pip install PyQt6 PyMuPDF Pillow numpy
```

## 📦 Installation & Setup

### 1. Clone or Download
Create a new directory for the project:
```bash
mkdir MeshPDF
cd MeshPDF
```

### 2. Save the Files
Save these four Python files in the MeshPDF directory:
- `main.py` - Main application window and UI
- `pdf_viewer.py` - PDF display and annotation handling
- `pdf_editor.py` - PDF modification and saving logic
- `signature_pad.py` - Signature drawing dialog

### 3. Install Dependencies
```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install required packages
pip install PyQt6 PyMuPDF Pillow numpy
```

## 🚀 Running the Application

```bash
python main.py
```

Or if you're using the virtual environment:
```bash
# Make sure venv is activated first
python main.py
```

## 📖 How to Use

### Basic Workflow
1. **Open a PDF** - Click "📂 Open" to load a PDF file
2. **Add Annotations**:
   - Click "✍️ Sign" to draw and place a signature
   - Click "📝 Text" to add text annotations
3. **Edit Annotations**:
   - **Drag** any annotation to reposition it
   - **Double-click** to edit (redraw signature or change text)
   - **Right-click** to delete
4. **Save or Print** - Click "💾 Save" to export or "🖨️ Print" to print

### Combining PDFs
1. Click "📑 Combine"
2. Select multiple PDF files (hold Ctrl/Cmd to select multiple)
3. Files will be merged in the order selected
4. The combined PDF opens automatically for editing

### Zoom Controls
- Use the zoom buttons (🔍-, 🔍↺, 🔍+) in the toolbar
- Current zoom level is displayed (e.g., "100%")
- Zoom persists while editing but resets when loading new PDFs

## 🏗️ Project Structure

```
MeshPDF/
├── main.py           # Main application and UI
├── pdf_viewer.py     # PDF display and interaction
├── pdf_editor.py     # PDF modification backend
├── signature_pad.py  # Signature drawing widget
└── README.md        # This file
```

## 🔧 Troubleshooting

### Common Issues

**Issue: "No module named 'PyQt6'"**
- Solution: Install PyQt6 with `pip install PyQt6`

**Issue: "No module named 'fitz'"**
- Solution: Install PyMuPDF with `pip install PyMuPDF`

**Issue: Signature appears with white background**
- Solution: This is a display issue; the saved PDF will have transparent signatures

**Issue: Text is too small/large after saving**
- Solution: Adjust zoom level before adding text, or edit the text size in the code

**Issue: Can't select multiple files when combining**
- Solution: Hold Ctrl (Windows/Linux) or Cmd (Mac) while clicking files

### Performance Tips
- For large PDFs (100+ pages), initial loading may take a few seconds
- Zoom operations re-render pages, which may be slow on older hardware
- Keep modifications minimal for faster saving

## 🛡️ Security Notes
- Temporary files are cleaned up automatically on exit
- No data is sent to external servers

## 🎨 Customization

### Changing Default Signature Size
In `pdf_viewer.py`, modify the signature scaling:
```python
base_width = int(200 * self.zoom_level)  # Change 200 to desired width
base_height = int(100 * self.zoom_level)  # Change 100 to desired height
```

### Changing Text Font Size
In `pdf_viewer.py`, modify the default font size:
```python
font.setPointSize(int(14 * self.zoom_level))  # Change 14 to desired size
```

### Changing Zoom Increments
In `main.py`, modify the zoom methods:
```python
def zoom_in(self):
    self.pdf_viewer.zoom(1.25)  # Change 1.25 for different increment

def zoom_out(self):
    self.pdf_viewer.zoom(0.8)   # Change 0.8 for different decrement
```

## 📝 Known Limitations
- Cannot edit existing PDF text, only add overlays
- Signature resize after placement not supported
- No multi-page view mode
- No rotation support for pages

## 🔄 Version History
- **v1.0** - Initial release with basic PDF editing
- **v2.0** - Added combine feature and smaller buttons
- **v3.0** - Added zoom, edit/delete overlays, improved UX (current)

## 📄 License
This is a demonstration project for educational purposes.

## 🤝 Contributing
Feel free to fork and improve! Key areas for enhancement:
- Add undo/redo stack
- Implement annotation resize handles
- Add page rotation
- Create multi-page thumbnail view
- Add keyboard shortcuts
- Implement annotation layers
- Wrapper to exe is needed

## 💡 Tips for Best Results
- Draw signatures slowly for smoother lines
- Use zoom for precise text placement
- Save your work frequently
- Test print settings with a single page first
- Keep original PDFs as backups

---
Built with Python, PyQt6, and PyMuPDF 🐍