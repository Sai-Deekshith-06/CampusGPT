import re

from core.metadata.normalizer import normalize_date, normalize_text
from core.metadata.schemas import (
    FacultyMetadata,
    PublicationMetadata,
    QualificationMetadata,
)

'''
The below fields also have to be extracted:

Conferences and presentations
Faculty development programs
Books and monographs
Patents
Awards and achievements
Research projects
Workshops and training programs
'''

class FacultyMetadataExtractor:
    """
    Extracts structured metadata from faculty profile documents.
    """

    @classmethod
    def extract(
        cls,
        markdown: str,
        source_file: str | None = None,
    ) -> FacultyMetadata:
        text = cls._normalize_markdown(markdown)

        publications, warnings = cls._extract_publications(text)

        return FacultyMetadata(
            name=cls._extract_faculty_name(markdown, text),
            designation=cls._extract_designation(text),
            department=cls._extract_department(text),
            qualifications=cls._extract_qualifications(text),
            certifications=cls._extract_certifications(text),
            specialization=cls._extract_specialization(text),
            research_interests=cls._extract_research_interests(text),
            teaching_experience=cls._extract_teaching_experience(text),
            research_experience=cls._extract_research_experience(text),
            date_of_joining=cls._extract_joining_date(text),
            email=cls._extract_email(text),
            publications=publications,
            achievements=cls._extract_achievements(text),
            source_file=source_file,
            warnings=warnings,
        )

    @staticmethod
    def _normalize_markdown(markdown: str) -> str:
        """
        Convert Markdown into searchable plain text.
        """

        text = re.sub(r"!\[.*?\]\(.*?\)", " ", markdown)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"[*_`>#]", " ", text)
        text = re.sub(r"\s+", " ", text)

        return normalize_text(text)

    @staticmethod
    def _extract_faculty_name(
        markdown: str,
        text: str,
    ) -> str | None:
        """
        Extract the faculty member's name.
        """

        heading_patterns = (
            r"^#\s*(?:Name\s*:\s*)?(?P<name>[A-Z][A-Za-z .'-]+)$",
            r"^\*\*Name\*\*\s*:\s*(?P<name>.+)$",
            r"^Name\s*:\s*(?P<name>.+)$",
            r"^Faculty\s+Name\s*:\s*(?P<name>.+)$",
        )

        for pattern in heading_patterns:
            match = re.search(
                pattern,
                markdown,
                re.IGNORECASE | re.MULTILINE,
            )

            if match:
                name = normalize_text(match.group("name"))

                if name:
                    return name

        name_patterns = (
            r"\bFaculty\s+Name\s*:\s*(?P<name>.+?)(?=\s*[-|]|$)",
            r"\bEmployee\s+Name\s*:\s*(?P<name>.+?)(?=\s*[-|]|$)",
            r"\bName\s*:\s*(?P<name>.+?)(?=\s*[-|]|$)",
        )

        for pattern in name_patterns:
            match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if match:
                name = normalize_text(match.group("name"))

                if name:
                    return name

        heading_match = re.search(
            r"^#{1,6}\s*(?P<name>.+?)\s*$",
            markdown,
            re.MULTILINE,
        )

        if heading_match:
            name = normalize_text(heading_match.group("name"))

            if name and name.lower() not in {
                "profile",
                "faculty profile",
                "faculty details",
                "personal details",
            }:
                return name

        return None

    @staticmethod
    def _extract_designation(
        text: str,
    ) -> str | None:
        patterns = (
            r"\bDesignation\s*:\s*(?P<value>.+?)(?=\s*[-|]|$)",
            r"\bPosition\s*:\s*(?P<value>.+?)(?=\s*[-|]|$)",
        )

        return FacultyMetadataExtractor._extract_value(
            text,
            patterns,
        )

    @staticmethod
    def _extract_department(
        text: str,
    ) -> str | None:
        patterns = (
            r"\bDepartment\s*:\s*(?P<value>.*?)(?=\s+-\s+(?:Joining Date|Date of Joining|Designation|Qualifications|Certification Program|Professional Experience)|$)",
            r"\bDept\.?\s*:\s*(?P<value>.*?)(?=\s+-\s+(?:Joining Date|Date of Joining|Designation|Qualifications|Certification Program|Professional Experience)|$)",
        )

        return FacultyMetadataExtractor._extract_value(
            text,
            patterns,
        )

    @classmethod
    def _extract_qualifications(
        cls,
        text: str,
    ) -> list[QualificationMetadata]:
        section = cls._extract_section(
            text=text,
            start_label="Qualifications",
            end_labels=(
                "Certification Program",
                "Professional Experience",
                "Core Competency Areas",
                "Achievements",
                "Achievements / Awards",
                "Publications",
            ),
        )

        if not section:
            return []

        qualification_pattern = re.compile(
            r"Qualification\s*:\s*(?P<level>.*?)"
            r"\s*-\s*Status\s*:\s*(?P<status>.*?)"
            r"\s*-\s*Course\s*:\s*(?P<course>.*?)"
            r"\s*-\s*Institute\s*:\s*(?P<institute>.*?)"
            r"\s*-\s*University\s*:\s*(?P<university>.*?)"
            r"\s*-\s*Completion\s+Date\s*:\s*"
            r"(?P<completion_date>"
            r"\d{4}-\d{2}-\d{2}"
            r"|\d{1,2}[./-]\d{1,2}[./-]\d{2,4}"
            r")",
            re.IGNORECASE | re.DOTALL,
        )

        qualifications = []

        for match in qualification_pattern.finditer(section):
            qualifications.append(
                QualificationMetadata(
                    level=normalize_text(match.group("level")),
                    status=normalize_text(match.group("status")),
                    course=normalize_text(match.group("course")),
                    institute=normalize_text(match.group("institute")),
                    university=normalize_text(match.group("university")),
                    completion_date=normalize_date(
                        match.group("completion_date")
                    ),
                )
            )

        return qualifications

    @classmethod
    def _extract_certifications(
        cls,
        text: str,
    ) -> list[QualificationMetadata]:
        section = cls._extract_section(
            text=text,
            start_label="Certification Program",
            end_labels=(
                "Professional Experience",
                "Core Competency Areas",
                "Achievements",
                "Achievements / Awards",
                "Publications",
            ),
        )

        if not section:
            return []

        certification_pattern = re.compile(
            r"Course\s+Name\s*:\s*(?P<course>.*?)"
            r"\s*-\s*"
            r"(?:Institute|Institution)\s*:\s*(?P<institute>.*?)"
            r"(?:\s*-\s*(?:University|Organization)\s*:\s*"
            r"(?P<university>.*?))?"
            r"(?:\s*-\s*(?:Completion\s+Date|Date)\s*:\s*"
            r"(?P<completion_date>"
            r"\d{4}-\d{2}-\d{2}"
            r"|\d{1,2}[./-]\d{1,2}[./-]\d{2,4}"
            r"))?",
            re.IGNORECASE | re.DOTALL,
        )

        certifications = []

        for match in certification_pattern.finditer(section):
            certifications.append(
                QualificationMetadata(
                    level="Certification",
                    status=None,
                    course=normalize_text(match.group("course")),
                    institute=normalize_text(
                        match.group("institute")
                    ),
                    university=normalize_text(
                        match.group("university")
                    ),
                    completion_date=normalize_date(
                        match.group("completion_date")
                    ),
                )
            )

        return certifications

    @classmethod
    def _extract_specialization(
        cls,
        text: str,
    ) -> str | None:
        patterns = (
            r"\bSpecialization\s*:\s*(?P<value>.+?)(?=\s*[-|]|$)",
            r"\bCore\s+Competency\s+Areas?\s*:\s*(?P<value>.+?)(?=\s*(?:Achievements|Publications|$))",
        )

        return cls._extract_value(text, patterns)

    @classmethod
    def _extract_research_interests(
        cls,
        text: str,
    ) -> list[str|None]:
        section = cls._extract_section(
            text=text,
            start_label="Research Interests",
            end_labels=(
                "Teaching Experience",
                "Research Experience",
                "Professional Experience",
                "Achievements",
                "Publications",
            ),
        )

        if not section:
            return []

        return cls._split_values(section)

    @classmethod
    def _extract_teaching_experience(
        cls,
        text: str,
    ) -> str | None:
        patterns = (
            r"\bTeaching\s+Experience\s*:\s*(?P<value>.+?)(?=\s*(?:Research Experience|Achievements|Publications|$))",
            r"\bTeaching\s+Experience\s*-\s*(?P<value>.+?)(?=\s*(?:Research Experience|Achievements|Publications|$))",
        )

        return cls._extract_value(text, patterns)

    @classmethod
    def _extract_research_experience(
        cls,
        text: str,
    ) -> str | None:
        patterns = (
            r"\bResearch\s+Experience\s*:\s*(?P<value>.+?)(?=\s*(?:Achievements|Publications|$))",
            r"\bResearch\s+Experience\s*-\s*(?P<value>.+?)(?=\s*(?:Achievements|Publications|$))",
        )

        return cls._extract_value(text, patterns)

    @staticmethod
    def _extract_joining_date(
        text: str,
    ) -> str | None:
        patterns = (
            r"\bJoining\s+Date\s*:\s*(?P<value>"
            r"\d{4}-\d{2}-\d{2}"
            r"|\d{1,2}[./-]\d{1,2}[./-]\d{2,4}"
            r"|\d{1,2}\s+[A-Za-z]+\s+\d{4}"
            r")",
            r"\bDate\s+of\s+Joining\s*:\s*(?P<value>"
            r"\d{4}-\d{2}-\d{2}"
            r"|\d{1,2}[./-]\d{1,2}[./-]\d{2,4}"
            r"|\d{1,2}\s+[A-Za-z]+\s+\d{4}"
            r")",
        )

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)

            if match:
                return normalize_date(match.group("value"))

        return None

    @staticmethod
    def _extract_email(
        text: str,
    ) -> str | None:
        match = re.search(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            text,
        )

        return match.group(0) if match else None

    @classmethod
    def _extract_publications(
        cls,
        text: str,
    ) -> tuple[list[PublicationMetadata], list[str]]:
        section = cls._extract_section(
            text=text,
            start_label="Publications",
            end_labels=(
                "Conferences / Presentation",
                "Conferences / Presentations",
                "Books / Monographs",
                "Patents",
                "Achievements",
                "Achievements / Awards",
                "References",
            ),
        )

        if not section:
            return [], []

        records = cls._split_publication_records(section)

        publications: list[PublicationMetadata] = []
        warnings: list[str] = []

        for record in records:
            publication = PublicationMetadata(
                publication_type=cls._extract_labeled_value(
                    record,
                    "Publication Type",
                ),
                title=cls._extract_labeled_value(
                    record,
                    "Title",
                ),
                indexed_in=cls._extract_labeled_value(
                    record,
                    "Indexed In",
                ),
                event_status=cls._extract_labeled_value(
                    record,
                    "Event Status",
                ),
                main_author=cls._extract_labeled_value(
                    record,
                    "Main Author",
                ),
                co_authors=cls._extract_authors(
                    cls._extract_labeled_value(
                        record,
                        "Co-Author",
                    )
                ),
                journal_name=cls._extract_labeled_value(
                    record,
                    "Journal Name",
                ),
                issn=cls._extract_labeled_value(
                    record,
                    "ISSN",
                ),
                volume=cls._extract_labeled_value(
                    record,
                    "Volume",
                ),
                issue=cls._extract_labeled_value(
                    record,
                    "Issue",
                ),
                page_number=cls._extract_labeled_value(
                    record,
                    "PageNumber",
                ),
                year=cls._extract_labeled_value(
                    record,
                    "Year",
                ),
                date=cls._extract_labeled_value(
                    record,
                    "Date",
                ),
            )

            if not publication.title and not publication.publication_type:
                continue

            if publication.journal_name:
                journal_name = publication.journal_name.strip()

                if journal_name.endswith("("):
                    warnings.append(
                        "Publication journal name appears incomplete "
                        f"for {publication.title or 'an unnamed publication'}."
                    )

            publications.append(publication)

        return publications, warnings

    @staticmethod
    def _split_publication_records(
        section: str,
    ) -> list[str]:
        """
        Split publication entries while preserving each entry's fields.
        """

        records = re.split(
            r"\s*(?=-?\s*Publication\s+Type\s*:)",
            section,
            flags=re.IGNORECASE,
        )

        return [
            normalize_text(record)
            for record in records
            if normalize_text(record)
        ]

    @staticmethod
    def _extract_authors(
        value: str | None,
    ) -> list[str]:
        if not value:
            return []

        value = value.replace("&", ";")

        authors = re.split(
            r"\s*;\s*|\s*,\s*|\s+and\s+",
            value,
            flags=re.IGNORECASE,
        )

        return [
            normalize_text(author)
            for author in authors
            if normalize_text(author)
        ]

    @staticmethod
    def _extract_labeled_value(
        text: str,
        label: str,
    ) -> str | None:
        labels = (
            "Publication Type",
            "Title",
            "Indexed In",
            "Event Status",
            "Main Author",
            "Co-Author",
            "Journal Name",
            "ISSN",
            "Volume",
            "Issue",
            "PageNumber",
            "Year",
            "Date",
            "UGC Approval",
        )

        other_labels = [
            item
            for item in labels
            if item.lower() != label.lower()
        ]

        end_pattern = "|".join(
            re.escape(item)
            for item in other_labels
        )

        pattern = (
            rf"{re.escape(label)}\s*:\s*"
            rf"(?P<value>.*?)"
            rf"(?=\s*-\s*(?:{end_pattern})\s*:|\Z)"
        )

        match = re.search(
            pattern,
            text,
            re.IGNORECASE | re.DOTALL,
        )

        if not match:
            return None

        value = normalize_text(match.group("value"))

        # Remove separators accidentally captured at the end.
        value = re.sub(r"\s*-{2,}\s*$", "", value)
        value = re.sub(r"\s*---\s*$", "", value)

        return value.strip() or None

    @staticmethod
    def _extract_achievements(text: str) -> list[str]:
        matches = re.findall(
            r"\bAchievments?\s*:\s*(?P<value>.*?)(?=\s+-\s+\w[\w /]*\s*:|\s*$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )

        values = []

        for value in matches:
            cleaned = FacultyMetadataExtractor._clean_achievement(value)
            if cleaned:
                values.append(cleaned)

        return values

    @staticmethod
    def _clean_achievement(value: str) -> str:
        value = re.sub(r"\s*-{2,}\s*$", "", value)
        value = re.sub(r"^\s*[-/:]+\s*", "", value)
        return normalize_text(value)

    @staticmethod
    def _extract_section(
        text: str,
        start_label: str,
        end_labels: tuple[str, ...],
    ) -> str | None:
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
    def _extract_value(
        text: str,
        patterns: tuple[str, ...],
    ) -> str | None:
        for pattern in patterns:
            match = re.search(
                pattern,
                text,
                re.IGNORECASE | re.DOTALL,
            )

            if match:
                value = normalize_text(match.group("value"))

                if value:
                    return value

        return None

    @staticmethod
    def _split_values(
        value: str,
    ) -> list[str|None]:
        values = re.split(
            r"\s*(?:,|;|\||\n|•)\s*",
            value,
        )

        return [
            normalize_text(item)
            for item in values
            if normalize_text(item)
        ]