"""Todos API — CRUD for user todo items."""

from ninja import Router, Schema
from typing import List, Optional
from datetime import date

router = Router()


class TodoOut(Schema):
    id: int
    title: str
    description: str
    completed: bool
    priority: str
    period_type: str
    due_date: Optional[date] = None
    is_overdue: bool
    created_at: str


class TodoIn(Schema):
    title: str
    description: str = ""
    priority: str = "medium"
    period_type: str = "day"
    due_date: Optional[date] = None


@router.get("", response=List[TodoOut])
def list_todos(request):
    """List current user's todos."""
    from todos.models import TodoItem
    items = TodoItem.objects.filter(user=request.user)
    return [_todo_out(t) for t in items]


@router.post("", response=TodoOut)
def create_todo(request, payload: TodoIn):
    """Create a new todo."""
    from todos.models import TodoItem
    item = TodoItem.objects.create(user=request.user, **payload.dict())
    return _todo_out(item)


@router.put("/{todo_id}/toggle")
def toggle_todo(request, todo_id: int):
    """Toggle todo completion status."""
    from todos.models import TodoItem
    item = TodoItem.objects.get(id=todo_id, user=request.user)
    item.completed = not item.completed
    item.save()
    return {"success": True, "completed": item.completed}


@router.delete("/{todo_id}")
def delete_todo(request, todo_id: int):
    """Delete a todo."""
    from todos.models import TodoItem
    TodoItem.objects.filter(id=todo_id, user=request.user).delete()
    return {"success": True}


def _todo_out(t):
    return {
        "id": t.id,
        "title": t.title,
        "description": t.description,
        "completed": t.completed,
        "priority": t.priority,
        "period_type": t.period_type,
        "due_date": t.due_date,
        "is_overdue": t.is_overdue(),
        "created_at": t.created_at.isoformat(),
    }
