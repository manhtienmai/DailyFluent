# Đề xuất Schema Database cho TOEIC

## 📋 Tổng quan cấu trúc TOEIC

### Listening (100 câu, ~45 phút)
- **Part 1**: Mô tả hình ảnh (6 câu) - có hình ảnh
- **Part 2**: Câu hỏi-Đáp án (25 câu) - không có hình
- **Part 3**: Hội thoại ngắn (39 câu, 13 đoạn, mỗi đoạn 3 câu) - có thể có hình/biểu đồ
- **Part 4**: Bài nói ngắn (30 câu, 10 đoạn, mỗi đoạn 3 câu) - có thể có hình/biểu đồ

### Reading (100 câu, ~75 phút)
- **Part 5**: Điền từ vào câu (30 câu) - độc lập
- **Part 6**: Điền từ vào đoạn văn (16 câu, 4 đoạn, mỗi đoạn 4 câu) - có passage
- **Part 7**: Đọc hiểu (54 câu) - có passage (đơn đoạn hoặc đa đoạn)

---

## ✅ Phần có thể TÁI SỬ DỤNG từ schema JLPT

### 1. **ExamBook** ✅
- **Tái sử dụng hoàn toàn**: Sách TOEIC (ví dụ: "ETS TOEIC Test 2024", "Economy TOEIC")
- Chỉ cần mở rộng `level` và `category` để hỗ trợ TOEIC

### 2. **ExamTemplate** ✅
- **Tái sử dụng hoàn toàn**: 1 đề TOEIC = 1 ExamTemplate
- Có thể là:
  - Full test (200 câu: 100 Listening + 100 Reading)
  - Chỉ Listening (100 câu)
  - Chỉ Reading (100 câu)
  - Theo Part (ví dụ: Part 1 practice, Part 5 practice)

### 3. **ExamQuestion** ✅ (cần mở rộng nhỏ)
- **Tái sử dụng 90%**: Đã có `audio`, `text`, `data`, `correct_answer`
- **Cần thêm**: `image` field cho Listening Part 1 (mô tả hình ảnh)
- **Cần thêm**: `toeic_part` field để phân loại Part 1-7

### 4. **ReadingPassage** ✅
- **Tái sử dụng hoàn toàn**: Dùng cho Reading Part 6, 7
- Đã có `text`, `image`, `order` - đủ cho TOEIC

### 5. **ExamAttempt** ✅
- **Tái sử dụng hoàn toàn**: Lần làm bài của user

### 6. **QuestionAnswer** ✅
- **Tái sử dụng hoàn toàn**: Đáp án user cho từng câu

---

## 🆕 Phần cần MỞ RỘNG / THÊM MỚI

### 1. Mở rộng `ExamLevel`
```python
class ExamLevel(models.TextChoices):
    # JLPT (giữ nguyên)
    N5 = "N5", "JLPT N5"
    N4 = "N4", "JLPT N4"
    N3 = "N3", "JLPT N3"
    N2 = "N2", "JLPT N2"
    N1 = "N1", "JLPT N1"
    
    # TOEIC (thêm mới)
    TOEIC = "TOEIC", "TOEIC"
```

### 2. Mở rộng `ExamCategory`
```python
class ExamCategory(models.TextChoices):
    # JLPT (giữ nguyên)
    MOJIGOI = "MOJI", "Moji・Goi"
    BUNPOU = "BUN", "Bunpou"
    DOKKAI = "DOKKAI", "Dokkai"
    CHOUKAI = "CHOUKAI", "Choukai"
    MIX = "MIX", "Mixed"
    
    # TOEIC (thêm mới)
    LISTENING = "LISTENING", "TOEIC Listening"
    READING = "READING", "TOEIC Reading"
    TOEIC_FULL = "TOEIC_FULL", "TOEIC Full Test"
```

### 3. Thêm `TOEICPart` (Choices)
```python
class TOEICPart(models.TextChoices):
    """Các phần của bài thi TOEIC"""
    LISTENING_1 = "L1", "Listening Part 1: Mô tả hình ảnh"
    LISTENING_2 = "L2", "Listening Part 2: Câu hỏi-Đáp án"
    LISTENING_3 = "L3", "Listening Part 3: Hội thoại ngắn"
    LISTENING_4 = "L4", "Listening Part 4: Bài nói ngắn"
    READING_5 = "R5", "Reading Part 5: Điền từ vào câu"
    READING_6 = "R6", "Reading Part 6: Điền từ vào đoạn văn"
    READING_7 = "R7", "Reading Part 7: Đọc hiểu"
```

