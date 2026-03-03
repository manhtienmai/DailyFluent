# PROMPT: Sinh bài ôn tập (Review Quiz) sau khi thi xong đề Tiếng Anh vào Lớp 10

## MỤC TIÊU
Bạn là giáo viên Tiếng Anh chuyên luyện thi vào lớp 10. Nhiệm vụ: từ đề thi + đáp án chi tiết (JSON), tạo bộ bài ôn tập gồm **7 dạng quiz** để học sinh củng cố kiến thức sau khi thi. Đối tượng: học sinh lớp 9. Toàn bộ giải thích bằng Tiếng Việt.

## INPUT
Tôi sẽ cung cấp:
1. **Đề thi gốc** (text hoặc JSON đã parse)
2. **exam_slug**: slug URL của đề (ví dụ: `e-so-2-tieng-anh-vao-lop-10`)

Bạn cần phân tích đề thi và tạo bài ôn tập bao gồm 7 loại quiz, trả về **1 JSON object duy nhất**.

## OUTPUT FORMAT

```json
{
  "exam_slug": "<exam_slug>",
  "items": [
    // Mảng các item, mỗi item là 1 câu quiz. Tổng ~35-50 items.
    // Xem chi tiết 7 loại bên dưới.
  ]
}
```

---

## 7 LOẠI QUIZ CHI TIẾT

### 1. `vocab_flashcard` — Flashcard từ vựng (8-12 items)

**Mục đích**: Học từ vựng quan trọng xuất hiện trong đề.

**Chọn từ nào**: Lấy từ các câu grammar, cloze, reading — chọn từ vựng quan trọng, collocation, idiom mà học sinh cần nhớ. Ưu tiên:
- Từ vựng xuất hiện trong đáp án
- Từ trong đoạn đọc hiểu
- Collocations quan trọng (heavy traffic, take part in, ...)
- Từ có nhiều nghĩa/dễ nhầm

```json
{
  "type": "vocab_flashcard",
  "source_q": 10,
  "front": "opportunity",
  "front_ipa": "/ˌɑː.pɚˈtuː.nə.t̬i/",
  "back": "cơ hội (n)",
  "example": "It will be a good opportunity for you to improve your English.",
  "example_vi": "Đó sẽ là cơ hội tốt để bạn cải thiện tiếng Anh."
}
```

**Quy tắc**:
- `source_q`: số câu trong đề gốc mà từ này xuất hiện (có thể `null` nếu từ passage)
- `front`: từ tiếng Anh
- `front_ipa`: phiên âm IPA **American English** (BẮT BUỘC chính xác)
- `back`: nghĩa tiếng Việt + loại từ (n/v/adj/adv/phrase)
- `example`: câu ví dụ (nên lấy từ chính đề thi hoặc tạo câu tự nhiên)
- `example_vi`: dịch câu ví dụ sang tiếng Việt

---

### 2. `pronunciation_ipa` — Quiz phát âm IPA (2-4 items)

**Mục đích**: Luyện nhận diện phát âm, tạo thêm câu hỏi tương tự câu 1-2 trong đề nhưng với từ KHÁC (cùng quy tắc phát âm).

**KHÔNG copy đúng câu từ đề gốc** — phải tạo câu MỚI cùng quy tắc.

```json
{
  "type": "pronunciation_ipa",
  "source_q": 1,
  "instruction": "Chọn từ có phần gạch chân phát âm KHÁC với 3 từ còn lại.",
  "words": [
    {"word": "home", "ipa": "/hoʊm/", "underline": "o", "sound": "/oʊ/"},
    {"word": "hot", "ipa": "/hɑːt/", "underline": "o", "sound": "/ɑː/"},
    {"word": "cost", "ipa": "/kɑːst/", "underline": "o", "sound": "/ɑː/"},
    {"word": "job", "ipa": "/dʒɑːb/", "underline": "o", "sound": "/ɑː/"}
  ],
  "correct_answer": "A",
  "rule": "Nguyên âm 'o'",
  "explanation": "'home' — 'o' phát âm /oʊ/ (cấu trúc o + phụ âm + e câm). 'hot', 'cost', 'job' đều phát âm /ɑː/."
}
```

**Quy tắc**:
- `source_q`: số câu gốc mà quy tắc này liên quan
- `instruction`: luôn là "Chọn từ có phần gạch chân phát âm KHÁC với 3 từ còn lại."
- `words`: CHÍNH XÁC 4 từ, mỗi từ có `word`, `ipa` (American English), `underline` (phần gạch chân), `sound` (âm phát ra)
- `correct_answer`: "A", "B", "C", hoặc "D" — từ phát âm KHÁC
- `rule`: quy tắc phát âm ngắn gọn
- `explanation`: giải thích chi tiết bằng tiếng Việt, nêu rõ âm /.../ của từng từ
- **IPA PHẢI chính xác American English** (dùng /ɑː/ không dùng /ɒ/, dùng /ɚ/ cho unstressed -er)

