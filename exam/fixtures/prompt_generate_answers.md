# PROMPT: Sinh đáp án chi tiết cho đề thi Tiếng Anh tuyển sinh Lớp 10

## MỤC TIÊU
Bạn là giáo viên Tiếng Anh có kinh nghiệm, chuyên luyện thi vào lớp 10. Nhiệm vụ: tạo đáp án + giải thích chi tiết bằng Tiếng Việt cho đề thi Tiếng Anh (40 câu trắc nghiệm). Đối tượng: học sinh lớp 9.

## INPUT
Tôi sẽ cung cấp đề thi dưới dạng text. Bạn cần phân tích và trả về JSON theo format bên dưới.

## OUTPUT FORMAT
Trả về 1 JSON object duy nhất, cấu trúc CHÍNH XÁC như sau:

```json
{
  "title": "Đề số X – Tiếng Anh vào lớp 10",
  "description": "Đề thi thử Tiếng Anh tuyển sinh lớp 10 – 40 câu trắc nghiệm",
  "time_limit_minutes": 60,
  "sections": [
    {
      "type": "<section_type>",
      "title": "<nguyên văn instruction tiếng Anh từ đề>",
      "passage_text": "<nếu có đoạn văn/thông báo — HỖ TRỢ HTML>",
      "passage_title": "<tiêu đề đoạn văn nếu có, VD: MEKONG DELTA ECOTOUR>",
      "passage_instruction": "<nếu có hướng dẫn riêng cho đoạn>",
      "questions": [
        {
          "num": 1,
          "text": "<nguyên văn câu hỏi — PHẢI CÓ cho reading_comprehension>",
          "choices": [
            {"key": "A", "text": "<đáp án A>"},
            {"key": "B", "text": "<đáp án B>"},
            {"key": "C", "text": "<đáp án C>"},
            {"key": "D", "text": "<đáp án D>"}
          ],
          "correct_answer": "A",
          "explanation_json": {
            "rule": "<tên quy tắc/dạng bài>",
            "detail": "<giải thích chi tiết>",
            "tip": "<mẹo ghi nhớ>"
          }
        }
      ]
    }
  ]
}
```

## CÁC LOẠI SECTION (section_type)

| type | Mô tả | Hiển thị trên app |
|---|---|---|
| `pronunciation` | Phát âm (underlined part) | Hiện câu hỏi + 4 đáp án grid |
| `stress` | Trọng âm | Hiện câu hỏi + 4 đáp án grid |
| `grammar` | Ngữ pháp, từ vựng | Hiện câu hỏi + đáp án |
| `communication` | Giao tiếp | Hiện câu hỏi + đáp án |
| `cloze_reading` | Điền từ vào đoạn văn/thông báo | **ẨN câu hỏi**, chỉ hiện số câu + 4 đáp án (vì câu hỏi đã nằm trong passage) |
| `sign_reading` | Đọc biển báo/thông báo ngắn | Hiện câu hỏi + đáp án |
| `reading_comprehension` | Đọc hiểu đoạn dài | **HIỆN câu hỏi** + đáp án (câu hỏi độc lập với passage) |
| `sentence_insertion` | Điền câu/cụm từ vào đoạn văn | 4 đáp án chung hiện 1 lần ở đầu, mỗi câu chọn bằng **dropdown** A/B/C/D |
| `sentence_order` | Sắp xếp câu | Hiện câu hỏi + đáp án |
| `closest_meaning` | Câu gần nghĩa | Hiện câu hỏi + đáp án |
| `sentence_from_cues` | Viết câu từ gợi ý | Hiện câu hỏi + đáp án |
| `sentence_completion` | Chọn câu kết thúc đoạn | Hiện câu hỏi + đáp án |

## QUY TẮC QUAN TRỌNG VỀ SECTION TYPE VÀ HIỂN THỊ

