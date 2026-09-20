# from pathlib import Path

# from processing.pipeline import DocumentPipeline


# def on_stage_change(stage: str, status) -> None:
#     print(f"[STAGE] {stage} → {status.value}")


# def main() -> None:
#     file_path = Path(
#         r"C:\Desktop\CampusGPT\data\md\faculty_details\ds\teaching\A_Srichandana.md"
#     )

#     pipeline = DocumentPipeline()

#     pipeline.processing_service.on_stage_change = on_stage_change

#     result = pipeline.process_file(file_path)

#     print("\nPROCESSING RESULT")
#     print("=" * 60)
#     print(result.model_dump_json(indent=2))


# if __name__ == "__main__":
#     main()

from pathlib import Path

from processing.pipeline import DocumentPipeline


def main():
    pdf_path = Path(
        # r"C:\Desktop\CampusGPT\data\pdfs\academic_calenders\Revised Academic Calendar for II B.Tech. I & II Semesters 2026-27.pdf"
        # r"C:\Desktop\CampusGPT\data\pdfs\Transcripts Form.pdf"
        r"C:\Desktop\CampusGPT\data\md\faculty_details\ds\teaching\A_Srichandana.md"
        # r"C:\Desktop\CampusGPT\data\pdfs\syllabus\CSE-DS R22 I year Syllabus.pdf"
        # r"C:\Desktop\CampusGPT\data\pdfs\CSE-DS R22 I year Syllabus pg1-10.pdf"
    )

    pipeline = DocumentPipeline()
    result = pipeline.process_file(pdf_path)

    print("\n" + "=" * 80)
    print("PROCESSING RESULT")
    print("=" * 80)

    print(f"Success: {result.success}")
    print(f"Status: {result.status}")
    # print(f"Document type: {result.document_type}")
    print(f"Warnings: {result.warnings}")
    print(f"Errors: {result.errors}")

    print("\nMetadata:")
    print(result.metadata)

    print("\nStage history:")
    for stage in result.stage_history:
        print(
            f"{stage.stage}: "
            f"{stage.status.value} "
            f"({stage.duration_ms} ms)"
        )


if __name__ == "__main__":
    main()