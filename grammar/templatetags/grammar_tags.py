from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()


@register.filter
def grammar_format(value):
    """
    Format grammar text với hỗ trợ:
    - **text** -> <strong>text</strong>
    - *text* -> <em>text</em>
    - Xuống dòng -> <br>
    - HTML tags được giữ nguyên
    """
    if not value:
        return ""
    
    text = str(value)
    
    # Xử lý markdown-style bold: **text**
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    
    # Xử lý markdown-style italic: *text* (không phải **)
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
    
    # Xử lý xuống dòng
    text = text.replace('\n', '<br>')
    
    return mark_safe(text)

