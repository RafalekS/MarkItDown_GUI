# MarkItDown GUI

A modern PyQt6 GUI application for converting various document formats to Markdown using Microsoft's [MarkItDown](https://github.com/microsoft/markitdown) library.

![MarkItDown GUI](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt-6-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Features

- **Multi-format Support**: Convert various file formats to Markdown
- **Drag & Drop**: Simply drag and drop files or folders into the application
- **Batch Processing**: Convert multiple files at once
- **Progress Tracking**: Real-time progress bar and detailed conversion log
- **User-Friendly Interface**: Clean, modern GUI built with PyQt6
- **Cross-Platform**: Works on Windows, macOS, and Linux

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

2. Install required packages:
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install 'markitdown[all]' PyQt6
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

1. **Add Files**:
   - Click "Add Files" to select individual files
   - Click "Add Folder" to add all supported files from a directory
   - Drag and drop files or folders directly into the file list

2. **Select Output Directory**:
   - Specify where you want the converted Markdown files to be saved
   - Default is your Documents folder

3. **Convert**:
   - Click "Convert to Markdown" to start the conversion process
   - Monitor progress in the progress bar and log area
   - Click "Stop" to cancel the conversion if needed

4. **Manage Files**:
   - Select files in the list and click "Remove Selected" to remove them
   - Click "Clear All" to remove all files from the list

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
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Technical Details

### Architecture

- **Main Window**: `MarkItDownGUI` class extends `QMainWindow`
- **Worker Thread**: `ConversionWorker` class extends `QThread` for background processing
- **Signals**: PyQt6 signals for thread-safe communication between worker and UI

### Key Components

1. **File Selection**: Multiple ways to add files (dialog, folder, drag-and-drop)
2. **Conversion Engine**: Uses MarkItDown library for actual conversion
3. **Progress Tracking**: Real-time updates via Qt signals
4. **Error Handling**: Graceful error handling with user feedback

## Dependencies

- **markitdown**: Microsoft's document-to-Markdown converter
- **PyQt6**: Modern Python binding for Qt6 GUI framework

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
