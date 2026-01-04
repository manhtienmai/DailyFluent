# 📚 Tài liệu TOEIC Listening - Hệ thống hoàn chỉnh

## 📋 Tổng quan

Hệ thống TOEIC Listening hỗ trợ 4 phần (Part 1-4) với các đặc điểm:
- **Part 1**: Mô tả hình ảnh (6 câu) - Mỗi câu có 1 hình + 1 audio
- **Part 2**: Câu hỏi-Đáp án (25 câu) - Mỗi câu có 1 audio
- **Part 3**: Hội thoại ngắn (39 câu, 13 đoạn) - Mỗi đoạn có 1 audio + 3 câu hỏi
- **Part 4**: Bài nói ngắn (30 câu, 10 đoạn) - Mỗi đoạn có 1 audio + 3 câu hỏi

---

## 🗄️ 1. Database Schema

### 1.1. TOEICPart Choices
```python
class TOEICPart(models.TextChoices):
    LISTENING_1 = "L1", "Listening Part 1: Mô tả hình ảnh"
    LISTENING_2 = "L2", "Listening Part 2: Câu hỏi-Đáp án"
    LISTENING_3 = "L3", "Listening Part 3: Hội thoại ngắn"
    LISTENING_4 = "L4", "Listening Part 4: Bài nói ngắn"
```

### 1.2. ListeningConversation Model
**File**: `exam/models.py`

**Mục đích**: Lưu trữ hội thoại/bài nói cho Part 3, 4

**Fields**:
- `template` (FK): ExamTemplate chứa conversation này
- `toeic_part` (CharField): "L3" hoặc "L4"
- `order` (PositiveInteger): Thứ tự trong Part (1-13 cho Part 3, 1-10 cho Part 4)
- `audio` (FileField): File audio bắt buộc, upload vào `exam/toeic/listening/`
- `image` (ImageField, optional): Hình/biểu đồ kèm theo, upload vào `exam/toeic/listening_images/`
- `transcript` (TextField, optional): Transcript để hiển thị sau khi submit
- `data` (JSONField): Metadata như `{"speakers": 2, "topic": "office meeting", "duration_seconds": 45}`

**Constraints**:
- `unique_together = ("template", "toeic_part", "order")`: Đảm bảo không trùng conversation trong cùng Part

**Relationships**:
- `template.listening_conversations`: Tất cả conversations của template
- `conversation.questions`: Tất cả questions gắn với conversation này

### 1.3. ExamQuestion Model (TOEIC Fields)
**File**: `exam/models.py`

**TOEIC-specific Fields**:
- `toeic_part` (CharField): "L1", "L2", "L3", "L4", "R5", "R6", "R7"
- `image` (ImageField, optional): Hình ảnh cho Part 1, upload vào `exam/toeic/images/`
- `listening_conversation` (FK, optional): Link đến ListeningConversation (cho Part 3, 4)
- `audio` (FileField, optional): Audio cho Part 1, 2, upload vào `exam/listening/`
- `audio_meta` (JSONField): Metadata như `{"cd": "CD1", "track": "03"}`

**Data Structure** (JSONField `data`):
```json
{
  "choices": [
    {"key": "1", "text": "She is talking on the phone."},
    {"key": "2", "text": "She is writing a report."},
    {"key": "3", "text": "She is reading a book."},
    {"key": "4", "text": "She is typing on a computer."}
  ]
}
```

### 1.4. ExamTemplate Model (TOEIC Fields)
**File**: `exam/models.py`

**TOEIC-specific Fields**:
- `is_full_toeic` (Boolean): True nếu là full test (200 câu)
- `listening_time_limit_minutes` (PositiveInteger, default=45): Thời gian cho Listening
- `reading_time_limit_minutes` (PositiveInteger, default=75): Thời gian cho Reading

---

## 🎛️ 2. Admin Interface

### 2.1. ListeningConversationAdmin
**File**: `exam/admin.py`

**List Display**:
- `id`, `template`, `toeic_part`, `order`
- `has_audio` (boolean icon)
- `has_image` (boolean icon)
- `has_transcript` (boolean icon)

**Filters**:
- `toeic_part` (Part 3 hoặc Part 4)
- `template__level`, `template__category`, `template__book`

**Search**:
- `template__title`, `transcript`

**Fieldsets**:
1. **Basic Information**: `template`, `toeic_part`, `order`
2. **Audio & Media**: `audio`, `image`
3. **Content**: `transcript`, `data`

