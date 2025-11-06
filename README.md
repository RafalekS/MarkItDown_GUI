# MarkItDown GUI

A modern PyQt6 GUI application for converting various document formats to Markdown using Microsoft's [MarkItDown](https://github.com/microsoft/markitdown) library.

![MarkItDown GUI](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt-6-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Features

- **🎯 Multi-Converter Fallback System**: Automatically tries multiple converters for maximum success
  - **MarkItDown** (Microsoft) - Primary converter
  - **Pypandoc** (Universal) - Fallback for non-PDF formats
  - **PyMuPDF** - Specialized PDF converter #1
  - **pdfplumber** - Specialized PDF converter #2 (with table support)
- **🎨 47 Beautiful Themes**: Choose from a wide variety of color schemes (from Fiori_Search)
- **📦 Multi-format Support**: Convert PDF, DOCX, PPTX, XLSX, HTML, images, audio, and more
- **🎪 Enhanced Drag & Drop**: Visual drag-and-drop zone with clear indicators
- **💾 Smart Output**: Save converted files in the same directory as source files (default)
- **⚡ Batch Processing**: Convert multiple files at once
- **📊 Progress Tracking**: Real-time progress bar and detailed conversion log
- **🎛️ Converter Selection**: Choose your preferred converter or use auto-fallback
- **💻 User-Friendly Interface**: Clean, modern GUI built with PyQt6
- **💿 Persistent Settings**: Your theme and preferences are saved automatically
- **🌍 Cross-Platform**: Works on Windows, macOS, and Linux

## Supported File Formats

The application supports conversion of the following file formats to Markdown:

- **Office Documents**: DOCX, PPTX, XLSX, XLS
- **PDF**: PDF files
- **Web**: HTML, HTM
- **Text**: TXT, CSV, JSON, XML
- **Images**: JPG, JPEG, PNG (with optional LLM integration for descriptions)
- **Audio**: WAV, MP3 (transcribed to text)
- **Archives**: ZIP

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package installer)

### Install Dependencies

1. Clone this repository:
```bash
git clone https://github.com/RafalekS/MarkItDown_GUI.git
cd MarkItDown_GUI
```

