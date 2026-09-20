from typing import Literal, Optional

from pydantic import BaseModel, Field

class DocumentMetadata(BaseModel):
    title: Optional[str] = None
    institution: Optional[str] = None
    department: Optional[str] = None
    document_number: Optional[str] = None
    document_date: Optional[str] = None
    academic_year: Optional[str] = None
    semester: list[str] = Field(default_factory=list)
    program: Optional[str] = None
    year_of_study: Optional[str] = None
    branch: Optional[str] = None
    source_file: Optional[str] = None


# class FacultyMetadata(BaseModel):
#     name: Optional[str] = None
#     designation: Optional[str] = None
#     department: Optional[str] = None
#     qualification: list[str] = Field(default_factory=list)
#     specialization: Optional[str] = None
#     research_interests: list[str] = Field(default_factory=list)
#     teaching_experience: Optional[str] = None
#     research_experience: Optional[str] = None
#     date_of_joining: Optional[str] = None
#     email: Optional[str] = None
#     publications_count: Optional[int] = None
#     source_file: Optional[str] = None


class QualificationMetadata(BaseModel):
    level: Optional[str] = None
    status: Optional[str] = None
    course: Optional[str] = None
    institute: Optional[str] = None
    university: Optional[str] = None
    completion_date: Optional[str] = None


class PublicationMetadata(BaseModel):
    publication_type: Optional[str] = None
    title: Optional[str] = None
    indexed_in: Optional[str] = None
    event_status: Optional[str] = None
    main_author: Optional[str] = None
    co_authors: list[str] = Field(default_factory=list)
    journal_name: Optional[str] = None
    issn: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    page_number: Optional[str] = None
    year: Optional[str] = None
    date: Optional[str] = None


class FacultyMetadata(BaseModel):
    name: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    qualifications: list[QualificationMetadata] = Field(default_factory=list)
    certifications: list[QualificationMetadata] = Field(default_factory=list)
    specialization: Optional[str] = None
    research_interests: list[str] = Field(default_factory=list)
    teaching_experience: Optional[str] = None
    research_experience: Optional[str] = None
    date_of_joining: Optional[str] = None
    email: Optional[str] = None
    publications: list[PublicationMetadata] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    source_file: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)

'''
class FacultyMetadata(BaseModel):
    name: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None

    qualifications: list[QualificationMetadata] = Field(
        default_factory=list
    )
    certifications: list[QualificationMetadata] = Field(
        default_factory=list
    )

    specialization: Optional[str] = None
    research_interests: list[str] = Field(
        default_factory=list
    )

    teaching_experience: Optional[str] = None
    research_experience: Optional[str] = None
    date_of_joining: Optional[str] = None
    email: Optional[str] = None

    publications: list[PublicationMetadata] = Field(
        default_factory=list
    )
    conferences: list[ConferenceMetadata] = Field(
        default_factory=list
    )
    books: list[BookMetadata] = Field(
        default_factory=list
    )
    patents: list[PatentMetadata] = Field(
        default_factory=list
    )
    achievements: list[str] = Field(
        default_factory=list
    )

    source_file: Optional[str] = None
'''


class MetadataExtractionResult(BaseModel):
    document_type: str = "unknown"
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    faculty: Optional[FacultyMetadata] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0,)
    method: Literal["rules","llm","hybrid","fallback",] = "rules"
    missing_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

