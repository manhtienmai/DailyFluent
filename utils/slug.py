# utils/slug.py
from django.utils.text import slugify
from pykakasi import kakasi

_kks = kakasi()
_kks.setMode("J", "a")  # Kanji -> ascii (romaji)
_kks.setMode("H", "a")  # Hiragana -> ascii
_kks.setMode("K", "a")  # Katakana -> ascii
_kks.setMode("r", "Hepburn")  # kiểu romaji
_converter = _kks.getConverter()

def to_romaji_slug(text: str) -> str:
    # 1) convert Japanese -> romaji
    romaji = _converter.do(text)
    # 2) Dùng slugify của Django để:
    #   - lowercase
    #   - space -> "-"
    #   - bỏ ký tự thừa
    return slugify(romaji)
