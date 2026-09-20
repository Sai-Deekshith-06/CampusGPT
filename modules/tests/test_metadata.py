from pathlib import Path
import json

from core.classification import classify_file
from core.metadata import MetadataExtractor, MetadataValidator


def process_file(file_path: str | Path):
    path = Path(file_path)

    # 1. Classify the Markdown document
    classification = classify_file(path)

    # 2. Extract metadata based on the classification result
    extractor = MetadataExtractor()
    metadata_result = extractor.extract_file(
        file_path=path,
        document_type=classification.document_type,
    )

    # 3. Validate metadata according to the document type
    validator = MetadataValidator()
    missing_fields = validator.validate(metadata_result)

    return {
        "classification": classification,
        "metadata": metadata_result,
        "missing_fields": missing_fields,
    }



def main():
    markdown_paths = (
        "C:/Desktop/CampusGPT/data/md/faculty_details/ds/teaching/A_Srichandana.md",
        Path(__file__).parent
        / ".temp"
        / "Academic Calendar for IV B.Tech. I & II Semesters 2026-27.md",
    )

    for markdown_path in markdown_paths:

        result = process_file(markdown_path)

        print("Classification:")
        print(json.dumps(
            result["classification"].model_dump(),
            indent=2,
            ensure_ascii=False,
        ))

        print("\nExtracted Metadata:")
        print(json.dumps(
            result["metadata"].model_dump(),
            indent=2,
            ensure_ascii=False,
        ))

        print("\nValidation:")
        missing_fields = result["missing_fields"]

        if missing_fields:
            print(f"Missing fields: {', '.join(missing_fields)}")
        else:
            print("Metadata is valid.")
        print('-'*50)


if __name__ == "__main__":
    main()