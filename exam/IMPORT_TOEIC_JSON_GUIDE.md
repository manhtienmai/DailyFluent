# 📥 Hướng dẫn Import TOEIC JSON (Format Mới - schema_version 1.0)

## Tổng quan

Chức năng này cho phép import câu hỏi TOEIC (Listening Part 1-4 và Reading Part 5-7) từ file JSON vào Django Admin.

**⚠️ Lưu ý**: Chỉ hỗ trợ format mới (schema_version 1.0) với cấu trúc `sections`/`passages`/`questions`.

---

## Cách sử dụng

### Bước 1: Tạo ExamTemplate

1. Vào Django Admin → **Exam Templates**
2. Click **Add Exam Template**
3. Điền thông tin:
   - **Title**: Tên đề thi (ví dụ: "TOEIC Test 2024 - Đề 01")
   - **Level**: Chọn **TOEIC**
   - **Category**: Chọn **LISTENING**, **READING**, hoặc **TOEIC_FULL**
   - Các thông tin khác tùy chọn
4. Click **Save**

### Bước 2: Import TOEIC JSON

1. Sau khi tạo ExamTemplate, vào trang **Change** của template đó
2. Ở góc trên bên phải, click nút **Import TOEIC JSON**
3. Chọn một trong hai cách:
   - **Upload file JSON**: Click "Choose File" và chọn file `.json`
   - **Paste JSON text**: Copy và paste JSON vào textarea
4. Click **Import**

### Bước 3: Kiểm tra kết quả

- Nếu thành công: Sẽ hiển thị thông báo "Successfully imported X questions and Y passages/conversations"
- Nếu có lỗi: Sẽ hiển thị thông báo lỗi chi tiết

---

## 📋 JSON Format (schema_version 1.0)

### Cấu trúc tổng quan

```json
{
  "schema_version": "1.0",
  "test_id": "READING_ETS2026_TEST1",
  "module": "READING",
  "timezone": "Asia/Bangkok",
  "sections": [...],
  "passages": [...],
  "questions": [...]
}
```

### Fields bắt buộc

- **schema_version**: `"1.0"` (bắt buộc)
- **module**: `"READING"` hoặc `"LISTENING"` (bắt buộc)
- **sections**: Array các section (bắt buộc)
- **passages**: Array các passage/conversation (bắt buộc, có thể là array rỗng)
- **questions**: Array tất cả các câu hỏi (bắt buộc)

### Fields optional

- **test_id**: ID của đề thi (optional, chỉ để metadata)
- **timezone**: Timezone (optional, chỉ để metadata)
- **language**: Ngôn ngữ (optional, chỉ để metadata)

---

## 📚 Sections

Mỗi section định nghĩa một phần trong đề thi (P5, P6, P7 cho Reading; P1-P4 cho Listening).

```json
{
  "section_id": "P5",
  "type": "incomplete_sentences",
  "instruction": "Choose the best answer to complete the sentence.",
  "question_numbers": [126, 127, 128, 129, 130]
}
```

**Hoặc cho Part 6, 7:**

```json
{
  "section_id": "P6",
  "type": "text_completion",
  "instruction": "Choose the best answer for each blank in the passage.",
  "passage_ids": [
    "READING_ETS2026_TEST1_L6_Q131-134",
    "READING_ETS2026_TEST1_L6_Q135-138"
  ]
}
```

**Fields:**
- `section_id`: `"P5"`, `"P6"`, `"P7"` (Reading) hoặc `"P1"`, `"P2"`, `"P3"`, `"P4"` (Listening)
- `type`: Loại section (optional)
- `instruction`: Hướng dẫn hiển thị (optional)
- `question_numbers`: Array số câu hỏi (cho Part 5)
- `passage_ids`: Array passage_id (cho Part 6, 7)

---

## 📄 Passages

Mỗi passage định nghĩa một đoạn văn (Reading) hoặc conversation/talk (Listening).

### Reading Passage (Part 6, 7)

```json
{
  "passage_id": "READING_ETS2026_TEST1_L6_Q131-134",
  "section_id": "P6",
  "type": "flyer",
  "instruction": "Questions 131-134 refer to the following flyer.",
  "question_numbers": [131, 132, 133, 134],
  "assets": [
    {
      "kind": "image",
      "url": "https://example.com/assets/READING_ETS2026_TEST1_L6_Q131-134.png"
    }
  ],
  "text": "Sample flyer content with blanks (131)-(134) shown in the image asset.",
  "meta": {
    "question_range": [131, 134],
    "source": "ETS2026"
  }
}
```

