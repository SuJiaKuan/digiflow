import base64

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from google import genai

from models.schemas import CropResponse, RecognitionResponse
from services.cropper import crop_document
from services.evaluator import evaluate as run_evaluation
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

    recognition_rows = result.get("辨識結果", [])

    try:
        evaluation = run_evaluation(recognition_rows, filename)
    except Exception as exc:
        evaluation = {"error": str(exc)}

    return RecognitionResponse(
        ok=True,
        filename=filename,
        辨識結果=recognition_rows,
        統計表=result.get("統計表", []),
        evaluation=evaluation,
    )


@router.post("/crop", response_model=CropResponse)
async def crop(file: UploadFile = File(...)):
    allowed = {"image/jpeg", "image/jpg", "image/png", "application/pdf"}
    if file.content_type and file.content_type not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"不支援的檔案類型：{file.content_type}",
        )

    file_bytes = await file.read()
    filename = file.filename or "unknown"

    try:
        jpeg_bytes = await crop_document(file_bytes, filename)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    b64 = base64.b64encode(jpeg_bytes).decode()
    return CropResponse(
        ok=True,
        filename=filename,
        cropped_image=f"data:image/jpeg;base64,{b64}",
    )
