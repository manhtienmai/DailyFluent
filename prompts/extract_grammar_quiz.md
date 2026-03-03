# Prompt: Extract + Giải thích đề thi ngữ pháp (文法 - Bunpou)

Bạn là trợ lý chuyên extract dữ liệu đề thi ngữ pháp tiếng Nhật JLPT. Tôi sẽ cung cấp HTML thô từ đề thi dạng điền chỗ trống (選択肢). Hãy extract thành JSON và giải thích chi tiết.

## Cấu trúc HTML đầu vào:
- Mỗi câu trong `<div class="thithu_ques" data-id="N">`
- Câu hỏi trong `<span class="txt1">` (có chứa chỗ trống （　　）)
- 4 đáp án trong `<div class="item_ans">`, đáp án đúng có class `dung`
- Giải thích trong `<div class="giaidap_ques">` bao gồm:
  - Câu hoàn chỉnh (đáp án đã điền)
  - Bản dịch tiếng Việt (trong `<p class="bg-cauvn">`)
  - Giải thích ngữ pháp cho đáp án đúng (trong `<div class="jlpt-lesson-right-tuvung">`)

## Quy tắc:
1. Trích xuất chính xác câu hỏi, 4 đáp án, đáp án đúng (số 1-4).
2. Trích xuất điểm ngữ pháp chính (grammar_point) từ phần giải thích.
3. **Nếu grammar_point có chứa kanji, BẮT BUỘC phải cung cấp trường `grammar_furigana`** — đây là phiên bản đọc bằng hiragana đầy đủ của grammar_point.
4. Trích xuất cấu trúc (structure), ý nghĩa (meaning) từ phần giải thích.
5. **Cung cấp trường `grammar_topic`** — chủ đề / nhóm ngữ pháp (VD: 接続表現, 仮定表現, 受身, 敬語, 時間表現, 原因・理由, 逆接...).
6. Giải thích ngắn gọn tại sao đáp án đúng là đúng.
7. Giải thích tại sao 3 đáp án sai là sai.
8. Giữ nguyên tất cả kanji/hiragana/katakana từ dữ liệu gốc.
9. Mỗi explanation phải giải thích **BẰNG TIẾNG VIỆT**, rõ ràng, dễ hiểu. KHÔNG dùng tiếng Trung.

## Cấu trúc JSON output:

```json
{
  "book_title": "Tên sách / đề thi",
  "exam_type": "文法",
  "questions": [
    {
      "id": 1,
      "sentence": "お客様にいろいろと文句を（　　）あげく、結局相手の勘違いだとわかった。",
      "sentence_completed": "お客様にいろいろと文句を（言われた）あげく、結局相手の勘違いだとわかった。",
      "sentence_vi": "Sau khi bị khách hàng phàn nàn về nhiều vấn đề, cuối cùng chúng tôi nhận ra rằng đó chỉ là sự hiểu lầm của họ。",
      "correct": 2,
      "options": ["言って", "言われた", "言う", "言い"],
      "grammar_point": "～あげく（に）",
      "grammar_furigana": "あげく（に）",
      "grammar_topic": "接続表現",
      "grammar_reading": "あげく",
      "grammar_meaning": "Cuối cùng thì..., sau khi đã...thì..., sau một thời gian dài... thì...",
      "grammar_structure": "Vた ／ Nの ＋ あげく（に）",
      "grammar_note": "Thể hiện kết quả có được sau một thời gian dài gặp phiền toái. Thường dùng với kết quả đáng tiếc.",
      "examples": [
        {
          "ja": "悩（なや）んだあげく、会社（かいしゃ）を辞（や）めることにした。",
          "vi": "Sau khi suy nghĩ mãi, tôi quyết định nghỉ việc."
        },
        {
          "ja": "長（なが）い議論（ぎろん）のあげく、結論（けつろん）が出（で）なかった。",
          "vi": "Sau cuộc tranh luận dài, không đưa ra được kết luận."
        }
      ],
      "explanations": [
        {
          "option": 1,
          "is_correct": false,
          "reason": "「言って」là thể て (te-form). Trước あげく cần dạng Vた hoặc Nの, không dùng thể て."
        },
        {
          "option": 2,
          "is_correct": true,
          "reason": "「言われた」là thể bị động quá khứ (Vた), đúng cấu trúc Vた＋あげく。Nghĩa: 'Sau khi bị nói (phàn nàn)'."
        },
        {
          "option": 3,
          "is_correct": false,
          "reason": "「言う」là thể từ điển (dictionary form), không phải Vた. あげく cần Vた phía trước."
        },
        {
          "option": 4,
          "is_correct": false,
          "reason": "「言い」là thể ます bỏ ます (masu-stem). Không đúng cấu trúc Vた＋あげく."
        }
      ]
    }
  ]
}
```

## Ví dụ grammar_furigana cho kanji:
- grammar_point: `～に関して` → grammar_furigana: `にかんして`
- grammar_point: `～を通じて` → grammar_furigana: `をつうじて`
- grammar_point: `～に基づいて` → grammar_furigana: `にもとづいて`
- grammar_point: `～に違いない` → grammar_furigana: `にちがいない`
- grammar_point: `～あげく（に）` → grammar_furigana: `あげく（に）` (không có kanji thì giữ nguyên)

## Lưu ý quan trọng:
- Trích xuất grammar_point, grammar_structure, grammar_meaning từ phần giải thích HTML nếu có.
- **`grammar_furigana`**: BẮT BUỘC nếu grammar_point hoặc grammar_structure có kanji. Ghi phiên âm hiragana đầy đủ.
- **`grammar_topic`**: Phân loại chủ đề ngữ pháp bằng tiếng Nhật (VD: 接続, 仮定, 受身, 敬語, 時間, 原因・理由, 逆接, 条件, 比較, 程度...).
- Nếu HTML không có giải thích chi tiết, hãy TỰ GIẢI THÍCH dựa trên kiến thức ngữ pháp JLPT.
- Mỗi explanation phải giải thích BẰNG TIẾNG VIỆT, rõ ràng, dễ hiểu. KHÔNG dùng tiếng Trung.
- **`examples`**: BẮT BUỘC tạo 2 câu ví dụ cho mỗi điểm ngữ pháp:
  - Câu ví dụ phải phù hợp trình độ JLPT của đề thi (N1/N2/N3/N4/N5).
  - Câu tiếng Nhật (`ja`) phải ghi furigana trong ngoặc đơn ngay sau kanji, VD: `食（た）べる`, `学校（がっこう）`.
  - Bản dịch tiếng Việt (`vi`) rõ ràng, tự nhiên.
  - 2 câu ví dụ phải khác ngữ cảnh, giúp hiểu rõ cách dùng ngữ pháp.
- CHỈ trả về JSON, không kèm markdown code fence hay text thừa.

Bây giờ hãy extract và giải thích dữ liệu từ đề thi sau:

