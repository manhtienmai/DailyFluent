"""
PDF Kanji Extractor Service.

Converts PDF pages to images, sends them to Gemini AI for kanji extraction,
and returns structured JSON matching the fixture format.
"""

import base64
import io
import json
import logging
import os
import uuid

import fitz  # PyMuPDF

from vocab.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

# ── PDF → Image conversion ─────────────────────────────────

UPLOAD_DIR = os.path.join("media", "kanji_pdf")


def save_pdf(file_bytes: bytes) -> tuple[str, int]:
    """
    Save uploaded PDF and return (session_id, page_count).
    Pages are rendered to PNG for AI processing.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    session_id = uuid.uuid4().hex[:12]
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    pdf_path = os.path.join(session_dir, "source.pdf")
    with open(pdf_path, "wb") as f:
        f.write(file_bytes)

    doc = fitz.open(pdf_path)
    page_count = len(doc)

    # Render each page to PNG
    for i in range(page_count):
        page = doc[i]
        # 2x zoom for better OCR quality
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_path = os.path.join(session_dir, f"page_{i}.png")
        pix.save(img_path)

    doc.close()
    return session_id, page_count


def get_page_thumbnails(session_id: str, page_count: int) -> list[str]:
    """Return base64-encoded thumbnails (smaller size for preview)."""
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    pdf_path = os.path.join(session_dir, "source.pdf")
    doc = fitz.open(pdf_path)
    thumbnails = []

    for i in range(page_count):
        page = doc[i]
        # Smaller zoom for thumbnails
        pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
        img_bytes = pix.tobytes("png")
        b64 = base64.b64encode(img_bytes).decode("ascii")
        thumbnails.append(f"data:image/png;base64,{b64}")

    doc.close()
    return thumbnails


def get_page_image_bytes(session_id: str, page_index: int) -> bytes:
    """Return the full-resolution page image bytes."""
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    img_path = os.path.join(session_dir, f"page_{page_index}.png")
    with open(img_path, "rb") as f:
        return f.read()


def get_page_image_base64(session_id: str, page_index: int) -> str:
    """Return base64-encoded full page image."""
    img_bytes = get_page_image_bytes(session_id, page_index)
    b64 = base64.b64encode(img_bytes).decode("ascii")
    return f"data:image/png;base64,{b64}"


# ── Gemini AI extraction ───────────────────────────────────

EXTRACTION_PROMPT = """Bạn là chuyên gia tiếng Nhật. Hãy trích xuất TẤT CẢ các chữ Kanji từ hình ảnh trang sách này.

Với MỖI chữ Kanji, hãy trả về:
- "character": chữ Kanji (1 ký tự)
- "han_viet": âm Hán Việt (viết hoa chữ cái đầu, VD: "Nhĩ", "Dân", "Hợp")
- "onyomi": mảng các âm on (katakana), VD: ["ジ"]
- "kunyomi": mảng các âm kun (hiragana), VD: ["みみ"]
- "meaning_vi": nghĩa tiếng Việt ngắn gọn
- "formation": cách hình thành (Tượng hình / Hội ý / Hình thanh / Chỉ sự) kèm giải thích
- "uncertain": true nếu bạn KHÔNG CHẮC CHẮN về bất kỳ thông tin nào, false nếu chắc chắn
- "uncertain_note": ghi chú cụ thể nếu uncertain=true (cái gì không chắc), bỏ trống nếu chắc chắn
- "examples": mảng 4-5 từ vựng mẫu chứa kanji đó, mỗi từ có:
  - "word": từ vựng (kanji + kana)
  - "hiragana": cách đọc hiragana
  - "meaning": nghĩa tiếng Việt
  - "jlpt": cấp JLPT (N5/N4/N3/N2/N1)

QUAN TRỌNG:
- Trích xuất CHÍNH XÁC từ hình ảnh, không bịa thêm kanji không có trong ảnh
- Âm Hán Việt phải CHÍNH XÁC (例: 日=Nhật, 月=Nguyệt, 火=Hỏa, 水=Thủy)
- Nếu không chắc chắn về âm Hán Việt hoặc nghĩa, đánh dấu uncertain=true
- Từ vựng mẫu nên ở cấp JLPT phù hợp (không quá khó so với kanji)

Trả về JSON THUẦN (không markdown, không ```) theo format:
{
  "kanji_list": [
    {
      "character": "...",
      "han_viet": "...",
      "onyomi": ["..."],
      "kunyomi": ["..."],
      "meaning_vi": "...",
      "formation": "...",
      "uncertain": false,
      "uncertain_note": "",
      "examples": [
        {"word": "...", "hiragana": "...", "meaning": "...", "jlpt": "N3"}
      ]
    }
  ]
}"""


def extract_kanji_from_page(session_id: str, page_index: int) -> dict:
    """
    Send a page image to Gemini and extract kanji data.
    Returns parsed JSON dict with kanji_list.
    """
    image_bytes = get_page_image_bytes(session_id, page_index)

    raw = GeminiService.generate_with_image(
        prompt=EXTRACTION_PROMPT,
        image_bytes=image_bytes,
        mime_type="image/png",
        caller=f"kanji_pdf_extract_page_{page_index}",
    )

    # Strip markdown code fences if present
    text = raw.strip()
    if text.startswith("```"):
        # Remove first line (```json) and last line (```)
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response for page {page_index}: {e}")
        logger.debug(f"Raw response: {text[:500]}")
        return {"kanji_list": [], "error": f"AI trả về dữ liệu không hợp lệ: {str(e)}"}

    return data


def cleanup_session(session_id: str):
    """Remove temporary files for a session."""
    import shutil
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    if os.path.exists(session_dir):
        shutil.rmtree(session_dir, ignore_errors=True)
