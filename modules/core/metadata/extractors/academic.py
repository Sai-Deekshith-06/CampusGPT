from pathlib import Path

from core.metadata.schemas import (
    DocumentMetadata,
    MetadataExtractionResult,
)
from core.metadata.extractors.common import CommonMetadataExtractor


class AcademicMetadataExtractor:
    """
    Extracts structured metadata from academic documents.

    Supported document types include:
    - Academic calendars
    - Syllabi
    - Timetables
    - Course structures
    - Curriculum documents
    - Examination schedules
    - Academic notifications
    """

    @classmethod
    def extract(
        cls,
        markdown: str,
        document_type: str = "unknown",
        source_file: str | None = None,
    ) -> MetadataExtractionResult:
        if not markdown or not markdown.strip():
            return MetadataExtractionResult(
                document_type=document_type,
                metadata=DocumentMetadata(
                    source_file=source_file,
                ),
                confidence=0.0,
                method="rules",
            )

        text = CommonMetadataExtractor.clean_markdown(markdown)

        metadata = DocumentMetadata(
            title=CommonMetadataExtractor.extract_title(markdown),
            institution=CommonMetadataExtractor.extract_institution(text),
            document_number=CommonMetadataExtractor.extract_document_number(text),
            document_date=CommonMetadataExtractor.extract_document_date(text),
            academic_year=CommonMetadataExtractor.extract_academic_year(text),
            semester=CommonMetadataExtractor.extract_semesters(text),
            program=CommonMetadataExtractor.extract_program(text),
            year_of_study=CommonMetadataExtractor.extract_year_of_study(markdown),
            source_file=source_file,
        )

        missing_fields = cls.find_missing_fields(
            metadata=metadata,
            document_type=document_type,
        )

        confidence = cls.calculate_confidence(
            metadata=metadata,
            missing_fields=missing_fields,
            document_type=document_type,
        )

        return MetadataExtractionResult(
            document_type=document_type,
            metadata=metadata,
            confidence=confidence,
            method="rules",
        )

    @staticmethod
    def find_missing_fields(
        metadata: DocumentMetadata,
        document_type: str,
    ) -> list[str]:
        """
        Find missing fields based on document type.

        Required fields are intentionally different for each
        academic document category.
        """

        required_fields_by_type = {
            "academic_calendar": (
                "title",
                "academic_year",
                "semester",
            ),
            "syllabus": (
                "title",
                "program",
            ),
            "timetable": (
                "title",
                "semester",
            ),
            "course_structure": (
                "title",
                "program",
            ),
            "curriculum": (
                "title",
                "program",
            ),
            "examination_schedule": (
                "title",
                "semester",
            ),
        }

        required_fields = required_fields_by_type.get(
            document_type,
            (),
        )

        return CommonMetadataExtractor.find_missing_fields(
            metadata=metadata,
            required_fields=required_fields,
        )

    @staticmethod
    def calculate_confidence(
        metadata: DocumentMetadata,
        missing_fields: list[str],
        document_type: str,
    ) -> float:
        """
        Calculate confidence for academic metadata extraction.

        A complete extraction receives a high confidence score.
        Missing required fields reduce confidence.
        """

        required_fields_by_type = {
            "academic_calendar": (
                "title",
                "academic_year",
                "semester",
            ),
            "syllabus": (
                "title",
                "program",
            ),
            "timetable": (
                "title",
                "semester",
            ),
            "course_structure": (
                "title",
                "program",
            ),
            "curriculum": (
                "title",
                "program",
            ),
            "examination_schedule": (
                "title",
                "semester",
            ),
        }

        required_fields = required_fields_by_type.get(
            document_type,
            (),
        )

        if not required_fields:
            # Unknown academic document type.
            # Use the number of populated common fields.
            fields = (
                metadata.title,
                metadata.institution,
                metadata.document_number,
                metadata.document_date,
                metadata.academic_year,
                metadata.semester,
                metadata.program,
                metadata.year_of_study,
            )

            extracted_count = sum(
                bool(value)
                for value in fields
            )

            if extracted_count == 0:
                return 0.0

            return round(
                min(extracted_count / len(fields), 0.99),
                2,
            )

        if not missing_fields:
            return 0.95

        if metadata.title:
            return 0.70

        return 0.40

    @classmethod
    def extract_file(
        cls,
        file_path: str | Path,
        document_type: str = "unknown",
    ) -> MetadataExtractionResult:
        """Extract metadata from a Markdown file."""

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Markdown file not found: {path}"
            )

        markdown = path.read_text(
            encoding="utf-8",
        )

        return cls.extract(
            markdown=markdown,
            document_type=document_type,
            source_file=str(path),
        )