**Fields:**
- `passage_id`: ID unique (bắt buộc)
- `section_id`: `"P6"` hoặc `"P7"` (bắt buộc)
- `type`: Loại passage (flyer, letter, email, notice, ...) (optional)
- `instruction`: Hướng dẫn hiển thị (optional)
- `question_numbers`: Array số câu hỏi trong passage này (optional)
- `assets`: Array assets (bắt buộc nếu có image)
  - `kind`: `"image"` hoặc `"audio"`
  - `url`: URL của asset
- `text`: Nội dung passage (optional)
- `meta`: Object metadata (optional)

### Listening Conversation (Part 3, 4)

```json
{
  "passage_id": "CONV_1",
  "section_id": "P3",
  "type": "conversation",
  "instruction": "Questions 32-34 refer to the following conversation.",
  "question_numbers": [32, 33, 34],
  "assets": [
    {
      "kind": "audio",
      "url": "https://example.com/audio/conv1.mp3"
    }
  ],
  "text": "Man: Good morning. I'd like to...",
  "meta": {
    "question_range": [32, 34]
  }
}
```

**Fields:** Tương tự Reading Passage, nhưng:
- `section_id`: `"P3"` hoặc `"P4"`
- `assets`: Thường có `kind: "audio"` thay vì `"image"`

---

## ❓ Questions

Mỗi question định nghĩa một câu hỏi trong đề thi.

### Reading Part 5 (Single Blank Sentence)

```json
{
  "question_id": "READING_ETS2026_TEST1_Q126",
  "number": 126,
  "section_id": "P5",
  "passage_id": null,
  "question_type": "single_blank_sentence",
  "stem": "With its fixed price ------, Omega Cellular guarantees no phone bill increases for three years.",
  "choices": [
    { "key": "A", "text": "assurance" },
    { "key": "B", "text": "assuredly" },
    { "key": "C", "text": "assuring" },
    { "key": "D", "text": "assures" }
  ],
  "answer_key": "A",
  "explanation": "Placeholder explanation",
  "meta": {}
}
```

### Reading Part 6, 7 (Passage Blank)

```json
{
  "question_id": "READING_ETS2026_TEST1_Q131",
  "number": 131,
  "section_id": "P6",
  "passage_id": "READING_ETS2026_TEST1_L6_Q131-134",
  "question_type": "passage_blank",
  "blank_ref": { "blank_number_in_passage": 131 },
  "stem": "Select the best option to fill blank (131) in the flyer.",
  "choices": [
    { "key": "A", "text": "Staff members have written articles..." },
    { "key": "B", "text": "Installing lights can enhance..." },
    { "key": "C", "text": "Local competitors cannot beat..." },
    { "key": "D", "text": "Riessler Landscaping's goal is to make your vision a reality." }
  ],
  "answer_key": "D",
  "explanation": "Placeholder explanation",
  "meta": {}
}
```

**Fields:**
- `question_id`: ID unique (optional, chỉ để debug)
- `number`: Số thứ tự câu hỏi trong đề (bắt buộc)
- `section_id`: `"P5"`, `"P6"`, `"P7"` (Reading) hoặc `"P1"`-`"P4"` (Listening) (bắt buộc)
- `passage_id`: ID của passage/conversation (null cho Part 5, bắt buộc cho Part 6, 7, 3, 4)
- `question_type`: Loại câu hỏi (optional)
  - `"single_blank_sentence"` (Part 5)
  - `"passage_blank"` (Part 6, 7)
  - `"passage_sentence_choice"` (Part 6, 7)
- `stem`: Nội dung câu hỏi (optional)
- `blank_ref`: Reference đến blank trong passage (optional, cho Part 6)
- `choices`: Array 4 options (bắt buộc)
  - `key`: `"A"`, `"B"`, `"C"`, hoặc `"D"`
  - `text`: Nội dung option
- `answer_key`: `"A"`, `"B"`, `"C"`, hoặc `"D"` (bắt buộc)
- `explanation`: Giải thích (optional)
- `meta`: Object metadata (optional)

---

## 🖼️ Hỗ trợ Assets từ URL

### Download tự động

Hệ thống sẽ tự động download:
- **Images** từ `passages[].assets[].url` (cho Reading passages)
- **Audio files** từ `passages[].assets[].url` (cho Listening conversations)

