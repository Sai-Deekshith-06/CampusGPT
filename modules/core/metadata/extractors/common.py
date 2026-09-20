import re
from typing import Callable

from core.metadata.normalizer import (
    normalize_date,
    normalize_list,
    normalize_text,
)


class CommonMetadataExtractor:
    """Shared utilities for metadata extraction."""

    @staticmethod
    def clean_markdown(markdown: str) -> str:
        """Convert Markdown into normalized searchable plain text."""

        text = re.sub(
            r"!\[[^\]]*\]\([^)]*\)",
            " ",
            markdown,
        )

        text = re.sub(
            r"\[([^\]]+)\]\([^)]*\)",
            r"\1",
            text,
        )

        text = re.sub(
            r"<[^>]+>",
            " ",
            text,
        )

        text = re.sub(
            r"[*_`>#]",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return normalize_text(text)

    @staticmethod
    def extract_title(markdown: str) -> str | None:
        """Extract the most relevant title from Markdown headings."""

        headings = re.findall(
            r"^\s*#{1,6}\s+(.+?)\s*$",
            markdown,
            re.MULTILINE,
        )

        if not headings:
            return None

        ignored_titles = {
            "cherabuddi education society's",
            "cvr college of engineering",
        }

        preferred_keywords = (
            "academic calendar",
            "syllabus",
            "curriculum",
            "course structure",
            "timetable",
            "examination",
            "notification",
            "regulation",
            "circular",
            "notice",
            "faculty",
            "profile",
            "details",
        )

        cleaned_headings = [
            normalize_text(heading)
            for heading in headings
            if normalize_text(heading)
        ]

        for heading in cleaned_headings:
            if heading.lower() in ignored_titles:
                continue

            if any(
                keyword in heading.lower()
                for keyword in preferred_keywords
            ):
                return heading

        for heading in cleaned_headings:
            if heading.lower() not in ignored_titles:
                return heading

        return None

    @staticmethod
    def extract_institution(text: str) -> str | None:
        """Extract the institution name."""

        patterns = (
            r"(Cherabuddi Education Society's\s+CVR College of Engineering)",
            r"(CVR\s+COLLEGE\s+OF\s+ENGINEERING)",
        )

        for pattern in patterns:
            match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if match:
                return normalize_text(match.group(1))

        return None

    @staticmethod
    def extract_department(text: str) -> str | None:
        """Extract department using labels or known aliases."""

        patterns = (
            r"\bdepartment\s*[:\-]\s*([^|,\n]+)",
            r"\bdept\.?\s*[:\-]\s*([^|,\n]+)",
            r"\bdepartment\s+of\s+([A-Za-z &]+)",
        )

        for pattern in patterns:
            match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if match:
                value = normalize_text(match.group(1))

                if value:
                    return value

        department_aliases = {
            "data science": "Data Science",
            "computer science and engineering": (
                "Computer Science and Engineering"
            ),
            "cse": "Computer Science and Engineering",
            "information technology": "Information Technology",
            "electronics and communication engineering": (
                "Electronics and Communication Engineering"
            ),
            "electrical and electronics engineering": (
                "Electrical and Electronics Engineering"
            ),
            "mechanical engineering": "Mechanical Engineering",
            "civil engineering": "Civil Engineering",
        }

        lowered_text = text.lower()

        for alias, department in department_aliases.items():
            if alias in lowered_text:
                return department

        return None

    @staticmethod
    def extract_document_number(text: str) -> str | None:
        """Extract a reference or document number."""

        patterns = (
            r"\bF\.?\s*No\.?\s*[:\-]?\s*([A-Z0-9/_.-]+)",
            r"\bRef(?:erence)?\.?\s*No\.?\s*[:\-]?\s*([A-Z0-9/_.-]+)",
            r"\bNo\.?\s*[:\-]\s*([A-Z0-9/_.-]+)",
        )

        for pattern in patterns:
            match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if match:
                return match.group(1).strip()

        return None

    @staticmethod
    def extract_document_date(text: str) -> str | None:
        """Extract a document date."""

        patterns = (
            r"\bDate\s*[:\-]\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",
            r"\bdated\s+(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",
        )

        for pattern in patterns:
            match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if match:
                return normalize_date(match.group(1))

        return None

    @staticmethod
    def extract_academic_year(text: str) -> str | None:
        """Extract and normalize an academic year."""

        patterns = (
            r"\bacademic\s+year\s*[:\-]?\s*"
            r"(20\d{2})\s*[-/]\s*(\d{2}|20\d{2})\b",

            r"\bAY\s*[:\-]?\s*"
            r"(20\d{2})\s*[-/]\s*(\d{2}|20\d{2})\b",

            r"(?<![\d-])"
            r"(20\d{2})\s*[-/]\s*(\d{2}|20\d{2})"
            r"(?![-/]\d{1,2}\b)",
        )

        for pattern in patterns:
            match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if not match:
                continue

            start_year = match.group(1)
            end_year = match.group(2)

            if len(end_year) == 4:
                end_year = end_year[-2:]

            return f"{start_year}-{end_year}"

        return None

    @staticmethod
    def extract_semesters(text: str) -> list[str]:
        """Extract semester labels such as I, II, III, and IV."""

        semesters = []

        patterns = (
            (r"\bI\s+and\s+II\s+Semesters?\b", ["I", "II"]),
            (r"\bI\s*&\s*II\s+Semesters?\b", ["I", "II"]),
            (r"\bI\s+Semester\b", ["I"]),
            (r"\bII\s+Semester\b", ["II"]),
            (r"\bIII\s+Semester\b", ["III"]),
            (r"\bIV\s+Semester\b", ["IV"]),
            (r"\bV\s+Semester\b", ["V"]),
            (r"\bVI\s+Semester\b", ["VI"]),
            (r"\bVII\s+Semester\b", ["VII"]),
            (r"\bVIII\s+Semester\b", ["VIII"]),
        )

        for pattern, values in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                for value in values:
                    if value not in semesters:
                        semesters.append(value)

        return semesters

    @staticmethod
    def extract_program(text: str) -> str | None:
        """Extract a degree/program name."""

        patterns = (
            r"\b(B\.?\s*Tech\.?)\b",
            r"\b(M\.?\s*Tech\.?)\b",
            r"\b(MBA)\b",
            r"\b(MCA)\b",
            r"\b(BCA)\b",
            r"\b(BBA)\b",
            r"\b(M\.?\s*Sc\.?)\b",
            r"\b(B\.?\s*Sc\.?)\b",
        )

        for pattern in patterns:
            match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if match:
                from core.metadata.normalizer import normalize_program

                return normalize_program(match.group(1))

        return None

    @staticmethod
    def extract_year_of_study(markdown: str) -> str | None:
        """Extract year of study and normalize ordinals to Roman numerals."""

        patterns = (
            r"\b(I{1,4})\s*B\.?\s*Tech\.?\b",
            r"\b(1st|2nd|3rd|4th)\s+year\b",
            r"\b(I{1,4})\s+year\b",
        )

        ordinal_mapping = {
            "1ST": "I",
            "2ND": "II",
            "3RD": "III",
            "4TH": "IV",
        }

        for pattern in patterns:
            match = re.search(
                pattern,
                markdown,
                re.IGNORECASE,
            )

            if not match:
                continue

            value = match.group(1).upper()
            return ordinal_mapping.get(value, value)

        return None

    @staticmethod
    def extract_branch(text: str) -> str | None:
        """Extract branch or specialization."""

        patterns = (
            r"\bbranch\s*[:\-]\s*([^|,\n]+)",
            r"\bspecialization\s*[:\-]\s*([^|,\n]+)",
        )

        for pattern in patterns:
            match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if match:
                return normalize_text(match.group(1))

        return None

    @staticmethod
    def extract_section(
        text: str,
        start_label: str,
        end_labels: tuple[str, ...],
    ) -> str | None:
        """Extract text between a section heading and the next section."""

        end_pattern = "|".join(
            re.escape(label)
            for label in end_labels
        )

        pattern = (
            rf"{re.escape(start_label)}\s*(?:[:\-])?\s*"
            rf"(.*?)"
            rf"(?=\s*(?:{end_pattern})\s*(?:[:\-]|$)|\Z)"
        )

        match = re.search(
            pattern,
            text,
            re.IGNORECASE | re.DOTALL,
        )

        if not match:
            return None

        return normalize_text(match.group(1))

    @staticmethod
    def extract_labeled_value(
        text: str,
        labels: str | tuple[str, ...],
        next_labels: tuple[str, ...] = (),
    ) -> str | None:
        """
        Extract a value after one or more labels.

        Example:
            Department: Computer Science - Designation: Professor
        """

        if isinstance(labels, str):
            labels = (labels,)

        label_pattern = "|".join(
            re.escape(label)
            for label in labels
        )

        if next_labels:
            next_label_pattern = "|".join(
                re.escape(label)
                for label in next_labels
            )

            ending_pattern = (
                rf"(?=\s*(?:{next_label_pattern})\s*[:\-]|\Z)"
            )
        else:
            ending_pattern = r"\Z"

        pattern = (
            rf"(?:{label_pattern})\s*[:\-]?\s*"
            rf"(.*?)"
            rf"{ending_pattern}"
        )

        match = re.search(
            pattern,
            text,
            re.IGNORECASE | re.DOTALL,
        )

        if not match:
            return None

        value = re.sub(
            r"\s+",
            " ",
            match.group(1),
        ).strip(" -:")

        return value or None

    @staticmethod
    def extract_labeled_date(
        text: str,
        labels: tuple[str, ...],
    ) -> str | None:
        """Extract a labeled date."""

        value = CommonMetadataExtractor.extract_labeled_value(
            text=text,
            labels=labels,
        )

        return normalize_date(value) if value else None

    @staticmethod
    def extract_list_field(
        text: str,
        labels: tuple[str, ...],
    ) -> list[str]:
        """Extract a labeled list separated by commas, semicolons, or 'and'."""

        value = CommonMetadataExtractor.extract_labeled_value(
            text=text,
            labels=labels,
        )

        if not value:
            return []

        parts = re.split(
            r",|;|\s+and\s+",
            value,
        )

        return normalize_list(parts)

    @staticmethod
    def split_values(value: str) -> list[str]:
        """Split a text value into normalized list items."""

        values = re.split(
            r"\s*(?:,|;|\||\n|•)\s*",
            value,
        )

        return [
            normalize_text(item)
            for item in values
            if normalize_text(item)
        ]

    @staticmethod
    def find_missing_fields(
        metadata: object,
        required_fields: tuple[str, ...],
    ) -> list[str]:
        """Return required fields that are missing."""

        missing = []

        for field in required_fields:
            value = getattr(metadata, field, None)

            if value is None or value == "" or value == []:
                missing.append(field)

        return missing

    @staticmethod
    def calculate_confidence(
        missing_fields: list[str],
        total_fields: int,
        minimum_with_title: float = 0.70,
        complete_confidence: float = 0.95,
    ) -> float:
        """Calculate a simple confidence score based on missing fields."""

        if not missing_fields:
            return complete_confidence

        if total_fields <= 0:
            return 0.0

        extracted_fields = total_fields - len(missing_fields)
        confidence = extracted_fields / total_fields

        if len(missing_fields) < total_fields:
            confidence = max(
                confidence,
                minimum_with_title,
            )

        return round(min(confidence, 0.99), 2)