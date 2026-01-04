from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from .models import TodoItem
import json


@login_required
def todo_list(request):
    """Danh sách todo items của user"""
    todos = TodoItem.objects.filter(user=request.user).order_by('-created_at')
    
    # Phân loại todos
    active_todos = todos.filter(completed=False)
    completed_todos = todos.filter(completed=True)
    
    context = {
        'active_todos': active_todos,
        'completed_todos': completed_todos,
        'total_count': todos.count(),
        'active_count': active_todos.count(),
        'completed_count': completed_todos.count(),
    }
    
    return render(request, 'todos/todo_list.html', context)


@login_required
@require_http_methods(["POST"])
@csrf_protect
def todo_create(request):
    """Tạo todo item mới"""
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        
        title = data.get('title', '').strip()
        if not title:
            return JsonResponse({'success': False, 'error': 'Tiêu đề không được để trống'}, status=400)
        
        todo = TodoItem.objects.create(
            user=request.user,
            title=title,
            description=data.get('description', '').strip(),
            priority=data.get('priority', 'medium'),
            due_date=data.get('due_date') or None,
            period_type=data.get('period_type', 'day'),
        )
        
        return JsonResponse({
            'success': True,
            'todo': {
                'id': todo.id,
                'title': todo.title,
                'description': todo.description,
                'completed': todo.completed,
                'priority': todo.priority,
                'period_type': todo.period_type,
                'due_date': str(todo.due_date) if todo.due_date else None,
                'created_at': todo.created_at.isoformat(),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST", "PUT", "PATCH"])
@csrf_protect
def todo_update(request, todo_id):
    """Cập nhật todo item"""
    todo = get_object_or_404(TodoItem, id=todo_id, user=request.user)
    
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        
        if 'title' in data:
            todo.title = data['title'].strip()
        if 'description' in data:
            todo.description = data['description'].strip()
        if 'completed' in data:
            todo.completed = data['completed'] in (True, 'true', 'True', '1', 1)
        if 'priority' in data:
            todo.priority = data['priority']
        if 'due_date' in data:
            todo.due_date = data['due_date'] if data['due_date'] else None
        if 'period_type' in data:
            todo.period_type = data['period_type']
        
        todo.save()
        
        return JsonResponse({
            'success': True,
            'todo': {
                'id': todo.id,
                'title': todo.title,
                'description': todo.description,
                'completed': todo.completed,
                'priority': todo.priority,
                'period_type': todo.period_type,
                'due_date': str(todo.due_date) if todo.due_date else None,
                'updated_at': todo.updated_at.isoformat(),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST", "DELETE"])
@csrf_protect
def todo_delete(request, todo_id):
    """Xóa todo item"""
    todo = get_object_or_404(TodoItem, id=todo_id, user=request.user)
    todo.delete()
    return JsonResponse({'success': True})


@login_required
@require_http_methods(["POST"])
@csrf_protect
def todo_toggle(request, todo_id):
    """Toggle trạng thái completed của todo"""
    todo = get_object_or_404(TodoItem, id=todo_id, user=request.user)
    todo.completed = not todo.completed
    todo.save()
    
    return JsonResponse({
        'success': True,
        'completed': todo.completed,
        'todo': {
            'id': todo.id,
            'title': todo.title,
            'completed': todo.completed,
        }
    })


@login_required
def todo_list_api(request):
    """API endpoint để lấy danh sách todos theo period"""
    from datetime import timedelta
    
    period = request.GET.get('period', 'day')
    today = timezone.localdate()
    todos_query = TodoItem.objects.filter(user=request.user, period_type=period)
    
    # Filter by time period
    if period == 'day':
        todos_query = todos_query.filter(created_at__date=today)
    elif period == 'week':
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        todos_query = todos_query.filter(created_at__date__gte=week_start, created_at__date__lte=week_end)
    elif period == 'month':
        month_start = today.replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)
        todos_query = todos_query.filter(created_at__date__gte=month_start, created_at__date__lte=month_end)
    elif period == 'year':
        year_start = today.replace(month=1, day=1)
        year_end = today.replace(month=12, day=31)
        todos_query = todos_query.filter(created_at__date__gte=year_start, created_at__date__lte=year_end)
    
    todos = todos_query.order_by("completed", "-created_at")[:20]
    
    todos_data = []
    for todo in todos:
        todos_data.append({
            'id': todo.id,
            'title': todo.title,
            'description': todo.description,
            'completed': todo.completed,
            'priority': todo.priority,
            'period_type': todo.period_type,
            'due_date': str(todo.due_date) if todo.due_date else None,
            'created_at': todo.created_at.isoformat(),
            'updated_at': todo.updated_at.isoformat(),
        })
    
    return JsonResponse({
        'success': True,
        'todos': todos_data,
        'period': period
    })
