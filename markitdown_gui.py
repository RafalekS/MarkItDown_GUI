#!/usr/bin/env python3
"""
MarkItDown GUI - A PyQt6 GUI for converting various document formats to Markdown
Supports: PDF, DOCX, PPTX, XLSX, XLS, HTML, TXT, CSV, JSON, XML, ZIP, JPG, PNG, WAV, MP3
"""

import sys
import os
import json
from pathlib import Path
from typing import List, Optional, Dict
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QLabel, QFileDialog, QTextEdit,
    QLineEdit, QGroupBox, QProgressBar, QMessageBox, QListWidgetItem,
    QComboBox, QCheckBox, QDialog, QTabWidget, QSpinBox, QFormLayout,
    QDoubleSpinBox, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QAction
from theme_manager import ThemeManager
from converter import MultiConverter, ConversionResult


class ConversionWorker(QThread):
    """Worker thread for converting files to markdown"""

    progress = pyqtSignal(int, int)  # current, total
    log = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str, str)  # filename, error message

    def __init__(self, files: List[str], output_dir: str, use_source_dir: bool = True,
                 converter_preference: str = 'auto', config: Dict = None):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.use_source_dir = use_source_dir
        self.converter_preference = converter_preference
        self.config = config or {}
        self._is_running = True

    def stop(self):
        """Stop the conversion process"""
        self._is_running = False

    def run(self):
        """Convert files in background thread"""
        try:
            # Initialize multi-converter with settings
            converter = MultiConverter(self.config)
            available = converter.get_available_converters()

            if not available:
                self.log.emit("⚠️ No converters available! Install: pip install 'markitdown[all]' pypandoc pymupdf4llm")
                return

            self.log.emit(f"🔧 Available converters: {', '.join(available)}")
            self.log.emit(f"📋 Strategy: {self.converter_preference}")

            total = len(self.files)

            for idx, file_path in enumerate(self.files):
                if not self._is_running:
                    self.log.emit("Conversion stopped by user")
                    break

                file_name = os.path.basename(file_path)

                try:
                    self.log.emit(f"Converting: {file_name}")

                    # Try conversion with fallback
                    result = converter.convert(file_path, self.converter_preference)

                    if not result.success:
                        raise Exception(result.error_message or "Conversion failed")

                    # Determine output directory
                    if self.use_source_dir:
                        # Use the same directory as the source file
                        output_dir = os.path.dirname(file_path)
                    else:
                        output_dir = self.output_dir

                    # Generate output filename
                    base_name = Path(file_path).stem
                    output_path = os.path.join(output_dir, f"{base_name}.md")

                    # Handle duplicate filenames
                    counter = 1
                    while os.path.exists(output_path):
                        output_path = os.path.join(output_dir, f"{base_name}_{counter}.md")
                        counter += 1

                    # Save markdown
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(result.content)

                    self.log.emit(f"✓ Saved: {output_path} (via {result.converter_used})")
                    self.progress.emit(idx + 1, total)

                except Exception as e:
                    error_msg = str(e)
                    self.error.emit(file_name, error_msg)
                    self.log.emit(f"✗ Error converting {file_name}: {error_msg}")
                    self.progress.emit(idx + 1, total)

            if self._is_running:
                self.log.emit("Conversion completed!")

        except Exception as e:
            self.log.emit(f"Fatal error: {str(e)}")
        finally:
            self.finished.emit()


