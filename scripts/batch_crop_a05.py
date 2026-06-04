#!/usr/bin/env python3
"""批次偵測 A05 維修明細表格區塊並標記紅框。

使用 Gemma 4 vllm server（邏輯共用 backend/services/cropper.py）。

前置條件：
  先啟動 Gemma 4 server：bash backend/scripts/start_gemma4_server.sh

用法：
  python scripts/batch_crop_a05.py [--input INPUT_DIR] [--output OUTPUT_DIR]

預設輸入：test_data/A05/print/
預設輸出：output/crop/A05/
"""

import argparse
import json
import sys
import time
from pathlib import Path

from PIL import Image

# Add backend/ to path so we can import services.cropper directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from services.cropper import detect_table_bbox_sync, draw_bbox  # noqa: E402

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}


def process_images(input_dir: Path, output_dir: Path) -> None:
    images = sorted(p for p in input_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    if not images:
        print(f"[ERROR] 找不到圖片：{input_dir}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"

    print(f"共 {len(images)} 張圖片，輸出至 {output_dir}\n")

    results = []

    for idx, img_path in enumerate(images, 1):
        t0 = time.time()
        status = "ok"
        error_msg = ""
        bbox = None

        try:
            image = Image.open(img_path).convert("RGB")
            x1, y1, x2, y2 = detect_table_bbox_sync(image)
            bbox = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
            annotated = draw_bbox(image, x1, y1, x2, y2)
            out_path = output_dir / img_path.name
            annotated.save(out_path, format="JPEG", quality=95)
            elapsed = round(time.time() - t0, 2)
            print(f"[{idx:3d}/{len(images)}] {img_path.name}  bbox={bbox}  {elapsed}s")
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
    parser = argparse.ArgumentParser(description="批次偵測 A05 維修明細表格")
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

    project_root = Path(__file__).resolve().parent.parent
    input_dir = (project_root / args.input).resolve()
    output_dir = (project_root / args.output).resolve()

    if not input_dir.exists():
        print(f"[ERROR] 輸入資料夾不存在：{input_dir}")
        sys.exit(1)

    process_images(input_dir, output_dir)


if __name__ == "__main__":
    main()
