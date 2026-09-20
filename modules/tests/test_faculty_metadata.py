from pathlib import Path

from core.metadata.extractors.faculty import FacultyMetadataExtractor


paths = [
    Path(r"C:\Desktop\CampusGPT\data\md\faculty_details\ds\teaching\A_Srichandana.md"),
    Path(r"C:\Desktop\CampusGPT\data\md\faculty_details\ds\teaching\A_Srinivasa_Reddy.md"),
]

for path in paths:
    markdown = path.read_text(encoding="utf-8")

    faculty = FacultyMetadataExtractor.extract(
        markdown=markdown,
        source_file=str(path),
    )

    print(faculty.model_dump_json(indent=2))
    print('-'*40)