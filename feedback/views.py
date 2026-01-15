from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.core.paginator import Paginator

from .models import FeedbackItem, FeedbackComment


def feedback_list(request):
    """
    Hiển thị danh sách đề xuất với bộ lọc và sắp xếp.
    - Filter theo status: all, in_progress, done
    - Sort: popular (số vote), latest (thời gian tạo)
    """
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    sort_by = request.GET.get('sort', 'popular')
    type_filter = request.GET.get('type', 'all')
    
    # Base queryset with vote count annotation
    queryset = FeedbackItem.objects.annotate(
        vote_count=Count('upvotes')
    ).select_related('user')
    
    # Apply status filter
    if status_filter == 'in_progress':
        queryset = queryset.filter(status__in=['planned', 'in_progress'])
    elif status_filter == 'done':
        queryset = queryset.filter(status='done')
    # 'all' shows everything
    
    # Apply type filter
    if type_filter == 'feature':
        queryset = queryset.filter(type='feature')
    elif type_filter == 'bug':
        queryset = queryset.filter(type='bug')
    
    # Apply sorting
    if sort_by == 'latest':
        queryset = queryset.order_by('-created_at')
    else:  # popular
        queryset = queryset.order_by('-vote_count', '-created_at')
    
    # Pagination
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get user's voted items for highlighting
    user_voted_ids = set()
    if request.user.is_authenticated:
        user_voted_ids = set(
            FeedbackItem.objects.filter(
                upvotes=request.user
            ).values_list('id', flat=True)
        )
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'type_filter': type_filter,
        'user_voted_ids': user_voted_ids,
    }
    return render(request, 'feedback/feedback_list.html', context)


def feedback_detail(request, pk):
    """
    Hiển thị chi tiết đề xuất với danh sách bình luận.
    """
    feedback = get_object_or_404(
        FeedbackItem.objects.annotate(
            vote_count=Count('upvotes')
        ).select_related('user'),
        pk=pk
    )
    
    comments = feedback.comments.select_related('user').order_by('created_at')
    
    # Check if user has voted
    user_has_voted = False
    if request.user.is_authenticated:
        user_has_voted = feedback.upvotes.filter(id=request.user.id).exists()
    
    context = {
        'feedback': feedback,
        'comments': comments,
        'user_has_voted': user_has_voted,
    }
    return render(request, 'feedback/feedback_detail.html', context)


@login_required
def feedback_create(request):
    """
    Form để tạo đề xuất mới.
    """
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        feedback_type = request.POST.get('type', 'feature')
        
        # Validation
        errors = []
        if not title:
            errors.append('Tiêu đề không được để trống.')
        if len(title) > 200:
            errors.append('Tiêu đề không được quá 200 ký tự.')
        if not description:
            errors.append('Mô tả không được để trống.')
        if feedback_type not in ['feature', 'bug']:
            feedback_type = 'feature'
        
        if errors:
            return render(request, 'feedback/feedback_form.html', {
                'errors': errors,
                'title': title,
                'description': description,
                'type': feedback_type,
            })
        
        # Create feedback
        feedback = FeedbackItem.objects.create(
            title=title,
            description=description,
            type=feedback_type,
            user=request.user,
        )
        
        return redirect('feedback:detail', pk=feedback.pk)
    
    return render(request, 'feedback/feedback_form.html')


@require_POST
def feedback_vote(request, pk):
    """
    Toggle vote cho đề xuất. Trả về JSON response.
    Nếu chưa vote → +1
    Nếu đã vote → -1 (bỏ vote)
    """
    feedback = get_object_or_404(FeedbackItem, pk=pk)
    
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Bạn cần đăng nhập để vote.',
            'login_required': True,
        }, status=401)
    
    # Toggle vote
    if feedback.upvotes.filter(id=request.user.id).exists():
        feedback.upvotes.remove(request.user)
        voted = False
    else:
        feedback.upvotes.add(request.user)
        voted = True
    
    return JsonResponse({
        'success': True,
        'voted': voted,
        'total_votes': feedback.total_votes(),
    })


@login_required
@require_POST
def feedback_add_comment(request, pk):
    """
    Thêm bình luận vào đề xuất.
    """
    feedback = get_object_or_404(FeedbackItem, pk=pk)
    content = request.POST.get('content', '').strip()
    
    if not content:
        return JsonResponse({
            'success': False,
            'error': 'Nội dung bình luận không được để trống.',
        }, status=400)
    
    # Check if admin (staff or superuser)
    is_admin_response = request.user.is_staff or request.user.is_superuser
    
    comment = FeedbackComment.objects.create(
        feedback=feedback,
        user=request.user,
        content=content,
        is_admin_response=is_admin_response,
    )
    
    # For AJAX requests, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'user_email': comment.user.email,
                'is_admin_response': comment.is_admin_response,
                'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M'),
            }
        })
    
    # For regular form submission, redirect back to detail
    return redirect('feedback:detail', pk=pk)