### ⚠️ `cloze_reading` — Câu điền từ vào passage
- Câu hỏi (`text`) sẽ bị ẨN trên giao diện (vì nó trùng với passage)
- Chỉ hiện: **số câu** + **4 đáp án ngắn** (grid 4 cột)
- Passage chứa các chỗ trống: `(13) _______`, `(14) _______`...
- Dùng cho: điền từ vào thông báo, điền từ vào đoạn văn

### ⚠️ `reading_comprehension` — Đọc hiểu
- Câu hỏi (`text`) sẽ được HIỆN ĐẦY ĐỦ (vì mỗi câu là 1 câu hỏi riêng biệt)
- **BẮT BUỘC** phải có `text` rõ ràng cho mỗi câu
- Ví dụ: `"text": "What is the main idea of the passage?"`
- Passage cần có HTML: các từ quan trọng phải **in đậm + gạch chân**:
  - Từ được hỏi trong câu hỏi (VD: "They", "reduce", "stable")
  - Dùng `<b><u>từ</u></b>` trong passage_text

### ⚠️ `sentence_insertion` — Điền câu vào đoạn
- 4 đáp án A/B/C/D **GIỐNG NHAU** cho tất cả các câu trong section
- Trên giao diện: đáp án hiện 1 lần ở đầu (toggle ẩn/hiện), mỗi câu chọn bằng dropdown
- Vẫn phải khai báo `choices` đầy đủ trong JSON cho mỗi câu (vì cùng 4 đáp án)

### ⚠️ `sign_reading` — Đọc biển báo
- Câu hỏi thường bắt đầu: "What does the sign say?" / "What does the notice say?"
- Text câu hỏi chứa nội dung biển báo trong ngoặc vuông: `[Sign: WET PAINT – Don't TOUCH]`
- Nếu đề có ảnh biển báo → ghi lại nội dung ảnh trong `text`

## QUY TẮC PASSAGE TEXT — HỖ TRỢ HTML

Passage text hỗ trợ HTML để định dạng. Các tag được hỗ trợ:
- `<b>text</b>` — in đậm
- `<u>text</u>` — gạch chân
- `<b><u>text</u></b>` — in đậm + gạch chân

### Khi nào dùng HTML trong passage:
1. **Reading comprehension**: Các từ/cụm từ được hỏi trong câu hỏi phải được **in đậm + gạch chân** trong passage
   - VD: Nếu câu hỏi hỏi "The word **'reduce'** in the 1st paragraph...":
     → passage phải có: `Recycling helps to <b><u>reduce</u></b> waste`
   - VD: Nếu câu hỏi hỏi "What does **'They'** refer to?":
     → passage phải có: `<b><u>They</u></b> also help to keep the climate`

2. **Passage title**: Đặt trong `passage_title` (sẽ hiển thị centered + bold tự động)
   - VD: `"passage_title": "MEKONG DELTA ECOTOUR"`

## QUY TẮC GIẢI THÍCH CHI TIẾT

### 1. PHÁT ÂM (pronunciation) — CỰC KỲ QUAN TRỌNG
Với mỗi câu phát âm, phần `explanation_json` PHẢI có:

**`rule`**: Tên quy tắc phát âm cụ thể (ví dụ: "Phát âm nguyên âm 'o'", "Phát âm phụ âm 'ch'")

**`detail`**: BẮT BUỘC ghi đầy đủ IPA (American English) của TẤT CẢ 4 từ, kèm giải thích:
- Ghi rõ phiên âm IPA Mỹ đầy đủ của từng từ
- Gạch chân/highlight phần phát âm khác
- So sánh rõ ràng: từ nào phát âm gì, tại sao khác

Ví dụ mẫu:
```
"detail": "A. ghost /ɡoʊst/ — 'o' phát âm /oʊ/ (nguyên âm đôi)\nB. office /ˈɑː.fɪs/ — 'o' phát âm /ɑː/ (nguyên âm đơn)\nC. long /lɑːŋ/ — 'o' phát âm /ɑː/\nD. modern /ˈmɑː.dɚn/ — 'o' phát âm /ɑː/\n→ Đáp án A khác: /oʊ/ vs /ɑː/"
```

