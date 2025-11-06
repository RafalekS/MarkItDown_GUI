"""
Converter module with fallback strategies for robust document conversion.
Tries multiple converters in order: MarkItDown → Pypandoc → PyMuPDF (PDF only)
"""

import os
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class ConversionResult:
    """Result of a conversion attempt"""
    success: bool
    content: str
    converter_used: str
    error_message: Optional[str] = None


class MultiConverter:
    """
    Multi-strategy document converter with automatic fallback.
    Tries multiple conversion methods to maximize success rate.
    """

    def __init__(self):
        """Initialize converter with available backends"""
        self.available_converters = []
        self._check_available_converters()

    def _check_available_converters(self):
        """Check which converters are available"""
        # Check MarkItDown
        try:
            import markitdown
            self.available_converters.append('markitdown')
        except ImportError:
            pass

        # Check Pypandoc (NOT for PDFs - doesn't support PDF input)
        try:
            import pypandoc
            # Check if pandoc binary is available
            pypandoc.get_pandoc_version()
            self.available_converters.append('pypandoc')
        except (ImportError, OSError):
            pass

        # Check PyMuPDF for PDF handling
        try:
            import pymupdf4llm
            self.available_converters.append('pymupdf')
        except ImportError:
            pass

        # Check pdfplumber for PDF text extraction
        try:
            import pdfplumber
            self.available_converters.append('pdfplumber')
        except ImportError:
            pass

        # Check marker for advanced PDF conversion
        try:
            import marker
            self.available_converters.append('marker')
        except ImportError:
            pass

        # Check PyPDF2 for basic PDF text extraction
        try:
            import pypdf
            self.available_converters.append('pypdf')
        except ImportError:
            pass

        # Check OCR tools for scanned PDFs
        try:
            import pytesseract
            import pdf2image
            # Try to get tesseract version to verify it's installed
            pytesseract.get_tesseract_version()
            self.available_converters.append('ocr')
        except (ImportError, Exception):
            pass

    def convert_with_markitdown(self, file_path: str) -> ConversionResult:
        """
        Convert using Microsoft MarkItDown.
        Best for: Office docs, PDFs, images, audio, HTML, JSON, XML, ZIP
        """
        try:
            from markitdown import MarkItDown

            md = MarkItDown()
            result = md.convert(file_path)

            if result and result.text_content and len(result.text_content.strip()) > 0:
                return ConversionResult(
                    success=True,
                    content=result.text_content,
                    converter_used='MarkItDown'
                )
            else:
                return ConversionResult(
                    success=False,
                    content='',
                    converter_used='MarkItDown',
                    error_message='Conversion resulted in empty content'
                )

        except Exception as e:
            return ConversionResult(
                success=False,
                content='',
                converter_used='MarkItDown',
                error_message=str(e)
            )

    def convert_with_pypandoc(self, file_path: str) -> ConversionResult:
        """
        Convert using Pandoc (via pypandoc).
        Best for: Universal converter, handles most document formats
        """
        try:
            import pypandoc

            # Determine input format from file extension
            ext = Path(file_path).suffix.lower()

            # Map extensions to pandoc format names
            format_map = {
                '.pdf': 'pdf',
                '.docx': 'docx',
                '.doc': 'doc',
                '.html': 'html',
                '.htm': 'html',
                '.epub': 'epub',
                '.txt': 'plain',
                '.rtf': 'rtf',
                '.odt': 'odt',
                '.tex': 'latex',
                '.rst': 'rst',
            }

            input_format = format_map.get(ext)
            if not input_format:
                return ConversionResult(
                    success=False,
                    content='',
                    converter_used='Pypandoc',
                    error_message=f'Unsupported format: {ext}'
                )

            # Convert to markdown
            output = pypandoc.convert_file(
                file_path,
                'markdown',
                format=input_format,
                extra_args=['--wrap=none']  # Don't wrap long lines
            )

            if output and len(output.strip()) > 0:
                return ConversionResult(
                    success=True,
                    content=output,
                    converter_used='Pypandoc'
                )
            else:
                return ConversionResult(
                    success=False,
                    content='',
                    converter_used='Pypandoc',
                    error_message='Conversion resulted in empty content'
                )

        except Exception as e:
            return ConversionResult(
                success=False,
                content='',
                converter_used='Pypandoc',
                error_message=str(e)
            )

    def convert_with_pdfplumber(self, file_path: str) -> ConversionResult:
        """
        Convert PDF using pdfplumber.
        Best for: PDF files with tables and structured content
        """
        try:
            import pdfplumber

            # Only works with PDFs
            ext = Path(file_path).suffix.lower()
            if ext != '.pdf':
                return ConversionResult(
                    success=False,
                    content='',
                    converter_used='pdfplumber',
                    error_message='pdfplumber only handles PDF files'
                )

            # Extract text from PDF
            text_content = []
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Add page header
                    text_content.append(f"\n## Page {page_num}\n")

                    # Extract text
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)

                    # Extract tables
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            # Convert table to markdown
                            text_content.append("\n")
                            for row in table:
                                text_content.append("| " + " | ".join(str(cell) if cell else "" for cell in row) + " |")
                            text_content.append("\n")

            md_text = "\n".join(text_content)

            if md_text and len(md_text.strip()) > 0:
                return ConversionResult(
                    success=True,
                    content=md_text,
                    converter_used='pdfplumber'
                )
            else:
                return ConversionResult(
                    success=False,
                    content='',
                    converter_used='pdfplumber',
                    error_message='No text extracted from PDF'
                )

        except Exception as e:
            return ConversionResult(
                success=False,
                content='',
                converter_used='pdfplumber',
                error_message=str(e)
            )

    def convert_with_marker(self, file_path: str) -> ConversionResult:
        """
        Convert PDF using Marker (datalab-to).
        Best for: Complex PDFs, scientific papers, documents with tables and formulas
        """
        try:
            from marker.convert import convert_single_pdf
            from marker.models import load_all_models

            # Only works with PDFs
            ext = Path(file_path).suffix.lower()
            if ext != '.pdf':
                return ConversionResult(
                    success=False,
                    content='',
                    converter_used='marker',
                    error_message='Marker only handles PDF files'
                )

            # Load models (this may take time on first run)
            model_lst = load_all_models()

            # Convert PDF to markdown
            full_text, images, out_meta = convert_single_pdf(file_path, model_lst)

            if full_text and len(full_text.strip()) > 0:
                return ConversionResult(
                    success=True,
                    content=full_text,
                    converter_used='marker'
                )
            else:
                return ConversionResult(
                    success=False,
                    content='',
                    converter_used='marker',
                    error_message='No text extracted from PDF'
                )

        except Exception as e:
            return ConversionResult(
                success=False,
                content='',
                converter_used='marker',
                error_message=str(e)
            )

    def convert_with_pypdf(self, file_path: str) -> ConversionResult:
        """
        Convert PDF using PyPDF2 (pypdf).
        Best for: Simple PDFs with plain text (basic fallback)
        """
        try:
            from pypdf import PdfReader

            # Only works with PDFs
            ext = Path(file_path).suffix.lower()
            if ext != '.pdf':
                return ConversionResult(
                    success=False,
                    content='',
                    converter_used='pypdf',
                    error_message='PyPDF only handles PDF files'
                )

            # Extract text from PDF
            reader = PdfReader(file_path)
            text_content = []

            for page_num, page in enumerate(reader.pages, 1):
                text_content.append(f"\n## Page {page_num}\n")
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)

            md_text = "\n".join(text_content)

            if md_text and len(md_text.strip()) > 0:
                return ConversionResult(
                    success=True,
                    content=md_text,
                    converter_used='pypdf'
                )
            else:
                return ConversionResult(
                    success=False,
                    content='',
                    converter_used='pypdf',
                    error_message='No text extracted from PDF'
                )

        except Exception as e:
            return ConversionResult(
                success=False,
                content='',
                converter_used='pypdf',
                error_message=str(e)
            )

    def convert_with_ocr(self, file_path: str) -> ConversionResult:
        """
        Convert PDF using OCR (Optical Character Recognition).
        Best for: Scanned PDFs, image-based PDFs with no extractable text
        Requires: Tesseract-OCR system package
        """
        try:
            import pytesseract
            from pdf2image import convert_from_path

            # Only works with PDFs
            ext = Path(file_path).suffix.lower()
            if ext != '.pdf':
                return ConversionResult(
                    success=False,
                    content='',
                    converter_used='OCR',
                    error_message='OCR only handles PDF files'
                )

            # Convert PDF pages to images
            try:
                images = convert_from_path(file_path, dpi=300)
            except Exception as e:
                return ConversionResult(
                    success=False,
                    content='',
                    converter_used='OCR',
                    error_message=f'Failed to convert PDF to images: {str(e)}'
                )

            # OCR each page
            text_content = []
            for page_num, image in enumerate(images, 1):
                text_content.append(f"\n## Page {page_num}\n")

                # Perform OCR on the image
                try:
                    page_text = pytesseract.image_to_string(image, lang='eng')
                    if page_text:
                        text_content.append(page_text)
                except Exception as e:
                    text_content.append(f"[OCR Error on page {page_num}: {str(e)}]\n")

            md_text = "\n".join(text_content)

            if md_text and len(md_text.strip()) > 0:
                return ConversionResult(
                    success=True,
                    content=md_text,
                    converter_used='OCR (Tesseract)'
                )
            else:
                return ConversionResult(
                    success=False,
                    content='',
                    converter_used='OCR',
                    error_message='No text extracted via OCR'
                )

        except Exception as e:
            return ConversionResult(
                success=False,
                content='',
                converter_used='OCR',
                error_message=str(e)
            )

    def convert_with_pymupdf(self, file_path: str) -> ConversionResult:
        """
        Convert PDF using PyMuPDF4LLM.
        Best for: PDF files (specialized PDF handler)
        """
        try:
            import pymupdf4llm

            # Only works with PDFs
            ext = Path(file_path).suffix.lower()
            if ext != '.pdf':
                return ConversionResult(
                    success=False,
                    content='',
                    converter_used='PyMuPDF',
                    error_message='PyMuPDF only handles PDF files'
                )

            # Convert PDF to markdown
            md_text = pymupdf4llm.to_markdown(file_path)

            if md_text and len(md_text.strip()) > 0:
                return ConversionResult(
                    success=True,
                    content=md_text,
                    converter_used='PyMuPDF'
                )
            else:
                return ConversionResult(
                    success=False,
                    content='',
                    converter_used='PyMuPDF',
                    error_message='Conversion resulted in empty content'
                )

        except Exception as e:
            return ConversionResult(
                success=False,
                content='',
                converter_used='PyMuPDF',
                error_message=str(e)
            )

    def convert(self, file_path: str, preferred_converter: str = 'auto') -> ConversionResult:
        """
        Convert file to markdown with automatic fallback.

        Args:
            file_path: Path to file to convert
            preferred_converter: 'auto', 'markitdown', 'pypandoc', or 'pymupdf'

        Returns:
            ConversionResult with success status and content
        """
        if not os.path.exists(file_path):
            return ConversionResult(
                success=False,
                content='',
                converter_used='None',
                error_message=f'File not found: {file_path}'
            )

        ext = Path(file_path).suffix.lower()
        errors = []

        # Define conversion strategy based on file type and preference
        if preferred_converter != 'auto':
            # User specified a converter
            strategies = [preferred_converter]
        else:
            # Auto mode: define optimal strategy per file type
            if ext == '.pdf':
                # For PDFs: try multiple specialized converters
                # Note: pypandoc does NOT support PDF input
                # Order: MarkItDown (fast) → marker (accurate) → PyMuPDF → pdfplumber → pypdf → OCR (scanned)
                strategies = ['markitdown', 'marker', 'pymupdf', 'pdfplumber', 'pypdf', 'ocr']
            elif ext in ['.docx', '.pptx', '.xlsx']:
                # For Office: MarkItDown is best, then Pypandoc
                strategies = ['markitdown', 'pypandoc']
            elif ext in ['.html', '.htm']:
                # For HTML: Pypandoc is great, MarkItDown works too
                strategies = ['markitdown', 'pypandoc']
            else:
                # For others: try MarkItDown first, then Pypandoc
                strategies = ['markitdown', 'pypandoc']

        # Filter to only available converters
        strategies = [s for s in strategies if s in self.available_converters]

        if not strategies:
            return ConversionResult(
                success=False,
                content='',
                converter_used='None',
                error_message='No converters available. Install markitdown, pypandoc, or pymupdf4llm'
            )

        # Try each strategy in order
        for converter_name in strategies:
            if converter_name == 'markitdown':
                result = self.convert_with_markitdown(file_path)
            elif converter_name == 'pypandoc':
                result = self.convert_with_pypandoc(file_path)
            elif converter_name == 'pymupdf':
                result = self.convert_with_pymupdf(file_path)
            elif converter_name == 'pdfplumber':
                result = self.convert_with_pdfplumber(file_path)
            elif converter_name == 'marker':
                result = self.convert_with_marker(file_path)
            elif converter_name == 'pypdf':
                result = self.convert_with_pypdf(file_path)
            elif converter_name == 'ocr':
                result = self.convert_with_ocr(file_path)
            else:
                continue

            if result.success:
                return result
            else:
                errors.append(f"{result.converter_used}: {result.error_message}")

        # All converters failed
        return ConversionResult(
            success=False,
            content='',
            converter_used='All Failed',
            error_message=' | '.join(errors)
        )

    def get_available_converters(self) -> list:
        """Get list of available converters"""
        return self.available_converters.copy()
