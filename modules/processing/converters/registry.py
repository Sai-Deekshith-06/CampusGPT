from pathlib import Path

from processing.converters.base import DocumentConverter
from processing.exceptions import UnsupportedFileError


class ConverterRegistry:
    def __init__(
        self,
        converters: list[DocumentConverter] | None = None,
    ):
        self._converters: list[DocumentConverter] = []

        for converter in converters or []:
            self.register(converter)

    def register(self, converter: DocumentConverter) -> None:
        if converter not in self._converters:
            self._converters.append(converter)

    def get_converter(
        self,
        file_path: str | Path,
    ) -> DocumentConverter:
        for converter in self._converters:
            if converter.supports(file_path):
                return converter

        raise UnsupportedFileError(
            f"No converter available for file: {file_path}"
        )