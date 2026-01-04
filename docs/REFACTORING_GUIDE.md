# Refactoring Guide - Component Structure

## Tổng quan

Project đã được refactor để tách các features thành modules/components riêng biệt, giúp code dễ đọc và phát triển hơn.

## Cấu trúc mới

### 1. App `common`

App chứa các components và utilities dùng chung:
- **Context Processors**: Cung cấp data cho templates (navigation items, etc.)
- **Template Components**: Các reusable components

**Location:** `common/`

### 2. Template Components

Các template components được tổ chức trong `templates/components/`:

```
templates/components/
├── navigation/          # Navigation components
│   ├── header.html
│   ├── logo.html
│   ├── desktop_menu.html
│   ├── mobile_menu.html
│   ├── mobile_menu_button.html
│   ├── account_menu.html
│   └── auth_buttons.html
├── footer.html
├── audio_player.html
├── loader.html
├── pagination.html
└── ...
```

### 3. JavaScript Modules

JavaScript được tách thành các file riêng:
- `static/js/navigation.js` - Navigation logic
- `static/js/audio-player.js` - Audio player logic

## Cách sử dụng

### Sử dụng Navigation Components

**Trong base.html:**
```django
{% include "components/navigation/header.html" %}
```

**Hoặc sử dụng từng component riêng:**
```django
{% include "components/navigation/logo.html" %}
{% include "components/navigation/desktop_menu.html" %}
```

### Thêm menu item mới

1. Sửa `common/context_processors.py`:
```python
nav_items = [
    # ... existing items
    {
        'name': 'Menu Mới',
        'url_name': 'app:view_name',
        'icon': None,
    },
]
```

Menu sẽ tự động xuất hiện trong cả desktop và mobile menu.

### Tạo component mới

1. Tạo file trong `templates/components/`:
```django
{# templates/components/my_component.html #}
{% comment %}
My Component
Usage: {% include "components/my_component.html" with param="value" %}
{% endcomment %}

<div class="my-component">
  {{ param }}
</div>
```

2. Sử dụng:
```django
{% include "components/my_component.html" with param="Hello" %}
```

## Lợi ích

1. **Dễ maintain**: Mỗi component ở một file riêng, dễ tìm và sửa
2. **Reusable**: Components có thể dùng lại ở nhiều nơi
3. **Separation of Concerns**: Logic tách biệt rõ ràng
4. **Scalable**: Dễ thêm features mới mà không ảnh hưởng code cũ
5. **Testable**: Có thể test từng component riêng

## Best Practices

1. **Component naming**: Đặt tên rõ ràng, mô tả chức năng
2. **Documentation**: Thêm comment ở đầu mỗi component
3. **Parameters**: Sử dụng `with` để truyền parameters
4. **Organization**: Nhóm các components liên quan vào thư mục con
5. **Context processors**: Dùng cho data dùng chung nhiều nơi

## Migration từ code cũ

Nếu có code cũ cần refactor:

1. **Tách HTML**: Di chuyển HTML vào component file
2. **Tách JavaScript**: Di chuyển JS vào file riêng
3. **Tách data**: Di chuyển data logic vào context processor nếu cần
4. **Update templates**: Thay thế code cũ bằng `{% include %}`

## Ví dụ: Refactor một feature

**Trước:**
```django
{# base.html - 200 dòng code navigation #}
<header>
  <!-- 200 dòng HTML -->
</header>
<script>
  // 50 dòng JavaScript
</script>
```

**Sau:**
```django
{# base.html - 1 dòng #}
{% include "components/navigation/header.html" %}

{# static/js/navigation.js - JavaScript riêng #}
// 50 dòng JavaScript
```

## Tương lai

Có thể mở rộng thêm:
- Component library documentation
- Storybook cho components
- Unit tests cho components
- TypeScript cho JavaScript
- Component versioning

