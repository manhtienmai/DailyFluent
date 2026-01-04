"""
Context processors for common app
Provides navigation items and other shared context
"""


def navigation_items(request):
    """
    Context processor that provides navigation menu items
    Can be extended to support dynamic menus, permissions, etc.
    """
    nav_items = [
        {
            'name': 'Trang chủ',
            'url_name': 'home',
            'icon': None,
        },
        {
            'name': 'Đề thi',
            'url_name': 'exam:exam_list',
            'icon': None,
        },
        {
            'name': 'TOEIC',
            'url_name': 'exam:toeic_list',
            'icon': None,
        },
        {
            'name': 'Courses',
            'url_name': 'core:course_list',
            'icon': None,
        },
        {
            'name': 'Từ vựng',
            'url_name': 'vocab:list',
            'icon': None,
        },
        {
            'name': 'Từ vựng EN',
            'url_name': 'vocab:english_list',
            'icon': None,
        },
        {
            'name': 'Grammar',
            'url_name': 'grammar:list',
            'icon': None,
        },
        {
            'name': 'Tiến độ',
            'url_name': 'vocab:progress',
            'icon': None,
        },
    ]
    
    return {
        'navigation_items': nav_items,
    }


def footer_data(request):
    """
    Context processor that provides footer data
    Includes footer links, social media, etc.
    """
    footer_courses = [
        {'name': 'Khóa học N5', 'url_name': 'core:course_list'},
        {'name': 'Khóa học N4', 'url_name': 'core:course_list'},
        {'name': 'Khóa học N3', 'url_name': 'core:course_list'},
        {'name': 'Khóa học N2', 'url_name': 'core:course_list'},
        {'name': 'Khóa học N1', 'url_name': 'core:course_list'},
    ]
    
    footer_company = [
        {'name': 'Về chúng tôi', 'url': '#'},
        {'name': 'Blog', 'url': '#'},
        {'name': 'Tuyển dụng', 'url': '#'},
        {'name': 'Đối tác', 'url': '#'},
        {'name': 'Báo chí', 'url': '#'},
    ]
    
    footer_support = [
        {'name': 'Trung tâm trợ giúp', 'url': '#'},
        {'name': 'Liên hệ', 'url': '#'},
        {'name': 'Cộng đồng', 'url': '#'},
        {'name': 'Câu hỏi thường gặp', 'url': '#'},
    ]
    
    social_media = [
        {
            'name': 'Twitter',
            'icon': 'twitter',
            'url': '#',
        },
        {
            'name': 'Facebook',
            'icon': 'facebook',
            'url': '#',
        },
        {
            'name': 'Instagram',
            'icon': 'instagram',
            'url': '#',
        },
        {
            'name': 'YouTube',
            'icon': 'youtube',
            'url': '#',
        },
    ]
    
    legal_links = [
        {'name': 'Privacy', 'url': '#'},
        {'name': 'Terms', 'url': '#'},
        {'name': 'Cookies', 'url': '#'},
    ]
    
    return {
        'footer_courses': footer_courses,
        'footer_company': footer_company,
        'footer_support': footer_support,
        'social_media': social_media,
        'legal_links': legal_links,
    }


def landing_page_data(request):
    """
    Context processor that provides landing page data
    Includes testimonials and features
    """
    student_testimonials = [
        {
            'text': 'DailyFluent giúp tôi chuyển từ marketing sang học tiếng Nhật. Các khóa học được cấu trúc tốt và cộng đồng rất hỗ trợ!',
            'name': 'Nguyễn Thị Lan',
            'title': 'Lập trình viên',
            'initial': 'L',
            'avatar_color': 'bg-pink-500',
        },
        {
            'text': 'Khóa học N5-N4 chính xác là những gì tôi cần. Tôi đã đạt được mục tiêu chỉ sau 3 tháng hoàn thành!',
            'name': 'Trần Văn Đức',
            'title': 'Thiết kế UX',
            'initial': 'Đ',
            'avatar_color': 'bg-blue-500',
        },
        {
            'text': 'Đầu tư tốt nhất tôi đã làm cho sự nghiệp. Khóa học từ vựng đã cho tôi kỹ năng thực tế tôi sử dụng mỗi ngày.',
            'name': 'Lê Thị Mai',
            'title': 'Phân tích dữ liệu',
            'initial': 'M',
            'avatar_color': 'bg-purple-500',
        },
    ]
    
    why_choose_us_features = [
        {
            'icon': 'clock',
            'title': 'Học theo tốc độ của bạn',
            'description': 'Truy cập khóa học mọi lúc, mọi nơi. Tạm dừng, tua lại và xem lại bài học khi cần.',
            'icon_bg': 'bg-pink-100',
        },
        {
            'icon': 'graduation',
            'title': 'Giảng viên chuyên nghiệp',
            'description': 'Học từ các chuyên gia trong ngành với kinh nghiệm thực tế.',
            'icon_bg': 'bg-blue-100',
        },
        {
            'icon': 'certificate',
            'title': 'Chứng chỉ',
            'description': 'Nhận chứng chỉ được công nhận để thể hiện kỹ năng mới của bạn.',
            'icon_bg': 'bg-cyan-100',
        },
        {
            'icon': 'community',
            'title': 'Hỗ trợ cộng đồng',
            'description': 'Tham gia cộng đồng người học. Đặt câu hỏi và chia sẻ kiến thức.',
            'icon_bg': 'bg-blue-100',
        },
    ]
    
    return {
        'student_testimonials': student_testimonials,
        'why_choose_us_features': why_choose_us_features,
    }

