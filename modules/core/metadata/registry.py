from core.metadata.extractors.faculty import FacultyMetadataExtractor
from core.metadata.extractors.academic import AcademicMetadataExtractor


EXTRACTOR_REGISTRY = {
    "faculty_profile": FacultyMetadataExtractor,
    "academic_calendar": AcademicMetadataExtractor,
}


def get_metadata_extractor(document_type: str):
    extractor_class = EXTRACTOR_REGISTRY.get(document_type)

    if extractor_class is None:
        # Fallback to academic extractor for all other types like course_structure, syllabus, etc.
        extractor_class = AcademicMetadataExtractor

    return extractor_class()