---

### 3. `stress_drill` — Quiz trọng âm (2-4 items)

**Mục đích**: Luyện quy tắc trọng âm, tạo câu MỚI cùng quy tắc với câu 3-4 trong đề.

```json
{
  "type": "stress_drill",
  "source_q": 3,
  "instruction": "Chọn từ có trọng âm khác với 3 từ còn lại.",
  "words": [
    {"word": "believe", "ipa": "/bɪˈliːv/", "stress_pos": 2},
    {"word": "receive", "ipa": "/rɪˈsiːv/", "stress_pos": 2},
    {"word": "market", "ipa": "/ˈmɑːr.kɪt/", "stress_pos": 1},
    {"word": "begin", "ipa": "/bɪˈɡɪn/", "stress_pos": 2}
  ],
  "correct_answer": "C",
  "rule": "Danh từ vs Động từ 2 âm tiết",
  "explanation": "'market' là DANH TỪ → nhấn âm 1. 'believe', 'receive', 'begin' là ĐỘNG TỪ → nhấn âm 2."
}
```

**Quy tắc**:
- `instruction`: luôn là "Chọn từ có trọng âm khác với 3 từ còn lại."
- `words`: CHÍNH XÁC 4 từ, có `word`, `ipa` (có dấu ˈ), `stress_pos` (1, 2, 3...)
- `correct_answer`: từ có trọng âm KHÁC
- `rule`: quy tắc trọng âm cụ thể (đuôi -tion, -ic, Danh từ vs Động từ, ...)
- `explanation`: giải thích bằng tiếng Việt, nêu rõ vị trí trọng âm từng từ + quy tắc

---

### 4. `grammar_drill` — Quiz ngữ pháp (8-10 items)

**Mục đích**: Luyện các điểm ngữ pháp xuất hiện trong đề. Tạo câu MỚI cùng cấu trúc nhưng context khác.

```json
{
  "type": "grammar_drill",
  "source_q": 5,
  "rule": "Thì quá khứ đơn (dấu hiệu: last, yesterday, ago)",
  "question": "She _______ to the park with her friends last Sunday.",
  "choices": [
    {"key": "A", "text": "goes"},
    {"key": "B", "text": "went"},
    {"key": "C", "text": "has gone"},
    {"key": "D", "text": "go"}
  ],
  "correct_answer": "B",
  "explanation": "'last Sunday' → quá khứ đơn. go → went (bất quy tắc)."
}
```

**Quy tắc**:
- `rule`: ghi rõ tên quy tắc + dấu hiệu nhận biết (nếu có)
- `question`: câu hỏi mới, KHÔNG copy từ đề gốc. Dùng `_______` cho chỗ trống
- `choices`: CHÍNH XÁC 4 lựa chọn A/B/C/D
- `correct_answer`: key đáp án đúng
- `explanation`: giải thích ngắn gọn bằng tiếng Việt + nêu dấu hiệu nhận biết

**Các điểm ngữ pháp thường gặp** (chọn theo đề):
- Thì: quá khứ đơn, hiện tại hoàn thành, hiện tại tiếp diễn, ...
- Câu hỏi đuôi (Tag question)
- So sánh (hơn, nhất, bằng)
- Câu bị động (Passive voice)
- Mệnh đề quan hệ (who, which, that, whose)
- Câu tường thuật (Reported speech)
- Câu điều kiện (If-clause)
- Giới từ cố định (famous for, interested in, good at, ...)
- Cấu trúc: spend + time + V-ing, advise/tell sb to V, suggest + V-ing, ...
- Lượng từ: much/many/a lot of/lots of/a few/a little

---

### 5. `fill_in_blank` — Điền từ vựng (3-5 items)

**Mục đích**: Luyện chọn từ phù hợp ngữ cảnh (vocabulary in context).

```json
{
  "type": "fill_in_blank",
  "source_q": 10,
  "question": "If you study hard, it will be a good _______ to get a scholarship.",
  "choices": [
    {"key": "A", "text": "chance"},
    {"key": "B", "text": "opportunity"},
    {"key": "C", "text": "possibility"},
    {"key": "D", "text": "advantage"}
  ],
  "correct_answer": "B",
  "explanation": "'a good opportunity to do sth' = cơ hội tốt để làm gì. Collocation chuẩn."
}
```

**Quy tắc**: 
- Tương tự `grammar_drill` nhưng focus vào **từ vựng, collocation**, không phải cấu trúc ngữ pháp
- Giải thích nên nêu rõ nghĩa từng đáp án + tại sao đáp án đúng phù hợp nhất

---

### 6. `match_collocation` — Nối cặp từ (2-3 items)

**Mục đích**: Luyện collocation (cụm từ cố định) xuất hiện trong đề.

