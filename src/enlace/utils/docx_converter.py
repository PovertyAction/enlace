"""DOCX/DOC to PDF converter using LibreOffice headless mode.

This module provides utilities for converting Microsoft Word documents to PDF
format for compatibility with PDF-only extraction tools like Camelot.
"""

import logging
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger("enlace.docx_converter")


class DocxConverterError(Exception):
    """Raised when DOCX to PDF conversion fails."""

    pass


class LibreOfficeNotFoundError(DocxConverterError):
    """Raised when LibreOffice is not installed or cannot be found."""

    pass


class DocxToPdfConverter:
    """Convert DOCX/DOC files to PDF using LibreOffice headless mode.

    This converter uses LibreOffice's command-line interface to convert
    Microsoft Word documents to PDF format while preserving table layouts
    and formatting.

    Example:
        >>> converter = DocxToPdfConverter()
        >>> pdf_path = converter.convert_to_pdf(Path("document.docx"))
        >>> print(pdf_path)
        PosixPath('/tmp/document.pdf')

    """

    def __init__(self, libreoffice_path: str | None = None) -> None:
        """Initialize the converter.

        Args:
            libreoffice_path: Custom path to LibreOffice executable.
                If None, will attempt to auto-detect.

        Raises:
            LibreOfficeNotFoundError: If LibreOffice cannot be found.

        """
        self.libreoffice_path = libreoffice_path or self._detect_libreoffice()
        if not self.libreoffice_path:
            raise LibreOfficeNotFoundError(
                "LibreOffice is not installed or cannot be found. "
                "Please install LibreOffice to enable DOCX/DOC conversion. "
                "Download from: https://www.libreoffice.org/download/"
            )

        logger.info(f"Using LibreOffice at: {self.libreoffice_path}")

    def _detect_libreoffice(self) -> str | None:
        """Detect LibreOffice installation on the system.

        Returns:
            Path to LibreOffice executable, or None if not found.

        """
        system = platform.system()

        # Common LibreOffice executable names
        if system == "Windows":
            candidates = [
                "soffice.exe",
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            ]
        elif system == "Darwin":  # macOS
            candidates = [
                "soffice",
                "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            ]
        else:  # Linux and others
            candidates = [
                "soffice",
                "libreoffice",
                "/usr/bin/soffice",
                "/usr/bin/libreoffice",
            ]

        # Try each candidate
        for candidate in candidates:
            # First check if it's in PATH
            if "/" not in candidate and "\\" not in candidate:
                if shutil.which(candidate):
                    return candidate
            # Then check if it exists as absolute path
            elif Path(candidate).exists():
                return candidate

        logger.warning("LibreOffice not found in common locations")
        return None

    def convert_to_pdf(
        self,
        docx_path: Path,
        output_dir: Path | None = None,
        keep_pdf: bool = False,
    ) -> tuple[Path, dict]:
        """Convert DOCX/DOC file to PDF.

        Args:
            docx_path: Path to DOCX or DOC file.
            output_dir: Directory for output PDF. If None, uses temp directory.
            keep_pdf: If True, keep PDF in output_dir. If False and output_dir
                is None, PDF will be in a temp directory that may be cleaned up.

        Returns:
            Tuple of (pdf_path, metadata_dict) where metadata contains:
                - source_file: Original DOCX/DOC path
                - output_file: Generated PDF path
                - conversion_time: Time taken in seconds
                - libreoffice_version: LibreOffice version string

        Raises:
            DocxConverterError: If conversion fails.
            FileNotFoundError: If docx_path does not exist.

        """
        if not docx_path.exists():
            raise FileNotFoundError(f"DOCX file not found: {docx_path}")

        if docx_path.suffix.lower() not in [".docx", ".doc"]:
            raise DocxConverterError(
                f"Unsupported file format: {docx_path.suffix}. "
                "Only .docx and .doc are supported."
            )

        # Determine output directory
        if output_dir is None:
            output_dir = Path(tempfile.gettempdir())
        else:
            output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Converting {docx_path.name} to PDF...")

        # Build LibreOffice command
        # --headless: Run without GUI
        # --convert-to pdf: Convert to PDF format
        # --outdir: Specify output directory
        cmd = [
            str(self.libreoffice_path),
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_dir),
            str(docx_path),
        ]

        try:
            import time

            start_time = time.time()

            # Run conversion
            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,  # 60 second timeout
                check=True,
            )

            conversion_time = time.time() - start_time

            # LibreOffice creates PDF with same name as input
            pdf_path = output_dir / f"{docx_path.stem}.pdf"

            if not pdf_path.exists():
                raise DocxConverterError(
                    f"Conversion appeared to succeed but PDF not found: {pdf_path}"
                )

            logger.info(
                f"Conversion successful: {pdf_path.name} ({conversion_time:.2f}s)"
            )

            # Get LibreOffice version
            version = self._get_libreoffice_version()

            metadata = {
                "source_file": str(docx_path),
                "output_file": str(pdf_path),
                "conversion_time": round(conversion_time, 2),
                "libreoffice_version": version,
                "keep_pdf": keep_pdf,
            }

            return pdf_path, metadata

        except subprocess.TimeoutExpired as e:
            raise DocxConverterError(
                f"Conversion timed out after 60 seconds: {docx_path.name}"
            ) from e
        except subprocess.CalledProcessError as e:
            raise DocxConverterError(
                f"LibreOffice conversion failed: {e.stderr}"
            ) from e
        except Exception as e:
            raise DocxConverterError(f"Unexpected error during conversion: {e}") from e

    def _get_libreoffice_version(self) -> str:
        """Get LibreOffice version string.

        Returns:
            Version string, or "unknown" if detection fails.

        """
        try:
            result = subprocess.run(
                [str(self.libreoffice_path), "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            # Parse version from output like "LibreOffice 7.4.2.3 ..."
            version_line = result.stdout.strip()
            return version_line
        except Exception:
            return "unknown"

    def convert_batch(
        self,
        docx_paths: list[Path],
        output_dir: Path,
        keep_pdfs: bool = False,
    ) -> list[tuple[Path, dict]]:
        """Convert multiple DOCX/DOC files to PDF.

        Args:
            docx_paths: List of DOCX/DOC file paths.
            output_dir: Directory for output PDFs.
            keep_pdfs: If True, keep PDFs in output_dir.

        Returns:
            List of (pdf_path, metadata) tuples for successful conversions.

        """
        results = []
        failures = []

        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Converting {len(docx_paths)} DOCX files to PDF...")

        for docx_path in docx_paths:
            try:
                pdf_path, metadata = self.convert_to_pdf(
                    docx_path, output_dir, keep_pdfs
                )
                results.append((pdf_path, metadata))
            except Exception as e:
                logger.error(f"Failed to convert {docx_path.name}: {e}")
                failures.append((docx_path, str(e)))

        logger.info(
            f"Batch conversion complete: {len(results)} succeeded, "
            f"{len(failures)} failed"
        )

        if failures:
            logger.warning(f"Failed conversions: {[f[0].name for f in failures]}")

        return results


def is_docx_file(file_path: Path) -> bool:
    """Check if file is a DOCX or DOC file.

    Args:
        file_path: Path to check.

    Returns:
        True if file has .docx or .doc extension.

    """
    return file_path.suffix.lower() in [".docx", ".doc"]


def ensure_pdf(
    file_path: Path,
    converter: DocxToPdfConverter | None = None,
    output_dir: Path | None = None,
) -> tuple[Path, dict | None]:
    """Ensure file is in PDF format, converting if necessary.

    Args:
        file_path: Path to PDF or DOCX/DOC file.
        converter: Optional converter instance. If None, creates one.
        output_dir: Directory for converted PDF. If None, uses temp directory.

    Returns:
        Tuple of (pdf_path, conversion_metadata). If file was already PDF,
        conversion_metadata is None.

    Raises:
        DocxConverterError: If conversion fails.
        FileNotFoundError: If file does not exist.

    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Already a PDF
    if file_path.suffix.lower() == ".pdf":
        return file_path, None

    # DOCX/DOC - convert to PDF
    if is_docx_file(file_path):
        if converter is None:
            converter = DocxToPdfConverter()

        pdf_path, metadata = converter.convert_to_pdf(
            file_path, output_dir, keep_pdf=True
        )
        return pdf_path, metadata

    # Unsupported format
    raise DocxConverterError(
        f"Unsupported file format: {file_path.suffix}. "
        "Only PDF, DOCX, and DOC are supported."
    )