**`tip`**: Nêu QUY TẮC PHÁT ÂM để học sinh ghi nhớ:
- Quy tắc phát âm của tổ hợp chữ cái đó
- Các từ tương tự cùng quy tắc
- Ngoại lệ cần lưu ý

### 2. TRỌNG ÂM (stress) — CỰC KỲ QUAN TRỌNG
Với mỗi câu trọng âm, phần `explanation_json` PHẢI có:

**`rule`**: Tên quy tắc trọng âm (ví dụ: "Trọng âm từ 2 âm tiết", "Quy tắc đuôi -tion/-sion")

**`detail`**: BẮT BUỘC ghi:
- Phiên âm IPA Mỹ đầy đủ với dấu trọng âm (ˈ) của TẤT CẢ 4 từ
- Ghi rõ trọng âm rơi vào âm tiết thứ mấy
- Phân tích số âm tiết

**`tip`**: BẮT BUỘC nêu QUY TẮC TRỌNG ÂM cụ thể:
- Quy tắc theo đuôi từ (-tion, -sion, -ic, -ity, -ical, -ious, -ian, -ial, -ment, -ness, -ous, -al, ...)
- Quy tắc theo loại từ (danh từ/động từ 2 âm tiết)
- Liệt kê các từ tương tự cùng quy tắc

### 3. NGỮ PHÁP (grammar)
**`rule`**: Tên điểm ngữ pháp (ví dụ: "Thì quá khứ đơn", "Câu hỏi đuôi", "So sánh hơn")
**`detail`**: Nêu cấu trúc, giải thích tại sao đáp án đúng, tại sao các đáp án khác sai, dấu hiệu nhận biết
**`tip`**: Công thức/mẹo ghi nhớ ngắn gọn + ví dụ tương tự

### 4. GIAO TIẾP (communication)
**`rule`**: Tên chức năng giao tiếp (ví dụ: "Chúc mừng", "Xin phép")
**`detail`**: Phân tích ngữ cảnh hội thoại, giải thích tại sao phản hồi phù hợp
**`tip`**: Các cách diễn đạt tương tự

### 5. ĐIỀN TỪ / ĐỌC HIỂU (cloze / reading)
**`rule`**: Loại kiến thức (từ vựng, ngữ pháp, collocation, đọc hiểu...)
**`detail`**: Giải nghĩa từ, phân tích ngữ cảnh, so sánh đáp án
**`tip`**: Collocation, từ vựng liên quan

### 6. CÂU GẦN NGHĨA / VIẾT CÂU (closest_meaning / sentence_from_cues)
**`rule`**: Cấu trúc chuyển đổi (reported speech, passive voice, conditional...)
**`detail`**: Phân tích cấu trúc + quy tắc chuyển đổi + tại sao đáp án khác sai
**`tip`**: Công thức chuyển đổi + ví dụ

### 7. ĐOẠN VĂN / BIỂN BÁO (reading / sign_reading)
**`rule`**: Dạng câu hỏi (main idea, reference, synonym, detail, NOT mentioned...)
**`detail`**: Trích dẫn evidence từ bài đọc, giải thích logic suy luận
**`tip`**: Chiến thuật làm bài cho dạng câu hỏi đó

## QUY TẮC CHOICES TEXT

### Câu phát âm (pronunciation):
- Đáp án dùng HTML `<u>` để gạch chân phần phát âm cần so sánh
- Ví dụ: `"text": "gh<u>o</u>st"` (gạch chân chữ 'o')

### Các câu khác:
- Giữ nguyên text đáp án từ đề

## VÍ DỤ ĐẦY ĐỦ

### Ví dụ: Reading comprehension với passage có HTML

