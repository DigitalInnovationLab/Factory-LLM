from tempfile import SpooledTemporaryFile

from pydantic import BaseModel, SkipValidation


class File(BaseModel):
    """
    Model for an uploaded file.
    """

    name: str
    content: SkipValidation[SpooledTemporaryFile]

    class Config:
        """
        Pydantic configuration.
        """

        arbitrary_types_allowed = True
