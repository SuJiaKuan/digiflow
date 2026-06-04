"""A05 維修明細裁切服務 - 使用 Gemma 4 (vllm) 偵測表格邊界並標記。

Gemma 4 server 需先啟動：bash backend/scripts/start_gemma4_server.sh
"""

import base64
import io
import os
import re

import httpx
from PIL import Image, ImageDraw

GEMMA4_SERVER_URL = os.getenv("GEMMA4_SERVER_URL", "http://localhost:8001/v1")
GEMMA4_MODEL = os.getenv("GEMMA4_MODEL", "google/gemma-4-31b-it")

_CROP_PROMPT = (
    "Return a bounding box around the repair/maintenance detail table in this automotive service receipt.\n\n"
    "The table region to enclose:\n"
    "- TOP: the table header row with column labels "
    "(e.g. OPERATION/TEXT, TIME/QTY, H.RATE/PRCE, 施工名稱, 工時代碼/零件號碼, NO, 工時碼/件號, 作業區分)\n"
    "- BOTTOM: the last row of actual repair/part data entries, "
    "before any totals/summary section (Parts, Labour, Net, V.A.T., 合計, etc.)\n"
    "- LEFT: the first meaningful data column (item code, operation code, or part number). "
    "Do NOT include status-only columns like '取貨' or single-character row indicators\n"
    "- RIGHT: the last price/amount column (TOTAL, 實收, 總價, 整備區分)\n\n"
    "Return ONLY a JSON array with no explanation: [ymin, xmin, ymax, xmax]\n"
    "Values are integers from 0 to 1000."
)


def _image_to_b64jpeg(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=95)
    return base64.b64encode(buf.getvalue()).decode()


async def detect_table_bbox(image: Image.Image) -> tuple[float, float, float, float]:
    """Calls Gemma 4 to locate the repair table. Returns (x1, y1, x2, y2) normalized to [0, 1]."""
    b64 = _image_to_b64jpeg(image)

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
        "max_tokens": 64,
        "temperature": 0,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(f"{GEMMA4_SERVER_URL}/chat/completions", json=payload)
    resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"].strip()

    # Gemini-style bounding boxes: 1000×1000 coordinate space, format [ymin, xmin, ymax, xmax]
    match = re.search(r"\[\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\]", content)
    if not match:
        raise ValueError(f"Gemma 4 回傳格式無法解析: {content[:300]}")

    ymin, xmin, ymax, xmax = (int(match.group(i)) for i in range(1, 5))

    # Convert from 1000×1000 space to normalized [0, 1]
    x1, y1 = max(0.0, xmin / 1000), max(0.0, ymin / 1000)
    x2, y2 = min(1.0, xmax / 1000), min(1.0, ymax / 1000)

    if x2 <= x1 or y2 <= y1:
        raise ValueError(
            f"Gemma 4 回傳無效邊界框: ymin={ymin} xmin={xmin} ymax={ymax} xmax={xmax}"
        )

    return x1, y1, x2, y2


def _draw_bbox(
    image: Image.Image, x1: float, y1: float, x2: float, y2: float
) -> Image.Image:
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
