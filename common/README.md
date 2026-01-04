# Common App

App chứa các components và utilities dùng chung cho toàn bộ project.

## Cấu trúc

```
common/
├── context_processors.py  # Context processors (navigation items, etc.)
├── apps.py                # App configuration
└── README.md              # This file
```

## Context Processors

### `navigation_items`

Cung cấp danh sách các menu items cho navigation. Được sử dụng trong templates thông qua context processor.

**Sử dụng:**
```python
# Trong settings.py đã được cấu hình
'common.context_processors.navigation_items'
```

**Trong template:**
```django
{% for item in navigation_items %}
  <a href="{% url item.url_name %}">{{ item.name }}</a>
{% endfor %}
```

**Thêm menu item mới:**
Chỉnh sửa `common/context_processors.py` và thêm vào list `nav_items`.

## Template Components

Các template components được đặt trong `templates/components/`:

### Navigation Components

- `components/navigation/header.html` - Header chính (bao gồm tất cả)
- `components/navigation/logo.html` - Logo component
- `components/navigation/desktop_menu.html` - Menu desktop
- `components/navigation/mobile_menu.html` - Menu mobile
- `components/navigation/mobile_menu_button.html` - Button hamburger
- `components/navigation/account_menu.html` - Account dropdown (desktop)
- `components/navigation/auth_buttons.html` - Login/Signup buttons

### Other Components

- `components/footer.html` - Footer component

## JavaScript

Navigation JavaScript được tách riêng trong `static/js/navigation.js`:
- Xử lý mobile menu toggle
- Xử lý account menu dropdown
- Toggle icon (hamburger ↔ X)

## Mở rộng

### Thêm menu item mới

1. Sửa `common/context_processors.py`:
```python
nav_items = [
    # ... existing items
    {
        'name': 'Menu Mới',
        'url_name': 'app:view_name',
        'icon': None,  # Có thể thêm icon sau
    },
]
```

### Tạo component mới

1. Tạo file trong `templates/components/your_component.html`
2. Sử dụng trong template:
```django
{% include "components/your_component.html" %}
```

### Thêm context processor mới

1. Tạo function trong `common/context_processors.py`
2. Thêm vào `TEMPLATES['OPTIONS']['context_processors']` trong `settings.py`

