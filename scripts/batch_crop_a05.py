#!/usr/bin/env python3
"""批次裁切 A05 維修明細表格區塊。

使用 Gemma 4 vllm server 偵測每張圖片中的維修明細表格位置，裁切後存入輸出資料夾。

前置條件：
  先啟動 Gemma 4 server：bash backend/scripts/start_gemma4_server.sh

用法：
  python scripts/batch_crop_a05.py [--input INPUT_DIR] [--output OUTPUT_DIR]

預設輸入：test_data/A05/print/
預設輸出：output/crop/A05/
"""

import argparse
import base64
import io
import json
import os
import re
import sys
import time
from pathlib import Path

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

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}


def load_image(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def image_to_b64jpeg(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=95)
    return base64.b64encode(buf.getvalue()).decode()


def detect_bbox(image: Image.Image, client: httpx.Client) -> tuple[float, float, float, float]:
    b64 = image_to_b64jpeg(image)
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

    resp = client.post(f"{GEMMA4_SERVER_URL}/chat/completions", json=payload)
    resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"].strip()

    match = re.search(r"\{[^}]+\}", content, re.DOTALL)
    if not match:
        raise ValueError(f"回傳格式無法解析: {content[:300]}")

    data = json.loads(match.group())
    x1, y1, x2, y2 = float(data["x1"]), float(data["y1"]), float(data["x2"]), float(data["y2"])

    # Gemma 4 may return pixel coordinates — normalize if any value exceeds 1.0
    if max(x1, y1, x2, y2) > 1.0:
        x1, y1, x2, y2 = x1 / w, y1 / h, x2 / w, y2 / h

    x1, y1 = max(0.0, x1), max(0.0, y1)
    x2, y2 = min(1.0, x2), min(1.0, y2)

    if x2 <= x1 or y2 <= y1:
        raise ValueError(f"無效邊界框: {data}")

    return x1, y1, x2, y2


def draw_bbox(image: Image.Image, x1: float, y1: float, x2: float, y2: float) -> Image.Image:
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


def process_images(input_dir: Path, output_dir: Path) -> None:
    images = sorted(p for p in input_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    if not images:
        print(f"[ERROR] 找不到圖片：{input_dir}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"

    print(f"共 {len(images)} 張圖片，輸出至 {output_dir}")
    print(f"Gemma 4 server: {GEMMA4_SERVER_URL}\n")

    results = []

    with httpx.Client(timeout=120.0) as client:
        for idx, img_path in enumerate(images, 1):
            t0 = time.time()
            status = "ok"
            error_msg = ""
            bbox = None

            try:
                image = load_image(img_path)
                x1, y1, x2, y2 = detect_bbox(image, client)
                bbox = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
                annotated = draw_bbox(image, x1, y1, x2, y2)
                out_path = output_dir / img_path.name
                annotated.save(out_path, format="JPEG", quality=95)
                elapsed = round(time.time() - t0, 2)
                print(f"[{idx:3d}/{len(images)}] {img_path.name}  bbox={bbox}  {elapsed}s  → {out_path.name}")
            except Exception as exc:
                elapsed = round(time.time() - t0, 2)
                status = "error"
                error_msg = str(exc)
                print(f"[{idx:3d}/{len(images)}] {img_path.name}  ERROR: {error_msg}  {elapsed}s")

            results.append({
                "filename": img_path.name,
                "status": status,
                "bbox": bbox,
                "elapsed_s": elapsed,
                "error": error_msg,
            })

    ok_count = sum(1 for r in results if r["status"] == "ok")
    print(f"\n完成：{ok_count}/{len(images)} 成功，摘要存至 {summary_path}")

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="批次裁切 A05 維修明細表格")
    parser.add_argument(
        "--input",
        default="test_data/A05/print",
        help="輸入圖片資料夾（預設：test_data/A05/print）",
    )
    parser.add_argument(
        "--output",
        default="output/crop/A05",
        help="輸出資料夾（預設：output/crop/A05）",
    )
    args = parser.parse_args()

    # Resolve relative to project root (where this script typically runs from)
    project_root = Path(__file__).resolve().parent.parent
    input_dir = (project_root / args.input).resolve()
    output_dir = (project_root / args.output).resolve()

    if not input_dir.exists():
        print(f"[ERROR] 輸入資料夾不存在：{input_dir}")
        sys.exit(1)

    process_images(input_dir, output_dir)


if __name__ == "__main__":
    main()
