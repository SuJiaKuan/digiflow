"""A05 維修明細辨識服務，移植自 ref/A05_print.ipynb。"""

import io
import json
import time

import fitz
from google import genai
from google.genai import types
from PIL import Image

EXCLUDED_RESULT_COLUMNS = {
    "員工名稱",
    "發票號碼",
    "領料人技師",
    "備註",
    "給點倍率",
    "整備區分",
}
EXCLUDED_RESULT_COLUMNS_NORMALIZED = {
    col.replace(" ", "") for col in EXCLUDED_RESULT_COLUMNS
}


def _to_number(v):
    """Gemini 標記為數值欄位的值 → int / float；無法轉換則原樣回傳。
    移除千分位逗號（如 "1,027" → 1027）再嘗試解析。"""
    if not isinstance(v, str):
        return v
    s = v.strip().replace(",", "")
    if not s:
        return v
    try:
        f = float(s)
        return int(f) if f == int(f) else f
    except ValueError:
        return v


SYSTEM_PROMPT = """
你是一個專業的台灣汽車結帳清單(A05)資料擷取系統。請仔細辨識提供的「維修明細表」文件，嚴格遵守以下規則，並且只以 JSON 格式回傳。

1.【辨識範圍】
(1) 只包括「表頭」、「估價日期」欄位、「牌照號碼」欄位與「維修明細表」區塊。
(2) 排除其他資訊，例如聯絡資訊、頁尾、注意事項、付款資訊、章戳內容、浮水印與非維修明細表區塊。

2.【提取估價單基本資訊】
(1) 「維修廠」名稱請優先從表頭提取；若沒有明確表頭，再從公司 Logo 或公司名稱辨識。
(2) 只提取上方對應欄位中的「估價日期」與「牌照號碼」。
(3) 若牌照號碼有遮蔽，請比照原格式「3碼英文-4碼數字」以 * 補齊，例如 ABC-12**。
(4) 若無值或文件上無此欄位，請輸出空字串。

3.【完整提取維修明細表】
(1) 務必提取「維修明細表」中所有維修項目的所有欄位與值，看到什麼就提取什麼，不要自行改寫欄位名稱。
(2) 每一個維修項目要由上而下逐一分列顯示，不可遺漏。
(3) 若同一欄位內有多行文字或數字，請合併在同一欄位中輸出。
(4) 若有手寫記號（例如 〃、V、X、△、P、?、… 等），請辨識並顯示於「核價」欄位。
(5) 若原表沒有「核價」欄位，但有手寫記號，請新增「核價」欄位承接這些記號。
(6) 若「維修明細表」區塊上有被蓋單位章，請不要擷取章上的文字或數字。

4.【Excel 表單規則】
(1) 每次只辨識一份文件。
(2) JSON 只允許輸出三個 key：「辨識結果」、「統計表」與「欄位類型」。
(3) 「辨識結果」中的每一列都必須包含：來源檔名、維修廠、估價日期、牌照號碼，再接各「維修廠」維修明細表的原始欄位。
(4) 欄位名稱請依該維修廠文件上的原始表頭輸出，不要轉成共通格式欄位。
(5) 維修明細表欄位必須排除：員工名稱、發票號碼、領料人技師、備註、給點倍率、整備區分。
(6) 不要虛構不存在的欄位，也不要漏掉原表有的欄位。

5.【統計表規則】
(1) 統計表固定輸出一列，欄位為：來源檔名、處理時間(秒)、信心水準、總欄位數(含空值)、有效值欄位數、異常備註。
(2) 「處理時間(秒)」先填 0，稍後由程式覆寫。
(3) 異常備註請逐一列出所有信心水準低於 90% 的欄位與原因；若無則輸出空字串。

6.【欄位類型標記】
(1) JSON 中新增頂層 key「欄位類型」，標記「維修明細表」各欄位的資料型別。
(2) 格式：{"number": ["欄位名1", ...], "string": ["欄位名2", ...]}
(3) 判斷原則：
    - number：欄位的值預期為純數字，例如 項次、NO、數量、單價、工時、金額、折數、售價、實收、單位費用 等
    - string ：欄位的值含文字或混合內容，例如 工時碼、件號、品名、名稱、代碼、領料別、作業區分、核價 等
(4) 固定 meta 欄位（來源檔名、維修廠、估價日期、牌照號碼）無需列入「欄位類型」。

請務必只回傳合法 JSON，不要包含 Markdown、說明文字、註解或任何額外內容。
格式如下：
{
  "辨識結果": [
    {
      "來源檔名": "example.pdf",
      "維修廠": "順益汽車",
      "估價日期": "2026/03/24",
      "牌照號碼": "ABC-1234",
      "項次": "1",
      "代碼": "...",
      "維修項目": "...",
      "估價": "...",
      "核價": "..."
    }
  ],
  "統計表": [
    {
      "來源檔名": "example.pdf",
      "處理時間(秒)": 0,
      "信心水準": "95%",
      "總欄位數(含空值)": 0,
      "有效值欄位數": 0,
      "異常備註": ""
    }
  ],
  "欄位類型": {
    "number": ["項次", "估價"],
    "string": ["代碼", "維修項目", "核價"]
  }
}
"""


