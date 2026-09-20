from abc import ABC, abstractmethod
from pathlib import Path


class DocumentConverter(ABC):
    @abstractmethod
    def supports(self, file_path: str | Path) -> bool:
        """Return whether this converter supports the given file."""

    @abstractmethod
    def convert(self, file_path: str | Path) -> str:
        """Convert the input file into Markdown text."""