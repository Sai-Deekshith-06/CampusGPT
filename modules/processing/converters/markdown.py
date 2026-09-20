from pathlib import Path

from processing.converters.base import DocumentConverter
from processing.exceptions import MarkdownReadError


class MarkdownConverter(DocumentConverter):
    SUPPORTED_EXTENSIONS = {".md", ".markdown"}

    def supports(self, file_path: str | Path) -> bool:
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS

    def convert(self, file_path: str | Path) -> str:
        path = Path(file_path)

        if not self.supports(path):
            raise MarkdownReadError(
                f"Unsupported Markdown file: {path}"
            )

        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise MarkdownReadError(
                f"Failed to read Markdown file: {path}"
            ) from exc