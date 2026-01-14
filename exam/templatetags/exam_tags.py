from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape

register = template.Library()


@register.filter
def number_to_letter(value):
    """
    Convert số (1, 2, 3, 4) thành chữ cái (A, B, C, D).
    """
    mapping = {
        "1": "A",
        "2": "B",
        "3": "C",
        "4": "D",
        1: "A",
        2: "B",
        3: "C",
        4: "D",
    }
    return mapping.get(value, str(value))


@register.filter
def render_stem_segments(data):
    """
    Render stem_segments to HTML with blank markers.
    
    Args:
        data: Question data dict containing 'stem_segments'
              [{"type": "text", "text": "..."}, {"type": "blank", "id": "b101"}, ...]
    
    Returns:
        SafeString: HTML with blank markers styled appropriately
    """
    if not data:
        return ""
    
    segments = data.get("stem_segments", [])
    if not segments:
        return ""
    
    result = []
    for segment in segments:
        seg_type = segment.get("type", "text")
        if seg_type == "blank":
            blank_id = segment.get("id", "")
            result.append(f'<span class="df-toeic-blank-marker" data-blank-id="{escape(blank_id)}">_____</span>')
        else:
            text = segment.get("text", "")
            result.append(escape(text))
    
    return mark_safe("".join(result))


@register.filter
def render_passage_segments(data):
    """
    Render content_segments (for P6 passages) to HTML with numbered blank markers.
    
    Args:
        data: Passage data dict containing 'content_segments'
              [{"type": "text", "text": "..."}, {"type": "blank", "id": "131"}, ...]
    
    Returns:
        SafeString: HTML with numbered blank markers
    """
    if not data:
        return ""
    
    segments = data.get("content_segments", [])
    if not segments:
        return ""
    
    result = []
    for segment in segments:
        seg_type = segment.get("type", "text")
        if seg_type == "blank":
            blank_id = segment.get("id", "")
            result.append(f'<span class="df-toeic-passage-blank" data-blank-id="{escape(blank_id)}">[{escape(blank_id)}]</span>')
        else:
            text = segment.get("text", "")
            # Preserve line breaks
            escaped_text = escape(text).replace("\n", "<br>")
            result.append(escaped_text)
    
    return mark_safe("".join(result))


@register.filter
def has_stem_segments(data):
    """Check if question data has stem_segments."""
    if not data:
        return False
    return bool(data.get("stem_segments"))


@register.filter
def has_content_segments(data):
    """Check if passage data has content_segments."""
    if not data:
        return False
    return bool(data.get("content_segments"))


@register.filter
def has_content_json(content_json):
    """
    Check if passage.content_json has something renderable.
    Accepts keys: html, content (plain text), or content_segments (same schema as render_passage_segments).
    Fallback: coi bất kỳ JSON không rỗng (dict/list/string/array) là hợp lệ để ưu tiên render JSON thay vì ảnh.
    """
    if content_json is None:
        return False
    if isinstance(content_json, str):
        return bool(content_json.strip())
    if isinstance(content_json, dict):
        if (
            content_json.get("html")
            or content_json.get("content")
            or content_json.get("content_segments")
            or content_json.get("documents")
        ):
            return True
        return bool(content_json)
    try:
        return len(content_json) > 0
    except Exception:
        return bool(content_json)


@register.filter
def has_documents(content_json):
    """Check if content_json contains 'documents' array (rich structured passages)."""
    if not isinstance(content_json, dict):
        return False
    docs = content_json.get("documents")
    return bool(docs)


@register.filter
def render_content_json(content_json):
    """
    Render passage.content_json with priority:
    1) html (trust content from admin)
    2) content_segments (reuse render_passage_segments logic)
    3) content (plain text with <br>)
    4) fallback: pretty-print JSON (escaped) nếu schema lạ
    """
    if not content_json:
        return ""

    html = content_json.get("html")
    if html:
        return mark_safe(html)

    segments = content_json.get("content_segments")
    if segments:
        # Reuse logic from render_passage_segments but without needing data wrapper
        data = {"content_segments": segments}
        return render_passage_segments(data)

    content = content_json.get("content")
    if content:
        return mark_safe(escape(content).replace("\n", "<br>"))

    # Fallback: render toàn bộ JSON để không bị coi là trống
    try:
        import json as _json
        return mark_safe(f"<pre>{escape(_json.dumps(content_json, ensure_ascii=False, indent=2))}</pre>")
    except Exception:
        return escape(str(content_json))