### 2.2. ListeningConversationInline
**File**: `exam/admin.py`

**Mục đích**: Quản lý conversations trực tiếp trong ExamTemplate admin

**Fields**:
- `toeic_part`, `order`, `audio`, `image`, `transcript`

**Ordering**: `toeic_part`, `order`

### 2.3. ExamQuestionAdmin (TOEIC Fields)
**File**: `exam/admin.py`

**List Display**: Thêm `toeic_part`

**Filters**: Thêm `toeic_part`

**Fieldsets**: Thêm section "TOEIC Specific" với:
- `listening_conversation`
- `image`
- `audio`, `audio_meta`

### 2.4. ExamTemplateAdmin (TOEIC Fields)
**File**: `exam/admin.py`

**List Display**: Thêm `is_full_toeic`, `listening_time_limit_minutes`, `reading_time_limit_minutes`

**Filters**: Thêm `is_full_toeic`

**Fieldsets**: Thêm section "TOEIC Settings" (collapse) với:
- `is_full_toeic`
- `listening_time_limit_minutes`
- `reading_time_limit_minutes`

**Inlines**: Thêm `ListeningConversationInline` (trước `ExamQuestionInline`)

---

## 🔄 3. Views & Logic

### 3.1. take_toeic_exam View
**File**: `exam/views.py`

**Flow**:
1. **Authentication**: Yêu cầu login (`@login_required`)
2. **Get Attempt**: Lấy `ExamAttempt` từ `session_id`
3. **Validation**: Kiểm tra `template.level == ExamLevel.TOEIC`, nếu không redirect về `take_exam`
4. **Load Questions**: 
   ```python
   questions = template.questions
       .select_related("passage", "listening_conversation")
       .order_by("toeic_part", "order", "id")
   ```
5. **Handle Submit** (POST):
   - Lặp qua tất cả questions
   - Lấy answer từ `request.POST.get(f"q{q.id}")`
   - Tạo/update `QuestionAnswer` với `raw_answer` và `is_correct`
   - Update `attempt.correct_count`, `attempt.status = SUBMITTED`
   - Redirect đến `exam_result`
6. **Group Questions by Part**:
   - Tạo `parts_data` dict với key là `toeic_part`
   - Mỗi part có:
     - `part`, `part_display`
     - `questions`: List tất cả questions
     - `conversations`: Dict group theo conversation (Part 3, 4)
     - `passages`: Dict group theo passage (Part 6, 7)
7. **Group Conversations** (Part 3, 4):
   ```python
   if q.listening_conversation:
       conv = q.listening_conversation
       conv_key = f"{conv.toeic_part}_{conv.order}"
       if conv_key not in parts_data[part]["conversations"]:
           parts_data[part]["conversations"][conv_key] = {
               "conversation": conv,
               "questions": [],
           }
       parts_data[part]["conversations"][conv_key]["questions"].append(q)
   ```
8. **Serialize Audio URLs**:
   - Part 1, 2: Audio từ `question.audio`
   - Part 3, 4: Audio từ `conversation.audio`
   - Serialize thành JSON cho JavaScript
9. **Calculate Time**:
   - Full test: `listening_time_limit_minutes + reading_time_limit_minutes`
   - Listening only: `listening_time_limit_minutes` (default 45)
   - Reading only: `reading_time_limit_minutes` (default 75)

**Context**:
- `session`: ExamAttempt
- `template_obj`: ExamTemplate
- `parts_list`: List parts đã sắp xếp (L1, L2, L3, L4, R5, R6, R7)
- `parts_list_json`: JSON string cho JavaScript
- `total_questions`: Tổng số câu hỏi
- `total_minutes`: Tổng thời gian (phút)

---

## 🎨 4. Templates & UI

### 4.1. toeic_exam_take.html
**File**: `templates/exam/toeic_exam_take.html`

#### 4.1.1. Layout Structure
```
┌─────────────────────────────────────────┐
│ Header: Title + Exit Button             │
├──────────────────┬──────────────────────┤
│                  │                      │
│  Main Content    │   Right Sidebar      │
│  - Part Nav     │   - Timer            │
│  - Audio Player │   - Submit Button     │
│  - Questions    │   - Question Nav      │
│                  │                      │
└──────────────────┴──────────────────────┘
```

#### 4.1.2. Part Navigation
- Buttons: "Part 1", "Part 2", "Part 3", "Part 4", "Part 5", "Part 6", "Part 7"
- Active state: Blue background
- Click: Switch to that part, load audio if Listening

#### 4.1.3. Audio Player
**Location**: Above exam form, only visible for Listening parts (L1-L4)

**Controls**:
- Play/Pause button (▶/⏸)
- Progress bar (shows current time / total duration)
- Time display (MM:SS)
- Speaker icon
- Volume slider (0-100)
- Settings button (⚙️)

**HTML**:
```html
<div id="audio-player-container" class="df-toeic-audio-player" style="display: none;">
  <audio id="toeic-audio" preload="auto"></audio>
  <div class="df-toeic-audio-controls">
    <button type="button" id="audio-play-btn">▶</button>
    <div class="df-toeic-audio-progress">
      <div class="df-toeic-audio-progress-bar">
        <div id="audio-progress" class="df-toeic-audio-progress-fill"></div>
      </div>
      <span id="audio-time" class="df-toeic-audio-time">00:00</span>
    </div>
    <button type="button" class="df-toeic-audio-speaker">🔊</button>
    <input type="range" id="audio-volume" class="df-toeic-audio-volume" min="0" max="100" value="100">
    <button type="button" class="df-toeic-audio-settings">⚙️</button>
  </div>
</div>
```

#### 4.1.4. Part 1: Mô tả hình ảnh
**Structure**:
```html
<div class="df-toeic-question-block" data-question-id="{{ q.id }}" data-audio-url="{{ q.audio.url }}">
  {% if q.image %}
    <div class="df-toeic-part1-image">
      <img src="{{ q.image.url }}" alt="Part 1 Image">
    </div>
  {% endif %}
  <div class="df-toeic-question">
    <div class="df-toeic-question-number">{{ q.order }}</div>
    <div class="df-toeic-question-options">
      {% for choice in q.mcq_choices %}
        <label class="df-toeic-option">
          <input type="radio" name="q{{ q.id }}" value="{{ choice.key }}">
          <span>{{ choice.key }}. {{ choice.text }}</span>
        </label>
      {% endfor %}
    </div>
  </div>
</div>
```

**Features**:
- Large image display (max-width: 600px)
- 4 MCQ options below image
- Each question has its own audio URL

#### 4.1.5. Part 2: Câu hỏi-Đáp án
**Structure**:
```html
<div class="df-toeic-question-block" data-question-id="{{ q.id }}" data-audio-url="{{ q.audio.url }}">
  <div class="df-toeic-question-number">{{ q.order }}</div>
  <div class="df-toeic-question-text">{{ q.text|default:"" }}</div>
  <div class="df-toeic-question-options">
    {% for choice in q.mcq_choices %}
      <label class="df-toeic-option">
        <input type="radio" name="q{{ q.id }}" value="{{ choice.key }}">
        <span>{{ choice.key }}. {{ choice.text }}</span>
      </label>
    {% endfor %}
  </div>
</div>
```

**Features**:
- No image
- Question text (optional, usually empty for Part 2)
- 4 MCQ options
- Each question has its own audio URL

#### 4.1.6. Part 3: Hội thoại ngắn
**Structure**:
```html
{% for conv_key, conv_data in part_data.conversations.items %}
  <div class="df-toeic-conversation-block" 
       data-conv-id="{{ conv_data.conversation.id }}"
       data-audio-url="{{ conv_data.conversation.audio.url }}">
    {% if conv_data.conversation.image %}
      <div class="df-toeic-conv-image">
        <img src="{{ conv_data.conversation.image.url }}" alt="Conversation Image">
      </div>
    {% endif %}
    {% for q in conv_data.questions %}
      <div class="df-toeic-question-block" data-question-id="{{ q.id }}">
        <div class="df-toeic-question-number">{{ q.order }}</div>
        <div class="df-toeic-question-text">{{ q.text|default:"" }}</div>
        <div class="df-toeic-question-options">
          {% for choice in q.mcq_choices %}
            <label class="df-toeic-option">
              <input type="radio" name="q{{ q.id }}" value="{{ choice.key }}">
              <span>{{ choice.key }}. {{ choice.text }}</span>
            </label>
          {% endfor %}
        </div>
      </div>
    {% endfor %}
  </div>
{% endfor %}
```

**Features**:
- 13 conversations, each with 3 questions
- 1 audio per conversation (shared by 3 questions)
- Optional image per conversation
- Questions grouped under conversation

#### 4.1.7. Part 4: Bài nói ngắn
**Structure**: Giống Part 3, nhưng:
- 10 conversations (bài nói)
- Mỗi bài nói có 3 câu hỏi
- 1 audio per conversation

#### 4.1.8. Right Sidebar
**Components**:
1. **Timer**:
   - Label: "Thời gian còn lại:"
   - Value: `MMM:SS` format (e.g., "119:48")
   - Updates every second
   - Auto-submit when reaches 0

2. **Submit Button**:
   - Large blue button: "NỘP BÀI"
   - Confirmation dialog before submit

3. **Instructions**:
   - "Khôi phục/lưu bài làm >"
   - "Chú ý: bạn có thể click vào số thứ tự câu hỏi trong bài để đánh dấu review"

4. **Question Navigation Grid**:
   - Grouped by Part
   - Each part shows grid of question numbers
   - Active question highlighted in blue
   - Click to scroll to question

---

## 🎵 5. Audio Handling

### 5.1. Audio Sources
- **Part 1, 2**: `question.audio.url` (mỗi câu 1 audio)
- **Part 3, 4**: `conversation.audio.url` (mỗi đoạn 1 audio, dùng chung cho 3 câu)

### 5.2. JavaScript Audio Logic
**File**: `templates/exam/toeic_exam_take.html` (script section)

**Functions**:
1. **`switchPart(part)`**:
   - Show/hide audio player based on part (L1-L4 show, R5-R7 hide)
   - Call `loadPartAudio(part)` if Listening

2. **`loadPartAudio(part)`**:
   ```javascript
   function loadPartAudio(part) {
     const partData = partsList.find(p => p.part === part);
     if (!partData || !partData.audio_urls || partData.audio_urls.length === 0) {
       return;
     }
     const firstAudio = partData.audio_urls[0];
     if (firstAudio && firstAudio.url) {
       audio.src = firstAudio.url;
       audio.load();
     }
   }
   ```

3. **Audio Player Controls**:
   - Play/Pause: Toggle `audio.play()` / `audio.pause()`
   - Progress: Update based on `audio.currentTime` / `audio.duration`
   - Volume: Set `audio.volume` (0-1)

### 5.3. Audio URL Serialization
**In View** (`take_toeic_exam`):
```python
# Part 1, 2: Audio từ từng question
if part_data["part"] in [TOEICPart.LISTENING_1, TOEICPart.LISTENING_2]:
    audio_urls = []
    for q in part_data["questions"]:
        if q.audio:
            audio_urls.append({
                "question_id": q.id,
                "url": q.audio.url,
            })
    part_json["audio_urls"] = audio_urls

# Part 3, 4: Audio từ conversations
elif part_data["part"] in [TOEICPart.LISTENING_3, TOEICPart.LISTENING_4]:
    audio_urls = []
    for conv_key, conv_data in part_data["conversations"].items():
        if conv_data["conversation"].audio:
            audio_urls.append({
                "conversation_id": conv_data["conversation"].id,
                "url": conv_data["conversation"].audio.url,
            })
    part_json["audio_urls"] = audio_urls
```

---

## 🔄 6. Flow Hoạt động

### 6.1. Tạo Đề Thi (Admin)
1. **Tạo ExamTemplate**:
   - Set `level = "TOEIC"`
   - Set `category = "LISTENING"` hoặc `"TOEIC_FULL"`
   - Set `listening_time_limit_minutes = 45` (default)

2. **Tạo ListeningConversation** (Part 3, 4):
   - Chọn `toeic_part = "L3"` hoặc `"L4"`
   - Set `order = 1, 2, 3, ...` (1-13 cho Part 3, 1-10 cho Part 4)
   - Upload `audio` file
   - Upload `image` (optional)
   - Nhập `transcript` (optional)

3. **Tạo ExamQuestion**:
   - **Part 1**: 
     - Set `toeic_part = "L1"`
     - Upload `image`
     - Upload `audio`
     - Set `data = {"choices": [...]}`
   - **Part 2**:
     - Set `toeic_part = "L2"`
     - Upload `audio`
     - Set `data = {"choices": [...]}`
   - **Part 3, 4**:
     - Set `toeic_part = "L3"` hoặc `"L4"`
     - Link `listening_conversation` (FK)
     - Set `data = {"choices": [...]}`

### 6.2. Làm Bài (User)
1. **Start Exam**:
   - User click "Bắt đầu" trên `toeic_list` page
   - `start_exam` view tạo `ExamAttempt`
   - Redirect đến `take_toeic_exam` (vì `level == TOEIC`)

2. **Load Exam Page**:
   - View `take_toeic_exam` load questions, group by part
   - Group conversations (Part 3, 4)
   - Serialize audio URLs
   - Render template với `parts_list`

