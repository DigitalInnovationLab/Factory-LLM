from pydantic import BaseModel

from common import File


class StartForm(BaseModel):
    """
    Model for the start form.
    """

    rag_technique: str
    chunk_size: int
    chunk_overlap: int
    vector_top_k: int
    files: list[File]


class EditForm(BaseModel):
    """
    Model for the edit form.
    """

    name: str
    description: str
    prompt: str
    model: str
    technique: str
