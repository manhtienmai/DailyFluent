"""
Ebook API — CRUD endpoints for the Book library.

Supports multipart/form-data upload for cover image + PDF file.
"""

from ninja import Router, Schema, File, Form
from ninja.files import UploadedFile
from typing import List, Optional
from datetime import datetime

router = Router()


# ── Schemas ────────────────────────────────────────────────


class BookOut(Schema):
    id: int
    title: str
    author: str
    cover_image: Optional[str] = None
    pdf_file: str
    description: str
    created_at: datetime


# ── Helpers ────────────────────────────────────────────────


def _book_out(book) -> dict:
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "cover_image": book.cover_image.url if book.cover_image else None,
        "pdf_file": book.pdf_file.url if book.pdf_file else "",
        "description": book.description,
        "created_at": book.created_at,
    }


# ── Endpoints ──────────────────────────────────────────────


@router.get("", response=List[BookOut])
def list_books(request):
    """List all books in the library."""
    from ebook.models import Book

    return [_book_out(b) for b in Book.objects.all()]


@router.get("/{book_id}", response=BookOut)
def get_book(request, book_id: int):
    """Get a single book by ID."""
    from ebook.models import Book

    book = Book.objects.get(id=book_id)
    return _book_out(book)


@router.post("", response=BookOut)
def create_book(
    request,
    title: str = Form(...),
    author: str = Form(""),
    description: str = Form(""),
    cover_image: UploadedFile = File(None),
    pdf_file: UploadedFile = File(...),
):
    """
    Create a new book.

    Accepts multipart/form-data with:
    - title (required)
    - author (optional)
    - description (optional)
    - cover_image (optional image file)
    - pdf_file (required PDF file)
    """
    from ebook.models import Book

    book = Book(
        title=title,
        author=author,
        description=description,
    )
    if cover_image:
        book.cover_image.save(cover_image.name, cover_image)
    book.pdf_file.save(pdf_file.name, pdf_file)
    book.save()
    return _book_out(book)


@router.delete("/{book_id}")
def delete_book(request, book_id: int):
    """Delete a book by ID."""
    from ebook.models import Book

    book = Book.objects.get(id=book_id)
    # Clean up files
    if book.cover_image:
        book.cover_image.delete(save=False)
    if book.pdf_file:
        book.pdf_file.delete(save=False)
    book.delete()
    return {"success": True}
