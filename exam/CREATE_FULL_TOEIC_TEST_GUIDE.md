# 📚 Hướng dẫn Tạo Full Test TOEIC trong Admin

## Tổng quan

Full Test TOEIC bao gồm:
- **Listening**: 100 câu (Part 1-4)
- **Reading**: 100 câu (Part 5-7)
- **Tổng cộng**: 200 câu
- **Thời gian**: 45 phút Listening + 75 phút Reading = 120 phút

---

## 📋 Bước 1: Tạo ExamTemplate

### 1.1. Vào Django Admin

1. Truy cập: `http://your-domain/admin/`
2. Đăng nhập với tài khoản admin
3. Vào **Exam Templates** (hoặc **Exam → Exam Templates**)

### 1.2. Tạo Template mới

1. Click nút **Add Exam Template** (góc trên bên phải)
2. Điền thông tin:

#### Basic Information
- **Book**: Chọn sách TOEIC (ví dụ: "ETS TOEIC Test 2024")
  - Nếu chưa có, tạo mới ở **Exam Books**
- **Title**: `TOEIC Test 2024 - Đề 01` (hoặc tên bạn muốn)
- **Slug**: Để trống (sẽ tự động tạo từ title)
- **Description**: Mô tả ngắn (optional)
- **Level**: Chọn **TOEIC**
- **Category**: 
  - ⚠️ **Quan trọng**: Category sẽ **TỰ ĐỘNG CẬP NHẬT** khi import:
    - Ban đầu: Chọn **READING** (nếu import Reading trước) hoặc **LISTENING** (nếu import Listening trước)
    - Sau khi import đủ cả 2 phần: Category sẽ tự động đổi thành **TOEIC_FULL**
  - Hoặc chọn **TOEIC_FULL** ngay từ đầu nếu bạn chắc chắn sẽ import đủ cả 2 phần

#### Organization
- **Group Type**: `TEST` hoặc `LESSON` (tùy bạn)
- **Lesson Index**: `1` (hoặc số thứ tự)
- **Subtitle**: `Full Test - 200 Questions` (optional)

#### Question Settings
- **Main Question Type**: `MCQ`
- **Reading Format**: Để trống
- **Dokkai Skill**: Để trống

#### TOEIC Settings (⚠️ Quan trọng)
- **Is Full TOEIC**: ✅ **Check** (Bật checkbox này)
- **Listening Time Limit Minutes**: `45`
- **Reading Time Limit Minutes**: `75`

#### Time & Status
- **Time Limit Minutes**: `120` (tổng thời gian, optional)
- **Is Active**: ✅ **Check** (để hiển thị cho users)

3. Click **Save** (hoặc **Save and continue editing**)

---

## 🎧 Bước 2: Import Listening Parts

### 2.1. Import Part 1 (6 câu)

1. Vào trang **Change** của ExamTemplate vừa tạo
2. Click nút **Import TOEIC JSON** (góc trên bên phải)
3. Upload hoặc paste JSON cho Part 1:

```json
{
  "part": "L1",
  "questions": [
    {
      "order": 1,
      "image_url": "https://example.com/part1_q1.jpg",
      "audio_url": "https://example.com/part1_q1.mp3",
      "choices": [
        {"key": "1", "text": "She is talking on the phone."},
        {"key": "2", "text": "She is writing a report."},
        {"key": "3", "text": "She is reading a book."},
        {"key": "4", "text": "She is typing on a computer."}
      ],
      "correct_answer": "1"
    },
    {
      "order": 2,
      "image_url": "https://example.com/part1_q2.jpg",
      "audio_url": "https://example.com/part1_q2.mp3",
      "choices": [
        {"key": "1", "text": "They are shaking hands."},
        {"key": "2", "text": "They are having a meeting."},
        {"key": "3", "text": "They are eating lunch."},
        {"key": "4", "text": "They are playing sports."}
      ],
      "correct_answer": "1"
    }
    // ... thêm 4 câu nữa (order 3-6)
  ]
}
```