# ===== Rich document renderer (invoice/email/etc.) =====
def _render_inlines(inlines):
    parts = []
    for item in inlines or []:
        if "br" in item and item.get("br"):
            parts.append("<br>")
            continue
        if "blank" in item:
            blank_id = item.get("blank")
            parts.append(f'<span class="df-doc-blank" data-blank-id="{escape(str(blank_id))}">[{escape(str(blank_id))}]</span>')
            continue
        text = escape(item.get("text", ""))
        marks = item.get("marks") or []
        if "bold" in marks:
            text = f"<strong>{text}</strong>"
        if "italic" in marks:
            text = f"<em>{text}</em>"
        if "underline" in marks:
            text = f"<u>{text}</u>"
        parts.append(text)
    return "".join(parts)


_CHAT_COLOR_CLASSES = [
    "df-chat-color-0",
    "df-chat-color-1",
    "df-chat-color-2",
    "df-chat-color-3",
    "df-chat-color-4",
    "df-chat-color-5",
]


def _chat_color_class(sender_name: str) -> str:
    if not sender_name:
        return _CHAT_COLOR_CLASSES[0]
    h = sum(ord(ch) for ch in sender_name)
    return _CHAT_COLOR_CLASSES[h % len(_CHAT_COLOR_CLASSES)]


def _render_block(block):
    btype = block.get("type")
    if btype == "chat_message":
        sender = escape(block.get("from", ""))
        time = escape(block.get("time", ""))
        body = _render_inlines(block.get("inlines"))
        color_class = _chat_color_class(sender)
        return (
            f"<div class='df-chat-msg {color_class}'>"
            f"<div class='df-chat-meta'><span class='df-chat-from'>{sender}</span>"
            f"<span class='df-chat-time'>{time}</span></div>"
            f"<div class='df-chat-bubble'>{body}</div>"
            "</div>"
        )
    if btype == "list":
        ordered = bool(block.get("ordered"))
        items = block.get("items") or []
        tag = "ol" if ordered else "ul"
        lis = []
        for item in items:
            # each item is an array of inline parts
            lis.append(f"<li>{_render_inlines(item)}</li>")
        return f"<{tag} class='df-doc-list'>{''.join(lis)}</{tag}>"
    if btype == "heading":
        level = block.get("level", 3)
        level = 1 if level < 1 else 6 if level > 6 else level
        return f"<h{level}>{_render_inlines(block.get('inlines'))}</h{level}>"
    if btype == "paragraph":
        align = block.get("align")
        align_style = f' style="text-align:{escape(align)};"' if align else ""
        return f"<p{align_style}>{_render_inlines(block.get('inlines'))}</p>"
    if btype == "divider":
        return "<hr>"
    if btype == "key_value":
        rows = []
        for pair in block.get("pairs") or []:
            key_html = _render_inlines(pair.get("key"))
            val_html = _render_inlines(pair.get("value"))
            rows.append(f"<div class='df-doc-kv-row'><span class='df-doc-kv-key'>{key_html}</span><span class='df-doc-kv-sep'>:</span><span class='df-doc-kv-val'>{val_html}</span></div>")
        return f"<div class='df-doc-keyvalue'>{''.join(rows)}</div>"
    if btype == "table":
        headers = block.get("headers") or []
        rows = block.get("rows") or []
        ths = "".join([
            f"<th style='text-align:{escape(h.get('align','left'))};'>{_render_inlines(h.get('content'))}</th>"
            for h in headers
        ])
        trs = []
        for row in rows:
            tds = []
            for cell in row:
                colspan = cell.get("colspan")
                align = cell.get("align", "left")
                colspan_attr = f" colspan='{int(colspan)}'" if colspan else ""
                tds.append(f"<td{colspan_attr} style='text-align:{escape(align)};'>{_render_inlines(cell.get('content'))}</td>")
            trs.append(f"<tr>{''.join(tds)}</tr>")
        return f"<table class='df-doc-table'><thead><tr>{ths}</tr></thead><tbody>{''.join(trs)}</tbody></table>"
    return ""


