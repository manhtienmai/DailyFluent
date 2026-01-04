from django import template
from django.conf import settings
import re

register = template.Library()


def _build_audio_path(audio_pack_uuid, audio_type, example_order=None):
    """
    Helper function để build audio path.
    
    Args:
        audio_pack_uuid: UUID của audio pack
        audio_type: "word" hoặc "example"
        example_order: Số thứ tự của example (1-based) nếu audio_type = "example"
    
    Returns:
        Base path (không có _us/_uk suffix và không có base URL)
    
    Format:
        - Word: dailyfluent/<uuid>/word
        - Example: dailyfluent/<uuid>/ex1, ex2, etc.
    """
    if not audio_pack_uuid:
        return ""
    
    # Validate audio_pack_uuid format (should be UUID)
    try:
        # Basic UUID format check (8-4-4-4-12 hex digits)
        uuid_str = str(audio_pack_uuid).strip()
        if len(uuid_str) != 36 or uuid_str.count('-') != 4:
            return ""
    except (AttributeError, TypeError):
        return ""
    
    if audio_type == "word":
        filename = "word"
    elif audio_type == "example":
        # Ensure example_order is a valid integer
        if example_order is None:
            return ""
        try:
            # Convert to int - handle both string and int
            if isinstance(example_order, str):
                order = int(example_order.strip())
            else:
                order = int(example_order)
            if order < 1:
                return ""
            filename = f"ex{order}"
        except (ValueError, TypeError) as e:
            # Debug: log error but don't break template
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Invalid example_order: {example_order}, error: {e}")
            return ""
    else:
        return ""
    
    # Build base path: audio/dailyfluent/<uuid>/<filename>
    # Format matches: https://dailyfluentaudio.blob.core.windows.net/audio/dailyfluent/<uuid>/ex1_us.mp3
    return f"dailyfluent/{uuid_str}/{filename}"


@register.simple_tag
def vocab_audio_url_us(audio_pack_uuid, audio_type, example_order=None):
    """
    Get US audio URL.
    
    Returns full URL in format:
    https://{account}.blob.core.windows.net/audio/dailyfluent/<uuid>/word_us.mp3
    or
    https://{account}.blob.core.windows.net/audio/dailyfluent/<uuid>/ex1_us.mp3
    """
    base_path = _build_audio_path(audio_pack_uuid, audio_type, example_order)
    if not base_path:
        return ""
    
    # Use AUDIO_BASE_URL from settings (configured separately for security)
    audio_base_url = getattr(settings, 'AUDIO_BASE_URL', '')
    if not audio_base_url:
        # Fallback: construct from MEDIA_URL if AUDIO_BASE_URL not set
        # This should not happen in production, but provides safety
        return ""
    
    return f"{audio_base_url}{base_path}_us.mp3"


@register.simple_tag
def vocab_audio_url_uk(audio_pack_uuid, audio_type, example_order=None):
    """
    Get UK audio URL.
    
    Returns full URL in format:
    https://{account}.blob.core.windows.net/audio/dailyfluent/<uuid>/word_uk.mp3
    or
    https://{account}.blob.core.windows.net/audio/dailyfluent/<uuid>/ex1_uk.mp3
    """
    base_path = _build_audio_path(audio_pack_uuid, audio_type, example_order)
    if not base_path:
        return ""
    
    # Use AUDIO_BASE_URL from settings (configured separately for security)
    audio_base_url = getattr(settings, 'AUDIO_BASE_URL', '')
    if not audio_base_url:
        # Fallback: construct from MEDIA_URL if AUDIO_BASE_URL not set
        # This should not happen in production, but provides safety
        return ""
    
    return f"{audio_base_url}{base_path}_uk.mp3"


@register.filter
def format_marked_sentence(value):
    """
    Xử lý sentence_marked: xóa marker và in đậm từ được đánh dấu.
    
    Format hỗ trợ:
    - ⟦word⟧ (double square brackets Unicode) - ưu tiên
    - [word] (single square brackets) - fallback
    
    Returns HTML với từ được đánh dấu được wrap trong <strong> tag.
    """
    if not value:
        return ""
    
    text = str(value)
    
    # Xử lý ⟦word⟧ (double square brackets Unicode) - ưu tiên
    # Pattern: ⟦...⟧
    text = re.sub(r'⟦([^⟧]+)⟧', r'<strong class="df-marked-word">\1</strong>', text)
    
    # Xử lý [word] (single square brackets) - chỉ nếu chưa có marker Unicode
    # Tránh match pattern như ([context]) ở cuối câu
    # Chỉ match [word] nếu không phải là pattern (text) hoặc [text] ở cuối
    # Match [word] ở giữa câu hoặc đầu câu
    text = re.sub(r'(?<!\()\[([^\]]+)\](?!\s*[\)])', r'<strong class="df-marked-word">\1</strong>', text)
    
    return text


@register.filter
def is_not_context(value):
    """
    Kiểm tra xem value có phải là context format [context] không.
    
    Returns True nếu value không phải là [context] format (bắt đầu bằng [ và kết thúc bằng ]).
    Returns False nếu value là [context] format hoặc empty.
    """
    if not value:
        return False
    
    text = str(value).strip()
    
    # Nếu bắt đầu bằng [ và kết thúc bằng ], đó là context format
    if text.startswith('[') and text.endswith(']'):
        return False
    
    return True
