# Hướng dẫn Tùy chỉnh Pagination - Số lượng từ vựng mỗi trang

## Tổng quan

Hệ thống pagination cho phần bài học từ vựng đã được tùy chỉnh để cho phép người dùng chọn số lượng từ vựng hiển thị trên mỗi trang.

## Tính năng

- **Dropdown selector** để chọn số lượng từ vựng mỗi trang (10, 20, 30, 50, 100)
- **Lưu preference** vào `localStorage` để nhớ lựa chọn của user
- **Tự động reset về trang 1** khi thay đổi số lượng
- **Hiển thị thông tin** số từ vựng hiện tại (ví dụ: "Hiển thị 1-20 / 150 từ vựng")

## Cách sử dụng

### 1. Vị trí

Tính năng này chỉ hoạt động ở **mode "vocab"** trong trang bài học:
```
/courses/{course_slug}/lessons/{lesson_slug}/?mode=vocab
```

### 2. UI

Dropdown selector nằm ở phía trên pagination, bên phải:
- **Label**: "Số từ/trang:"
- **Options**: 10, 20, 30, 50, 100
- **Default**: 20 từ/trang

### 3. Cách hoạt động

1. User chọn số lượng từ dropdown
2. Hệ thống lưu vào `localStorage` với key `df_vocab_per_page`
3. Tự động reload trang với `per_page` mới và reset về trang 1
4. Lần sau khi vào trang, hệ thống tự động load preference đã lưu

## Implementation Details

### Backend (`core/views.py`)

```python
if mode == "vocab":
    page_number = request.GET.get("page", 1)
    # Get per_page from request, default to 20, validate allowed values
    per_page = request.GET.get("per_page", "20")
    allowed_per_page = [10, 20, 30, 50, 100]
    try:
        per_page = int(per_page)
        if per_page not in allowed_per_page:
            per_page = 20
    except (ValueError, TypeError):
        per_page = 20
    
    paginator = Paginator(en_qs, per_page)
    # ... rest of pagination logic
```

**Lưu ý:**
- Chỉ chấp nhận các giá trị: 10, 20, 30, 50, 100
- Nếu giá trị không hợp lệ, mặc định là 20
- `per_page` được giữ trong URL query string nếu khác 20

### Frontend (`templates/courses/course_lesson.html`)

#### HTML Structure:
```django
<div class="flex items-center justify-between gap-4 mb-4">
  <div class="text-xs text-slate-500">
    Hiển thị <span class="font-semibold">{{ page_obj.start_index }}</span>-<span class="font-semibold">{{ page_obj.end_index }}</span> / <span class="font-semibold">{{ total_count }}</span> từ vựng
  </div>
  <div class="flex items-center gap-2">
    <label for="vocab-per-page" class="text-xs text-slate-600">Số từ/trang:</label>
    <select id="vocab-per-page" class="...">
      <option value="10" {% if page_obj.paginator.per_page == 10 %}selected{% endif %}>10</option>
      <option value="20" {% if page_obj.paginator.per_page == 20 %}selected{% endif %}>20</option>
      <!-- ... -->
    </select>
  </div>
</div>
```

#### JavaScript Logic:
- Load preference từ `localStorage` khi trang load
- Nếu có preference khác với giá trị hiện tại → redirect với preference đó
- Khi user thay đổi → lưu vào `localStorage` và redirect với `per_page` mới

### URL Structure

**Default (20 items):**
```
/courses/complete-toeic/lessons/lesson-1/?mode=vocab&page=2
```

**Custom per_page:**
```
/courses/complete-toeic/lessons/lesson-1/?mode=vocab&per_page=50&page=1
```

## Tùy chỉnh

### Thay đổi số lượng options

1. **Backend** (`core/views.py`):
   - Sửa `allowed_per_page = [10, 20, 30, 50, 100]` thành giá trị mong muốn

2. **Frontend** (`templates/courses/course_lesson.html`):
   - Thêm/bớt `<option>` trong dropdown selector

### Thay đổi default value

1. **Backend** (`core/views.py`):
   - Sửa `per_page = request.GET.get("per_page", "20")` → `"30"` (ví dụ)

2. **Frontend**:
   - Thêm `selected` attribute cho option mặc định

### Thêm vào các mode khác

Để thêm pagination tùy chỉnh cho các mode khác (mcq, matching, etc.):

1. Thêm logic tương tự trong `core/views.py` cho mode đó
2. Thêm UI selector trong template
3. Thêm JavaScript để xử lý change event

## Troubleshooting

### Preference không được lưu

- Kiểm tra `localStorage` có bị disable không
- Kiểm tra console có lỗi JavaScript không

### URL không cập nhật đúng

- Kiểm tra `base_qs` có chứa `per_page` không
- Kiểm tra pagination component có giữ `per_page` trong URL không

### Pagination hiển thị sai

- Đảm bảo `per_page` được truyền vào `Paginator`
- Kiểm tra `page_obj.paginator.per_page` trong template

## Best Practices

1. **Validation**: Luôn validate `per_page` từ request để tránh abuse
2. **Default**: Có default value hợp lý (20 là tốt cho UX)
3. **LocalStorage**: Lưu preference để user không phải chọn lại mỗi lần
4. **URL**: Giữ `per_page` trong URL để có thể share/bookmark
5. **Reset page**: Khi thay đổi `per_page`, luôn reset về trang 1

