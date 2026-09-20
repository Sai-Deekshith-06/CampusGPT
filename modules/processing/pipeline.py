from datetime import datetime, timezone
from pathlib import Path

from processing.status import ProcessingStatus
from processing.converters import (
    MarkdownConverter,
    PDFConverter,
)
from processing.converters.registry import ConverterRegistry
from processing.schemas import ProcessingResult, StageRecord
from processing.stages import STAGE_CONVERSION
from processing.service import DocumentProcessingService


from collections.abc import Callable

class DocumentPipeline:
    def __init__(
        self,
        processing_service: DocumentProcessingService | None = None,
        converter_registry: ConverterRegistry | None = None,
        api_key: str | None = None,
        on_stage_change: Callable[[str, ProcessingStatus], None] | None = None,
    ):
        self.on_stage_change = on_stage_change
        
        self.processing_service = (
            processing_service or DocumentProcessingService(on_stage_change=self.on_stage_change)
        )

        self.converter_registry = (
            converter_registry
            or self._create_default_registry(api_key)
        )

    def process_markdown(
        self,
        markdown: str,
        source_file: str | None = None,
    ) -> ProcessingResult:
        return self.processing_service.process(
            markdown=markdown,
            source_file=source_file,
        )

    def process_file(
        self,
        file_path: str | Path,
    ) -> ProcessingResult:
        path = Path(file_path)

        conversion_started_at = datetime.now(timezone.utc)

        if self.on_stage_change:
            self.on_stage_change(STAGE_CONVERSION.name, STAGE_CONVERSION.status)

        conversion_record = StageRecord(
            stage=STAGE_CONVERSION.name,
            status=STAGE_CONVERSION.status,
            started_at=conversion_started_at,
        )

        try:
            converter = self.converter_registry.get_converter(path)
            markdown = converter.convert(path)

            conversion_record.complete()

            result = self.process_markdown(
                markdown=markdown,
                source_file=str(path),
            )

            result.stage_history.insert(0, conversion_record)

            return result

        except Exception as exc:
            conversion_record.complete()
            
            if self.on_stage_change:
                self.on_stage_change(STAGE_CONVERSION.name, ProcessingStatus.FAILED)

            result = ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                current_stage=STAGE_CONVERSION.name,
                source_file=str(path),
                errors=[str(exc)],
                stage_history=[conversion_record],
            )
            result.complete()

            return result

    @staticmethod
    def _create_default_registry(
        api_key: str | None = None,
    ) -> ConverterRegistry:
        return ConverterRegistry(
            converters=[
                MarkdownConverter(),
                PDFConverter(api_key=api_key),
            ]
        )