### 4. Mở rộng `ExamQuestion`
```python
class ExamQuestion(models.Model):
    # ... (giữ nguyên tất cả fields hiện tại)
    
    # Thêm mới cho TOEIC
    toeic_part = models.CharField(
        max_length=2,
        choices=TOEICPart.choices,
        blank=True,
        null=True,
        help_text="Phần TOEIC (L1-L4, R5-R7). Để trống nếu không phải TOEIC.",
    )
    
    image = models.ImageField(
        upload_to="exam/toeic/images/",
        blank=True,
        null=True,
        help_text="Hình ảnh cho Listening Part 1 hoặc Reading Part 7 (nếu có).",
    )
    
    # Note: `audio` field đã có sẵn, dùng cho Listening Part 1-4
```

### 5. Thêm `ListeningConversation` (Cho Part 3, 4)
```python
class ListeningConversation(models.Model):
    """
    Hội thoại / Bài nói cho Listening Part 3, 4.
    
    Part 3: 13 đoạn hội thoại, mỗi đoạn 3 câu hỏi
    Part 4: 10 đoạn bài nói, mỗi đoạn 3 câu hỏi
    """
    template = models.ForeignKey(
        ExamTemplate,
        related_name="listening_conversations",
        on_delete=models.CASCADE,
    )
    
    toeic_part = models.CharField(
        max_length=2,
        choices=[(TOEICPart.LISTENING_3, "Part 3"), (TOEICPart.LISTENING_4, "Part 4")],
    )
    
    order = models.PositiveIntegerField(
        default=1,
        help_text="Thứ tự đoạn trong Part (1-13 cho Part 3, 1-10 cho Part 4)",
    )
    
    audio = models.FileField(
        upload_to="exam/toeic/listening/",
        help_text="File audio cho đoạn hội thoại/bài nói",
    )
    
    # Có thể có hình/biểu đồ (optional)
    image = models.ImageField(
        upload_to="exam/toeic/listening_images/",
        blank=True,
        null=True,
        help_text="Hình/biểu đồ kèm theo (nếu có)",
    )
    
    # Context/transcript (optional, để hiển thị sau khi làm xong)
    transcript = models.TextField(
        blank=True,
        help_text="Transcript của đoạn audio (hiển thị sau khi submit)",
    )
    
    # Metadata
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text='VD: {"speakers": 2, "topic": "office meeting"}',
    )
    
    class Meta:
        ordering = ["template_id", "toeic_part", "order", "id"]
        unique_together = ("template", "toeic_part", "order")
    
    def __str__(self):
        return f"{self.template} – {self.get_toeic_part_display()} – Conversation {self.order}"
```

### 6. Mở rộng `ReadingPassage` (đã có, chỉ cần dùng)
- **Part 6**: 4 đoạn văn, mỗi đoạn 4 câu hỏi → dùng `ReadingPassage` với `order=1..4`
- **Part 7**: Đơn đoạn hoặc đa đoạn → dùng `ReadingPassage` với `order=1..N`

### 7. Mở rộng `ExamTemplate` (thêm field nhỏ)
```python
class ExamTemplate(models.Model):
    # ... (giữ nguyên tất cả fields hiện tại)
    
    # Thêm mới cho TOEIC
    is_full_toeic = models.BooleanField(
        default=False,
        help_text="True nếu là full test TOEIC (200 câu: Listening + Reading)",
    )
    
    listening_time_limit_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Giới hạn thời gian cho phần Listening (phút). Mặc định 45 phút.",
    )
    
    reading_time_limit_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Giới hạn thời gian cho phần Reading (phút). Mặc định 75 phút.",
    )
```

---

## 📊 Ví dụ cấu trúc dữ liệu