class DragDropLabel(QLabel):
    """Custom label that shows drag and drop hint"""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                font-size: 14px;
                padding: 20px;
                opacity: 0.6;
            }
        """)


class DragDropListWidget(QListWidget):
    """Custom QListWidget with drag and drop support"""

    files_dropped = pyqtSignal(list)  # Signal emitted when files are dropped

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """Handle drag move event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        """Handle drop event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

            files = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path:
                    files.append(file_path)

            if files:
                self.files_dropped.emit(files)
        else:
            event.ignore()


class SettingsDialog(QDialog):
    """Comprehensive settings dialog for all converter configurations"""

    def __init__(self, config: Dict, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Converter Settings - Comprehensive Configuration")
        self.setMinimumSize(750, 650)
        self.init_ui()

    def init_ui(self):
        """Initialize the settings UI"""
        layout = QVBoxLayout(self)

        # Create tab widget
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.West)  # Tabs on left side for better navigation

        # Add all tabs
        tabs.addTab(self.create_markitdown_tab(), "📝 MarkItDown")
        tabs.addTab(self.create_ocr_tab(), "🔍 OCR/Tesseract")
        tabs.addTab(self.create_pymupdf_tab(), "📄 PyMuPDF")
        tabs.addTab(self.create_pdfplumber_tab(), "📊 pdfplumber")
        tabs.addTab(self.create_pypdf_tab(), "📑 PyPDF")
        tabs.addTab(self.create_marker_tab(), "🤖 Marker")
        tabs.addTab(self.create_pypandoc_tab(), "🔄 Pypandoc")
        tabs.addTab(self.create_general_tab(), "⚙️ General")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()

        reset_btn = QPushButton("Reset All to Defaults")
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_btn)

        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def create_markitdown_tab(self) -> QWidget:
        """Create MarkItDown settings tab"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QFormLayout(content)

        # LLM Integration Group
        llm_group = QGroupBox("LLM Integration (for Image Descriptions)")
        llm_layout = QFormLayout()

        self.md_llm_enable = QCheckBox()
        self.md_llm_enable.setChecked(self.config.get("md_llm_enable", False))
        self.md_llm_enable.setToolTip("Enable LLM for automatic image description generation")
        llm_layout.addRow("Enable LLM:", self.md_llm_enable)

        self.md_llm_provider = QComboBox()
        self.md_llm_provider.addItems(["OpenAI", "Azure OpenAI", "Anthropic Claude", "Local (Ollama)"])
        self.md_llm_provider.setCurrentIndex(self.config.get("md_llm_provider", 0))
        llm_layout.addRow("Provider:", self.md_llm_provider)

        self.md_llm_model = QLineEdit()
        self.md_llm_model.setText(self.config.get("md_llm_model", "gpt-4o"))
        self.md_llm_model.setPlaceholderText("e.g., gpt-4o, claude-3-opus-20240229, llama3")
        llm_layout.addRow("Model:", self.md_llm_model)

        self.md_llm_api_key = QLineEdit()
        self.md_llm_api_key.setText(self.config.get("md_llm_api_key", ""))
        self.md_llm_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.md_llm_api_key.setPlaceholderText("Your API key (stored in config.json)")
        llm_layout.addRow("API Key:", self.md_llm_api_key)

        self.md_llm_base_url = QLineEdit()
        self.md_llm_base_url.setText(self.config.get("md_llm_base_url", ""))
        self.md_llm_base_url.setPlaceholderText("Optional: http://localhost:11434/v1 for Ollama")
        llm_layout.addRow("Base URL:", self.md_llm_base_url)

        llm_group.setLayout(llm_layout)
        layout.addRow(llm_group)

        # Image Settings
        self.md_extract_images = QCheckBox()
        self.md_extract_images.setChecked(self.config.get("md_extract_images", False))
        self.md_extract_images.setToolTip("Extract and reference images in markdown")
        layout.addRow("Extract images:", self.md_extract_images)

        self.md_image_dir = QLineEdit()
        self.md_image_dir.setText(self.config.get("md_image_dir", "./images"))
        self.md_image_dir.setPlaceholderText("./images")
        self.md_image_dir.setToolTip("Directory to save extracted images")
        layout.addRow("Image directory:", self.md_image_dir)

        scroll.setWidget(content)
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(scroll)
        return tab

    def create_ocr_tab(self) -> QWidget:
        """Create OCR/Tesseract settings tab"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QFormLayout(content)

        # Basic OCR Settings
        self.ocr_dpi = QSpinBox()
        self.ocr_dpi.setRange(72, 600)
        self.ocr_dpi.setValue(self.config.get("ocr_dpi", 300))
        self.ocr_dpi.setSuffix(" DPI")
        self.ocr_dpi.setToolTip("Higher DPI = better quality but slower (recommended: 300)")
        layout.addRow("Image DPI:", self.ocr_dpi)

        self.ocr_language = QLineEdit()
        self.ocr_language.setText(self.config.get("ocr_language", "eng"))
        self.ocr_language.setToolTip("Language code: eng, fra, deu, spa, chi_sim, jpn, etc. Use + for multiple (eng+fra)")
        layout.addRow("Language(s):", self.ocr_language)

        # PSM Mode
        self.ocr_psm = QComboBox()
        psm_modes = [
            "0 - OSD only",
            "1 - Auto + OSD",
            "2 - Auto (no OSD)",
            "3 - Fully auto (default)",
            "4 - Single column",
            "5 - Vertical block",
            "6 - Uniform block",
            "7 - Single line",
            "8 - Single word",
            "9 - Word in circle",
            "10 - Single character",
            "11 - Sparse text",
            "12 - Sparse + OSD",
            "13 - Raw line"
        ]
        self.ocr_psm.addItems(psm_modes)
        self.ocr_psm.setCurrentIndex(self.config.get("ocr_psm", 3))
        self.ocr_psm.setToolTip("Page Segmentation Mode - how Tesseract analyzes layout")
        layout.addRow("PSM Mode:", self.ocr_psm)

        # OEM Mode
        self.ocr_oem = QComboBox()
        oem_modes = [
            "0 - Legacy only",
            "1 - LSTM only",
            "2 - Legacy + LSTM",
            "3 - Default"
        ]
        self.ocr_oem.addItems(oem_modes)
        self.ocr_oem.setCurrentIndex(self.config.get("ocr_oem", 3))
        self.ocr_oem.setToolTip("OCR Engine: LSTM is more accurate but slower")
        layout.addRow("Engine Mode:", self.ocr_oem)

        # Preprocessing
        preprocessing_group = QGroupBox("Preprocessing")
        prep_layout = QFormLayout()

        self.ocr_denoise = QCheckBox()
        self.ocr_denoise.setChecked(self.config.get("ocr_denoise", False))
        self.ocr_denoise.setToolTip("Remove noise from images before OCR")
        prep_layout.addRow("Denoise:", self.ocr_denoise)

        self.ocr_deskew = QCheckBox()
        self.ocr_deskew.setChecked(self.config.get("ocr_deskew", False))
        self.ocr_deskew.setToolTip("Automatically rotate skewed images")
        prep_layout.addRow("Deskew:", self.ocr_deskew)

        self.ocr_sharpen = QCheckBox()
        self.ocr_sharpen.setChecked(self.config.get("ocr_sharpen", False))
        self.ocr_sharpen.setToolTip("Sharpen images for better text recognition")
        prep_layout.addRow("Sharpen:", self.ocr_sharpen)

        self.ocr_threshold = QCheckBox()
        self.ocr_threshold.setChecked(self.config.get("ocr_threshold", False))
        self.ocr_threshold.setToolTip("Convert to black & white for better contrast")
        prep_layout.addRow("Threshold:", self.ocr_threshold)

        preprocessing_group.setLayout(prep_layout)
        layout.addRow(preprocessing_group)

        # Advanced
        self.ocr_whitelist = QLineEdit()
        self.ocr_whitelist.setText(self.config.get("ocr_whitelist", ""))
        self.ocr_whitelist.setPlaceholderText("e.g., 0123456789 for numbers only")
        self.ocr_whitelist.setToolTip("Only recognize these characters")
        layout.addRow("Whitelist chars:", self.ocr_whitelist)

        self.ocr_blacklist = QLineEdit()
        self.ocr_blacklist.setText(self.config.get("ocr_blacklist", ""))
        self.ocr_blacklist.setPlaceholderText("e.g., @#$% to ignore symbols")
        self.ocr_blacklist.setToolTip("Ignore these characters")
        layout.addRow("Blacklist chars:", self.ocr_blacklist)

        scroll.setWidget(content)
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(scroll)
        return tab

    def create_pymupdf_tab(self) -> QWidget:
        """Create PyMuPDF settings tab"""
        tab = QWidget()
        layout = QFormLayout(tab)

        # Page range
        self.pymupdf_pages = QLineEdit()
        self.pymupdf_pages.setText(self.config.get("pymupdf_pages", ""))
        self.pymupdf_pages.setPlaceholderText("e.g., 1-5, 10, 15-20 (empty = all)")
        self.pymupdf_pages.setToolTip("Specify page ranges to convert")
        layout.addRow("Page range:", self.pymupdf_pages)

        # Extract images
        self.pymupdf_images = QCheckBox()
        self.pymupdf_images.setChecked(self.config.get("pymupdf_images", True))
        self.pymupdf_images.setToolTip("Extract and save images from PDF")
        layout.addRow("Extract images:", self.pymupdf_images)

        # Table detection
        self.pymupdf_tables = QCheckBox()
        self.pymupdf_tables.setChecked(self.config.get("pymupdf_tables", True))
        self.pymupdf_tables.setToolTip("Detect and convert tables to markdown")
        layout.addRow("Detect tables:", self.pymupdf_tables)

        # Page numbers
        self.pymupdf_page_numbers = QCheckBox()
        self.pymupdf_page_numbers.setChecked(self.config.get("pymupdf_page_numbers", True))
        self.pymupdf_page_numbers.setToolTip("Include page number headers")
        layout.addRow("Page numbers:", self.pymupdf_page_numbers)

        # Margins
        margins_group = QGroupBox("Margin Settings (inches)")
        margins_layout = QFormLayout()

        self.pymupdf_margin_left = QDoubleSpinBox()
        self.pymupdf_margin_left.setRange(0, 5)
        self.pymupdf_margin_left.setValue(self.config.get("pymupdf_margin_left", 0.5))
        self.pymupdf_margin_left.setSingleStep(0.1)
        margins_layout.addRow("Left:", self.pymupdf_margin_left)

        self.pymupdf_margin_right = QDoubleSpinBox()
        self.pymupdf_margin_right.setRange(0, 5)
        self.pymupdf_margin_right.setValue(self.config.get("pymupdf_margin_right", 0.5))
        self.pymupdf_margin_right.setSingleStep(0.1)
        margins_layout.addRow("Right:", self.pymupdf_margin_right)

        self.pymupdf_margin_top = QDoubleSpinBox()
        self.pymupdf_margin_top.setRange(0, 5)
        self.pymupdf_margin_top.setValue(self.config.get("pymupdf_margin_top", 0.5))
        self.pymupdf_margin_top.setSingleStep(0.1)
        margins_layout.addRow("Top:", self.pymupdf_margin_top)

        self.pymupdf_margin_bottom = QDoubleSpinBox()
        self.pymupdf_margin_bottom.setRange(0, 5)
        self.pymupdf_margin_bottom.setValue(self.config.get("pymupdf_margin_bottom", 0.5))
        self.pymupdf_margin_bottom.setSingleStep(0.1)
        margins_layout.addRow("Bottom:", self.pymupdf_margin_bottom)

        margins_group.setLayout(margins_layout)
        layout.addRow(margins_group)

        return tab

    def create_pdfplumber_tab(self) -> QWidget:
        """Create pdfplumber settings tab"""
        tab = QWidget()
        layout = QFormLayout(tab)

        # Layout
        self.pdfp_layout = QCheckBox()
        self.pdfp_layout.setChecked(self.config.get("pdfplumber_layout", True))
        self.pdfp_layout.setToolTip("Preserve spatial layout of text")
        layout.addRow("Preserve layout:", self.pdfp_layout)

        # Table detection strategy
        self.pdfp_table_strategy = QComboBox()
        self.pdfp_table_strategy.addItems(["lines", "lines_strict", "text", "explicit"])
        strategy_index = ["lines", "lines_strict", "text", "explicit"].index(
            self.config.get("pdfplumber_table_strategy", "lines")
        )
        self.pdfp_table_strategy.setCurrentIndex(strategy_index)
        self.pdfp_table_strategy.setToolTip("How to detect table boundaries")
        layout.addRow("Table strategy:", self.pdfp_table_strategy)

        # Tolerance settings
        tolerance_group = QGroupBox("Tolerance Settings")
        tol_layout = QFormLayout()

        self.pdfp_x_tolerance = QSpinBox()
        self.pdfp_x_tolerance.setRange(0, 50)
        self.pdfp_x_tolerance.setValue(self.config.get("pdfplumber_x_tolerance", 3))
        self.pdfp_x_tolerance.setToolTip("Horizontal tolerance for grouping characters")
        tol_layout.addRow("X tolerance:", self.pdfp_x_tolerance)

        self.pdfp_y_tolerance = QSpinBox()
        self.pdfp_y_tolerance.setRange(0, 50)
        self.pdfp_y_tolerance.setValue(self.config.get("pdfplumber_y_tolerance", 3))
        self.pdfp_y_tolerance.setToolTip("Vertical tolerance for grouping characters")
        tol_layout.addRow("Y tolerance:", self.pdfp_y_tolerance)

        tolerance_group.setLayout(tol_layout)
        layout.addRow(tolerance_group)

        # Page range
        self.pdfp_pages = QLineEdit()
        self.pdfp_pages.setText(self.config.get("pdfplumber_pages", ""))
        self.pdfp_pages.setPlaceholderText("e.g., 1-5, 10 (empty = all)")
        layout.addRow("Page range:", self.pdfp_pages)

        return tab

    def create_pypdf_tab(self) -> QWidget:
        """Create PyPDF settings tab"""
        tab = QWidget()
        layout = QFormLayout(tab)

        # Password
        self.pypdf_password = QLineEdit()
        self.pypdf_password.setText(self.config.get("pypdf_password", ""))
        self.pypdf_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.pypdf_password.setPlaceholderText("For encrypted PDFs")
        self.pypdf_password.setToolTip("Password for encrypted/protected PDFs")
        layout.addRow("PDF Password:", self.pypdf_password)

        # Page range
        self.pypdf_pages = QLineEdit()
        self.pypdf_pages.setText(self.config.get("pypdf_pages", ""))
        self.pypdf_pages.setPlaceholderText("e.g., 1-5, 10 (empty = all)")
        layout.addRow("Page range:", self.pypdf_pages)

        # Extraction mode
        self.pypdf_mode = QComboBox()
        self.pypdf_mode.addItems(["Text only", "Text with layout", "Text + images"])
        self.pypdf_mode.setCurrentIndex(self.config.get("pypdf_mode", 0))
        layout.addRow("Extraction mode:", self.pypdf_mode)

        # Include page numbers
        self.pypdf_page_numbers = QCheckBox()
        self.pypdf_page_numbers.setChecked(self.config.get("pypdf_page_numbers", True))
        layout.addRow("Page number headers:", self.pypdf_page_numbers)

        return tab

    def create_marker_tab(self) -> QWidget:
        """Create Marker settings tab"""
        tab = QWidget()
        layout = QFormLayout(tab)

        # Max pages
        self.marker_max_pages = QSpinBox()
        self.marker_max_pages.setRange(0, 10000)
        self.marker_max_pages.setValue(self.config.get("marker_max_pages", 0))
        self.marker_max_pages.setSpecialValueText("Unlimited")
        self.marker_max_pages.setToolTip("Max pages to process (0 = all)")
        layout.addRow("Max pages:", self.marker_max_pages)

        # Languages
        self.marker_languages = QLineEdit()
        self.marker_languages.setText(self.config.get("marker_languages", ""))
        self.marker_languages.setPlaceholderText("e.g., English, Spanish")
        self.marker_languages.setToolTip("Expected languages (comma-separated)")
        layout.addRow("Languages:", self.marker_languages)

        # Batch multiplier
        self.marker_batch_multiplier = QSpinBox()
        self.marker_batch_multiplier.setRange(1, 10)
        self.marker_batch_multiplier.setValue(self.config.get("marker_batch_multiplier", 2))
        self.marker_batch_multiplier.setToolTip("Higher = faster but more memory (2 recommended)")
        layout.addRow("Batch multiplier:", self.marker_batch_multiplier)

        # OCR quality
        self.marker_ocr_quality = QComboBox()
        self.marker_ocr_quality.addItems(["Low (fast)", "Medium", "High (slow)"])
        self.marker_ocr_quality.setCurrentIndex(self.config.get("marker_ocr_quality", 1))
        layout.addRow("OCR quality:", self.marker_ocr_quality)

        # Extract images
        self.marker_extract_images = QCheckBox()
        self.marker_extract_images.setChecked(self.config.get("marker_extract_images", True))
        self.marker_extract_images.setToolTip("Extract images from PDF")
        layout.addRow("Extract images:", self.marker_extract_images)

        # Parallel processing
        self.marker_parallel = QCheckBox()
        self.marker_parallel.setChecked(self.config.get("marker_parallel", True))
        self.marker_parallel.setToolTip("Use parallel processing for speed")
        layout.addRow("Parallel processing:", self.marker_parallel)

        return tab

    def create_pypandoc_tab(self) -> QWidget:
        """Create Pypandoc settings tab"""
        tab = QWidget()
        layout = QFormLayout(tab)

        # No wrap
        self.pypandoc_wrap = QCheckBox()
        self.pypandoc_wrap.setChecked(not self.config.get("pypandoc_wrap", True))
        self.pypandoc_wrap.setToolTip("Disable line wrapping")
        layout.addRow("No wrap:", self.pypandoc_wrap)

        # Column width
        self.pypandoc_columns = QSpinBox()
        self.pypandoc_columns.setRange(40, 200)
        self.pypandoc_columns.setValue(self.config.get("pypandoc_columns", 80))
        self.pypandoc_columns.setToolTip("Column width for wrapping (if enabled)")
        layout.addRow("Column width:", self.pypandoc_columns)

        # Extract media
        self.pypandoc_extract_media = QCheckBox()
        self.pypandoc_extract_media.setChecked(self.config.get("pypandoc_extract_media", False))
        layout.addRow("Extract media:", self.pypandoc_extract_media)

        self.pypandoc_media_dir = QLineEdit()
        self.pypandoc_media_dir.setText(self.config.get("pypandoc_media_dir", "./media"))
        self.pypandoc_media_dir.setPlaceholderText("./media")
        layout.addRow("Media directory:", self.pypandoc_media_dir)

        # Smart typography
        self.pypandoc_smart = QCheckBox()
        self.pypandoc_smart.setChecked(self.config.get("pypandoc_smart", False))
        self.pypandoc_smart.setToolTip("Convert straight quotes to curly, --- to em-dashes, etc.")
        layout.addRow("Smart typography:", self.pypandoc_smart)

        # Table of contents
        self.pypandoc_toc = QCheckBox()
        self.pypandoc_toc.setChecked(self.config.get("pypandoc_toc", False))
        layout.addRow("Generate TOC:", self.pypandoc_toc)

        # Extra arguments
        self.pypandoc_extra_args = QLineEdit()
        self.pypandoc_extra_args.setText(self.config.get("pypandoc_extra_args", ""))
        self.pypandoc_extra_args.setPlaceholderText("Advanced: space-separated pandoc args")
        layout.addRow("Extra arguments:", self.pypandoc_extra_args)

        return tab

    def create_general_tab(self) -> QWidget:
        """Create General settings tab"""
        tab = QWidget()
        layout = QFormLayout(tab)

        # Output encoding
        self.general_encoding = QComboBox()
        self.general_encoding.addItems(["utf-8", "utf-16", "utf-8-sig", "ascii", "iso-8859-1", "cp1252"])
        encoding = self.config.get("output_encoding", "utf-8")
        index = self.general_encoding.findText(encoding)
        if index >= 0:
            self.general_encoding.setCurrentIndex(index)
        layout.addRow("Output encoding:", self.general_encoding)

        # Log verbosity
        self.general_log_level = QComboBox()
        self.general_log_level.addItems(["Minimal", "Normal", "Verbose", "Debug"])
        self.general_log_level.setCurrentIndex(self.config.get("log_level", 1))
        layout.addRow("Log verbosity:", self.general_log_level)

        # Performance
        perf_group = QGroupBox("Performance Settings")
        perf_layout = QFormLayout()

        self.general_timeout = QSpinBox()
        self.general_timeout.setRange(0, 600)
        self.general_timeout.setValue(self.config.get("conversion_timeout", 300))
        self.general_timeout.setSuffix(" seconds")
        self.general_timeout.setSpecialValueText("No timeout")
        self.general_timeout.setToolTip("Maximum time per file (0 = unlimited)")
        perf_layout.addRow("Timeout:", self.general_timeout)

        self.general_max_filesize = QSpinBox()
        self.general_max_filesize.setRange(0, 10000)
        self.general_max_filesize.setValue(self.config.get("max_filesize_mb", 0))
        self.general_max_filesize.setSuffix(" MB")
        self.general_max_filesize.setSpecialValueText("No limit")
        self.general_max_filesize.setToolTip("Skip files larger than this (0 = no limit)")
        perf_layout.addRow("Max file size:", self.general_max_filesize)

        self.general_parallel = QCheckBox()
        self.general_parallel.setChecked(self.config.get("parallel_processing", False))
        self.general_parallel.setToolTip("Process multiple files simultaneously (experimental)")
        perf_layout.addRow("Parallel processing:", self.general_parallel)

        self.general_num_workers = QSpinBox()
        self.general_num_workers.setRange(1, 16)
        self.general_num_workers.setValue(self.config.get("num_workers", 4))
        self.general_num_workers.setToolTip("Number of parallel workers")
        perf_layout.addRow("Worker threads:", self.general_num_workers)

        perf_group.setLayout(perf_layout)
        layout.addRow(perf_group)

        # Error handling
        error_group = QGroupBox("Error Handling")
        error_layout = QFormLayout()

        self.general_continue_on_error = QCheckBox()
        self.general_continue_on_error.setChecked(self.config.get("continue_on_error", True))
        error_layout.addRow("Continue on error:", self.general_continue_on_error)

        self.general_save_error_log = QCheckBox()
        self.general_save_error_log.setChecked(self.config.get("save_error_log", False))
        error_layout.addRow("Save error log:", self.general_save_error_log)

        error_group.setLayout(error_layout)
        layout.addRow(error_group)

        return tab

    def reset_to_defaults(self):
        """Reset all settings to default values"""
        # MarkItDown
        self.md_llm_enable.setChecked(False)
        self.md_llm_provider.setCurrentIndex(0)
        self.md_llm_model.setText("gpt-4o")
        self.md_llm_api_key.setText("")
        self.md_llm_base_url.setText("")
        self.md_extract_images.setChecked(False)
        self.md_image_dir.setText("./images")

        # OCR
        self.ocr_dpi.setValue(300)
        self.ocr_language.setText("eng")
        self.ocr_psm.setCurrentIndex(3)
        self.ocr_oem.setCurrentIndex(3)
        self.ocr_denoise.setChecked(False)
        self.ocr_deskew.setChecked(False)
        self.ocr_sharpen.setChecked(False)
        self.ocr_threshold.setChecked(False)
        self.ocr_whitelist.setText("")
        self.ocr_blacklist.setText("")

        # PyMuPDF
        self.pymupdf_pages.setText("")
        self.pymupdf_images.setChecked(True)
        self.pymupdf_tables.setChecked(True)
        self.pymupdf_page_numbers.setChecked(True)
        self.pymupdf_margin_left.setValue(0.5)
        self.pymupdf_margin_right.setValue(0.5)
        self.pymupdf_margin_top.setValue(0.5)
        self.pymupdf_margin_bottom.setValue(0.5)

        # pdfplumber
        self.pdfp_layout.setChecked(True)
        self.pdfp_table_strategy.setCurrentIndex(0)
        self.pdfp_x_tolerance.setValue(3)
        self.pdfp_y_tolerance.setValue(3)
        self.pdfp_pages.setText("")

        # PyPDF
        self.pypdf_password.setText("")
        self.pypdf_pages.setText("")
        self.pypdf_mode.setCurrentIndex(0)
        self.pypdf_page_numbers.setChecked(True)

        # Marker
        self.marker_max_pages.setValue(0)
        self.marker_languages.setText("")
        self.marker_batch_multiplier.setValue(2)
        self.marker_ocr_quality.setCurrentIndex(1)
        self.marker_extract_images.setChecked(True)
        self.marker_parallel.setChecked(True)

        # Pypandoc
        self.pypandoc_wrap.setChecked(True)
        self.pypandoc_columns.setValue(80)
        self.pypandoc_extract_media.setChecked(False)
        self.pypandoc_media_dir.setText("./media")
        self.pypandoc_smart.setChecked(False)
        self.pypandoc_toc.setChecked(False)
        self.pypandoc_extra_args.setText("")

        # General
        self.general_encoding.setCurrentIndex(0)
        self.general_log_level.setCurrentIndex(1)
        self.general_timeout.setValue(300)
        self.general_max_filesize.setValue(0)
        self.general_parallel.setChecked(False)
        self.general_num_workers.setValue(4)
        self.general_continue_on_error.setChecked(True)
        self.general_save_error_log.setChecked(False)

    def get_settings(self) -> Dict:
        """Get current settings as dictionary"""
        return {
            # MarkItDown
            "md_llm_enable": self.md_llm_enable.isChecked(),
            "md_llm_provider": self.md_llm_provider.currentIndex(),
            "md_llm_model": self.md_llm_model.text(),
            "md_llm_api_key": self.md_llm_api_key.text(),
            "md_llm_base_url": self.md_llm_base_url.text(),
            "md_extract_images": self.md_extract_images.isChecked(),
            "md_image_dir": self.md_image_dir.text(),

            # OCR
            "ocr_dpi": self.ocr_dpi.value(),
            "ocr_language": self.ocr_language.text(),
            "ocr_psm": self.ocr_psm.currentIndex(),
            "ocr_oem": self.ocr_oem.currentIndex(),
            "ocr_denoise": self.ocr_denoise.isChecked(),
            "ocr_deskew": self.ocr_deskew.isChecked(),
            "ocr_sharpen": self.ocr_sharpen.isChecked(),
            "ocr_threshold": self.ocr_threshold.isChecked(),
            "ocr_whitelist": self.ocr_whitelist.text(),
            "ocr_blacklist": self.ocr_blacklist.text(),

            # PyMuPDF
            "pymupdf_pages": self.pymupdf_pages.text(),
            "pymupdf_images": self.pymupdf_images.isChecked(),
            "pymupdf_tables": self.pymupdf_tables.isChecked(),
            "pymupdf_page_numbers": self.pymupdf_page_numbers.isChecked(),
            "pymupdf_margin_left": self.pymupdf_margin_left.value(),
            "pymupdf_margin_right": self.pymupdf_margin_right.value(),
            "pymupdf_margin_top": self.pymupdf_margin_top.value(),
            "pymupdf_margin_bottom": self.pymupdf_margin_bottom.value(),

            # pdfplumber
            "pdfplumber_layout": self.pdfp_layout.isChecked(),
            "pdfplumber_table_strategy": self.pdfp_table_strategy.currentText(),
            "pdfplumber_x_tolerance": self.pdfp_x_tolerance.value(),
            "pdfplumber_y_tolerance": self.pdfp_y_tolerance.value(),
            "pdfplumber_pages": self.pdfp_pages.text(),

            # PyPDF
            "pypdf_password": self.pypdf_password.text(),
            "pypdf_pages": self.pypdf_pages.text(),
            "pypdf_mode": self.pypdf_mode.currentIndex(),
            "pypdf_page_numbers": self.pypdf_page_numbers.isChecked(),

            # Marker
            "marker_max_pages": self.marker_max_pages.value(),
            "marker_languages": self.marker_languages.text(),
            "marker_batch_multiplier": self.marker_batch_multiplier.value(),
            "marker_ocr_quality": self.marker_ocr_quality.currentIndex(),
            "marker_extract_images": self.marker_extract_images.isChecked(),
            "marker_parallel": self.marker_parallel.isChecked(),

            # Pypandoc
            "pypandoc_wrap": not self.pypandoc_wrap.isChecked(),
            "pypandoc_columns": self.pypandoc_columns.value(),
            "pypandoc_extract_media": self.pypandoc_extract_media.isChecked(),
            "pypandoc_media_dir": self.pypandoc_media_dir.text(),
            "pypandoc_smart": self.pypandoc_smart.isChecked(),
            "pypandoc_toc": self.pypandoc_toc.isChecked(),
            "pypandoc_extra_args": self.pypandoc_extra_args.text(),

            # General
            "output_encoding": self.general_encoding.currentText(),
            "log_level": self.general_log_level.currentIndex(),
            "conversion_timeout": self.general_timeout.value(),
            "max_filesize_mb": self.general_max_filesize.value(),
            "parallel_processing": self.general_parallel.isChecked(),
            "num_workers": self.general_num_workers.value(),
            "continue_on_error": self.general_continue_on_error.isChecked(),
            "save_error_log": self.general_save_error_log.isChecked(),
        }
class MarkItDownGUI(QMainWindow):
    """Main GUI window for MarkItDown converter"""

    SUPPORTED_FORMATS = [
        "PDF Files (*.pdf)",
        "Word Documents (*.docx)",
        "PowerPoint (*.pptx)",
        "Excel (*.xlsx *.xls)",
        "HTML Files (*.html *.htm)",
        "Text Files (*.txt)",
        "CSV Files (*.csv)",
        "JSON Files (*.json)",
        "XML Files (*.xml)",
        "ZIP Archives (*.zip)",
        "Images (*.jpg *.jpeg *.png)",
        "Audio Files (*.wav *.mp3)",
        "All Supported Files (*.pdf *.docx *.pptx *.xlsx *.xls *.html *.htm *.txt *.csv *.json *.xml *.zip *.jpg *.jpeg *.png *.wav *.mp3)"
    ]

    def __init__(self):
        super().__init__()
        self.files_to_convert: List[str] = []
        self.worker: Optional[ConversionWorker] = None
        self.theme_manager = ThemeManager()
        self.config_file = Path(__file__).parent / "config.json"
        self.config = self.load_config()
        self.init_ui()
        self.apply_saved_theme()

    def load_config(self) -> Dict:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
        return {"theme": "Espresso", "use_source_dir": True}

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def apply_saved_theme(self):
        """Apply the saved theme from config"""
        theme_name = self.config.get("theme", "Espresso")
        if theme_name in self.theme_manager.get_theme_names():
            self.theme_manager.apply_theme(QApplication.instance(), theme_name)

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("MarkItDown GUI - Document to Markdown Converter")
        self.setMinimumSize(900, 700)

        # Create menu bar
        self.create_menu_bar()

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Title
        title_label = QLabel("MarkItDown - Convert Documents to Markdown")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # File selection group
        file_group = QGroupBox("Input Files")
        file_layout = QVBoxLayout()

        # Drag and drop hint label
        self.drag_hint_label = DragDropLabel(
            "📁 Drag and drop files or folders here 📁\n"
            "or use the buttons below to add files"
        )
        file_layout.addWidget(self.drag_hint_label)

        # File list with drag-drop support
        self.file_list = DragDropListWidget()
        self.file_list.files_dropped.connect(self.handle_dropped_files)
        self.file_list.setMinimumHeight(150)
        file_layout.addWidget(self.file_list)

        # File buttons
        file_btn_layout = QHBoxLayout()

        add_files_btn = QPushButton("Add Files")
        add_files_btn.clicked.connect(self.add_files)
        file_btn_layout.addWidget(add_files_btn)

        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(self.add_folder)
        file_btn_layout.addWidget(add_folder_btn)

        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_selected)
        file_btn_layout.addWidget(remove_btn)

        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_all)
        file_btn_layout.addWidget(clear_btn)

        file_layout.addLayout(file_btn_layout)
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)

        # Output directory group
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout()

        # Converter strategy selection
        converter_layout = QHBoxLayout()
        converter_layout.addWidget(QLabel("Converter Strategy:"))
        self.converter_combo = QComboBox()
        self.converter_combo.addItems([
            "Auto (Smart Fallback)",
            "MarkItDown Only",
            "Pypandoc Only",
            "Marker Only (PDF - Best)",
            "PyMuPDF Only (PDF)",
            "pdfplumber Only (PDF)",
            "PyPDF Only (PDF - Simple)",
            "OCR Only (Scanned PDFs)"
        ])
        self.converter_combo.setCurrentIndex(0)
        self.converter_combo.setToolTip(
            "Auto: Tries multiple converters for best results (6 for PDFs!)\n"
            "MarkItDown: Microsoft's converter (fast, primary)\n"
            "Pypandoc: Universal converter (NOT for PDFs)\n"
            "Marker: Advanced PDF converter (best for complex PDFs)\n"
            "PyMuPDF: Fast PDF converter\n"
            "pdfplumber: PDF text & table extractor\n"
            "PyPDF: Simple PDF text extractor (basic)\n"
            "OCR: For scanned PDFs (requires Tesseract)"
        )
        converter_layout.addWidget(self.converter_combo)
        converter_layout.addStretch()
        output_layout.addLayout(converter_layout)

        # Use source directory checkbox
        self.use_source_dir_checkbox = QCheckBox(
            "✓ Save converted files in the same directory as source files (Recommended)"
        )
        self.use_source_dir_checkbox.setChecked(self.config.get("use_source_dir", True))
        self.use_source_dir_checkbox.stateChanged.connect(self.on_use_source_dir_changed)
        output_layout.addWidget(self.use_source_dir_checkbox)

        # Output directory selection
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(QLabel("Custom Output Directory:"))
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setText(os.path.expanduser("~/Documents"))
        self.output_dir_edit.setEnabled(not self.use_source_dir_checkbox.isChecked())
        output_dir_layout.addWidget(self.output_dir_edit)

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_output_dir)
        browse_btn.setEnabled(not self.use_source_dir_checkbox.isChecked())
        self.browse_btn = browse_btn
        output_dir_layout.addWidget(browse_btn)

        output_layout.addLayout(output_dir_layout)
        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        # Log area
        log_group = QGroupBox("Conversion Log")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)

        log_btn_layout = QHBoxLayout()
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.log_text.clear)
        log_btn_layout.addWidget(clear_log_btn)
        log_btn_layout.addStretch()
        log_layout.addLayout(log_btn_layout)

        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        # Convert button
        convert_btn_layout = QHBoxLayout()
        convert_btn_layout.addStretch()

        self.convert_btn = QPushButton("🚀 Convert to Markdown")
        self.convert_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 10px 20px;
            }
        """)
        self.convert_btn.clicked.connect(self.start_conversion)
        convert_btn_layout.addWidget(self.convert_btn)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 10px 20px;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_conversion)
        self.stop_btn.setVisible(False)
        convert_btn_layout.addWidget(self.stop_btn)

        convert_btn_layout.addStretch()
        main_layout.addLayout(convert_btn_layout)

        # Status bar
        self.statusBar().showMessage("Ready - Drag and drop files to get started!")

        # Info label
        info_label = QLabel(
            "Supported formats: PDF, DOCX, PPTX, XLSX, XLS, HTML, TXT, CSV, JSON, XML, ZIP, JPG, PNG, WAV, MP3"
        )
        info_label.setStyleSheet("color: gray; font-size: 10px; padding: 5px;")
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)

        # Update drag hint visibility
        self.update_drag_hint_visibility()

    def create_menu_bar(self):
        """Create menu bar with theme selection"""
        menubar = self.menuBar()

        # Settings menu
        settings_menu = menubar.addMenu("⚙️ Settings")

        converter_settings_action = QAction("Converter Settings", self)
        converter_settings_action.triggered.connect(self.show_settings)
        settings_menu.addAction(converter_settings_action)

        # Themes menu
        themes_menu = menubar.addMenu("🎨 Themes")

        # Get all theme names
        theme_names = self.theme_manager.get_theme_names()
        current_theme = self.config.get("theme", "Espresso")

        # Create theme actions
        for theme_name in theme_names:
            action = QAction(theme_name, self)
            action.setCheckable(True)
            if theme_name == current_theme:
                action.setChecked(True)
            action.triggered.connect(lambda checked, name=theme_name: self.change_theme(name))
            themes_menu.addAction(action)

        # Help menu
        help_menu = menubar.addMenu("❓ Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def change_theme(self, theme_name: str):
        """Change the application theme"""
        self.theme_manager.apply_theme(QApplication.instance(), theme_name)
        self.config["theme"] = theme_name
        self.save_config()

        # Update checkmarks in menu
        for action in self.menuBar().actions()[0].menu().actions():
            action.setChecked(action.text() == theme_name)

        self.log(f"Theme changed to: {theme_name}")

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About MarkItDown GUI",
            "MarkItDown GUI v3.0\n\n"
            "A PyQt6 GUI for converting various document formats to Markdown.\n\n"
            "Features:\n"
            "• 47 beautiful themes\n"
            "• Multi-converter fallback system\n"
            "• Enhanced drag and drop support\n"
            "• Batch conversion\n"
            "• Multiple file format support\n"
            "• Smart output directory\n\n"
            "Converters:\n"
            "• MarkItDown (Microsoft - Fast)\n"
            "• Marker (Complex PDFs - Best)\n"
            "• PyMuPDF (PDF - Fast)\n"
            "• pdfplumber (PDF tables)\n"
            "• PyPDF (PDF - Simple)\n"
            "• OCR/Tesseract (Scanned PDFs)\n"
            "• Pypandoc (NOT for PDFs)\n\n"
            "Theme system from Fiori_Search"
        )

    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update config with new settings
            new_settings = dialog.get_settings()
            self.config.update(new_settings)
            self.save_config()
            self.log("Settings saved successfully")

    def on_use_source_dir_changed(self, state):
        """Handle use source directory checkbox change"""
        use_source = state == Qt.CheckState.Checked.value
        self.config["use_source_dir"] = use_source
        self.save_config()

        # Enable/disable custom directory controls
        self.output_dir_edit.setEnabled(not use_source)
        self.browse_btn.setEnabled(not use_source)

    def update_drag_hint_visibility(self):
        """Show or hide drag hint label based on file list"""
        self.drag_hint_label.setVisible(len(self.files_to_convert) == 0)

    def handle_dropped_files(self, file_paths: List[str]):
        """Handle files dropped onto the list widget"""
        files = []
        for file_path in file_paths:
            if os.path.isfile(file_path):
                files.append(file_path)
            elif os.path.isdir(file_path):
                files.extend(self.get_supported_files_from_dir(file_path))

        if files:
            self.add_files_to_list(files)
            self.log(f"📥 Added {len(files)} file(s) via drag and drop")

    def add_files(self):
        """Open file dialog to add files"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files to Convert",
            "",
            ";;".join(self.SUPPORTED_FORMATS)
        )

        if files:
            self.add_files_to_list(files)
            self.log(f"Added {len(files)} file(s)")

    def add_folder(self):
        """Open folder dialog to add all supported files from a folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            ""
        )

        if folder:
            files = self.get_supported_files_from_dir(folder)
            if files:
                self.add_files_to_list(files)
                self.log(f"Added {len(files)} file(s) from folder")
            else:
                self.log("⚠️ No supported files found in the selected folder")

    def get_supported_files_from_dir(self, directory: str) -> List[str]:
        """Get all supported files from a directory"""
        supported_extensions = {
            '.pdf', '.docx', '.pptx', '.xlsx', '.xls', '.html', '.htm',
            '.txt', '.csv', '.json', '.xml', '.zip', '.jpg', '.jpeg',
            '.png', '.wav', '.mp3'
        }

        files = []
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                if Path(filename).suffix.lower() in supported_extensions:
                    files.append(os.path.join(root, filename))

        return files

    def add_files_to_list(self, files: List[str]):
        """Add files to the list widget"""
        added = 0
        for file_path in files:
            if file_path not in self.files_to_convert:
                self.files_to_convert.append(file_path)
                item = QListWidgetItem(f"📄 {file_path}")
                self.file_list.addItem(item)
                added += 1

        if added > 0:
            self.statusBar().showMessage(f"Total files: {len(self.files_to_convert)}")
            self.update_drag_hint_visibility()

    def remove_selected(self):
        """Remove selected files from the list"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            file_path = item.text().replace("📄 ", "")
            if file_path in self.files_to_convert:
                self.files_to_convert.remove(file_path)
            self.file_list.takeItem(self.file_list.row(item))

        self.log(f"Removed {len(selected_items)} file(s)")
        self.statusBar().showMessage(f"Total files: {len(self.files_to_convert)}")
        self.update_drag_hint_visibility()

    def clear_all(self):
        """Clear all files from the list"""
        self.files_to_convert.clear()
        self.file_list.clear()
        self.log("Cleared all files")
        self.statusBar().showMessage("Ready - Drag and drop files to get started!")
        self.update_drag_hint_visibility()

    def browse_output_dir(self):
        """Browse for output directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.output_dir_edit.text()
        )

        if directory:
            self.output_dir_edit.setText(directory)

    def log(self, message: str):
        """Add message to log"""
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def start_conversion(self):
        """Start the conversion process"""
        if not self.files_to_convert:
            QMessageBox.warning(
                self,
                "No Files",
                "Please add files to convert first.\n\n"
                "Tip: Drag and drop files into the file list!"
            )
            return

        use_source_dir = self.use_source_dir_checkbox.isChecked()
        output_dir = self.output_dir_edit.text()

        if not use_source_dir and not output_dir:
            QMessageBox.warning(
                self,
                "No Output Directory",
                "Please specify an output directory or enable 'Use source directory'."
            )
            return

        # Create output directory if it doesn't exist and not using source dir
        if not use_source_dir:
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to create output directory: {str(e)}"
                )
                return

        # Disable UI elements
        self.convert_btn.setVisible(False)
        self.stop_btn.setVisible(True)
        self.file_list.setEnabled(False)
        self.statusBar().showMessage("Converting...")

        # Clear log
        self.log_text.clear()
        self.log("🚀 Starting conversion...")
        self.log(f"📊 Files to convert: {len(self.files_to_convert)}")

        # Get converter preference
        converter_map = {
            "Auto (Smart Fallback)": "auto",
            "MarkItDown Only": "markitdown",
            "Pypandoc Only": "pypandoc",
            "Marker Only (PDF - Best)": "marker",
            "PyMuPDF Only (PDF)": "pymupdf",
            "pdfplumber Only (PDF)": "pdfplumber",
            "PyPDF Only (PDF - Simple)": "pypdf",
            "OCR Only (Scanned PDFs)": "ocr"
        }
        converter_pref = converter_map.get(
            self.converter_combo.currentText(),
            "auto"
        )

        # Create and start worker thread
        self.worker = ConversionWorker(
            self.files_to_convert.copy(),
            output_dir,
            use_source_dir,
            converter_pref,
            self.config
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.log.connect(self.log)
        self.worker.error.connect(self.handle_error)
        self.worker.finished.connect(self.conversion_finished)
        self.worker.start()

    def stop_conversion(self):
        """Stop the conversion process"""
        if self.worker and self.worker.isRunning():
            self.log("⏹ Stopping conversion...")
            self.worker.stop()
            self.worker.wait()

    def update_progress(self, current: int, total: int):
        """Update progress bar"""
        progress = int((current / total) * 100)
        self.progress_bar.setValue(progress)
        self.statusBar().showMessage(f"Converting: {current}/{total} files ({progress}%)")

    def handle_error(self, filename: str, error_msg: str):
        """Handle conversion error"""
        # Log is already updated by the worker
        pass

    def conversion_finished(self):
        """Handle conversion completion"""
        # Re-enable UI elements
        self.convert_btn.setVisible(True)
        self.stop_btn.setVisible(False)
        self.file_list.setEnabled(True)
        self.statusBar().showMessage("✓ Conversion complete")

        # Show completion message
        use_source_dir = self.use_source_dir_checkbox.isChecked()
        if use_source_dir:
            msg = f"✓ Converted {len(self.files_to_convert)} file(s) to Markdown.\n\n" \
                  f"Files saved in their respective source directories."
        else:
            msg = f"✓ Converted {len(self.files_to_convert)} file(s) to Markdown.\n\n" \
                  f"Output directory: {self.output_dir_edit.text()}"

        QMessageBox.information(
            self,
            "Conversion Complete",
            msg
        )

        # Reset progress bar
        self.progress_bar.setValue(0)

        # Clear file list
        self.clear_all()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Create and show main window
    window = MarkItDownGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
