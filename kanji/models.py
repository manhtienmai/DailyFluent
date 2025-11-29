from django.db import models


class Kanji(models.Model):
    """
    Một Hán tự đơn (受, 制, 旦...), dùng cho deck kanji riêng.
    """
    # Chữ kanji
    char = models.CharField("Hán tự", max_length=1, unique=True)

    # Âm Hán Việt, vd: 受 = Thụ, 制 = Chế
    sino_vi = models.CharField("Âm Hán Việt", max_length=50, blank=True)

    # Keyword (giống Accept, Control, Dawn...) – bạn dùng tiếng Anh/VN tuỳ ý
    keyword = models.CharField(
        "Keyword",
        max_length=100,
        blank=True,
        help_text="Ví dụ: Accept, Control, Dawn ..."
    )

    # Âm on / kun (nếu sau này cần)
    onyomi = models.CharField("Âm on", max_length=100, blank=True)
    kunyomi = models.CharField("Âm kun", max_length=100, blank=True)

    # Level học (như Level 25, 26...)
    level = models.PositiveIntegerField("Level", default=1)

    # JLPT (tuỳ chọn)
    jlpt_level = models.CharField("JLPT", max_length=4, blank=True)

    # Số nét
    strokes = models.PositiveIntegerField("Số nét", null=True, blank=True)

    # Ghi chú / mnemonic
    note = models.TextField("Ghi chú / câu chuyện nhớ", blank=True)

    class Meta:
        verbose_name = "Hán tự đơn"
        verbose_name_plural = "Hán tự đơn"
        ordering = ["level", "char"]

    def __str__(self):
        return f"{self.char} - {self.keyword or self.sino_vi or ''}"