### Ví dụ 1: Full TOEIC Test (200 câu)
```
ExamTemplate:
  - title: "TOEIC Test 2024 - Đề 01"
  - level: "TOEIC"
  - category: "TOEIC_FULL"
  - is_full_toeic: True
  - listening_time_limit_minutes: 45
  - reading_time_limit_minutes: 75

ExamQuestion (100 câu Listening):
  - Q1-Q6:   toeic_part="L1", image=<hình>, audio=<audio>
  - Q7-Q31:  toeic_part="L2", audio=<audio>
  - Q32-Q70: toeic_part="L3", passage=<ListeningConversation>, audio=<audio>
  - Q71-Q100: toeic_part="L4", passage=<ListeningConversation>, audio=<audio>

ExamQuestion (100 câu Reading):
  - Q101-Q130: toeic_part="R5" (độc lập, không có passage)
  - Q131-Q146: toeic_part="R6", passage=<ReadingPassage> (4 đoạn)
  - Q147-Q200: toeic_part="R7", passage=<ReadingPassage> (đơn/đa đoạn)
```

### Ví dụ 2: Practice Part 3 (Listening)
```
ExamTemplate:
  - title: "TOEIC Listening Part 3 - Practice"
  - level: "TOEIC"
  - category: "LISTENING"
  - is_full_toeic: False

ListeningConversation (13 đoạn):
  - Conversation 1: audio=<audio>, order=1
  - Conversation 2: audio=<audio>, order=2
  - ...

ExamQuestion (39 câu):
  - Q1-Q3:   passage=<ListeningConversation order=1>, toeic_part="L3"
  - Q4-Q6:   passage=<ListeningConversation order=2>, toeic_part="L3"
  - ...
```

---

## 🎯 Kế hoạch triển khai

### Phase 1: Mở rộng Models (Migration)
1. Thêm `TOEICPart` choices
2. Mở rộng `ExamLevel`, `ExamCategory`
3. Thêm `toeic_part`, `image` vào `ExamQuestion`
4. Thêm `ListeningConversation` model
5. Mở rộng `ExamTemplate` (is_full_toeic, time limits)

### Phase 2: Admin Interface
1. Cập nhật `ExamQuestionAdmin` để hiển thị `toeic_part`, `image`
2. Tạo `ListeningConversationAdmin`
3. Thêm filter theo `toeic_part` trong admin

### Phase 3: Views & Templates
1. Cập nhật `take_exam` view để xử lý TOEIC format
2. Tạo template riêng cho TOEIC (nếu cần UI khác)
3. Xử lý audio playback cho Listening
4. Xử lý hình ảnh cho Part 1

### Phase 4: Import Data
1. Tạo management command `import_toeic_test` để import đề từ JSON/Excel
2. Hỗ trợ import full test hoặc từng part

---

## 💡 Lưu ý quan trọng

1. **Backward Compatibility**: Tất cả mở rộng đều optional (`blank=True, null=True`), không ảnh hưởng dữ liệu JLPT hiện tại.

2. **Reusability**: 
   - `ReadingPassage` dùng chung cho JLPT Dokkai và TOEIC Reading Part 6, 7
   - `ExamQuestion` dùng chung, chỉ thêm fields mới
   - `ExamAttempt`, `QuestionAnswer` dùng chung hoàn toàn

3. **Flexibility**: 
   - Có thể tạo full test (200 câu) hoặc practice từng part
   - `data` JSON field trong `ExamQuestion` vẫn linh hoạt cho các dạng câu đặc biệt

4. **Audio Management**:
   - Listening Part 1-4: `audio` trong `ExamQuestion` hoặc `ListeningConversation`
   - Có thể dùng Azure Blob Storage (đã setup sẵn)

5. **Image Management**:
   - Part 1: `image` trong `ExamQuestion`
   - Part 3, 4, 7: `image` trong `ListeningConversation` hoặc `ReadingPassage`
   - Dùng Azure Blob Storage (đã setup sẵn)

---

## ✅ Kết luận

**Có thể tái sử dụng ~85% schema hiện tại:**
- ✅ ExamBook, ExamTemplate, ExamAttempt, QuestionAnswer: 100%
- ✅ ReadingPassage: 100% (dùng cho Part 6, 7)
- ✅ ExamQuestion: 90% (chỉ cần thêm `toeic_part`, `image`)

**Chỉ cần thêm mới:**
- 🆕 `ListeningConversation` model (cho Part 3, 4)
- 🆕 Mở rộng choices: `TOEICPart`, `ExamLevel`, `ExamCategory`
- 🆕 Mở rộng fields: `toeic_part`, `image` trong `ExamQuestion`

**Ưu điểm:**
- Tận dụng tối đa code hiện có
- Dễ maintain, không duplicate logic
- Flexible, có thể mở rộng thêm sau

