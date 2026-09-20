from typing import Any

from core.metadata.schemas import MetadataExtractionResult


class MetadataValidator:
    REQUIRED_FIELDS_BY_TYPE = {
        "academic_calendar": (
            "metadata.title",
            "metadata.academic_year",
            "metadata.semester",
            "metadata.program",
        ),
        "syllabus": (
            "metadata.title",
            "metadata.program",
        ),
        "timetable": (
            "metadata.title",
            "metadata.semester",
        ),
        "faculty_profile": (
            "faculty.name",
            "faculty.department",
            "faculty.designation",
        ),
    }

    def validate(
        self,
        result: MetadataExtractionResult,
    ) -> list[str]:
        required_fields = self.REQUIRED_FIELDS_BY_TYPE.get(
            result.document_type,
            (),
        )

        missing_fields = []

        for field_path in required_fields:
            value = self._get_nested_value(result, field_path)

            if value is None or value == "" or value == []:
                missing_fields.append(field_path)

        return missing_fields

    def is_valid(
        self,
        result: MetadataExtractionResult,
    ) -> bool:
        return not self.validate(result)

    @staticmethod
    def _get_nested_value(
        obj: Any,
        field_path: str,
    ) -> Any:
        value = obj

        for field in field_path.split("."):
            if value is None:
                return None

            if isinstance(value, dict):
                value = value.get(field)
            else:
                value = getattr(value, field, None)

        return value