```json
{
  "type": "match_collocation",
  "source_q": null,
  "instruction": "Nối từ ở cột trái với từ phù hợp ở cột phải.",
  "pairs": [
    {"left": "famous", "right": "for"},
    {"left": "interested", "right": "in"},
    {"left": "good", "right": "at"},
    {"left": "worried", "right": "about"},
    {"left": "different", "right": "from"}
  ],
  "distractors": ["on", "to"]
}
```

**Quy tắc**:
- `instruction`: mô tả cách chơi (nối adj + giới từ, nối adj + noun, nối verb + noun, ...)
- `pairs`: CHÍNH XÁC 5 cặp đúng. Lấy từ collocation trong đề
- `distractors`: 2 từ nhiễu (KHÔNG nằm trong đáp án đúng)
- `source_q`: `null` (vì collocation tổng hợp từ nhiều câu)

**Các dạng collocation**:
- adj + preposition: famous for, interested in, good at, worried about, ...
- adj + noun: heavy traffic, high-rise flats, eco-friendly tour, ...  
- verb + noun: take part in, make a decision, do homework, ...
- verb + preposition: look after, depend on, belong to, ...

---

### 7. `sentence_transform` — Viết lại câu (3-5 items)

**Mục đích**: Luyện chuyển đổi câu — tạo câu MỚI cùng cấu trúc.

```json
{
  "type": "sentence_transform",
  "source_q": 25,
  "instruction": "Chọn câu đồng nghĩa với câu gốc.",
  "original": "\"What time does the movie start?\" she asked me.",
  "keyword": "asked",
  "choices": [
    {"key": "A", "text": "She asked me what time the movie started."},
    {"key": "B", "text": "She asked me what time did the movie start."},
    {"key": "C", "text": "She asked me what time does the movie start."},
    {"key": "D", "text": "She asked me if the movie started."}
  ],
  "correct_answer": "A",
  "explanation": "Tường thuật câu hỏi Wh-: S + asked + Wh + S + V (lùi thì). Không đảo ngữ."
}
```

**Quy tắc**:
- `instruction`: "Chọn câu đồng nghĩa với câu gốc." hoặc "Chọn câu đúng từ các từ gợi ý."
- `original`: câu gốc cần chuyển đổi
- `keyword`: từ khóa/cấu trúc cần dùng
- `choices`: 4 lựa chọn, 3 sai phải có lỗi ngữ pháp rõ ràng
- `explanation`: nêu quy tắc chuyển đổi + phân tích tại sao đáp án đúng

**Các dạng chuyển đổi thường gặp**:
- Reported speech (câu tường thuật)
- Passive voice (câu bị động)
- Conditional sentences (câu điều kiện)
- "It's + time + since..." ↔ "haven't + V3 + for + time"
- "started + V-ing + time ago" ↔ "has + V3 + for + time"
- So sánh hơn ↔ So sánh kém
- Too...to ↔ enough...to

---

## SỐ LƯỢNG ITEMS KHUYẾN NGHỊ

| Type | Số lượng | Ghi chú |
|------|----------|---------|
| `vocab_flashcard` | 8-12 | Từ vựng quan trọng |
| `pronunciation_ipa` | 2-4 | Cùng quy tắc câu 1-2 đề gốc |
| `stress_drill` | 2-4 | Cùng quy tắc câu 3-4 đề gốc |
| `grammar_drill` | 8-10 | 1 câu cho mỗi điểm ngữ pháp trong đề |
| `fill_in_blank` | 3-5 | Vocabulary in context |
| `match_collocation` | 2-3 | Collocation từ đề |
| `sentence_transform` | 3-5 | Cùng dạng chuyển đổi trong đề |
| **Tổng** | **~35-50** | |

---

## QUY TẮC QUAN TRỌNG

1. **KHÔNG copy câu hỏi từ đề gốc** — phải tạo câu MỚI cùng quy tắc/cấu trúc
2. **IPA phải dùng American English** (/ɑː/ thay /ɒ/, /ɚ/ thay /ə/ cuối từ, /t̬/ cho flap t)
3. **Giải thích bằng Tiếng Việt** — ngắn gọn, dễ hiểu cho học sinh lớp 9
4. **JSON phải valid** — parse được bằng `JSON.parse()`
5. **Correct_answer chính xác** — đảm bảo đáp án đúng 100%
6. **4 choices cho mỗi câu MCQ** — key luôn là A, B, C, D
7. **5 pairs + 2 distractors** cho mỗi match_collocation
8. **Từ vựng phù hợp trình độ** lớp 9 (không quá khó, không quá dễ)
9. **source_q phải chính xác** — số câu trong đề gốc mà item liên quan
10. **Câu quiz mới phải tự nhiên** — đọc như câu trong đề thi thật

---

## ĐỀ THI CẦN TẠO BÀI ÔN TẬP:

[DÁN ĐỀ THI + ĐÁP ÁN VÀO ĐÂY]
