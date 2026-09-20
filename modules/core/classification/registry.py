import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class DocumentTypeRule:
    domain: str
    keywords: tuple[str, ...]
    strong_keywords: tuple[str, ...] = ()
    compiled_keywords: tuple[re.Pattern, ...] = field(init=False)
    compiled_strong_keywords: tuple[re.Pattern, ...] = field(init=False)

    def __post_init__(self):
        # Precompile word-boundary regular expressions to avoid substring bugs
        compiled_kw = tuple(
            re.compile(rf"\b{re.escape(k)}\b", re.IGNORECASE) 
            for k in self.keywords
        )
        compiled_skw = tuple(
            re.compile(rf"\b{re.escape(k)}\b", re.IGNORECASE) 
            for k in self.strong_keywords
        )
        object.__setattr__(self, "compiled_keywords", compiled_kw)
        object.__setattr__(self, "compiled_strong_keywords", compiled_skw)

DOCUMENT_TYPE_RULES: dict[str, DocumentTypeRule] = {
    "academic_calendar": DocumentTypeRule(
        domain="academic",
        keywords=(
            "academic calendar",
            "calendar of academic activities",
            "commencement of classwork",
            "spell of instruction",
        ),
        strong_keywords=("academic calendar",),
    ),
    "syllabus": DocumentTypeRule(
        domain="academic",
        keywords=(
            "syllabus",
            "course outcomes",
            "course objectives",
            "units of instruction",
            "learning outcomes",
        ),
        strong_keywords=("syllabus",),
    ),
    "curriculum": DocumentTypeRule(
        domain="academic",
        keywords=(
            "curriculum",
            "curriculum structure",
            "credit distribution",
            "program structure",
        ),
        strong_keywords=("curriculum",),
    ),
    "course_structure": DocumentTypeRule(
        domain="academic",
        keywords=(
            "course structure",
            "course code",
            "course title",
            "credits",
            "contact hours",
        ),
        strong_keywords=("course structure",),
    ),
    "timetable": DocumentTypeRule(
        domain="academic",
        keywords=(
            "class timetable",
            "class schedule",
            "period",
            "room number",
            "lecture timetable",
        ),
        strong_keywords=("class timetable",),
    ),
    "exam_timetable": DocumentTypeRule(
        domain="examination",
        keywords=(
            "examination timetable",
            "exam timetable",
            "examination schedule",
            "exam schedule",
            "date of examination",
            "time of examination",
        ),
        strong_keywords=("examination timetable", "exam timetable"),
    ),
    "exam_notification": DocumentTypeRule(
        domain="examination",
        keywords=(
            "examination notification",
            "exam notification",
            "examination fee",
            "exam registration",
            "examination instructions",
        ),
        strong_keywords=("examination notification", "exam notification"),
    ),
    "hall_ticket": DocumentTypeRule(
        domain="examination",
        keywords=(
            "hall ticket",
            "hall-ticket",
            "admit card",
            "examination admission card",
        ),
        strong_keywords=("hall ticket", "hall-ticket"),
    ),
    "result": DocumentTypeRule(
        domain="examination",
        keywords=(
            "examination results",
            "results",
            "grade sheet",
            "marks memo",
            "result notification",
        ),
        strong_keywords=("result notification", "examination results"),
    ),
    "revaluation": DocumentTypeRule(
        domain="examination",
        keywords=(
            "revaluation",
            "recounting",
            "challenge valuation",
            "reverification",
        ),
        strong_keywords=("revaluation",),
    ),
    "admission_notification": DocumentTypeRule(
        domain="admissions",
        keywords=(
            "admission notification",
            "admissions open",
            "admission schedule",
            "application notification",
        ),
        strong_keywords=("admission notification",),
    ),
    "eligibility": DocumentTypeRule(
        domain="admissions",
        keywords=(
            "eligibility criteria",
            "eligibility",
            "qualifications required",
            "minimum qualification",
        ),
        strong_keywords=("eligibility criteria",),
    ),
    "fee_structure": DocumentTypeRule(
        domain="admissions",
        keywords=(
            "fee structure",
            "tuition fee",
            "admission fee",
            "fee details",
        ),
        strong_keywords=("fee structure",),
    ),
    "circular": DocumentTypeRule(
        domain="administration",
        keywords=(
            "circular",
            "all concerned",
            "this is to inform",
        ),
        strong_keywords=("circular",),
    ),
    "notice": DocumentTypeRule(
        domain="administration",
        keywords=(
            "notice",
            "notice to students",
            "general notice",
        ),
        strong_keywords=("notice",),
    ),
    "office_order": DocumentTypeRule(
        domain="administration",
        keywords=(
            "office order",
            "office proceedings",
        ),
        strong_keywords=("office order",),
    ),
    "policy": DocumentTypeRule(
        domain="administration",
        keywords=(
            "policy",
            "institutional policy",
            "policy document",
        ),
        strong_keywords=("policy",),
    ),
    "regulation": DocumentTypeRule(
        domain="administration",
        keywords=(
            "regulations",
            "rules and regulations",
            "regulation code",
        ),
        strong_keywords=("regulations",),
    ),
    "scholarship": DocumentTypeRule(
        domain="student_services",
        keywords=(
            "scholarship",
            "scholarships",
            "scholarship application",
        ),
        strong_keywords=("scholarship",),
    ),
    "hostel": DocumentTypeRule(
        domain="student_services",
        keywords=(
            "hostel",
            "hostel accommodation",
            "hostel fee",
        ),
        strong_keywords=("hostel",),
    ),
    "transport": DocumentTypeRule(
        domain="student_services",
        keywords=(
            "transport",
            "bus route",
            "bus pass",
            "transportation",
        ),
        strong_keywords=("transport",),
    ),
    "library": DocumentTypeRule(
        domain="student_services",
        keywords=(
            "library",
            "library rules",
            "library timings",
        ),
        strong_keywords=("library",),
    ),
    "academic_notification": DocumentTypeRule(
        domain="academic",
        keywords=(
            "academic notification",
            "academic notice",
            "academic instructions",
            "academic activities",
        ),
        strong_keywords=("academic notification",),
    ),
    "exam_regulation": DocumentTypeRule(
        domain="examination",
        keywords=(
            "examination regulations",
            "exam regulations",
            "rules for examinations",
            "examination rules",
        ),
        strong_keywords=("examination regulations",),
    ),
    "admission_guidelines": DocumentTypeRule(
        domain="admissions",
        keywords=(
            "admission guidelines",
            "admission procedure",
            "admission instructions",
            "application guidelines",
        ),
        strong_keywords=("admission guidelines",),
    ),
    "student_welfare": DocumentTypeRule(
        domain="student_services",
        keywords=(
            "student welfare",
            "student support",
            "student assistance",
            "student welfare services",
        ),
        strong_keywords=("student welfare",),
    ),
        "department_circular": DocumentTypeRule(
        domain="department_faculty",
        keywords=(
            "department circular",
            "department notice",
            "department instructions",
            "department communication",
        ),
        strong_keywords=(
            "department circular",
        ),
    ),

    "faculty_notice": DocumentTypeRule(
        domain="department_faculty",
        keywords=(
            "faculty notice",
            "notice to faculty",
            "faculty instructions",
            "faculty communication",
        ),
        strong_keywords=(
            "faculty notice",
        ),
    ),

    "faculty_workload": DocumentTypeRule(
        domain="department_faculty",
        keywords=(
            "faculty workload",
            "teaching workload",
            "workload distribution",
            "workload allocation",
            "faculty teaching load",
        ),
        strong_keywords=(
            "faculty workload",
            "workload distribution",
        ),
    ),

    "faculty_timetable": DocumentTypeRule(
        domain="department_faculty",
        keywords=(
            "faculty timetable",
            "faculty schedule",
            "faculty time table",
            "teaching schedule",
            "faculty workload timetable",
        ),
        strong_keywords=(
            "faculty timetable",
            "faculty time table",
        ),
    ),

    "faculty_meeting_notice": DocumentTypeRule(
        domain="department_faculty",
        keywords=(
            "faculty meeting notice",
            "notice for faculty meeting",
            "faculty meeting",
            "meeting notice for faculty",
        ),
        strong_keywords=(
            "faculty meeting notice",
        ),
    ),

    "meeting_agenda": DocumentTypeRule(
        domain="department_faculty",
        keywords=(
            "meeting agenda",
            "agenda of the meeting",
            "agenda for the meeting",
            "items for discussion",
            "agenda items",
        ),
        strong_keywords=(
            "meeting agenda",
        ),
    ),

    "meeting_minutes": DocumentTypeRule(
        domain="department_faculty",
        keywords=(
            "meeting minutes",
            "minutes of the meeting",
            "minutes of meeting",
            "proceedings of the meeting",
            "resolution of the meeting",
            "action items",
        ),
        strong_keywords=(
            "meeting minutes",
            "minutes of the meeting",
        ),
    ),

    "department_activity_report": DocumentTypeRule(
        domain="department_faculty",
        keywords=(
            "department activity report",
            "department activities report",
            "activity report",
            "department annual report",
            "department events report",
            "activities conducted",
        ),
        strong_keywords=(
            "department activity report",
        ),
    ),

    "faculty_development_program": DocumentTypeRule(
        domain="department_faculty",
        keywords=(
            "faculty development program",
            "faculty development programme",
            "fdp",
            "faculty development",
            "professional development program",
            "professional development programme",
        ),
        strong_keywords=(
            "faculty development program",
            "faculty development programme",
            "fdp",
        ),
    ),

    "workshop": DocumentTypeRule(
        domain="department_faculty",
        keywords=(
            "workshop",
            "technical workshop",
            "hands-on workshop",
            "training workshop",
            "workshop program",
            "workshop programme",
        ),
        strong_keywords=(
            "workshop",
        ),
    ),

    "seminar": DocumentTypeRule(
        domain="department_faculty",
        keywords=(
            "seminar",
            "technical seminar",
            "seminar program",
            "seminar programme",
            "guest lecture",
            "expert lecture",
        ),
        strong_keywords=(
            "seminar",
        ),
    ),

    "conference": DocumentTypeRule(
        domain="department_faculty",
        keywords=(
            # "conference",
            "academic conference",
            "technical conference",
            "research conference",
            "conference proceedings",
            "conference program",
            "conference programme",
        ),
        strong_keywords=(
            "conference",
        ),
    ),
    "faculty_profile": DocumentTypeRule(
        domain="faculty_records",
        keywords=(
            "faculty profile",
            "faculty details",
            "faculty information",
            "faculty biodata",
            "faculty bio-data",
            "personal details",
            "professional details",
            "professional profile",
            "employee profile",
            "staff profile",
            "staff details",
            "educational qualifications",
            "academic qualifications",
            "professional qualifications",
            "teaching experience",
            "research interests",
            "publications",
            "journal publications",
            "conference publications",
            "faculty experience",
            "designation",
            "department",
            "date of joining",
            "area of specialization",
            "area of interest",
        ),
        strong_keywords=(
            "faculty profile",
            "faculty details",
            "faculty biodata",
            "staff profile",
            "professional profile",
        ),
    ),
}