4. Click **Import**
5. Kiểm tra: Sẽ hiển thị "Successfully imported 6 questions"

### 2.2. Import Part 2 (25 câu)

1. Vẫn ở trang Import TOEIC JSON
2. Upload hoặc paste JSON cho Part 2:

```json
{
  "part": "L2",
  "questions": [
    {
      "order": 7,
      "audio_url": "https://example.com/part2_q1.mp3",
      "choices": [
        {"key": "1", "text": "Yes, I do."},
        {"key": "2", "text": "No, thank you."},
        {"key": "3", "text": "It's on the desk."},
        {"key": "4", "text": "I'll call you later."}
      ],
      "correct_answer": "2"
    },
    {
      "order": 8,
      "audio_url": "https://example.com/part2_q2.mp3",
      "choices": [
        {"key": "1", "text": "At 3 PM."},
        {"key": "2", "text": "In the conference room."},
        {"key": "3", "text": "With the manager."},
        {"key": "4", "text": "For two hours."}
      ],
      "correct_answer": "1"
    }
    // ... thêm 23 câu nữa (order 9-31)
  ]
}
```

**Lưu ý**: Order bắt đầu từ 7 (sau 6 câu Part 1)

3. Click **Import**

### 2.3. Import Part 3 (39 câu, 13 conversations)

1. Upload hoặc paste JSON cho Part 3:

```json
{
  "part": "L3",
  "conversations": [
    {
      "order": 1,
      "audio_url": "https://example.com/part3_conv1.mp3",
      "image_url": "https://example.com/part3_conv1.jpg",
      "transcript": "Man: Good morning. I'd like to schedule a meeting...",
      "questions": [
        {
          "order": 32,
          "text": "What is the man's occupation?",
          "choices": [
            {"key": "1", "text": "A teacher"},
            {"key": "2", "text": "A doctor"},
            {"key": "3", "text": "A manager"},
            {"key": "4", "text": "A student"}
          ],
          "correct_answer": "3"
        },
        {
          "order": 33,
          "text": "Where does the conversation take place?",
          "choices": [
            {"key": "1", "text": "At a restaurant"},
            {"key": "2", "text": "In an office"},
            {"key": "3", "text": "At a hospital"},
            {"key": "4", "text": "In a school"}
          ],
          "correct_answer": "2"
        },
        {
          "order": 34,
          "text": "What will the man do next?",
          "choices": [
            {"key": "1", "text": "Make a phone call"},
            {"key": "2", "text": "Send an email"},
            {"key": "3", "text": "Schedule a meeting"},
            {"key": "4", "text": "Prepare a report"}
          ],
          "correct_answer": "3"
        }
      ]
    },
    {
      "order": 2,
      "audio_url": "https://example.com/part3_conv2.mp3",
      "questions": [
        {
          "order": 35,
          "text": "...",
          "choices": [...],
          "correct_answer": "1"
        },
        {
          "order": 36,
          "text": "...",
          "choices": [...],
          "correct_answer": "2"
        },
        {
          "order": 37,
          "text": "...",
          "choices": [...],
          "correct_answer": "3"
        }
      ]
    }
    // ... thêm 11 conversations nữa (order 3-13)
  ]
}
```

**Lưu ý**: 
- Order của questions: 32-70 (39 câu)
- Mỗi conversation có 3 câu hỏi
- Tổng cộng 13 conversations

2. Click **Import**

### 2.4. Import Part 4 (30 câu, 10 conversations)

1. Upload hoặc paste JSON cho Part 4:

```json
{
  "part": "L4",
  "conversations": [
    {
      "order": 1,
      "audio_url": "https://example.com/part4_talk1.mp3",
      "transcript": "Good morning, everyone. Today I'd like to...",
      "questions": [
        {
          "order": 71,
          "text": "What is the main topic of this talk?",
          "choices": [
            {"key": "1", "text": "Company policies"},
            {"key": "2", "text": "New products"},
            {"key": "3", "text": "Employee benefits"},
            {"key": "4", "text": "Market trends"}
          ],
          "correct_answer": "2"
        },
        {
          "order": 72,
          "text": "Who is the speaker?",
          "choices": [
            {"key": "1", "text": "A manager"},
            {"key": "2", "text": "A salesperson"},
            {"key": "3", "text": "A customer"},
            {"key": "4", "text": "A student"}
          ],
          "correct_answer": "1"
        },
        {
          "order": 73,
          "text": "When will the product be available?",
          "choices": [
            {"key": "1", "text": "Next week"},
            {"key": "2", "text": "Next month"},
            {"key": "3", "text": "Next year"},
            {"key": "4", "text": "In two years"}
          ],
          "correct_answer": "2"
        }
      ]
    }
    // ... thêm 9 conversations nữa (order 2-10)
  ]
}
```

**Lưu ý**:
- Order của questions: 71-100 (30 câu)
- Mỗi conversation có 3 câu hỏi
- Tổng cộng 10 conversations

2. Click **Import**

---

## 📖 Bước 3: Import Reading Parts

### 3.1. Import Part 5 (30 câu)

1. Vẫn ở trang Import TOEIC JSON
2. Upload hoặc paste JSON cho Part 5:

```json
{
  "part": "R5",
  "questions": [
    {
      "order": 101,
      "text": "The meeting will be held _____ the conference room.",
      "choices": [
        {"key": "1", "text": "at"},
        {"key": "2", "text": "in"},
        {"key": "3", "text": "on"},
        {"key": "4", "text": "by"}
      ],
      "correct_answer": "2",
      "explanation_vi": "Giải thích: 'in' dùng cho không gian kín"
    },
    {
      "order": 102,
      "text": "She _____ to the office every day.",
      "choices": [
        {"key": "1", "text": "go"},
        {"key": "2", "text": "goes"},
        {"key": "3", "text": "going"},
        {"key": "4", "text": "went"}
      ],
      "correct_answer": "2"
    }
    // ... thêm 28 câu nữa (order 103-130)
  ]
}
```

**Lưu ý**: Order bắt đầu từ 101 (sau 100 câu Listening)

3. Click **Import**

### 3.2. Import Part 6 (16 câu, 4 passages)

1. Upload hoặc paste JSON cho Part 6:

```json
{
  "part": "R6",
  "passages": [
    {
      "order": 1,
      "title": "Email về cuộc họp",
      "text": "Dear Team,\n\nWe would like to inform you that the monthly meeting will be held on Friday, March 15th, at 2:00 PM in the main conference room. Please make sure to arrive on time.\n\nBest regards,\nManagement",
      "image_url": "https://example.com/passage1.jpg",
      "questions": [
        {
          "order": 131,
          "text": "What is the main purpose of this email?",
          "choices": [
            {"key": "1", "text": "To cancel a meeting"},
            {"key": "2", "text": "To announce a meeting"},
            {"key": "3", "text": "To reschedule a meeting"},
            {"key": "4", "text": "To request attendance"}
          ],
          "correct_answer": "2"
        },
        {
          "order": 132,
          "text": "When will the meeting take place?",
          "choices": [
            {"key": "1", "text": "Monday, March 15th"},
            {"key": "2", "text": "Friday, March 15th"},
            {"key": "3", "text": "Friday, March 14th"},
            {"key": "4", "text": "Monday, March 14th"}
          ],
          "correct_answer": "2"
        },
        {
          "order": 133,
          "text": "Where will the meeting be held?",
          "choices": [
            {"key": "1", "text": "In the lobby"},
            {"key": "2", "text": "In the main conference room"},
            {"key": "3", "text": "In the cafeteria"},
            {"key": "4", "text": "In the parking lot"}
          ],
          "correct_answer": "2"
        },
        {
          "order": 134,
          "text": "What should employees do?",
          "choices": [
            {"key": "1", "text": "Cancel the meeting"},
            {"key": "2", "text": "Arrive on time"},
            {"key": "3", "text": "Bring food"},
            {"key": "4", "text": "Reschedule"}
          ],
          "correct_answer": "2"
        }
      ]
    },
    {
      "order": 2,
      "title": "Passage 2",
      "text": "...",
      "questions": [
        {
          "order": 135,
          "text": "...",
          "choices": [...],
          "correct_answer": "1"
        }
        // ... thêm 3 câu nữa (order 136-138)
      ]
    }
    // ... thêm 2 passages nữa (order 3-4)
  ]
}
```

