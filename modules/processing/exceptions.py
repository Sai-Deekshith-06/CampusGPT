class ProcessingError(Exception):
    """Base exception for document-processing errors."""


class FileConversionError(ProcessingError):
    """Raised when file-to-Markdown conversion fails."""


class UnsupportedFileError(ProcessingError):
    """Raised when the input file type is unsupported."""


class MarkdownReadError(FileConversionError):
    """Raised when Markdown cannot be read."""