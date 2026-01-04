# Debug: Icon nghe không hiển thị ở câu ví dụ

## Các lỗi có thể gây ra icon không hiển thị

### 1. **Template Tag không nhận được `forloop.counter`**
**Nguyên nhân:**
- Django template tag có thể không nhận được giá trị `forloop.counter` trực tiếp
- `forloop.counter` là một số nguyên, nhưng template tag có thể expect string

**Giải pháp:**
- Dùng `{% with example_num=forloop.counter %}` để convert sang biến
- Hoặc dùng `{% as %}` syntax để lưu kết quả template tag vào biến trước

**Code hiện tại:**
```django
{% with example_num=forloop.counter %}
  {% vocab_audio_url_us w.audio_pack_uuid 'example' example_num as audio_us_url %}
  {% vocab_audio_url_uk w.audio_pack_uuid 'example' example_num as audio_uk_url %}
  {% if audio_us_url or audio_uk_url %}
    <!-- Hiển thị button -->
  {% endif %}
{% endwith %}
```

---

### 2. **Template Tag trả về empty string**
**Nguyên nhân:**
- `_build_audio_path()` trả về `""` nếu:
  - `audio_pack_uuid` không hợp lệ (không phải UUID format)
  - `example_order` không hợp lệ (< 1 hoặc không phải số)
  - `AUDIO_BASE_URL` không được set trong settings

**Kiểm tra:**
```python
# Trong settings.py
AUDIO_BASE_URL = f"https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/{AZURE_AUDIO_CONTAINER}/"
```

**Debug:**
- Thêm logging vào `_build_audio_path()` để xem giá trị nhận được
- Kiểm tra `audio_pack_uuid` có đúng format UUID không (36 ký tự, 4 dấu gạch ngang)

---

### 3. **CSS đang ẩn icon**
**Nguyên nhân:**
- CSS khác có thể override với `display: none` hoặc `visibility: hidden`
- Tailwind CSS có thể ẩn element
- Parent element có thể có `overflow: hidden` và icon bị cắt

**Kiểm tra:**
- Inspect element trong browser DevTools
- Kiểm tra computed styles của `.df-example-audio-controls` và `.df-audio-btn-sm`
- Xem có CSS nào với `!important` đang override không

**Giải pháp:**
- Đã thêm `!important` vào CSS quan trọng
- Đảm bảo `display: flex !important` và `visibility: visible !important`

---

### 4. **JavaScript không attach event listener**
**Nguyên nhân:**
- JavaScript chỉ attach listener cho `.df-audio-btn` khi `DOMContentLoaded`
- Nếu button được render sau khi script chạy, listener sẽ không được attach
- Selector có thể không match với button

**Kiểm tra:**
- Mở browser console và chạy:
  ```javascript
  document.querySelectorAll('.df-audio-btn-sm').length
  ```
- Nếu trả về 0, button không được render
- Nếu trả về số > 0, button được render nhưng có thể bị ẩn

---

### 5. **Điều kiện `{% if w.audio_pack_uuid %}` fail**
**Nguyên nhân:**
- `w.audio_pack_uuid` có thể là `None`, `""`, hoặc `False`
- Django template coi tất cả các giá trị này là falsy

**Kiểm tra:**
- Thêm debug output:
  ```django
  <!-- Debug -->
  <div>audio_pack_uuid: {{ w.audio_pack_uuid|default:"EMPTY" }}</div>
  <div>Has examples: {{ w.examples.all|length }}</div>
  ```

---

### 6. **Template tag không được load**
**Nguyên nhân:**
- Quên `{% load vocab_tags %}` ở đầu template
- Template tag library chưa được register đúng

**Kiểm tra:**
- Xem đầu file template có `{% load vocab_tags %}` không
- Kiểm tra `vocab/templatetags/__init__.py` có tồn tại không
- Restart Django server sau khi tạo template tag mới

---

### 7. **`forloop.counter` không hoạt động trong nested loop**
**Nguyên nhân:**
- Nếu có nested `{% for %}`, `forloop.counter` có thể refer đến loop bên ngoài
- Django template có thể không resolve đúng context

**Giải pháp:**
- Dùng `forloop.parentloop.counter` nếu cần
- Hoặc dùng `ex.order` từ database thay vì `forloop.counter`

---

## Cách debug

### Bước 1: Kiểm tra HTML output
1. View page source hoặc inspect element
2. Tìm `<button class="df-audio-btn-sm">` trong HTML
3. Kiểm tra:
   - Button có tồn tại không?
   - `data-audio-us` và `data-audio-uk` có giá trị không?
   - Nếu empty, template tag đang trả về `""`

### Bước 2: Kiểm tra CSS
1. Inspect element `.df-example-audio-controls`
2. Kiểm tra computed styles:
   - `display` phải là `flex`
   - `visibility` phải là `visible`
   - `opacity` phải là `1`
   - `width` và `height` phải > 0

### Bước 3: Kiểm tra JavaScript
1. Mở browser console
2. Chạy:
   ```javascript
   const buttons = document.querySelectorAll('.df-audio-btn-sm');
   console.log('Found buttons:', buttons.length);
   buttons.forEach((btn, i) => {
     console.log(`Button ${i}:`, {
       hasUs: !!btn.dataset.audioUs,
       hasUk: !!btn.dataset.audioUk,
       usUrl: btn.dataset.audioUs,
       ukUrl: btn.dataset.audioUk
     });
   });
   ```

### Bước 4: Kiểm tra Template Tag
1. Thêm debug output vào template:
   ```django
   {% vocab_audio_url_us w.audio_pack_uuid 'example' forloop.counter as test_url %}
   <div style="background: red; color: white; padding: 10px;">
     Debug: UUID={{ w.audio_pack_uuid }}, Counter={{ forloop.counter }}, URL={{ test_url }}
   </div>
   ```

---

## Giải pháp đã áp dụng

1. ✅ Dùng `{% as %}` syntax để lưu kết quả template tag
2. ✅ Kiểm tra URL có tồn tại trước khi hiển thị button
3. ✅ Thêm `!important` vào CSS quan trọng
4. ✅ Xử lý cả string và int cho `example_order`
5. ✅ Thêm logging vào template tag để debug

---

## Next steps nếu vẫn không hoạt động

1. **Kiểm tra browser console** xem có lỗi JavaScript không
2. **Kiểm tra Django logs** xem có warning về template tag không
3. **Thử hardcode URL** trong template để test:
   ```django
   data-audio-us="https://dailyfluentaudio.blob.core.windows.net/audio/dailyfluent/99976bbb-051c-44ca-9062-cfe279082962/ex1_us.mp3"
   ```
4. **Kiểm tra `AUDIO_BASE_URL`** trong settings có đúng không
5. **Restart Django server** sau khi sửa template tag

