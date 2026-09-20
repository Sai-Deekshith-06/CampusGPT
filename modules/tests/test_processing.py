from pathlib import Path

from processing.pipeline import DocumentPipeline
from processing.service import DocumentProcessingService


def on_stage_change(stage: str, status) -> None:
    print(f"[STAGE] {stage} → {status.value}")


markdown_path = Path(
    r"C:\Desktop\CampusGPT\data\md\faculty_details\ds\teaching\A_Srichandana.md"
)

service = DocumentProcessingService(
    on_stage_change=on_stage_change,
)

pipeline = DocumentPipeline(
    processing_service=service,
)

result = pipeline.process_file(markdown_path)

print(result.model_dump_json(indent=2))