def _render_document(doc):
    doc_type = doc.get("doc_type", "").lower()
    meta_label = ""
    meta = doc.get("meta") or {}
    # if meta.get("label"):
    #     meta_label = f"<div class='df-doc-label'>{escape(meta.get('label'))}</div>"
    body_blocks = doc.get("body") or []

    # Special handling for email: split header (To/From/Date/Subject) from body
    rendered_blocks = ""
    if doc_type == "email":
        header_html = ""
        remaining_blocks = body_blocks
        if body_blocks and body_blocks[0].get("type") == "key_value":
            kv = body_blocks[0].get("pairs") or []
            header_rows = []
            label_map = {"to": "To", "from": "From", "date": "Date", "subject": "Subject"}
            # Render known keys in order if present
            for key_name in ["to", "from", "date", "subject"]:
                for pair in kv:
                    key_parts = pair.get("key") or []
                    key_text = "".join([p.get("text", "").lower() for p in key_parts])
                    if key_name in key_text:
                        val_html = _render_inlines(pair.get("value"))
                        header_rows.append(
                            f"<div class='df-email-header-row'><span class='df-email-header-key'>{label_map[key_name]}:</span> <span class='df-email-header-val'>{val_html}</span></div>"
                        )
                        break
            # Fallback: if nothing matched, render the whole key_value block
            if not header_rows:
                header_rows.append(_render_block(body_blocks[0]))
            header_html = "<div class='df-email-header'>" + "".join(header_rows) + "</div>"
            remaining_blocks = body_blocks[1:]
        # Render remaining blocks as body
        rendered_blocks = header_html + "".join(_render_block(b) for b in remaining_blocks)
    elif doc_type == "article":
        # Render a faux address bar if we can detect a URL in the first paragraph
        url = ""
        skip_first = False
        if body_blocks and body_blocks[0].get("type") == "paragraph":
            for inline in body_blocks[0].get("inlines") or []:
                t = inline.get("text", "")
                if isinstance(t, str) and t.startswith(("http://", "https://")):
                    url = t
                    # Nếu block đầu chỉ chứa URL, bỏ khỏi render để tránh trùng lặp
                    if len(body_blocks[0].get("inlines") or []) == 1:
                        skip_first = True
                    break
        webbar = ""
        if url:
            safe_url = escape(url)
            webbar = (
                "<div class='df-webbar'>"
                f"<div class='df-webbar-link'>{safe_url}</div>"
                "</div>"
            )
        remaining_blocks = body_blocks[1:] if skip_first else body_blocks
        rendered_blocks = webbar + "".join(_render_block(b) for b in remaining_blocks)
    elif doc_type == "chat":
        # Render chat messages as stacked bubbles
        rendered_blocks = "<div class='df-doc-chat'>"
        rendered_blocks += "".join(_render_block(b) for b in body_blocks)
        rendered_blocks += "</div>"
    else:
        rendered_blocks = "".join(_render_block(b) for b in body_blocks)

    doc_class = f"df-doc df-doc-{escape(doc_type)}"
    # Black border block, no scroll/overflow constraints
    return (
        f"<div class='{doc_class}' "
        f"style='border:1px solid #0f172a;border-radius:6px;padding:12px;margin-bottom:12px;background:#fff;'>"
        f"{meta_label}{rendered_blocks}"
        f"</div>"
    )


@register.filter
def render_documents(content_json):
    """
    Render structured documents (invoice/email/etc.) from content_json.documents
    """
    if not isinstance(content_json, dict):
        return ""
    docs = content_json.get("documents") or []
    if not docs:
        return ""

    group_type = content_json.get("group_type")
    instruction = content_json.get("instruction")

    header_parts = []
    if instruction:
        header_parts.append(f"<div class='df-doc-instruction'>{escape(instruction)}</div>")

    rendered_docs = "".join(_render_document(doc) for doc in docs)
    # Wrap all docs to keep spacing; no scroll applied
    return mark_safe(
        "".join(header_parts)
        + f"<div class='df-docs-block' style='display:flex;flex-direction:column;gap:12px;'>{rendered_docs}</div>"
    )