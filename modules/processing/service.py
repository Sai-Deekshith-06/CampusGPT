from collections.abc import Callable
from datetime import datetime, timezone


from core.classification.classifier import DocumentClassifier
from core.metadata.registry import get_metadata_extractor
from processing.schemas import ProcessingResult, StageRecord
from processing.status import ProcessingStatus
from processing.stages import (
    STAGE_CLASSIFICATION,
    STAGE_COMPLETED,
    STAGE_COMPLETED_WITH_WARNINGS,
    STAGE_EXTRACTION,
    STAGE_FAILED,
    STAGE_VALIDATION,
    ProcessingStage
)


class DocumentProcessingService:
    def __init__(
        self,
        on_stage_change: Callable[[str, ProcessingStatus], None] | None = None,
    ):
        self.classifier = DocumentClassifier()
        self.on_stage_change = on_stage_change

    def process(
        self,
        markdown: str,
        source_file: str | None = None,
    ) -> ProcessingResult:
        result = ProcessingResult(source_file=source_file)

        try:
            self._set_stage(result, STAGE_CLASSIFICATION)

            classification = self.classifier.classify(markdown)
            result.classification = classification

            document_type = self._get_document_type(classification)
            result.document_type = document_type

            self._set_stage(result, STAGE_EXTRACTION)

            extractor = get_metadata_extractor(document_type)
            metadata = extractor.extract(
                markdown=markdown,
                source_file=source_file,
            )
            result.metadata = metadata
            
            # CHUNKING
            from processing.stages import STAGE_CHUNKING
            self._set_stage(result, STAGE_CHUNKING)
            raise NotImplementedError("Chunking and embedding are not implemented yet.")

            self._set_stage(result, STAGE_VALIDATION)

            validation_errors, warnings = self._validate_result(
                markdown=markdown,
                document_type=document_type,
                metadata=metadata,
            )

            result.errors.extend(validation_errors)
            result.warnings.extend(warnings)

            if validation_errors:
                result.success = False
                result.status = ProcessingStatus.FAILED
                if result.stage_history:
                    result.stage_history[-1].status = ProcessingStatus.FAILED
                if self.on_stage_change and result.current_stage:
                    self.on_stage_change(result.current_stage, ProcessingStatus.FAILED)
            else:
                result.success = True

                if result.warnings:
                    self._set_stage(
                        result,
                        STAGE_COMPLETED_WITH_WARNINGS,
                    )
                else:
                    self._set_stage(
                        result,
                        STAGE_COMPLETED,
                    )

            if result.warnings and result.success:
                self._set_stage(
                    result,
                    STAGE_COMPLETED_WITH_WARNINGS,
                )
            elif result.success:
                self._set_stage(
                    result,
                    STAGE_COMPLETED,
                )

            self._complete_current_stage(result)
            result.complete()

            return result

        except Exception as exc:
            result.success = False
            result.errors.append(str(exc))

            result.status = ProcessingStatus.FAILED
            if result.stage_history:
                result.stage_history[-1].status = ProcessingStatus.FAILED
            if self.on_stage_change and result.current_stage:
                self.on_stage_change(result.current_stage, ProcessingStatus.FAILED)
                
            self._complete_current_stage(result)
            result.complete()

            return result

    @staticmethod
    def _validate_result(
        markdown: str,
        document_type: str | None,
        metadata,
    ) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []

        if not markdown or not markdown.strip():
            errors.append("Markdown content is empty.")

        if not document_type:
            errors.append("Document type is missing.")

        if metadata is None:
            errors.append("Metadata extraction returned no result.")

        if hasattr(metadata, "warnings") and metadata.warnings:
            warnings.extend(metadata.warnings)

        elif isinstance(metadata, dict):
            metadata_warnings = metadata.get("warnings", [])

            if metadata_warnings:
                warnings.extend(metadata_warnings)

        return errors, warnings

    @staticmethod
    def _complete_current_stage(
        result: ProcessingResult,
    ) -> None:
        if not result.stage_history:
            return

        current_stage = result.stage_history[-1]

        if current_stage.completed_at is None:
            current_stage.complete()

    def _set_stage(
        self,
        result: ProcessingResult,
        stage: ProcessingStage,
    ) -> None:
        now = datetime.now(timezone.utc)

        if result.stage_history:
            previous_stage = result.stage_history[-1]

            if previous_stage.completed_at is None:
                previous_stage.completed_at = now
                previous_stage.duration_ms = (
                    now - previous_stage.started_at
                ).total_seconds() * 1000

        result.current_stage = stage.name
        result.status = stage.status

        result.stage_history.append(
            StageRecord(
                stage=stage.name,
                status=stage.status,
                started_at=now,
            )
        )

        if self.on_stage_change:
            self.on_stage_change(stage.name, stage.status)

    @staticmethod
    def _get_document_type(classification) -> str:
        if hasattr(classification, "document_type"):
            return classification.document_type

        if isinstance(classification, dict):
            document_type = classification.get("document_type")
            if document_type:
                return document_type

        raise ValueError(
            "Classification result does not contain document_type"
        )

    @staticmethod
    def _get_warnings(metadata) -> list[str]:
        if hasattr(metadata, "warnings"):
            warnings = metadata.warnings
            if warnings:
                return list(warnings)

        if isinstance(metadata, dict):
            warnings = metadata.get("warnings", [])
            if warnings:
                return list(warnings)

        return []