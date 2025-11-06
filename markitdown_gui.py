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
    QComboBox, QCheckBox
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
                 converter_preference: str = 'auto'):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.use_source_dir = use_source_dir
        self.converter_preference = converter_preference
        self._is_running = True

    def stop(self):
        """Stop the conversion process"""
        self._is_running = False

    def run(self):
        """Convert files in background thread"""
        try:
            # Initialize multi-converter
            converter = MultiConverter()
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
            "PyMuPDF Only (PDF)"
        ])
        self.converter_combo.setCurrentIndex(0)
        self.converter_combo.setToolTip(
            "Auto: Tries multiple converters for best results\n"
            "MarkItDown: Microsoft's converter (primary)\n"
            "Pypandoc: Universal converter (fallback)\n"
            "PyMuPDF: Specialized PDF converter"
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
            "• MarkItDown (Microsoft)\n"
            "• Pypandoc (Universal)\n"
            "• PyMuPDF (PDF specialist)\n\n"
            "Theme system from Fiori_Search"
        )

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
            "PyMuPDF Only (PDF)": "pymupdf"
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
            converter_pref
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