def _normalize_column_name(col: str) -> str:
    return str(col).strip().replace(" ", "")


def _is_excluded(col: str) -> bool:
    return _normalize_column_name(col) in EXCLUDED_RESULT_COLUMNS_NORMALIZED


def load_document_as_image(
    file_bytes: bytes, filename: str, zoom: float = 2.0
) -> Image.Image:
    """Accepts raw bytes. Supports JPG, PNG, PDF.
    PDF: renders each page at 2x zoom, merges vertically (same logic as notebook)."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "pdf":
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        rendered_pages = []

        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
            rendered_pages.append(img)

        doc.close()

        if not rendered_pages:
            raise ValueError(f"PDF 無可讀頁面: {filename}")

        if len(rendered_pages) == 1:
            return rendered_pages[0]

        max_width = max(img.width for img in rendered_pages)
        total_height = sum(img.height for img in rendered_pages)
        merged = Image.new("RGB", (max_width, total_height), "white")

        current_y = 0
        for img in rendered_pages:
            if img.width < max_width:
                canvas = Image.new("RGB", (max_width, img.height), "white")
                canvas.paste(img, (0, 0))
                img = canvas
            merged.paste(img, (0, current_y))
            current_y += img.height

        return merged

    return Image.open(io.BytesIO(file_bytes)).convert("RGB")


def recognize_a05(image: Image.Image, filename: str, client: genai.Client) -> dict:
    """Calls Gemini 2.5 Pro with the A05 system prompt. Returns raw parsed dict."""
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=95)
    image_bytes = buf.getvalue()

    image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")

    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[SYSTEM_PROMPT, f"目前處理檔案：{filename}", image_part],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0,
        ),
    )

    return json.loads(response.text.strip())


def normalize_result(raw: dict, filename: str, duration: float) -> dict:
    """Column aliasing, default values, excluded columns, duration injection.
    Verbatim port of notebook Block 3 normalize_result_json."""
    if not isinstance(raw, dict):
        raise ValueError("Gemini 回傳格式不是 JSON 物件")

    raw.setdefault("辨識結果", [])
    raw.setdefault("統計表", [])

    if isinstance(raw["辨識結果"], dict):
        raw["辨識結果"] = [raw["辨識結果"]]
    if isinstance(raw["統計表"], dict):
        raw["統計表"] = [raw["統計表"]]

    # 從 Gemini 的欄位類型 hint 取出數值欄位集合，然後從頂層移除
    col_types = raw.pop("欄位類型", {})
    numeric_cols = {str(c).strip() for c in col_types.get("number", [])}

    cleaned_rows = []
    for row in raw["辨識結果"]:
        if not isinstance(row, dict):
            continue

        if "車牌號碼" in row and "牌照號碼" not in row:
            row["牌照號碼"] = row.pop("車牌號碼")
        if "車牌" in row and "牌照號碼" not in row:
            row["牌照號碼"] = row.pop("車牌")

        row.setdefault("來源檔名", filename)
        row.setdefault("維修廠", "")
        row.setdefault("估價日期", "")
        row.setdefault("牌照號碼", "")

        cleaned_rows.append(
            {
                k: (_to_number(v) if k in numeric_cols else v)
                for k, v in row.items()
                if not _is_excluded(k)
            }
        )

    raw["辨識結果"] = cleaned_rows

    if not raw["統計表"]:
        raw["統計表"] = [
            {
                "來源檔名": filename,
                "處理時間(秒)": duration,
                "信心水準": "",
                "總欄位數(含空值)": 0,
                "有效值欄位數": 0,
                "異常備註": "",
            }
        ]
    else:
        stat = raw["統計表"][0]
        stat["來源檔名"] = filename
        stat["處理時間(秒)"] = duration
        stat.setdefault("信心水準", "")
        stat.setdefault("總欄位數(含空值)", 0)
        stat.setdefault("有效值欄位數", 0)
        stat.setdefault("異常備註", "")

    return raw


def process_document(file_bytes: bytes, filename: str, client: genai.Client) -> dict:
    """End-to-end: bytes → Gemini → normalized dict. Raises on failure."""
    start = time.time()
    image = load_document_as_image(file_bytes, filename)
    raw = recognize_a05(image, filename, client)
    duration = round(time.time() - start, 2)
    return normalize_result(raw, filename, duration)
