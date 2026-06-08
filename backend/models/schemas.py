from typing import Any, Optional
from pydantic import BaseModel


class RecognitionResponse(BaseModel):
    ok: bool
    filename: str
    辨識結果: list[dict[str, Any]] = []
    統計表: list[dict[str, Any]] = []
    evaluation: Optional[dict[str, Any]] = None


class CropResponse(BaseModel):
    ok: bool
    filename: str
    cropped_image: str  # data URL: "data:image/jpeg;base64,..."


class ErrorResponse(BaseModel):
    ok: bool
    error: str
    detail: str = ""
