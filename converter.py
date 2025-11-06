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

        # Check Pypandoc
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
                # For PDFs: try MarkItDown first, then specialized PDF tools
                strategies = ['markitdown', 'pymupdf', 'pypandoc']
            elif ext in ['.docx', '.pptx', '.xlsx']:
                # For Office: MarkItDown is best, then Pypandoc
                strategies = ['markitdown', 'pypandoc']
            elif ext in ['.html', '.htm']:
                # For HTML: Pypandoc is great, MarkItDown works too
                strategies = ['markitdown', 'pypandoc']
            else:
                # For others: try all in order
                strategies = ['markitdown', 'pypandoc', 'pymupdf']

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
