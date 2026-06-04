"""A05 維修明細裁切服務 - 使用 Gemma 4 (vllm) 偵測表格邊界並裁切。

Gemma 4 server 需先啟動：bash backend/scripts/start_gemma4_server.sh
"""

import base64
import io
import json
import os
import re

import httpx
from PIL import Image, ImageDraw

GEMMA4_SERVER_URL = os.getenv("GEMMA4_SERVER_URL", "http://localhost:8001/v1")
GEMMA4_MODEL = os.getenv("GEMMA4_MODEL", "google/gemma-4-31b-it")

_CROP_PROMPT = (
    "Analyze this automotive service repair receipt/invoice image (Taiwan format).\n\n"
    "Locate the repair/maintenance detail table and return its bounding box in pixel coordinates.\n\n"
    "Boundary rules:\n"
    "- TOP: the table header row containing column labels "
    "(e.g. OPERATION/TEXT, TIME/QTY, H.RATE/PRCE, 施工名稱, 工時代碼/零件號碼, NO, 工時碼/件號, 作業區分)\n"
    "- BOTTOM: the last row of actual repair/part data entries, "
    "stopping before any totals/summary section (Parts, Labour, Net, V.A.T., etc.)\n"
    "- LEFT: the first meaningful data column — typically the item code, operation code, "
    "or part number column. Do NOT include pure status-only columns like '取貨' or single-character row indicators\n"
    "- RIGHT: the last price/amount column (e.g. TOTAL, 實收, 總價, 整備區分)\n\n"
    "Respond with ONLY this JSON object. No explanation, no markdown, no extra text:\n"
    '{"x1": <left_px>, "y1": <top_px>, "x2": <right_px>, "y2": <bottom_px>}'
)


def _image_to_b64jpeg(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=95)
    return base64.b64encode(buf.getvalue()).decode()


async def detect_table_bbox(image: Image.Image) -> tuple[float, float, float, float]:
    """Calls Gemma 4 to locate the repair table. Returns (x1, y1, x2, y2) normalized to [0, 1]."""
    b64 = _image_to_b64jpeg(image)
    w, h = image.size

    payload = {
        "model": GEMMA4_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    },
                    {"type": "text", "text": _CROP_PROMPT},
                ],
            }
        ],
        "max_tokens": 128,
        "temperature": 0,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(f"{GEMMA4_SERVER_URL}/chat/completions", json=payload)
    resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"].strip()

    match = re.search(r"\{[^}]+\}", content, re.DOTALL)
    if not match:
        raise ValueError(f"Gemma 4 回傳格式無法解析: {content[:300]}")

    data = json.loads(match.group())
    x1, y1, x2, y2 = float(data["x1"]), float(data["y1"]), float(data["x2"]), float(data["y2"])

    # Gemma 4 may return pixel coordinates — normalize if any value exceeds 1.0
    if max(x1, y1, x2, y2) > 1.0:
        x1, y1, x2, y2 = x1 / w, y1 / h, x2 / w, y2 / h

    x1, y1 = max(0.0, x1), max(0.0, y1)
    x2, y2 = min(1.0, x2), min(1.0, y2)

    if x2 <= x1 or y2 <= y1:
        raise ValueError(f"Gemma 4 回傳無效邊界框: {data}")

    return x1, y1, x2, y2


def _draw_bbox(image: Image.Image, x1: float, y1: float, x2: float, y2: float) -> Image.Image:
    w, h = image.size
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    line_w = max(4, int(min(w, h) * 0.004))
    draw.rectangle(
        [int(x1 * w), int(y1 * h), int(x2 * w), int(y2 * h)],
        outline="red",
        width=line_w,
    )
    return annotated


async def crop_document(file_bytes: bytes, filename: str) -> bytes:
    """End-to-end: file bytes → JPEG bytes of original image with red bbox drawn."""
    from services.recognizer import load_document_as_image
    image = load_document_as_image(file_bytes, filename)
    x1, y1, x2, y2 = await detect_table_bbox(image)
    annotated = _draw_bbox(image, x1, y1, x2, y2)
    buf = io.BytesIO()
    annotated.save(buf, format="JPEG", quality=95)
    return buf.getvalue()
