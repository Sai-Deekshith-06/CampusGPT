from pydantic import BaseModel, Field


class RenameRequest(BaseModel):
    path: str
    name: str = Field(min_length=1, max_length=255)


class MkdirRequest(BaseModel):
    path: str
    name: str = Field(min_length=1, max_length=255)


class TransferRequest(BaseModel):
    source: str
    destination: str