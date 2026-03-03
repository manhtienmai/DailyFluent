# Prompt: Extract + Giải thích đề thi sắp xếp câu (並べ替え - Sentence Ordering)

Bạn là trợ lý chuyên extract dữ liệu đề thi tiếng Nhật JLPT dạng sắp xếp câu (並べ替え). Tôi sẽ cung cấp HTML thô từ đề thi. Hãy extract thành JSON và giải thích chi tiết.

## Cấu trúc HTML đầu vào:
- Mỗi câu trong `<div class="thithu_ques" data-id="N">`
- Câu hỏi trong `<span class="txt1">` (có chứa 4 chỗ trống （　　）, trong đó 1 chỗ có dấu ＊: （　*　）)
- 4 đáp án (các mảnh câu) trong `<div class="item_ans">`, đáp án đúng (mảnh nằm ở vị trí ＊) có class `dung`
- Giải thích trong `<div class="giaidap_ques">` bao gồm:
  - Câu hoàn chỉnh đã sắp xếp đúng (trong `<p>` đầu tiên)
  - Thứ tự đúng (VD: `2 - 4 - 1 - 3`) và bản dịch tiếng Việt (trong `<p class="bg-cauvn">`)
  - Giải thích ngữ pháp chi tiết

## Quy tắc:
1. Trích xuất chính xác câu hỏi, 4 mảnh câu (options), đáp án đúng.
2. `correct` = số thứ tự đáp án có class `dung` (nằm ở vị trí ＊), giá trị 1-4.
3. `correct_order` = thứ tự đúng hoàn chỉnh, VD: `"2,4,1,3"` (dùng dấu phẩy, không có khoảng trắng).
4. Trích xuất `sentence_completed` = câu đã điền đầy đủ đúng thứ tự.
5. Trích xuất điểm ngữ pháp chính (grammar_point) từ phần giải thích.
6. Trích xuất cấu trúc (structure), ý nghĩa (meaning), ghi chú và ví dụ nếu có.
7. Giữ nguyên tất cả kanji/hiragana/katakana từ dữ liệu gốc.

## Cấu trúc JSON output:

```json
{
  "book_title": "Tên sách / đề thi",
  "exam_type": "並べ替え",
  "questions": [
    {
      "id": 1,
      "sentence": "今度、海外へ転勤することになったので、（　　）（　　）（　*　）（　　）いるが、大変だ。",
      "sentence_completed": "今度、海外へ転勤することになったので、（ビザに）（関する）（書類を）（準備して）いるが、大変だ。",
      "sentence_vi": "Lần này, vì tôi phải chuyển công tác ra nước ngoài nên đang chuẩn bị các giấy tờ liên quan đến visa, thật là vất vả.",
      "correct": 1,
      "correct_order": "2,4,1,3",
      "options": ["書類を", "ビザに", "準備して", "関する"],
      "grammar_point": "～に関して／に関する",
      "grammar_reading": "にかんして",
      "grammar_meaning": "Về, liên quan đến, liên quan tới...",
      "grammar_structure": "N ＋ に関して（は／も）\nN1 ＋ に関する ＋ N2",
      "grammar_note": "Dùng khi muốn nói về chủ đề, đề tài câu chuyện hoặc điều tra, tìm hiểu. Đây là cách nói trang trọng hơn について.",
      "grammar_examples": [
        {
          "ja": "このゼミでは、自身のテーマに関して、段階的に知識を深め、プレゼンテーションを行う。",
          "vi": "Trong hội thảo này, sinh viên sẽ từng bước đào sâu kiến thức về chủ đề của mình và thực hiện bài thuyết trình."
        }
      ]
    }
  ]
}
```

## Lưu ý quan trọng:
- `correct` là số đáp án (1-4) nằm ở vị trí ＊ (đáp án có class `dung` trong HTML).
- `correct_order` là thứ tự sắp xếp đúng của 4 mảnh câu, lấy từ phần giải thích.
- Trích xuất grammar_point, grammar_structure, grammar_meaning từ phần giải thích HTML nếu có.
- Nếu HTML không có giải thích chi tiết, hãy TỰ GIẢI THÍCH dựa trên kiến thức ngữ pháp JLPT.
- Tất cả giải thích phải BẰNG TIẾNG VIỆT, rõ ràng, dễ hiểu.
- CHỈ trả về JSON, không kèm markdown code fence hay text thừa.

Bây giờ hãy extract và giải thích dữ liệu từ đề thi sau:
