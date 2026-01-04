# Enhanced Vocabulary Fields - Chi tiết các field mới

## Tổng quan

Đã thêm các field mới vào `EnglishVocabulary` và `EnglishVocabularyExample` để lưu đầy đủ dữ liệu từ JSON format mới.

---

## EnglishVocabulary - Các field mới

### 1. `pos` (Part of Speech)
- **Type**: `CharField(max_length=50)`
- **Description**: Từ loại của từ vựng (noun, verb, adjective, adverb, etc.)
- **Example**: `"adverb"`, `"noun"`, `"adjective"`
- **Mapping từ JSON**: `word.pos`

### 2. `pos_candidates`
- **Type**: `JSONField(default=list)`
- **Description**: Danh sách các từ loại có thể của từ vựng (JSON array)
- **Example**: `["adverb", "adjective"]`
- **Mapping từ JSON**: `word.pos_candidates`

### 3. `audio_pack_uuid`
- **Type**: `CharField(max_length=100)`
- **Description**: UUID của audio pack để tải về sau
- **Example**: `"209e9163-1c19-461b-beb9-81415a8d11cf"`
- **Mapping từ JSON**: `word.audio_pack_uuid`

---

## EnglishVocabularyExample - Các field mới

### 1. `sentence_marked`
- **Type**: `TextField`
- **Description**: Câu ví dụ với từ vựng được đánh dấu (ví dụ: `⟦word⟧`)
- **Example**: `"The system downloaded updates ⟦overnight⟧ and applied them..."`
- **Mapping từ JSON**: `examples[].sentence_marked`

### 2. `sentence_en`
- **Type**: `TextField`
- **Description**: Câu ví dụ tiếng Anh không có đánh dấu (plain text)
- **Example**: `"The system downloaded updates overnight and applied them..."`
- **Mapping từ JSON**: `examples[].sentence_en`

### 3. `context`
- **Type**: `CharField(max_length=200)`
- **Description**: Ngữ cảnh sử dụng từ vựng
- **Example**: `"system update"`, `"order processing"`, `"shift safety"`
- **Mapping từ JSON**: `examples[].context`

### 4. `word_count`
- **Type**: `PositiveIntegerField(null=True, blank=True)`
- **Description**: Số từ trong câu ví dụ
- **Example**: `14`, `16`, `20`
- **Mapping từ JSON**: `examples[].word_count`

---

## Mapping JSON → Database

### EnglishVocabulary

| JSON Field | Database Field | Notes |
|------------|---------------|-------|
| `word` | `en_word` | ✓ |
| `meaning_vn` | `vi_meaning` | ✓ |
| `definition_en_simple` | `en_definition` | ✓ |
| `pronunciation_uk_ipa` | `phonetic` | ✓ |
| `pos` | `pos` | **NEW** |
| `pos_candidates` | `pos_candidates` | **NEW** (JSON array) |
| `audio_pack_uuid` | `audio_pack_uuid` | **NEW** |
| `notes` | `notes` | ✓ (optional) |

### EnglishVocabularyExample

| JSON Field | Database Field | Notes |
|------------|---------------|-------|
| `order` | `order` | ✓ |
| `sentence_marked` | `sentence_marked` | **NEW** |
| `sentence_en` | `sentence_en` | **NEW** |
| `context` | `context` | **NEW** |
| `word_count` | `word_count` | **NEW** |
| `vi` | `vi` | ✓ (optional, fallback to `[context]` if empty) |

**Lưu ý**: 
- Nếu `sentence_marked` có giá trị, nó sẽ được lưu vào `sentence_marked` và `en` (để backward compatibility)
- Nếu không có `sentence_marked`, `sentence_en` sẽ được dùng cho cả `sentence_en` và `en`
- Nếu không có `vi`, hệ thống sẽ tự động tạo từ `context`: `"[context]"`

---

## Migration

File migration: `vocab/migrations/0015_add_enhanced_vocab_fields.py`

**Để chạy migration:**
```bash
python manage.py migrate vocab
```

---

## Import Logic

Import function (`vocab/admin.py`) đã được cập nhật để:

1. **Lưu đầy đủ dữ liệu vào các field mới:**
   - `pos`, `pos_candidates`, `audio_pack_uuid` vào `EnglishVocabulary`
   - `sentence_marked`, `sentence_en`, `context`, `word_count` vào `EnglishVocabularyExample`

2. **Backward compatibility:**
   - Vẫn hỗ trợ format cũ (`en_word`, `vi_meaning`, `examples[].en`, `examples[].vi`)
   - Tự động convert và lưu vào các field mới

3. **Auto-fill logic:**
   - Nếu không có `sentence_marked`, dùng `sentence_en`
   - Nếu không có `vi`, dùng `[context]` làm fallback
   - `word_count` được convert sang integer tự động

---

## Admin Interface

### EnglishVocabularyAdmin
- **list_display**: Thêm `pos` vào danh sách hiển thị
- **list_filter**: Thêm `pos` vào filter
- **search_fields**: Thêm `pos`, `audio_pack_uuid` vào search

### EnglishVocabularyExampleInline
- **fields**: Hiển thị các field mới: `sentence_marked`, `sentence_en`, `context`, `word_count`
- Các field cũ (`en`, `vi`) vẫn được giữ để backward compatibility

---

## Ví dụ Import

### JSON Input:
```json
{
  "word": "overnight",
  "pos": "adverb",
  "pos_candidates": ["adverb", "adjective"],
  "meaning_vn": "qua đêm",
  "definition_en_simple": "in a way that happens during the night",
  "pronunciation_uk_ipa": "/ˌəʊvəˈnaɪt/",
  "examples": [
    {
      "order": 1,
      "context": "system update",
      "sentence_marked": "The system downloaded updates ⟦overnight⟧ and applied them...",
      "sentence_en": "The system downloaded updates overnight and applied them...",
      "word_count": 14
    }
  ],
  "audio_pack_uuid": "209e9163-1c19-461b-beb9-81415a8d11cf"
}
```

### Database Result:

**EnglishVocabulary:**
- `en_word`: `"overnight"`
- `pos`: `"adverb"`
- `pos_candidates`: `["adverb", "adjective"]`
- `vi_meaning`: `"qua đêm"`
- `en_definition`: `"in a way that happens during the night"`
- `phonetic`: `"/ˌəʊvəˈnaɪt/"`
- `audio_pack_uuid`: `"209e9163-1c19-461b-beb9-81415a8d11cf"`

**EnglishVocabularyExample (1):**
- `order`: `1`
- `sentence_marked`: `"The system downloaded updates ⟦overnight⟧ and applied them..."`
- `sentence_en`: `"The system downloaded updates overnight and applied them..."`
- `en`: `"The system downloaded updates ⟦overnight⟧ and applied them..."` (backward compatibility)
- `context`: `"system update"`
- `word_count`: `14`
- `vi`: `""` (empty, sẽ hiển thị `[system update]` nếu cần)

---

## Kết luận

Tất cả dữ liệu từ JSON format mới đã được lưu đầy đủ vào database với các field chuyên dụng, không còn phải lưu vào `notes` nữa. Hệ thống vẫn hỗ trợ format cũ để đảm bảo backward compatibility.