**Lưu ý**:
- Order của questions: 131-146 (16 câu)
- Mỗi passage có 4 câu hỏi
- Tổng cộng 4 passages

2. Click **Import**

### 3.3. Import Part 7 (54 câu)

1. Upload hoặc paste JSON cho Part 7:

```json
{
  "part": "R7",
  "passages": [
    {
      "order": 1,
      "title": "Company Announcement",
      "text": "We are pleased to announce that our company will be expanding its operations to Southeast Asia. This expansion will create new job opportunities and strengthen our presence in the region.",
      "image_url": "https://example.com/announcement.jpg",
      "questions": [
        {
          "order": 147,
          "text": "What is the main topic of this announcement?",
          "choices": [
            {"key": "1", "text": "New product launch"},
            {"key": "2", "text": "Company expansion"},
            {"key": "3", "text": "Employee benefits"},
            {"key": "4", "text": "Market analysis"}
          ],
          "correct_answer": "2",
          "explanation_vi": "Đoạn văn nói về việc mở rộng công ty"
        },
        {
          "order": 148,
          "text": "Where will the company expand?",
          "choices": [
            {"key": "1", "text": "Europe"},
            {"key": "2", "text": "Southeast Asia"},
            {"key": "3", "text": "North America"},
            {"key": "4", "text": "South America"}
          ],
          "correct_answer": "2"
        }
        // ... thêm các câu hỏi khác
      ]
    }
    // ... thêm các passages khác
  ]
}
```

**Lưu ý**:
- Order của questions: 147-200 (54 câu)
- Có thể có single passage hoặc multiple passages
- Mỗi passage có thể có nhiều câu hỏi

2. Click **Import**

---

## ✅ Bước 4: Kiểm tra và Xác nhận

### 4.1. Kiểm tra số lượng câu hỏi

1. Vào trang **Change** của ExamTemplate
2. Scroll xuống phần **Exam Questions** (inline)
3. Kiểm tra:
   - **Listening**: 100 câu (order 1-100)
   - **Reading**: 100 câu (order 101-200)
   - **Tổng cộng**: 200 câu

### 4.2. Kiểm tra Conversations và Passages

1. Scroll xuống phần **Listening Conversations** (inline)
2. Kiểm tra:
   - **Part 3**: 13 conversations
   - **Part 4**: 10 conversations
   - **Tổng cộng**: 23 conversations

3. Scroll xuống phần **Passages** (nếu có trong inline, hoặc vào **Reading Passages**)
4. Kiểm tra:
   - **Part 6**: 4 passages
   - **Part 7**: N passages (tùy số lượng)

### 4.3. Kiểm tra Settings

1. Scroll lên phần **TOEIC Settings**
2. Đảm bảo:
   - ✅ **Is Full TOEIC**: Checked
   - **Listening Time Limit Minutes**: 45
   - **Reading Time Limit Minutes**: 75

---

## 🎯 Tóm tắt Order Numbers

| Part | Questions | Order Range | Notes |
|------|-----------|-------------|-------|
| L1   | 6         | 1-6         | Mô tả hình ảnh |
| L2   | 25        | 7-31        | Câu hỏi-Đáp án |
| L3   | 39        | 32-70       | Hội thoại (13 conversations) |
| L4   | 30        | 71-100      | Bài nói (10 conversations) |
| **Listening Total** | **100** | **1-100** | |
| R5   | 30        | 101-130     | Điền từ vào câu |
| R6   | 16        | 131-146     | Điền từ vào đoạn (4 passages) |
| R7   | 54        | 147-200     | Đọc hiểu (N passages) |
| **Reading Total** | **100** | **101-200** | |
| **GRAND TOTAL** | **200** | **1-200** | |

