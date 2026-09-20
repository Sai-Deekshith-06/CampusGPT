from typing import Literal
from pydantic import BaseModel, Field


DocumentDomain = Literal[
    "academic",
    "examination",
    "admissions",
    "administration",
    "student_services",
    "department_faculty",
    "faculty_records",
    "unknown",
]

DocumentType = Literal[
    "academic_calendar",
    "syllabus",
    "curriculum",
    "course_structure",
    "timetable",
    "academic_notification",
    "exam_timetable",
    "exam_notification",
    "hall_ticket",
    "result",
    "revaluation",
    "exam_regulation",
    "admission_notification",
    "eligibility",
    "fee_structure",
    "admission_guidelines",
    "circular",
    "notice",
    "office_order",
    "policy",
    "regulation",
    "scholarship",
    "hostel",
    "transport",
    "library",
    "student_welfare",

    "department_circular",
    "faculty_notice",
    "faculty_workload",
    "faculty_timetable",
    "faculty_meeting_notice",
    "meeting_agenda",
    "meeting_minutes",
    "department_activity_report",
    "faculty_development_program",
    "workshop",
    "seminar",
    "conference",

    "faculty_profile",

    "unknown",
]


class ClassificationResult(BaseModel):
    domain: DocumentDomain = Field(
        ..., 
        description="The high-level institutional domain of the document."
    )
    document_type: DocumentType = Field(
        ..., 
        description="The exact functional classification of the document."
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Confidence score between 0.0 and 1.0."
    )
    method: Literal["rules", "llm", "fallback"] = Field(
        ..., 
        description="Mechanism used to determine the classification."
    )
    reason: str = Field(
        ..., 
        description="Concise rationale for why this classification was selected."
    )