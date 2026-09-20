from pathlib import Path

from core.metadata.schemas import MetadataExtractionResult
from core.metadata.extractors.academic import AcademicMetadataExtractor
from core.metadata.extractors.faculty import FacultyMetadataExtractor


class MetadataExtractor:
    """
    Main metadata extraction dispatcher.

    Routes documents to the appropriate specialized extractor.
    """

    def extract(
        self,
        markdown: str,
        document_type: str = "unknown",
        source_file: str | None = None,
    ) -> MetadataExtractionResult:
        if document_type == "faculty_profile":
            faculty = FacultyMetadataExtractor.extract(
                markdown=markdown,
                source_file=source_file,
            )

            return MetadataExtractionResult(
                document_type=document_type,
                faculty=faculty,
                confidence=0.99,
                method="rules",
            )

        return AcademicMetadataExtractor.extract(
            markdown=markdown,
            document_type=document_type,
            source_file=source_file,
        )

    def extract_file(
        self,
        file_path: str | Path,
        document_type: str = "unknown",
    ) -> MetadataExtractionResult:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Markdown file not found: {path}"
            )

        markdown = path.read_text(
            encoding="utf-8",
        )

        return self.extract(
            markdown=markdown,
            document_type=document_type,
            source_file=str(path),
        )