**Lưu ý**:
- URL phải là URL hợp lệ (http:// hoặc https://)
- Images sẽ được lưu vào: `exam/dokkai_passages/`
- Audio sẽ được lưu vào: `exam/toeic/listening/`
- Nếu download thất bại, record vẫn được tạo nhưng không có image/audio

---

## ⚠️ Lưu ý quan trọng

1. **schema_version phải là "1.0"**: Format cũ không còn được hỗ trợ
2. **module phải đúng**: `"READING"` hoặc `"LISTENING"`
3. **section_id phải hợp lệ**: P5/P6/P7 (Reading) hoặc P1-P4 (Listening)
4. **passage_id phải match**: `questions[].passage_id` phải tồn tại trong `passages[]`
5. **answer_key bắt buộc**: Tất cả questions phải có `answer_key` ("A", "B", "C", hoặc "D")
6. **choices phải đủ 4 options**: Mỗi question phải có đúng 4 choices với key "A", "B", "C", "D"
7. **number phải unique**: Không được trùng số câu hỏi trong cùng một module

---

## 📊 Mapping Section ID → TOEIC Part

| section_id | TOEIC Part | Mô tả |
|------------|------------|-------|
| P1 | L1 | Listening Part 1: Mô tả hình ảnh |
| P2 | L2 | Listening Part 2: Câu hỏi-Đáp án |
| P3 | L3 | Listening Part 3: Hội thoại ngắn |
| P4 | L4 | Listening Part 4: Bài nói ngắn |
| P5 | R5 | Reading Part 5: Điền từ vào câu |
| P6 | R6 | Reading Part 6: Điền từ vào đoạn văn |
| P7 | R7 | Reading Part 7: Đọc hiểu |

---

## 🔄 Auto-update Category

Hệ thống sẽ **tự động cập nhật category** khi import:

1. **Ban đầu chỉ có Reading** (P5, P6, P7):
   - Category → `READING`
   - `is_full_toeic` → `False`

2. **Ban đầu chỉ có Listening** (P1, P2, P3, P4):
   - Category → `LISTENING`
   - `is_full_toeic` → `False`

3. **Sau khi import đủ cả Listening VÀ Reading**:
   - Category → `TOEIC_FULL` (tự động)
   - `is_full_toeic` → `True` (tự động)
   - Hiển thị thông báo: "Category đã tự động cập nhật: READING → TOEIC Full Test"

---

## 📚 Ví dụ đầy đủ

Xem file `JSON_FORMAT_COMPARISON.md` để xem ví dụ JSON đầy đủ cho cả Reading và Listening.

---

## ✅ Checklist trước khi import

- [ ] JSON có `schema_version: "1.0"`
- [ ] JSON có `module: "READING"` hoặc `"LISTENING"`
- [ ] JSON có `sections[]` với ít nhất 1 section
- [ ] JSON có `passages[]` (có thể rỗng nếu Part 5)
- [ ] JSON có `questions[]` với ít nhất 1 question
- [ ] Tất cả questions có `answer_key` ("A", "B", "C", hoặc "D")
- [ ] Tất cả questions có `section_id` hợp lệ
- [ ] Questions có `passage_id` phải match với `passages[].passage_id`
- [ ] Image/Audio URLs (nếu có) phải là URL hợp lệ

---

## 🐛 Troubleshooting

### Lỗi: "Unsupported schema_version"
- **Nguyên nhân**: JSON không có `schema_version: "1.0"`
- **Giải pháp**: Thêm `"schema_version": "1.0"` vào JSON

### Lỗi: "Invalid module"
- **Nguyên nhân**: `module` không phải `"READING"` hoặc `"LISTENING"`
- **Giải pháp**: Sửa `module` thành `"READING"` hoặc `"LISTENING"`

### Lỗi: "Question references unknown passage_id"
- **Nguyên nhân**: `questions[].passage_id` không tồn tại trong `passages[]`
- **Giải pháp**: Kiểm tra `passage_id` trong questions phải match với `passages[].passage_id`

### Lỗi: "Question missing or invalid 'answer_key'"
- **Nguyên nhân**: Question không có `answer_key` hoặc `answer_key` không phải "A"/"B"/"C"/"D"
- **Giải pháp**: Thêm `answer_key` với giá trị hợp lệ

---

## 📝 Tóm tắt

| Khái niệm | Giải thích |
|-----------|------------|
| **schema_version** | Phải là "1.0" |
| **module** | "READING" hoặc "LISTENING" |
| **sections** | Định nghĩa các phần trong đề (P5/P6/P7 hoặc P1-P4) |
| **passages** | Định nghĩa các đoạn văn/conversations |
| **questions** | Tất cả các câu hỏi trong đề |
| **section_id** | P5/P6/P7 (Reading) hoặc P1-P4 (Listening) |
| **passage_id** | ID unique của passage/conversation |
| **answer_key** | "A", "B", "C", hoặc "D" (bắt buộc) |
| **choices** | Array 4 options với key "A"/"B"/"C"/"D" |

---

**Kết luận**: Format mới (schema_version 1.0) hỗ trợ metadata đầy đủ, import cả module một lần, và cấu trúc rõ ràng hơn format cũ.