2. **Install Pandoc** (required for fallback converter):
   - **Windows**: Download from [pandoc.org](https://pandoc.org/installing.html) or use `winget install pandoc`
   - **macOS**: `brew install pandoc`
   - **Linux**: `sudo apt install pandoc` (Ubuntu/Debian) or `sudo yum install pandoc` (RHEL/CentOS)

3. Install Python packages:
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install PyQt6 'markitdown[all]' pypandoc pymupdf4llm pdfplumber
```

## Usage

### Running the Application

Simply run the main script:

```bash
python markitdown_gui.py
```

Or make it executable (Linux/macOS):
```bash
chmod +x markitdown_gui.py
./markitdown_gui.py
```

### Using the GUI

1. **Choose a Theme** (Optional):
   - Go to the "Themes" menu at the top
   - Select from 47 beautiful color schemes
   - Your choice is saved automatically

2. **Select Converter Strategy**:
   - **Auto (Recommended)**: Automatically tries multiple converters for best results
   - **MarkItDown Only**: Use only Microsoft's converter
   - **Pypandoc Only**: Use only Pandoc (NOT for PDFs)
   - **PyMuPDF Only**: Use only PyMuPDF (for PDFs)
   - **pdfplumber Only**: Use only pdfplumber (for PDFs with tables)

3. **Add Files**:
   - **Drag and Drop**: Simply drag files or folders into the drop zone
   - Click "Add Files" to select individual files
   - Click "Add Folder" to add all supported files from a directory

4. **Configure Output**:
   - **Default (Recommended)**: Files are saved in the same directory as the source
   - **Custom Directory**: Uncheck the box and specify a custom output folder

5. **Convert**:
   - Click "Convert to Markdown" to start the conversion process
   - Watch the log to see which converter succeeded
   - Monitor progress in the progress bar
   - Click "Stop" to cancel if needed

6. **Manage Files**:
   - Select files in the list and click "Remove Selected" to remove them
   - Click "Clear All" to remove all files from the list

### Theme Gallery

The application includes 47 themes from various categories:

**Dark Themes**: Espresso, Atom, GruvboxDark, GitHub Dark, catppuccin-mocha, cyberpunk, ayu, Batman, matrix, The Hulk

**Light Themes**: Github, PencilLight, Novel, nord-light, zenbones, neobones_light, coffee_theme

**Colorful Themes**: Spiderman, Jackie Brown, MonaLisa, Sakura, Ocean, Red Alert, Grass

**And many more!** Try them all to find your favorite.

## Multi-Converter System

The application uses a smart fallback system to maximize conversion success:

### How It Works

1. **Auto Mode (Recommended)**:
   - For PDFs: MarkItDown → PyMuPDF → pdfplumber
   - For Office files: MarkItDown → Pypandoc
   - For HTML: MarkItDown → Pypandoc
   - Automatically selects the best strategy per file type
   - **Note**: Pypandoc does NOT support PDF input

2. **Manual Selection**:
   - Choose a specific converter if you know what works best
   - Useful for debugging or specific requirements

3. **Fallback Logic**:
   - If first converter fails or returns empty content
   - Automatically tries the next available converter
   - Shows which converter succeeded in the log

### Which Converter to Use?

- **MarkItDown**: Best for most files, especially Office documents and images
- **Pypandoc**: Universal converter for DOCX, HTML, and text formats (NOT for PDFs!)
- **PyMuPDF**: Specialized for PDFs, handles most PDF types
- **pdfplumber**: Excellent for PDFs with tables and structured content

## Advanced Usage

### LLM Integration for Images

MarkItDown can integrate with Large Language Models (like GPT-4) to generate descriptive captions for images. To enable this feature:

1. Install the OpenAI package:
```bash
pip install openai
```

2. Modify the `markitdown_gui.py` file to include your OpenAI API key:

```python
from openai import OpenAI

# In the ConversionWorker.run() method, replace:
md = MarkItDown()

# With:
client = OpenAI(api_key="your-api-key-here")
md = MarkItDown(llm_client=client, llm_model="gpt-4o")
```

## Project Structure

```
MarkItDown_GUI/
├── markitdown_gui.py    # Main application file
├── converter.py         # Multi-converter fallback system
├── theme_manager.py     # Theme management system
├── themes/
│   └── themes.json      # 47 color scheme definitions
├── config.json          # User preferences (auto-generated)
├── requirements.txt     # Python dependencies
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Technical Details

### Architecture

- **Main Window**: `MarkItDownGUI` class extends `QMainWindow`
- **Multi-Converter**: `MultiConverter` class handles fallback strategy
- **Worker Thread**: `ConversionWorker` class extends `QThread` for background processing
- **Theme Manager**: `ThemeManager` class loads and applies themes
- **Signals**: PyQt6 signals for thread-safe communication between worker and UI

### Key Components

1. **File Selection**: Multiple ways to add files (dialog, folder, drag-and-drop)
2. **Multi-Converter Engine**: Intelligent fallback system with 3 converters
3. **Progress Tracking**: Real-time updates via Qt signals
4. **Error Handling**: Graceful error handling with automatic fallback
5. **Theme System**: 47 pre-defined color schemes with live switching

## Dependencies

### Required
- **PyQt6**: Modern Python binding for Qt6 GUI framework
- **markitdown**: Microsoft's document-to-Markdown converter (primary)

### Highly Recommended
- **pypandoc**: Python wrapper for Pandoc (universal fallback for non-PDFs)
- **Pandoc**: Universal document converter (system package)
- **pymupdf4llm**: Specialized PDF converter
- **pdfplumber**: PDF text and table extractor

See `requirements.txt` for specific versions.

## Troubleshooting

### Common Issues

**"No module named 'markitdown'"**
- Solution: Install MarkItDown with `pip install 'markitdown[all]'`

**"No module named 'PyQt6'"**
- Solution: Install PyQt6 with `pip install PyQt6`

**Files not converting**
- Check the log area for specific error messages
- Ensure files are not corrupted
- Verify you have write permissions to the output directory
- For PDFs: Install `pip install pymupdf4llm pdfplumber` for better success
- **Note**: Some scanned PDFs (image-only) cannot be converted without OCR

**Images not generating descriptions**
- This requires LLM integration (see Advanced Usage section)
- Without LLM, images will be converted with basic metadata only

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Microsoft MarkItDown](https://github.com/microsoft/markitdown) - The underlying conversion library
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [Real Python Tutorial](https://realpython.com/python-markitdown/) - Excellent MarkItDown guide

## Resources

- [MarkItDown Documentation](https://github.com/microsoft/markitdown)
- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Python-Markdown](https://python-markdown.github.io/)
- [Pandoc](https://pandoc.org/)

## Author

Created with the help of Claude Code

## Support

For issues, questions, or suggestions, please open an issue on the [GitHub repository](https://github.com/RafalekS/MarkItDown_GUI/issues).
