from dataclasses import dataclass

from processing.status import ProcessingStatus


@dataclass(frozen=True)
class ProcessingStage:
    name: str
    status: ProcessingStatus

STAGE_CONVERSION = ProcessingStage(
    name="conversion",
    status=ProcessingStatus.CONVERTING,
)

STAGE_CLASSIFICATION = ProcessingStage(
    name="classification",
    status=ProcessingStatus.CLASSIFYING,
)

STAGE_EXTRACTION = ProcessingStage(
    name="extraction",
    status=ProcessingStatus.EXTRACTING,
)

STAGE_CHUNKING = ProcessingStage(
    name="chunking",
    status=ProcessingStatus.CHUNKING,
)

STAGE_EMBEDDINGS = ProcessingStage(
    name="embeddings",
    status=ProcessingStatus.EMBEDDING,
)

STAGE_VALIDATION = ProcessingStage(
    name="validation",
    status=ProcessingStatus.VALIDATING,
)

STAGE_COMPLETED = ProcessingStage(
    name="completed",
    status=ProcessingStatus.COMPLETED,
)

STAGE_COMPLETED_WITH_WARNINGS = ProcessingStage(
    name="completed",
    status=ProcessingStatus.COMPLETED_WITH_WARNINGS,
)

STAGE_FAILED = ProcessingStage(
    name="failed",
    status=ProcessingStatus.FAILED,
)