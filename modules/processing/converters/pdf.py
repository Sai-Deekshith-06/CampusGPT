from pathlib import Path

from core.ocr import OCR
from processing.converters.base import DocumentConverter
from processing.exceptions import FileConversionError


class PDFConverter(DocumentConverter):
    SUPPORTED_EXTENSIONS = {".pdf"}

    def __init__(self, api_key: str | None = None):
        self.ocr = OCR(api_key=api_key)

    def supports(self, file_path: str | Path) -> bool:
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS

    def convert(self, file_path: str | Path) -> str:
        path = Path(file_path)

        if not self.supports(path):
            raise FileConversionError(
                f"Unsupported PDF file: {path}"
            )

        if not path.exists():
            raise FileConversionError(
                f"PDF file not found: {path}"
            )

        try:
            return self.ocr.process_file(
                file_path=str(path),
            )
        except Exception as exc:
            raise FileConversionError(
                f"Failed to convert PDF to Markdown: {path}"
            ) from exc