---

## 💡 Tips & Best Practices

### 1. Chuẩn bị JSON Files

- Tạo file JSON riêng cho mỗi part để dễ quản lý
- Đặt tên file: `toeic_part1.json`, `toeic_part2.json`, ...
- Validate JSON trước khi import (dùng JSON validator online)

### 2. Order Numbers

- **Quan trọng**: Order phải liên tục và không trùng
- Listening: 1-100
- Reading: 101-200
- Nếu import sai order, có thể sửa thủ công trong admin

### 3. Audio & Image URLs

- Đảm bảo URLs hợp lệ và có thể truy cập được
- Hệ thống sẽ tự động download và lưu vào storage
- Nếu download thất bại, record vẫn được tạo nhưng không có audio/image

### 4. Correct Answer

- **Bắt buộc**: Tất cả questions phải có `correct_answer`
- Format: String `"1"`, `"2"`, `"3"`, hoặc `"4"` (không phải số)

### 5. Testing

- Sau khi import xong, vào trang `/exam/toeic/` để xem đề thi
- Click "Bắt đầu" để test làm bài
- Kiểm tra audio player hoạt động đúng
- Kiểm tra timer đếm ngược đúng (45 phút Listening + 75 phút Reading)

---

## 🔧 Troubleshooting

### Lỗi: "Invalid part"

- **Nguyên nhân**: Part không phải L1-L4 hoặc R5-R7
- **Giải pháp**: Kiểm tra lại JSON, đảm bảo `"part"` đúng format

### Lỗi: "No questions found"

- **Nguyên nhân**: Part 1, 2, 5 không có `questions` array
- **Giải pháp**: Thêm `"questions": [...]` vào JSON

### Lỗi: "No conversations found"

- **Nguyên nhân**: Part 3, 4 không có `conversations` array
- **Giải pháp**: Thêm `"conversations": [...]` vào JSON

### Lỗi: "No passages found"

- **Nguyên nhân**: Part 6, 7 không có `passages` array
- **Giải pháp**: Thêm `"passages": [...]` vào JSON

### Lỗi: "Error downloading file"

- **Nguyên nhân**: URL không hợp lệ hoặc không truy cập được
- **Giải pháp**: 
  - Kiểm tra URL có đúng format không
  - Kiểm tra URL có thể truy cập được không
  - Nếu cần, upload file lên storage trước rồi dùng URL từ storage

### Order bị trùng

- **Nguyên nhân**: Import nhiều lần với cùng order
- **Giải pháp**: 
  - Xóa questions cũ trước khi import lại
  - Hoặc sửa order trong JSON để không trùng

---

## 📝 Checklist

Trước khi publish đề thi, đảm bảo:

- [ ] ExamTemplate có `level = "TOEIC"`
- [ ] ExamTemplate có `category = "TOEIC_FULL"`
- [ ] ✅ `is_full_toeic = True`
- [ ] `listening_time_limit_minutes = 45`
- [ ] `reading_time_limit_minutes = 75`
- [ ] ✅ `is_active = True`
- [ ] Đã import đủ 100 câu Listening (order 1-100)
- [ ] Đã import đủ 100 câu Reading (order 101-200)
- [ ] Đã import đủ 13 conversations cho Part 3
- [ ] Đã import đủ 10 conversations cho Part 4
- [ ] Đã import đủ 4 passages cho Part 6
- [ ] Tất cả questions đều có `correct_answer`
- [ ] Tất cả audio URLs đều hoạt động
- [ ] Đã test làm bài và submit thành công

---

## 🔗 Liên kết

- **Import Guide**: `exam/IMPORT_TOEIC_JSON_GUIDE.md`
- **Admin URL**: `/admin/exam/examtemplate/`
- **Import URL**: `/admin/exam/examtemplate/{id}/import-toeic-json/`
- **User View**: `/exam/toeic/`

---

**Chúc bạn tạo đề thi thành công! 🎉**

