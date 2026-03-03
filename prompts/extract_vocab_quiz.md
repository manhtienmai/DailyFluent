# Prompt: Extract + Giải thích đề thi từ vựng (用法 - Cách dùng từ)

Bạn là một trợ lý chuyên extract dữ liệu đề thi tiếng Nhật. Tôi sẽ cung cấp nội dung đề thi dạng "Cách dùng từ" (用法). Hãy extract thành JSON và giải thích chi tiết từng câu.

## Quy tắc:
1. Mỗi câu hỏi có 1 từ vựng chính và 4 đáp án (4 câu ví dụ), chỉ 1 đáp án đúng.
2. Đáp án đúng là câu mà từ vựng được dùng đúng ngữ cảnh (có kèm bản dịch tiếng Việt trong đề).
3. Giữ nguyên tất cả furigana/hiragana từ dữ liệu gốc. KHÔNG tự thêm hoặc bỏ furigana.
4. Trường "han_viet" lấy từ phần 【...】 trong đề (ví dụ: 【CẤM CHỈ】).
5. Trường "meaning_vi" lấy từ phần giải thích tiếng Việt sau dấu ►.
6. Trường "correct" là số thứ tự đáp án đúng (1-4).
7. Giải thích tại sao đáp án đúng là đúng và tại sao 3 đáp án sai là sai.
8. Gợi ý từ thay thế hợp lý cho mỗi đáp án sai — từ thay thế phải cùng trình độ JLPT, không dùng từ quá dễ hoặc quá khó.

## Cấu trúc JSON output:

```json
{
  "book_title": "Tên sách",
  "exam_type": "用法",
  "questions": [
    {
      "id": 1,
      "word": "禁止",
      "reading": "きんし",
      "han_viet": "CẤM CHỈ",
      "meaning_vi": "cấm, cấm đoán",
      "correct": 2,
      "correct_translation": "Việc vào trong tòa nhà này bị cấm.",
      "options": [
        "免許がないのに車を運転するのは法律（禁止）だ。",
        "このビルの中に立ち入ることは（禁止）されています。",
        "あなたの考えにはまったく（禁止）できない。",
        "速足で歩いていた彼は急に（禁止）した。"
      ],
      "explanations": [
        {
          "option": 1,
          "is_correct": false,
          "reason": "「法律禁止」không tự nhiên. 「法律」đi với「違反」(vi phạm).",
          "suggested_word": "違反（いはん）【VI PHẠM】",
          "corrected_sentence": "免許がないのに車を運転するのは法律（違反）だ。",
          "corrected_translation": "Lái xe mà không có bằng lái là vi phạm pháp luật."
        },
        {
          "option": 2,
          "is_correct": true,
          "reason": "「禁止されている」là cách dùng chuẩn, nghĩa là 'bị cấm'."
        },
        {
          "option": 3,
          "is_correct": false,
          "reason": "Ngữ cảnh muốn nói 'không thể đồng ý'.「禁止」không mang nghĩa đồng ý/phản đối.",
          "suggested_word": "賛成（さんせい）【TÁN THÀNH】",
          "corrected_sentence": "あなたの考えにはまったく（賛成）できない。",
          "corrected_translation": "Tôi hoàn toàn không thể đồng ý với suy nghĩ của bạn."
        },
        {
          "option": 4,
          "is_correct": false,
          "reason": "Ngữ cảnh muốn nói 'đột nhiên dừng lại'.「禁止」không có nghĩa dừng lại.",
          "suggested_word": "停止（ていし）【ĐÌNH CHỈ】",
          "corrected_sentence": "速足で歩いていた彼は急に（停止）した。",
          "corrected_translation": "Anh ấy đang đi nhanh thì đột nhiên dừng lại."
        }
      ]
    }
  ]
}
```
## Lưu ý quan trọng:
- Nếu từ vựng có kanji, BẮT BUỘC phải có trường "reading" (hiragana đầy đủ).
- Giữ nguyên dấu ngoặc （） quanh từ vựng trong các options.
- Từ thay thế (suggested_word) phải cùng trình độ, có đầy đủ: kanji, reading, hán việt 【】.
- Đáp án sai phải có `corrected_sentence` (câu đã sửa dùng từ đúng) và `corrected_translation` (dịch tiếng Việt câu đã sửa).
- Đáp án đúng KHÔNG cần trường "suggested_word", "corrected_sentence", "corrected_translation".
- CHỈ trả về JSON, không kèm markdown code fence hay text thừa.

Bây giờ hãy extract và giải thích dữ liệu từ đề thi sau:
