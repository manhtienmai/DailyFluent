# 📊 Cấu trúc Database cho TOEIC Exam

## Tổng quan

**1 đề thi TOEIC = 1 ExamTemplate** chứa tất cả các câu hỏi (Listening + Reading).

---

## 🗄️ Các Bảng (Models) Liên quan

### 1. **ExamTemplate** (Bảng chính - 1 đề thi)

**Mục đích**: Đại diện cho 1 đề thi TOEIC hoàn chỉnh.

**Fields quan trọng**:
- `id`: ID duy nhất
- `title`: Tên đề thi (ví dụ: "ETS Test 1", "TOEIC Test 2024 - Đề 01")
- `level`: `"TOEIC"` (bắt buộc)
- `category`: 
  - `"READING"` - Nếu chỉ có Reading
  - `"LISTENING"` - Nếu chỉ có Listening  
  - `"TOEIC_FULL"` - Nếu có cả Listening + Reading (tự động update)
- `is_full_toeic`: `True` nếu là full test (200 câu)
- `listening_time_limit_minutes`: 45 (mặc định)
- `reading_time_limit_minutes`: 75 (mặc định)

**Ví dụ**:
```
ExamTemplate:
  id: 1
  title: "ETS Test 1"
  level: "TOEIC"
  category: "TOEIC_FULL"  (tự động update khi có đủ cả 2 phần)
  is_full_toeic: True
  listening_time_limit_minutes: 45
  reading_time_limit_minutes: 75
```

**Quan hệ**:
- 1 ExamTemplate → N ExamQuestion (tất cả câu hỏi)
- 1 ExamTemplate → N ListeningConversation (cho Part 3, 4)
- 1 ExamTemplate → N ReadingPassage (cho Part 6, 7)

---

### 2. **ExamQuestion** (Tất cả câu hỏi)

**Mục đích**: Lưu từng câu hỏi trong đề thi.

**Fields quan trọng**:
- `id`: ID duy nhất
- `template`: ForeignKey → ExamTemplate (câu hỏi thuộc đề nào)
- `toeic_part`: `"L1"`, `"L2"`, `"L3"`, `"L4"`, `"R5"`, `"R6"`, `"R7"`
- `order`: Số thứ tự trong đề (1-200 cho full test)
- `text`: Câu hỏi (optional cho Part 1, 2)
- `data`: JSON chứa choices `{"choices": [{"key": "1", "text": "..."}, ...]}`
- `correct_answer`: `"1"`, `"2"`, `"3"`, hoặc `"4"`
- `image`: Hình ảnh (cho Part 1)
- `audio`: Audio file (cho Part 1, 2)
- `listening_conversation`: ForeignKey → ListeningConversation (cho Part 3, 4)
- `passage`: ForeignKey → ReadingPassage (cho Part 6, 7)

**Ví dụ**:
```
ExamQuestion (Part 1 - Câu 1):
  id: 101
  template_id: 1  (ETS Test 1)
  toeic_part: "L1"
  order: 1
  text: ""  (Part 1 không có text)
  data: {"choices": [{"key": "1", "text": "She is talking..."}, ...]}
  correct_answer: "1"
  image: "exam/toeic/images/part1_q1.jpg"
  audio: "exam/listening/part1_q1.mp3"

ExamQuestion (Part 5 - Câu 101):
  id: 201
  template_id: 1  (CÙNG ETS Test 1)
  toeic_part: "R5"
  order: 101
  text: "The meeting will be held _____ the conference room."
  data: {"choices": [{"key": "1", "text": "at"}, ...]}
  correct_answer: "2"
  image: null
  audio: null
```

**Quan hệ**:
- N ExamQuestion → 1 ExamTemplate (tất cả câu hỏi thuộc cùng 1 đề)
- N ExamQuestion → 1 ListeningConversation (cho Part 3, 4)
- N ExamQuestion → 1 ReadingPassage (cho Part 6, 7)

---

### 3. **ListeningConversation** (Cho Part 3, 4)

**Mục đích**: Lưu đoạn hội thoại/bài nói (mỗi đoạn có 3 câu hỏi).

**Fields quan trọng**:
- `id`: ID duy nhất
- `template`: ForeignKey → ExamTemplate
- `toeic_part`: `"L3"` hoặc `"L4"`
- `order`: Thứ tự conversation (1-13 cho Part 3, 1-10 cho Part 4)
- `audio`: File audio chung cho cả 3 câu hỏi
- `image`: Hình/biểu đồ (optional)
- `transcript`: Transcript (optional)

**Ví dụ**:
```
ListeningConversation (Part 3 - Conversation 1):
  id: 1
  template_id: 1  (ETS Test 1)
  toeic_part: "L3"
  order: 1
  audio: "exam/toeic/listening/part3_conv1.mp3"
  image: null
  transcript: "Man: Good morning. I'd like to..."

→ 3 ExamQuestion sẽ link đến conversation này:
  - Question order 32 (toeic_part="L3", listening_conversation_id=1)
  - Question order 33 (toeic_part="L3", listening_conversation_id=1)
  - Question order 34 (toeic_part="L3", listening_conversation_id=1)
```

**Quan hệ**:
- 1 ListeningConversation → N ExamQuestion (3 câu hỏi)
- N ListeningConversation → 1 ExamTemplate

---

### 4. **ReadingPassage** (Cho Part 6, 7)

**Mục đích**: Lưu đoạn văn (passage) cho Reading Part 6, 7.

**Fields quan trọng**:
- `id`: ID duy nhất
- `template`: ForeignKey → ExamTemplate
- `order`: Thứ tự passage (1-4 cho Part 6, 1-N cho Part 7)
- `title`: Tiêu đề passage (optional)
- `text`: Nội dung passage
- `image`: Hình ảnh (optional)

**Ví dụ**:
```
ReadingPassage (Part 6 - Passage 1):
  id: 1
  template_id: 1  (ETS Test 1)
  order: 1
  title: "Email về cuộc họp"
  text: "Dear Team,\n\nWe would like to inform you..."
  image: "exam/dokkai_passages/passage1.jpg"

→ 4 ExamQuestion sẽ link đến passage này:
  - Question order 131 (toeic_part="R6", passage_id=1)
  - Question order 132 (toeic_part="R6", passage_id=1)
  - Question order 133 (toeic_part="R6", passage_id=1)
  - Question order 134 (toeic_part="R6", passage_id=1)
```

**Quan hệ**:
- 1 ReadingPassage → N ExamQuestion (nhiều câu hỏi)
- N ReadingPassage → 1 ExamTemplate

---

## 🔗 Quan hệ giữa các Bảng

```
ExamTemplate (1 đề thi)
  │
  ├── ExamQuestion (200 câu hỏi)
  │   ├── Part 1-2: Questions độc lập (có audio/image riêng)
  │   ├── Part 3-4: Questions link đến ListeningConversation
  │   └── Part 5-7: Questions (Part 6-7 link đến ReadingPassage)
  │
  ├── ListeningConversation (23 conversations)
  │   ├── Part 3: 13 conversations
  │   └── Part 4: 10 conversations
  │
  └── ReadingPassage (N passages)
      ├── Part 6: 4 passages
      └── Part 7: N passages
```

---

## 📝 Workflow: Tạo 1 đề thi TOEIC

### Bước 1: Tạo ExamTemplate

**Trong Admin**:
1. Click "Add Exam Template"
2. Điền:
   - `title`: "ETS Test 1"
   - `level`: "TOEIC"
   - `category`: "READING" (hoặc "LISTENING", hoặc "TOEIC_FULL")
3. Click "Save"

**Kết quả**:
```
ExamTemplate:
  id: 1
  title: "ETS Test 1"
  level: "TOEIC"
  category: "READING"  (ban đầu)
  is_full_toeic: False
  questions: []  (chưa có câu hỏi nào)
```

---

### Bước 2: Import Reading (Part 5, 6, 7)

**Trong Admin**:
1. Vào trang "Change" của ExamTemplate vừa tạo
2. Click "Import TOEIC JSON"
3. Import Part 5, 6, 7

**Kết quả**:
```
ExamTemplate:
  id: 1
  title: "ETS Test 1"
  category: "READING"  (vẫn là READING)
  questions: [
    ExamQuestion(order=101, toeic_part="R5", ...),
    ExamQuestion(order=102, toeic_part="R5", ...),
    ...
    ExamQuestion(order=200, toeic_part="R7", ...),
  ]  (100 câu Reading)

ReadingPassage:
  - Passage 1 (Part 6)
  - Passage 2 (Part 6)
  - Passage 3 (Part 6)
  - Passage 4 (Part 6)
  - Passage 5+ (Part 7)
```

---

### Bước 3: Import Listening (Part 1, 2, 3, 4)

**Trong Admin**:
1. Vẫn ở trang "Change" của ExamTemplate đó
2. Click "Import TOEIC JSON" lại
3. Import Part 1, 2, 3, 4

**Kết quả**:
```
ExamTemplate:
  id: 1  (CÙNG template)
  title: "ETS Test 1"
  category: "TOEIC_FULL"  (TỰ ĐỘNG ĐỔI)
  is_full_toeic: True  (TỰ ĐỘNG ĐỔI)
  questions: [
    // Listening (order 1-100)
    ExamQuestion(order=1, toeic_part="L1", ...),
    ExamQuestion(order=2, toeic_part="L1", ...),
    ...
    ExamQuestion(order=100, toeic_part="L4", ...),
    
    // Reading (order 101-200)
    ExamQuestion(order=101, toeic_part="R5", ...),
    ...
    ExamQuestion(order=200, toeic_part="R7", ...),
  ]  (200 câu - CẢ Listening VÀ Reading)

ListeningConversation:
  - Conversation 1 (Part 3)
  - Conversation 2 (Part 3)
  ...
  - Conversation 13 (Part 3)
  - Conversation 14 (Part 4)
  ...
  - Conversation 23 (Part 4)

ReadingPassage:
  (giữ nguyên từ bước 2)
```

---

## ❓ Câu hỏi thường gặp

### Q1: 1 đề thi có nhiều section không?

**A**: Không. **1 đề thi = 1 ExamTemplate**. Tất cả câu hỏi (Listening + Reading) đều thuộc cùng 1 ExamTemplate.

**Section** chỉ là cách phân loại trong code:
- Listening: Questions có `toeic_part` bắt đầu bằng "L" (L1-L4)
- Reading: Questions có `toeic_part` bắt đầu bằng "R" (R5-R7)

---

### Q2: Category là gì? Có phải là cách tách đề thi không?

**A**: Không. **Category chỉ là label để phân loại**, không phải cách tách đề thi.

**Category dùng để**:
- Filter trong admin: "Show only Reading tests"
- Hiển thị trong UI: "TOEIC Reading", "TOEIC Listening", "TOEIC Full Test"
- Logic tự động: Khi có đủ cả Listening + Reading → Category tự động = `TOEIC_FULL`

**Tất cả questions vẫn thuộc cùng 1 ExamTemplate**, dù category là gì.

---

### Q3: Làm sao để thêm Listening sau khi đã tạo Reading?

**A**: Đơn giản! Chỉ cần:

1. Vào trang **Change** của ExamTemplate đó (cùng template đã có Reading)
2. Click **Import TOEIC JSON**
3. Import Part 1, 2, 3, 4

**Hệ thống sẽ**:
- Thêm questions vào **cùng template đó**
- Tự động update `category` → `TOEIC_FULL`
- Tự động update `is_full_toeic` → `True`

**Không cần tạo template mới!**

---

### Q4: Có thể import Listening trước, Reading sau không?

**A**: Có! Bạn có thể import theo bất kỳ thứ tự nào:

- **Option 1**: Reading trước → Listening sau
- **Option 2**: Listening trước → Reading sau
- **Option 3**: Import từng part một (L1, L2, R5, L3, R6, ...)

Hệ thống sẽ tự động:
- Thêm questions vào cùng template
- Update category khi có đủ cả 2 phần

---

### Q5: Có thể tạo 2 template riêng biệt (1 cho Listening, 1 cho Reading) không?

**A**: Có, nhưng **không khuyến khích** cho full test.

**Nếu muốn tách riêng**:
- Template 1: `category = "LISTENING"`, chỉ có Part 1-4
- Template 2: `category = "READING"`, chỉ có Part 5-7

**Nhưng**:
- User sẽ phải làm 2 lần (1 lần Listening, 1 lần Reading)
- Không có timer tổng hợp (45 phút + 75 phút)
- Không đúng format TOEIC thực tế (full test là 1 đề liền mạch)

**Khuyến khích**: Dùng 1 template cho full test.

---

## 📊 Ví dụ Database thực tế

### Full Test TOEIC (200 câu)

```sql
-- 1 ExamTemplate
INSERT INTO exam_examtemplate (id, title, level, category, is_full_toeic) 
VALUES (1, 'ETS Test 1', 'TOEIC', 'TOEIC_FULL', true);

-- 200 ExamQuestion (tất cả link đến template_id=1)
INSERT INTO exam_examquestion (id, template_id, toeic_part, order, correct_answer, data) VALUES
  (1, 1, 'L1', 1, '1', '{"choices": [...]}'),      -- Listening Part 1
  (2, 1, 'L1', 2, '2', '{"choices": [...]}'),
  ...
  (6, 1, 'L1', 6, '1', '{"choices": [...]}'),
  (7, 1, 'L2', 7, '2', '{"choices": [...]}'),      -- Listening Part 2
  ...
  (31, 1, 'L2', 31, '3', '{"choices": [...]}'),
  (32, 1, 'L3', 32, '1', '{"choices": [...]}'),    -- Listening Part 3 (link đến conversation)
  ...
  (100, 1, 'L4', 100, '2', '{"choices": [...]}'),   -- Listening Part 4
  (101, 1, 'R5', 101, '2', '{"choices": [...]}'),   -- Reading Part 5
  ...
  (200, 1, 'R7', 200, '4', '{"choices": [...]}');   -- Reading Part 7

-- 23 ListeningConversation (link đến template_id=1)
INSERT INTO exam_listeningconversation (id, template_id, toeic_part, order, audio) VALUES
  (1, 1, 'L3', 1, 'exam/toeic/listening/part3_conv1.mp3'),  -- Part 3
  ...
  (13, 1, 'L3', 13, 'exam/toeic/listening/part3_conv13.mp3'),
  (14, 1, 'L4', 1, 'exam/toeic/listening/part4_talk1.mp3'),  -- Part 4
  ...
  (23, 1, 'L4', 10, 'exam/toeic/listening/part4_talk10.mp3');

-- N ReadingPassage (link đến template_id=1)
INSERT INTO exam_readingpassage (id, template_id, order, text) VALUES
  (1, 1, 1, 'Dear Team,...'),  -- Part 6
  (2, 1, 2, '...'),
  (3, 1, 3, '...'),
  (4, 1, 4, '...'),
  (5, 1, 5, 'We are pleased...'),  -- Part 7
  ...;
```

---

## 🎯 Tóm tắt

| Khái niệm | Giải thích |
|-----------|------------|
| **1 đề thi** | = 1 ExamTemplate |
| **Section** | Chỉ là cách phân loại (Listening/Reading), không phải tách đề thi |
| **Category** | Label để filter/hiển thị, tự động update khi có đủ cả 2 phần |
| **Questions** | Tất cả 200 câu (Listening + Reading) đều thuộc cùng 1 ExamTemplate |
| **Import** | Có thể import Reading trước, Listening sau (hoặc ngược lại) vào **cùng template** |
| **Auto Update** | Category tự động đổi thành `TOEIC_FULL` khi có đủ cả Listening + Reading |

---

**Kết luận**: Bạn chỉ cần tạo **1 ExamTemplate**, sau đó import tất cả parts vào đó. Category sẽ tự động update!

