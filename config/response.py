"""
Standardized response helpers for DailyFluent API.

Provides consistent JSON structure across all endpoints,
compatible with both web (Next.js) and mobile clients.

Usage:
    from config.response import ok, fail, paginated

    @router.get("/items")
    def list_items(request, page: int = 1):
        qs = Item.objects.all()
        return paginated(qs, page=page, page_size=20, serializer=lambda i: {"id": i.id, "name": i.name})

    @router.post("/items")
    def create_item(request):
        return ok(data={"id": 1}, message="Created")

    @router.post("/items")
    def create_fail(request):
        return fail(message="Validation error", status=400)
"""

from math import ceil


def ok(data=None, message="", status=200):
    """Success response."""
    body = {"success": True}
    if message:
        body["message"] = message
    if data is not None:
        body["data"] = data
    return status, body


def fail(message="Error", status=400, errors=None):
    """Error response."""
    body = {"success": False, "message": message}
    if errors:
        body["errors"] = errors
    return status, body


def paginated(queryset, page=1, page_size=20, serializer=None):
    """
    Paginate a queryset and return standardized response.

    Args:
        queryset: Django QuerySet
        page: 1-indexed page number
        page_size: items per page (max 100)
        serializer: callable that converts model instance to dict
    """
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    total = queryset.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size

    items = queryset[offset:offset + page_size]
    data = [serializer(item) for item in items] if serializer else list(items)

    return 200, {
        "success": True,
        "data": data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }
