from django.db import models


class Book(models.Model):
    """Ebook in the library."""

    title = models.CharField(max_length=300, verbose_name="Tên sách")
    author = models.CharField(max_length=200, blank=True, default="", verbose_name="Tác giả")
    cover_image = models.ImageField(
        upload_to="ebook/covers/",
        blank=True,
        null=True,
        verbose_name="Ảnh bìa",
    )
    pdf_file = models.FileField(
        upload_to="ebook/pdfs/",
        verbose_name="File PDF",
    )
    description = models.TextField(blank=True, default="", verbose_name="Mô tả")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Ebook"
        verbose_name_plural = "Ebooks"

    def __str__(self):
        return self.title
