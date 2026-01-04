# 📊 So sánh JSON Format: Cũ vs Mới

## Format hiện tại (Cũ)

### Cấu trúc:
```json
{
  "part": "R5",  // hoặc R6, R7
  "questions": [...]  // hoặc "passages": [...]
}
```

### Đặc điểm:
- ✅ **Đơn giản**: Mỗi part import riêng
- ✅ **Dễ hiểu**: Structure rõ ràng theo từng part
- ✅ **Nhẹ**: Ít nested data
- ❌ **Thiếu metadata**: Không có instruction, type, explanation
- ❌ **Không có sections**: Không có concept "section" rõ ràng
- ❌ **Assets riêng lẻ**: Image URL trong từng question/passage

---

## Format mới (Đề xuất)

### Cấu trúc:
```json
{
  "schema_version": "1.0",
  "test_id": "READING_ETS2026_TEST1",
  "module": "READING",
  "sections": [
    {
      "section_id": "P5",
      "type": "incomplete_sentences",
      "instruction": "...",
      "question_numbers": [126, 127, ...]
    }
  ],
  "passages": [...],
  "questions": [...]
}
```

### Đặc điểm:
- ✅ **Cấu trúc rõ ràng**: Có sections, passages, questions tách biệt
- ✅ **Metadata phong phú**: instruction, type, explanation, meta
- ✅ **Assets tập trung**: Có thể quản lý assets trong passages
- ✅ **Blank reference**: Có `blank_ref` cho Part 6 (blank_number_in_passage)
- ✅ **Question types chi tiết**: single_blank_sentence, passage_blank, passage_sentence_choice
- ✅ **Import một lần**: Có thể import cả Reading (P5+P6+P7) trong 1 file
- ❌ **Phức tạp hơn**: Nhiều nested data, cần mapping nhiều
- ❌ **Mapping phức tạp**: Cần map section_id → toeic_part, passage_id → ReadingPassage

---

## So sánh chi tiết

| Tiêu chí | Format Cũ | Format Mới |
|----------|-----------|------------|
| **Import từng part** | ✅ Dễ (1 file = 1 part) | ⚠️ Phức tạp hơn (1 file = nhiều sections) |
| **Import cả Reading** | ❌ Phải import 3 lần (R5, R6, R7) | ✅ Import 1 lần (P5+P6+P7) |
| **Metadata** | ❌ Thiếu (không có instruction, type) | ✅ Đầy đủ (instruction, type, explanation) |
| **Assets** | ⚠️ Rải rác trong questions/passages | ✅ Tập trung trong passages.assets[] |
| **Blank reference** | ❌ Không có | ✅ Có blank_ref cho Part 6 |
| **Question types** | ⚠️ Chỉ biết qua part | ✅ Rõ ràng (single_blank_sentence, passage_blank, ...) |
| **Mapping DB** | ✅ Đơn giản (part → toeic_part) | ⚠️ Phức tạp (section_id → toeic_part, passage_id → ReadingPassage) |
| **Backward compatibility** | ✅ Hiện tại | ❌ Không tương thích |

---

## Đề xuất: Hybrid Approach (Tối ưu nhất)

### Option 1: Hỗ trợ cả 2 format (Khuyến nghị)

**Ưu điểm**:
- ✅ Backward compatible với format cũ
- ✅ Hỗ trợ format mới cho nhu cầu phức tạp
- ✅ User có thể chọn format phù hợp

**Cách làm**:
1. Detect format dựa trên keys:
   - Format cũ: Có `"part"` và (`"questions"` hoặc `"passages"`)
   - Format mới: Có `"sections"`, `"passages"`, `"questions"` ở top level
2. Route đến handler tương ứng:
   - Format cũ → `import_toeic_json_legacy()`
   - Format mới → `import_toeic_json_v2()`

### Option 2: Chỉ hỗ trợ format mới

**Ưu điểm**:
- ✅ Code đơn giản hơn (chỉ 1 format)
- ✅ Metadata đầy đủ

**Nhược điểm**:
- ❌ Breaking change: Phải convert tất cả JSON cũ
- ❌ User phải học format mới

---

## Mapping Format Mới → Database

### Sections → TOEIC Parts:
```python
SECTION_TO_PART = {
    "P5": "R5",  # Reading Part 5
    "P6": "R6",  # Reading Part 6
    "P7": "R7",  # Reading Part 7
    "P1": "L1",  # Listening Part 1 (nếu có)
    "P2": "L2",  # Listening Part 2
    "P3": "L3",  # Listening Part 3
    "P4": "L4",  # Listening Part 4
}
```

### Passages → ReadingPassage:
```python
# Tạo ReadingPassage từ passage data
passage = ReadingPassage.objects.create(
    template=template,
    order=passage_data.get("order", 1),
    title=passage_data.get("instruction", ""),  # hoặc từ meta
    text=passage_data.get("text", ""),
    # Download image từ assets[0].url nếu có
)
```

### Questions → ExamQuestion:
```python
# Map question data
question = ExamQuestion.objects.create(
    template=template,
    toeic_part=SECTION_TO_PART[q_data["section_id"]],
    order=q_data["number"],  # hoặc q_data["number"]
    text=q_data.get("stem", ""),  # stem → text
    question_type=QuestionType.MCQ,
    data={"choices": q_data["choices"]},
    correct_answer=q_data["answer_key"],  # answer_key → correct_answer
    explanation_vi=q_data.get("explanation", ""),
    passage=passage if q_data.get("passage_id") else None,
)
```

---

## Code Changes Cần Thiết

### 1. Thêm function detect format:
```python
def detect_json_format(json_data: Dict) -> str:
    """Detect JSON format: 'legacy' or 'v2'"""
    if "sections" in json_data and "passages" in json_data:
        return "v2"
    elif "part" in json_data:
        return "legacy"
    else:
        raise ValueError("Unknown JSON format")
```

### 2. Thêm handler cho format mới:
```python
def import_toeic_json_v2(template: ExamTemplate, json_data: Dict) -> Dict[str, any]:
    """
    Import TOEIC từ format mới (có sections, passages, questions).
    """
    # 1. Parse sections → map to parts
    # 2. Create passages từ passages[]
    # 3. Create questions từ questions[] → link to passages
    # 4. Download assets từ passages[].assets[]
    pass
```

### 3. Update import_toeic_json() để route:
```python
def import_toeic_json(template: ExamTemplate, json_data: Dict) -> Dict[str, any]:
    format_type = detect_json_format(json_data)
    
    if format_type == "v2":
        return import_toeic_json_v2(template, json_data)
    else:
        return import_toeic_json_legacy(template, json_data)
```

---

## Kết luận & Khuyến nghị

### ✅ Nên làm:
1. **Hỗ trợ cả 2 format** (Hybrid Approach):
   - Giữ format cũ để backward compatible
   - Thêm format mới cho nhu cầu phức tạp
   - Auto-detect format khi import

2. **Ưu tiên format mới**:
   - Format mới tốt hơn cho metadata, assets, và import cả Reading một lần
   - Nhưng vẫn hỗ trợ format cũ để không breaking change

3. **Cải thiện dần**:
   - Bắt đầu với hybrid approach
   - Sau đó có thể deprecate format cũ nếu không còn dùng

### ❌ Không nên:
- Chỉ hỗ trợ format mới ngay (breaking change)
- Bỏ format cũ hoàn toàn (mất backward compatibility)

---

## Next Steps

1. ✅ Implement `detect_json_format()`
2. ✅ Implement `import_toeic_json_v2()` cho format mới
3. ✅ Rename `import_toeic_json()` hiện tại thành `import_toeic_json_legacy()`
4. ✅ Update `import_toeic_json()` để route đến handler phù hợp
5. ✅ Update documentation với cả 2 format
6. ✅ Test với cả 2 format

