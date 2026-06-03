from typing import Any
from pydantic import BaseModel


class RecognitionResponse(BaseModel):
    ok: bool
    filename: str
    辨識結果: list[dict[str, Any]] = []
    統計表: list[dict[str, Any]] = []


class ErrorResponse(BaseModel):
    ok: bool
    error: str
    detail: str = ""
