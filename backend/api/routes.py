from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from google import genai

from models.schemas import RecognitionResponse
from services.recognizer import process_document

router = APIRouter()


@router.post("/recognize", response_model=RecognitionResponse)
async def recognize(request: Request, file: UploadFile = File(...)):
    allowed = {"image/jpeg", "image/jpg", "image/png", "application/pdf"}
    if file.content_type and file.content_type not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"不支援的檔案類型：{file.content_type}。請上傳 JPG、PNG 或 PDF。",
        )

    file_bytes = await file.read()
    filename = file.filename or "unknown"

    client: genai.Client = request.app.state.genai_client

    try:
        result = process_document(file_bytes, filename, client)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return RecognitionResponse(
        ok=True,
        filename=filename,
        辨識結果=result.get("辨識結果", []),
        統計表=result.get("統計表", []),
    )
