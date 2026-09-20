from core.classification.schemas import ClassificationResult


DOMAIN_DOCUMENT_TYPES = {
    "academic": {
        "academic_calendar",
        "syllabus",
        "curriculum",
        "course_structure",
        "timetable",
    },
    "examination": {
        "exam_timetable",
        "exam_notification",
        "hall_ticket",
        "result",
        "revaluation",
        "exam_regulation",
    },
    "admissions": {
        "admission_notification",
        "eligibility",
        "fee_structure",
        "admission_guidelines",
    },
    "administration": {
        "circular",
        "notice",
        "office_order",
        "policy",
        "regulation",
    },
    "student_services": {
        "scholarship",
        "hostel",
        "transport",
        "library",
        "student_welfare",
    },
    "department_faculty": {
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
    },
}


def validate_classification(
    result: ClassificationResult,
) -> ClassificationResult:
    if result.domain == "unknown" or result.document_type == "unknown":
        return result

    valid_types = DOMAIN_DOCUMENT_TYPES.get(result.domain, set())

    if result.document_type not in valid_types:
        return result.model_copy(
            update={
                "domain": "unknown",
                "document_type": "unknown",
                "confidence": 0.0,
                "method": "fallback",
                "reason": (
                    "The selected document type is inconsistent "
                    "with the selected domain."
                ),
            }
        )

    return result