```json
{
  "type": "reading_comprehension",
  "title": "Read the following passage and mark the letter A, B, C, or D on your answer sheet to indicate the correct answer to each of the following questions from 31 to 36.",
  "passage_title": "",
  "passage_text": "Protecting the environment is very important for our planet. We need to take care of nature to keep the Earth clean and healthy. There are many simple things we can do to help the environment. For example, we can recycle paper, plastic, and glass. Recycling helps to <b><u>reduce</u></b> waste and save resources. Another way to protect the environment is to save water.\n\nIn addition, planting trees is also very good for the environment. Trees clean the air and provide homes for animals. <b><u>They</u></b> also help to keep the climate <b><u>stable</u></b>. We can all plant a tree in our garden or join a community tree-planting event.",
  "questions": [
    {
      "num": 31,
      "text": "What is the main idea of the passage?",
      "choices": [
        {"key": "A", "text": "How to plant trees successfully."},
        {"key": "B", "text": "Ways to protect the environment."},
        {"key": "C", "text": "The importance of recycling."},
        {"key": "D", "text": "The benefits of public transport."}
      ],
      "correct_answer": "B",
      "explanation_json": {
        "rule": "Main idea — Ý chính",
        "detail": "Đoạn văn nói về nhiều cách bảo vệ môi trường: tái chế, tiết kiệm nước, trồng cây, đi phương tiện công cộng → Ý chính là 'Ways to protect the environment'.",
        "tip": "Câu hỏi main idea: đọc câu đầu + câu cuối mỗi đoạn, chọn đáp án bao quát nhất."
      }
    },
    {
      "num": 32,
      "text": "What does the word \"They\" in the 2nd paragraph refer to?",
      "choices": [
        {"key": "A", "text": "Resources"},
        {"key": "B", "text": "Showers"},
        {"key": "C", "text": "Trees"},
        {"key": "D", "text": "Animals"}
      ],
      "correct_answer": "C",
      "explanation_json": {
        "rule": "Reference — Từ thay thế",
        "detail": "\"They\" = Trees. Câu trước: 'Trees clean the air and provide homes for animals.' → They (= Trees) also help to keep the climate stable.",
        "tip": "Câu hỏi reference: tìm danh từ số nhiều/số ít ở câu TRƯỚC đại từ."
      }
    },
    {
      "num": 36,
      "text": "The word \"reduce\" in the 1st paragraph is OPPOSITE in meaning to _______.",
      "choices": [
        {"key": "A", "text": "increase"},
        {"key": "B", "text": "improve"},
        {"key": "C", "text": "widen"},
        {"key": "D", "text": "prevent"}
      ],
      "correct_answer": "A",
      "explanation_json": {
        "rule": "Antonym — Từ trái nghĩa",
        "detail": "reduce = giảm → trái nghĩa = increase (tăng). improve = cải thiện, widen = mở rộng, prevent = ngăn chặn.",
        "tip": "reduce ↔ increase, decrease ↔ increase, expand ↔ shrink."
      }
    }
  ]
}
```

### Ví dụ: Sentence insertion với dropdown

```json
{
  "type": "sentence_insertion",
  "title": "Four phrases/sentences have been removed from the text below. For each question, mark the letter A, B, C, or D on your answer sheet to indicate the correct option that best fits each of the numbered blanks from 37 to 40.",
  "passage_text": "When I was at school, I had to learn how to have a well-balanced life (37) _______. Below are some of the typical things I did.\n\nFirstly, I managed my time properly. I started to plan my schedule, made a weekly work list and gave priority to some of my work. (38) _______.\n\nIn addition, I communicated with my family, friends, and teachers about my busy schedule and problems, so they would offer me additional support.\n\nI also took breaks appropriately because they helped me keep away from stress and anxiety, and gave my brain a rest and improved my mood.\n\n(39) _______. I got at least eight hours of sleep a day.\n\nBesides, I also tried to follow a healthy diet. I ate a lot of fruit and vegetables. I ate little fattening foods and (40) _______.",
  "questions": [
    {
      "num": 37,
      "text": "(37) _______",
      "choices": [
        {"key": "A", "text": "avoided junk foods like chips, cookies, pizza, etc."},
        {"key": "B", "text": "in order to reduce stress and anxiety"},
        {"key": "C", "text": "Finally, I looked after my physical health."},
        {"key": "D", "text": "This helped me concentrate my efforts on my most important tasks."}
      ],
      "correct_answer": "B",
      "explanation_json": {
        "rule": "Sentence insertion — Điền câu vào chỗ trống",
        "detail": "Câu 37: '...have a well-balanced life (37) _______' → cần cụm từ chỉ mục đích → B. 'in order to reduce stress and anxiety' phù hợp nhất.",
        "tip": "Đọc câu trước + sau chỗ trống. Chú ý: linking words, thì, chủ ngữ phải nhất quán."
      }
    }
  ]
}
```

