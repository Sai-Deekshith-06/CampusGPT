from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    CONVERTING = "converting"
    CLASSIFYING = "classifying"
    EXTRACTING = "extracting"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    VALIDATING = "validating"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"

# class ProcessingStatus(str, Enum):
#     PENDING = "pending"
#     RUNNING = "running"
#     COMPLETED = "completed"
#     COMPLETED_WITH_WARNINGS = "completed_with_warnings"
#     FAILED = "failed"
#     CANCELLED = "cancelled"

# class ProcessingStageStatus(str, Enum):
#     CONVERTING = "converting"
#     CLASSIFYING = "classifying"
#     EXTRACTING = "extracting"
#     VALIDATING = "validating"
#     CHUNKING = "chunking"
#     EMBEDDINGS = "embeddings"