3. **User Interaction**:
   - Click Part button → Switch part, load audio
   - Click question number in sidebar → Scroll to question
   - Play audio → Listen to question/conversation
   - Select answer → Radio button checked
   - Timer counts down → Auto-submit at 0

4. **Submit**:
   - User click "NỘP BÀI" → Confirmation dialog
   - Form POST → View processes answers
   - Create/update `QuestionAnswer` records
   - Calculate score → Update `attempt.correct_count`
   - Set `attempt.status = SUBMITTED`
   - Redirect to `exam_result`

### 6.3. Xem Kết Quả
- `exam_result` view shows:
  - Total questions, correct count, score percentage
  - List of answers with correct/incorrect status
  - Transcript (if available) for Part 3, 4

---

## 📁 7. File Structure

```
exam/
├── models.py              # ListeningConversation, ExamQuestion (TOEIC fields)
├── admin.py               # ListeningConversationAdmin, Inlines
├── views.py               # take_toeic_exam view
├── urls.py                # URL patterns
└── TOEIC_LISTENING_DOCUMENTATION.md  # This file

templates/exam/
└── toeic_exam_take.html   # Main template với audio player, questions

static/
└── (audio files stored in Azure Blob Storage)
    ├── exam/toeic/listening/          # Conversation audio (Part 3, 4)
    ├── exam/toeic/listening_images/   # Conversation images (Part 3, 4)
    ├── exam/toeic/images/             # Question images (Part 1)
    └── exam/listening/                # Question audio (Part 1, 2)
```

---

## 🎯 8. Key Features

### ✅ Đã Implement
- [x] Database schema cho Listening (Part 1-4)
- [x] Admin interface để quản lý conversations và questions
- [x] View logic để group questions theo part và conversation
- [x] Template với audio player, part navigation, question display
- [x] Audio handling (load, play, pause, progress, volume)
- [x] Timer countdown với auto-submit
- [x] Question navigation grid trong sidebar
- [x] Submit và scoring logic

### 🔄 Có thể Cải thiện
- [ ] Auto-play audio khi chuyển part
- [ ] Auto-advance to next question after audio ends
- [ ] Save progress to localStorage (resume later)
- [ ] Highlight selected answers in navigation grid
- [ ] Review mode (show transcript after submit)
- [ ] Audio speed control (0.5x, 1x, 1.5x, 2x)
- [ ] Repeat audio button
- [ ] Keyboard shortcuts (Space = play/pause, Arrow keys = next/prev question)

---

## 📝 9. Example Data Structure

### Part 1 Question
```python
ExamQuestion(
    template=toeic_template,
    toeic_part="L1",
    order=1,
    image="exam/toeic/images/part1_q1.jpg",
    audio="exam/listening/part1_q1.mp3",
    data={
        "choices": [
            {"key": "1", "text": "She is talking on the phone."},
            {"key": "2", "text": "She is writing a report."},
            {"key": "3", "text": "She is reading a book."},
            {"key": "4", "text": "She is typing on a computer."}
        ]
    },
    correct_answer="1"
)
```

### Part 3 Conversation
```python
# Conversation
conv = ListeningConversation(
    template=toeic_template,
    toeic_part="L3",
    order=1,
    audio="exam/toeic/listening/part3_conv1.mp3",
    image="exam/toeic/listening_images/part3_conv1.jpg",  # optional
    transcript="Man: Good morning. I'd like to...",  # optional
    data={"speakers": 2, "topic": "office meeting"}
)

# 3 Questions for this conversation
q1 = ExamQuestion(
    template=toeic_template,
    toeic_part="L3",
    order=32,
    listening_conversation=conv,
    text="What is the man's occupation?",
    data={"choices": [...]},
    correct_answer="2"
)
q2 = ExamQuestion(...)  # order=33
q3 = ExamQuestion(...)  # order=34
```

---

## 🔗 10. Related Files

- **Models**: `exam/models.py` (lines 47-55, 307-375, 402-432)
- **Admin**: `exam/admin.py` (lines 34-44, 167-209)
- **Views**: `exam/views.py` (lines 342-486)
- **Template**: `templates/exam/toeic_exam_take.html`
- **URLs**: `exam/urls.py` (line 10)

---

**Tài liệu này mô tả toàn bộ hệ thống TOEIC Listening từ database đến UI. Mọi thắc mắc hoặc cần mở rộng, vui lòng tham khảo code trong các file đã liệt kê.**