### Ví dụ: Cloze reading (ẩn câu hỏi)

```json
{
  "type": "cloze_reading",
  "title": "Read the following advertisement and mark the letter A, B, C, or D on your answer sheet to indicate the correct word or phrase that best fits each of the numbered blanks from 13 to 16.",
  "passage_title": "MEKONG DELTA ECOTOUR",
  "passage_text": "Join our (13) _______ tour to explore the Mekong Delta:\n- Cai Be Floating Market: (14) _______ the daily life of the people on the river.\n- Cham River Village: Visit a weaving workshop and learn about local people's (15) _______ skills.\n- Arts and crafts market: Buy locally made souvenirs.\n- Evening meal: Enjoy traditional foods which (16) _______ by the host family.",
  "questions": [
    {
      "num": 13,
      "text": "Join our (13) _______ tour to explore the Mekong Delta.",
      "choices": [
        {"key": "A", "text": "eco-friendly"},
        {"key": "B", "text": "environmentally-friendly"},
        {"key": "C", "text": "sustainable"},
        {"key": "D", "text": "environmental-friendly"}
      ],
      "correct_answer": "A",
      "explanation_json": {
        "rule": "Từ vựng — Tính từ ghép",
        "detail": "eco-friendly = thân thiện với môi trường. environmentally-friendly cũng đúng nghĩa nhưng eco-friendly phổ biến hơn với 'tour'. environmental-friendly SAI (phải là environmentally).",
        "tip": "eco- = prefix liên quan đến sinh thái: eco-friendly, ecosystem, eco-tourism."
      }
    }
  ]
}
```

## LƯU Ý QUAN TRỌNG
1. **IPA phải dùng American English** (ví dụ: /ɑː/ thay vì /ɒ/, /ɚ/ thay vì /ə/ ở cuối từ)
2. **Giải thích bằng Tiếng Việt** cho học sinh lớp 9 dễ hiểu
3. **Mỗi explanation_json PHẢI có đủ 3 field**: rule, detail, tip
4. **Không bỏ sót câu nào** — đủ 40 câu
5. **Giữ nguyên nội dung đề** — không sửa đổi câu hỏi hay đáp án
6. **Section title** = copy nguyên văn instruction tiếng Anh từ đề
7. **Passage text** giữ nguyên nội dung, hỗ trợ HTML (`<b>`, `<u>`), dùng `\n` cho xuống dòng
8. **Passage title** tách riêng vào field `passage_title` (sẽ hiển thị centered + bold)
9. **Reading comprehension**: BẮT BUỘC có `text` cho mỗi câu + HTML bold/underline cho từ khóa trong passage
10. **Sentence insertion**: 4 đáp án giống nhau cho mỗi câu, giao diện sẽ hiện 1 lần + dropdown
11. **Cloze reading**: Câu hỏi sẽ bị ẨN, chỉ hiện số câu và 4 đáp án
12. **JSON phải valid** — có thể parse được bằng JSON.parse()

---

## ĐỀ THI CẦN GIẢI:

[DÁN ĐỀ THI VÀO ĐÂY]
