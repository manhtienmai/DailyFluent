"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

/* ─── DATA ────────────────────────────────────────────── */
interface GrammarLesson {
  title: string;
  titleVi: string;
  emoji: string;
  sections: { heading: string; content: string }[];
  formulas: { name: string; formula: string; example: string; exampleVi: string }[];
  exercises: { question: string; options: string[]; correct: number; explanation: string }[];
}

const LESSONS: Record<string, GrammarLesson> = {
  tenses: {
    title: "Tenses", titleVi: "Các thì trong tiếng Anh", emoji: "⏰",
    sections: [
      { heading: "1. Thì Hiện tại đơn (Present Simple)", content: "Diễn tả thói quen, sự thật hiển nhiên, lịch trình.\n\n**Dấu hiệu**: always, usually, often, sometimes, every day/week/month.\n\n**Cấu trúc**:\n• (+) S + V(s/es) + O\n• (−) S + do/does + not + V + O\n• (?) Do/Does + S + V + O?" },
      { heading: "2. Thì Quá khứ đơn (Past Simple)", content: "Diễn tả hành động đã xảy ra và kết thúc trong quá khứ.\n\n**Dấu hiệu**: yesterday, last week/month/year, ago, in 2020.\n\n**Cấu trúc**:\n• (+) S + V-ed / V2 + O\n• (−) S + did + not + V + O\n• (?) Did + S + V + O?" },
      { heading: "3. Thì Hiện tại hoàn thành (Present Perfect)", content: "Diễn tả hành động đã xảy ra, không rõ thời điểm, hoặc còn tiếp tục.\n\n**Dấu hiệu**: already, yet, just, ever, never, since, for, so far, recently.\n\n**Cấu trúc**:\n• (+) S + have/has + V3/ed + O\n• (−) S + have/has + not + V3/ed + O\n• (?) Have/Has + S + V3/ed + O?" },
      { heading: "4. Thì Tương lai đơn (Future Simple)", content: "Diễn tả hành động sẽ xảy ra, quyết định tức thời, lời hứa, dự đoán.\n\n**Dấu hiệu**: tomorrow, next week/month/year, I think, probably.\n\n**Cấu trúc**:\n• (+) S + will + V + O\n• (−) S + will + not + V + O\n• (?) Will + S + V + O?" },
    ],
    formulas: [
      { name: "Present Simple (+)", formula: "S + V(s/es)", example: "She plays tennis every Sunday.", exampleVi: "Cô ấy chơi tennis mỗi Chủ nhật." },
      { name: "Past Simple (+)", formula: "S + V-ed / V2", example: "I visited Ha Noi last year.", exampleVi: "Tôi đã đến Hà Nội năm ngoái." },
      { name: "Present Perfect (+)", formula: "S + have/has + V3", example: "They have lived here since 2010.", exampleVi: "Họ đã sống ở đây từ 2010." },
      { name: "Future Simple (+)", formula: "S + will + V", example: "I will call you tomorrow.", exampleVi: "Tôi sẽ gọi bạn ngày mai." },
    ],
    exercises: [
      { question: "She ___ to school every day.", options: ["go", "goes", "going", "went"], correct: 1, explanation: "Thì hiện tại đơn, chủ ngữ 'She' (ngôi 3 số ít) → V thêm -es: goes." },
      { question: "They ___ a new house last month.", options: ["buy", "buys", "bought", "have bought"], correct: 2, explanation: "Dấu hiệu 'last month' → quá khứ đơn → bought (V2 của buy)." },
      { question: "I ___ this movie three times.", options: ["see", "saw", "have seen", "am seeing"], correct: 2, explanation: "Hành động lặp lại, không rõ thời điểm → hiện tại hoàn thành: have seen." },
      { question: "We ___ you at the party tomorrow.", options: ["see", "saw", "seeing", "will see"], correct: 3, explanation: "Dấu hiệu 'tomorrow' → tương lai đơn: will see." },
      { question: "He ___ English since he was 6.", options: ["learns", "learned", "has learned", "is learning"], correct: 2, explanation: "'since he was 6' → hiện tại hoàn thành: has learned." },
      { question: "My mother usually ___ dinner at 6 PM.", options: ["cook", "cooks", "cooked", "is cooking"], correct: 1, explanation: "'usually' → hiện tại đơn, chủ ngữ ngôi 3 → cooks." },
      { question: "They ___ to Japan last summer.", options: ["travel", "travels", "traveled", "have traveled"], correct: 2, explanation: "'last summer' → quá khứ đơn: traveled." },
      { question: "I think it ___ rain tonight.", options: ["will", "is", "was", "has"], correct: 0, explanation: "'I think' + dự đoán → tương lai đơn: will rain." },
      { question: "She has ___ finished her homework.", options: ["yet", "already", "ago", "yesterday"], correct: 1, explanation: "'already' dùng trong câu khẳng định hiện tại hoàn thành." },
      { question: "The sun ___ in the east.", options: ["rise", "rises", "rose", "has risen"], correct: 1, explanation: "Sự thật hiển nhiên → hiện tại đơn: rises (ngôi 3)." },
    ],
  },
  "passive-voice": {
    title: "Passive Voice", titleVi: "Câu bị động", emoji: "🔄",
    sections: [
      { heading: "1. Khái niệm", content: "Câu bị động dùng khi muốn nhấn mạnh đối tượng chịu tác động.\n\n**Công thức chung**: S + be + V3/ed + (by + O)" },
      { heading: "2. Chuyển đổi các thì", content: "• **Hiện tại đơn**: S + am/is/are + V3\n• **Quá khứ đơn**: S + was/were + V3\n• **Hiện tại hoàn thành**: S + have/has been + V3\n• **Tương lai đơn**: S + will be + V3" },
      { heading: "3. Lưu ý quan trọng", content: "• Tân ngữ (O) câu chủ động → Chủ ngữ (S) câu bị động.\n• Chủ ngữ câu chủ động → by + O.\n• Chỉ động từ CÓ TÂN NGỮ mới chuyển được sang bị động." },
    ],
    formulas: [
      { name: "Present Simple", formula: "S + am/is/are + V3", example: "English is spoken worldwide.", exampleVi: "Tiếng Anh được nói trên toàn giới." },
      { name: "Past Simple", formula: "S + was/were + V3", example: "The cake was made by my mom.", exampleVi: "Chiếc bánh được làm bởi mẹ tôi." },
      { name: "Present Perfect", formula: "S + have/has been + V3", example: "The report has been finished.", exampleVi: "Bản báo cáo đã được hoàn thành." },
      { name: "Future Simple", formula: "S + will be + V3", example: "The meeting will be held tomorrow.", exampleVi: "Cuộc họp sẽ được tổ chức ngày mai." },
    ],
    exercises: [
      { question: "This song ___ by millions of people.", options: ["love", "loves", "is loved", "loving"], correct: 2, explanation: "Bị động hiện tại đơn: is loved." },
      { question: "The window ___ by the boy yesterday.", options: ["broke", "was broken", "is broken", "has broken"], correct: 1, explanation: "'yesterday' → bị động quá khứ đơn: was broken." },
      { question: "The homework ___ already ___.", options: ["has / been done", "have / been done", "was / done", "is / done"], correct: 0, explanation: "'already' → bị động hiện tại hoàn thành: has been done." },
      { question: "A new school ___ next year.", options: ["builds", "built", "will be built", "is building"], correct: 2, explanation: "'next year' → bị động tương lai: will be built." },
      { question: "Milk ___ in many countries.", options: ["produce", "is produced", "produces", "producing"], correct: 1, explanation: "Sự thật → bị động hiện tại đơn: is produced." },
      { question: "The email ___ to all employees last week.", options: ["sent", "was sent", "is sent", "has sent"], correct: 1, explanation: "'last week' → bị động quá khứ đơn: was sent." },
      { question: "Many houses ___ by the storm.", options: ["destroyed", "were destroyed", "are destroyed", "destroying"], correct: 1, explanation: "Bị động quá khứ đơn: were destroyed." },
      { question: "The test results ___ tomorrow.", options: ["announce", "announced", "will be announced", "are announcing"], correct: 2, explanation: "'tomorrow' → bị động tương lai đơn: will be announced." },
    ],
  },
  "reported-speech": {
    title: "Reported Speech", titleVi: "Câu tường thuật", emoji: "💬",
    sections: [
      { heading: "1. Khái niệm", content: "Câu tường thuật dùng để thuật lại lời nói của người khác.\nVD: \"I am tired.\" → She said (that) she was tired." },
      { heading: "2. Quy tắc lùi thì", content: "• Present Simple → Past Simple\n• Present Continuous → Past Continuous\n• Present Perfect → Past Perfect\n• Past Simple → Past Perfect\n• will → would\n• can → could\n• may → might" },
      { heading: "3. Đổi đại từ & trạng từ", content: "• I → he/she  •  my → his/her\n• now → then  •  today → that day\n• tomorrow → the next day\n• yesterday → the day before\n• here → there  •  this → that" },
    ],
    formulas: [
      { name: "Câu trần thuật", formula: "S + said (that) + S + V (lùi thì)", example: "\"I like music.\" → He said he liked music.", exampleVi: "\"Tôi thích nhạc.\" → Anh ấy nói anh ấy thích nhạc." },
      { name: "Câu hỏi Yes/No", formula: "S + asked + if/whether + S + V", example: "\"Do you like it?\" → She asked if I liked it.", exampleVi: "\"Bạn thích không?\" → Cô ấy hỏi tôi có thích không." },
      { name: "Câu hỏi Wh-", formula: "S + asked + Wh- + S + V", example: "\"Where do you live?\" → He asked where I lived.", exampleVi: "\"Bạn sống ở đâu?\" → Anh ấy hỏi tôi sống ở đâu." },
    ],
    exercises: [
      { question: "\"I am happy.\" → She said she ___ happy.", options: ["is", "was", "has been", "would be"], correct: 1, explanation: "am → was (lùi thì)." },
      { question: "\"I will come tomorrow.\" → He said he ___ come the next day.", options: ["will", "would", "can", "could"], correct: 1, explanation: "will → would." },
      { question: "\"Do you speak English?\" → She asked me ___ I spoke English.", options: ["that", "what", "if", "do"], correct: 2, explanation: "Câu hỏi Yes/No → if/whether." },
      { question: "\"Where is the station?\" → He asked where the station ___.", options: ["is", "was", "were", "be"], correct: 1, explanation: "is → was." },
      { question: "\"I can swim.\" → She said she ___ swim.", options: ["can", "could", "may", "might"], correct: 1, explanation: "can → could." },
      { question: "\"We are studying.\" → They said they ___ studying.", options: ["are", "were", "have been", "had been"], correct: 1, explanation: "are → were." },
      { question: "\"I bought a car.\" → He said he ___ a car.", options: ["bought", "had bought", "has bought", "buys"], correct: 1, explanation: "bought → had bought." },
      { question: "\"Don't touch it!\" → She told me ___ touch it.", options: ["don't", "not to", "to not", "didn't"], correct: 1, explanation: "Mệnh lệnh phủ định → told + O + not to + V." },
    ],
  },
  conditionals: {
    title: "Conditionals", titleVi: "Câu điều kiện", emoji: "🔀",
    sections: [
      { heading: "1. Loại 0 — Sự thật hiển nhiên", content: "**If + S + V(s), S + V(s)**\nVD: If you heat water to 100°C, it boils." },
      { heading: "2. Loại 1 — Có thể xảy ra", content: "**If + S + V(s), S + will + V**\nVD: If it rains, I will stay home." },
      { heading: "3. Loại 2 — Không có thật ở hiện tại", content: "**If + S + V-ed, S + would + V**\nVD: If I were you, I would study harder.\n⚠️ Với \"be\" luôn dùng **were**." },
      { heading: "4. Loại 3 — Không có thật ở quá khứ", content: "**If + S + had V3, S + would have V3**\nVD: If I had studied harder, I would have passed." },
    ],
    formulas: [
      { name: "Type 0", formula: "If + V(s), S + V(s)", example: "If ice melts, it becomes water.", exampleVi: "Nếu đá tan, nó thành nước." },
      { name: "Type 1", formula: "If + V(s), S + will + V", example: "If you study, you will pass.", exampleVi: "Nếu bạn học, bạn sẽ đậu." },
      { name: "Type 2", formula: "If + V-ed, S + would + V", example: "If I had money, I would travel.", exampleVi: "Nếu tôi có tiền, tôi sẽ du lịch." },
      { name: "Type 3", formula: "If + had V3, S + would have V3", example: "If she had come, she would have seen.", exampleVi: "Nếu cô ấy đến, cô ấy đã thấy." },
    ],
    exercises: [
      { question: "If it rains, we ___ at home.", options: ["stay", "stayed", "will stay", "would stay"], correct: 2, explanation: "Loại 1: will + V." },
      { question: "If I ___ you, I would apologize.", options: ["am", "was", "were", "be"], correct: 2, explanation: "Loại 2: dùng 'were'." },
      { question: "If she had studied, she ___ the exam.", options: ["will pass", "would pass", "would have passed", "passes"], correct: 2, explanation: "Loại 3: would have + V3." },
      { question: "If you heat ice, it ___.", options: ["melt", "melts", "will melt", "would melt"], correct: 1, explanation: "Loại 0: V(s) cả 2 vế." },
      { question: "If I ___ a bird, I would fly.", options: ["am", "was", "were", "be"], correct: 2, explanation: "Loại 2: If + were." },
      { question: "If he ___ earlier, he wouldn't have missed the bus.", options: ["woke", "wakes", "had woken", "would wake"], correct: 2, explanation: "Loại 3: If + had V3." },
      { question: "I ___ call you if I have time.", options: ["would", "will", "can", "could"], correct: 1, explanation: "Loại 1: will + V." },
      { question: "If we ___ more trees, the air would be cleaner.", options: ["plant", "planted", "had planted", "will plant"], correct: 1, explanation: "Loại 2: If + V-ed." },
    ],
  },
  "relative-clauses": {
    title: "Relative Clauses", titleVi: "Mệnh đề quan hệ", emoji: "🔗",
    sections: [
      { heading: "1. Đại từ quan hệ", content: "• **who** — người (chủ ngữ)\n• **whom** — người (tân ngữ)\n• **which** — vật\n• **that** — cả người và vật\n• **whose** — sở hữu" },
      { heading: "2. Trạng từ quan hệ", content: "• **where** — nơi chốn\n• **when** — thời gian\n• **why** — lý do" },
      { heading: "3. Lưu ý", content: "• Xác định: KHÔNG dấu phẩy, cần thiết.\n• Không xác định: CÓ dấu phẩy, bổ sung.\n• Không xác định KHÔNG dùng 'that'." },
    ],
    formulas: [
      { name: "Who", formula: "N (person) + who + V", example: "The girl who sits next to me is kind.", exampleVi: "Cô gái ngồi cạnh tôi rất tốt bụng." },
      { name: "Which", formula: "N (thing) + which + V", example: "The book which I read was interesting.", exampleVi: "Cuốn sách tôi đọc rất thú vị." },
      { name: "Where", formula: "N (place) + where + S + V", example: "That's the school where I studied.", exampleVi: "Đó là trường tôi đã học." },
    ],
    exercises: [
      { question: "The man ___ lives next door is a teacher.", options: ["which", "who", "whom", "where"], correct: 1, explanation: "Người, chủ ngữ → who." },
      { question: "The book ___ I bought is really good.", options: ["who", "where", "which", "whose"], correct: 2, explanation: "Vật → which." },
      { question: "That's the restaurant ___ we had dinner.", options: ["which", "who", "that", "where"], correct: 3, explanation: "Nơi chốn → where." },
      { question: "The girl ___ bag was stolen cried.", options: ["who", "which", "whose", "whom"], correct: 2, explanation: "Sở hữu → whose." },
      { question: "I remember the day ___ we first met.", options: ["which", "where", "who", "when"], correct: 3, explanation: "Thời gian → when." },
      { question: "The teacher ___ I respect most is Mrs. Lan.", options: ["who", "whom", "which", "where"], correct: 1, explanation: "Người, tân ngữ → whom/who." },
    ],
  },
  comparisons: {
    title: "Comparisons", titleVi: "So sánh", emoji: "📊",
    sections: [
      { heading: "1. So sánh hơn", content: "• **Tính từ ngắn**: S + adj-ER + than\n• **Tính từ dài**: S + MORE + adj + than" },
      { heading: "2. So sánh nhất", content: "• **Ngắn**: S + THE + adj-EST\n• **Dài**: S + THE MOST + adj" },
      { heading: "3. Ngang bằng", content: "**S + as + adj + as + N**\nPhủ định: S + not as/so + adj + as" },
    ],
    formulas: [
      { name: "Hơn (ngắn)", formula: "S + adj-ER + than", example: "This road is longer than that one.", exampleVi: "Con đường này dài hơn." },
      { name: "Hơn (dài)", formula: "S + MORE + adj + than", example: "Math is more difficult than English.", exampleVi: "Toán khó hơn Anh." },
      { name: "Nhất (ngắn)", formula: "S + THE + adj-EST", example: "She is the youngest.", exampleVi: "Cô ấy nhỏ nhất." },
    ],
    exercises: [
      { question: "She is ___ than her sister.", options: ["tall", "taller", "tallest", "more tall"], correct: 1, explanation: "Ngắn → taller + than." },
      { question: "This is the ___ movie I've ever seen.", options: ["good", "better", "best", "most good"], correct: 2, explanation: "good → best." },
      { question: "English is ___ difficult ___ Math.", options: ["more/than", "most/in", "as/as", "the/of"], correct: 0, explanation: "Dài → more... than." },
      { question: "Tom is ___ tall ___ his brother.", options: ["as/as", "more/than", "the/est", "so/that"], correct: 0, explanation: "Ngang bằng: as + adj + as." },
      { question: "She is the ___ student in the class.", options: ["smart", "smarter", "smartest", "most smart"], correct: 2, explanation: "Nhất, ngắn → the smartest." },
      { question: "This exercise is ___ than the last one.", options: ["easy", "easier", "easiest", "more easy"], correct: 1, explanation: "easy → easier + than." },
    ],
  },
  "tag-questions": {
    title: "Tag Questions", titleVi: "Câu hỏi đuôi", emoji: "❓",
    sections: [
      { heading: "1. Quy tắc", content: "• Khẳng định → tag phủ định (và ngược lại).\n• Tag dùng trợ động từ tương ứng.\n• Chủ ngữ tag luôn là đại từ nhân xưng." },
      { heading: "2. Ví dụ", content: "• She is a student, **isn't she**?\n• They don't like coffee, **do they**?\n• He can swim, **can't he**?" },
      { heading: "3. Đặc biệt", content: "• I am → **aren't I?**\n• Let's → **shall we?**\n• Imperative → **will you?**\n• Nobody → tag **khẳng định**" },
    ],
    formulas: [
      { name: "KĐ → PĐ", formula: "S + V, aux + n't + pronoun?", example: "She likes music, doesn't she?", exampleVi: "Cô ấy thích nhạc, phải không?" },
      { name: "PĐ → KĐ", formula: "S + V not, aux + pronoun?", example: "They don't know, do they?", exampleVi: "Họ không biết, đúng không?" },
    ],
    exercises: [
      { question: "She is a doctor, ___?", options: ["is she", "isn't she", "does she", "doesn't she"], correct: 1, explanation: "KĐ (is) → PĐ: isn't she?" },
      { question: "They can't swim, ___?", options: ["can't they", "do they", "can they", "don't they"], correct: 2, explanation: "PĐ (can't) → KĐ: can they?" },
      { question: "You went to school, ___?", options: ["did you", "didn't you", "don't you", "do you"], correct: 1, explanation: "KĐ (went) → didn't you?" },
      { question: "I am right, ___?", options: ["am I", "aren't I", "don't I", "isn't I"], correct: 1, explanation: "I am → aren't I? (ngoại lệ)." },
      { question: "Let's go, ___?", options: ["shall we", "will we", "do we", "let we"], correct: 0, explanation: "Let's → shall we?" },
      { question: "He hasn't finished, ___?", options: ["hasn't he", "has he", "did he", "does he"], correct: 1, explanation: "PĐ (hasn't) → KĐ: has he?" },
    ],
  },
  "word-forms": {
    title: "Word Forms", titleVi: "Dạng từ", emoji: "🔤",
    sections: [
      { heading: "1. Vị trí từ loại", content: "• **N**: sau a/an/the, sau tính từ.\n• **Adj**: trước danh từ, sau be/look/seem.\n• **Adv**: cuối câu, trước V.\n• **V**: sau chủ ngữ, sau trợ động từ." },
      { heading: "2. Đuôi phổ biến", content: "• **N**: -tion, -ment, -ness, -ity, -ance\n• **Adj**: -ful, -less, -ous, -ive, -able\n• **Adv**: -ly\n• **V**: -ize, -fy, -en" },
    ],
    formulas: [
      { name: "V → N", formula: "V + -tion / -ment", example: "educate → education", exampleVi: "giáo dục → sự giáo dục" },
      { name: "N → Adj", formula: "N + -ful / -less", example: "beauty → beautiful", exampleVi: "đẹp" },
      { name: "Adj → Adv", formula: "Adj + -ly", example: "careful → carefully", exampleVi: "cẩn thận → một cách cẩn thận" },
    ],
    exercises: [
      { question: "She is a ___ student. (beauty)", options: ["beauty", "beautiful", "beautifully", "beautify"], correct: 1, explanation: "Trước N cần Adj: beautiful." },
      { question: "He drives very ___. (careful)", options: ["careful", "carefully", "careless", "care"], correct: 1, explanation: "Bổ nghĩa V cần Adv: carefully." },
      { question: "The ___ of the project is important. (succeed)", options: ["succeed", "successful", "successfully", "success"], correct: 3, explanation: "Sau 'The' cần N: success." },
      { question: "This exercise is ___. (difficulty)", options: ["difficulty", "difficult", "difficultly", "difficulties"], correct: 1, explanation: "Sau 'is' cần Adj: difficult." },
      { question: "They live ___ in the countryside. (happy)", options: ["happy", "happiness", "happily", "unhappy"], correct: 2, explanation: "Bổ nghĩa V cần Adv: happily." },
      { question: "The ___ was very interesting. (perform)", options: ["perform", "performer", "performance", "performing"], correct: 2, explanation: "Sau 'The' cần N: performance." },
      { question: "He is an ___ teacher. (experience)", options: ["experience", "experienced", "experiencing", "experiential"], correct: 1, explanation: "Trước N cần Adj: experienced." },
      { question: "She made a ___ decision. (wisdom)", options: ["wisdom", "wise", "wisely", "wiser"], correct: 1, explanation: "Trước N cần Adj: wise." },
    ],
  },
};

/* ═══════════════════════════════════════════════════════ */
export default function GrammarDetailPage() {
  const params = useParams();
  const topicId = params.topicId as string;
  const lesson = LESSONS[topicId];

  const [showExercise, setShowExercise] = useState(false);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [checked, setChecked] = useState(false);

  if (!lesson) {
    return (
      <div className="gd-page" style={{ textAlign: "center", paddingTop: 48 }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>📚</div>
        <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)", marginBottom: 8 }}>Chủ đề đang được xây dựng</h2>
        <p style={{ fontSize: 14, color: "var(--text-tertiary)", marginBottom: 16 }}>Chủ đề &quot;{topicId}&quot; sẽ sớm được cập nhật.</p>
        <Link href="/exam/english/grammar" style={{ color: "var(--action-primary)", fontSize: 14 }}>← Quay lại danh sách</Link>
      </div>
    );
  }

  const correctCount = checked ? lesson.exercises.filter((ex, i) => answers[i] === ex.correct).length : 0;
  const score10 = lesson.exercises.length > 0 ? Math.round(correctCount / lesson.exercises.length * 100) / 10 : 0;

  return (
    <div className="gd-page">
      <nav className="gd-breadcrumb">
        <Link href="/exam/english">English Lớp 10</Link>
        <span>/</span>
        <Link href="/exam/english/grammar">Ngữ pháp</Link>
        <span>/</span>
        <span>{lesson.title}</span>
      </nav>

      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 40, marginBottom: 8 }}>{lesson.emoji}</div>
        <h1 className="gd-title">{lesson.title}</h1>
        <p style={{ fontSize: 14, color: "var(--text-secondary)", margin: 0 }}>{lesson.titleVi}</p>
      </div>

      {/* Theory */}
      <div style={{ display: "flex", flexDirection: "column", gap: 20, marginBottom: 32 }}>
        {lesson.sections.map((sec, i) => (
          <div key={i} className="gd-section">
            <h2 className="gd-section-heading">
              <span className="gd-accent-bar" />
              {sec.heading}
            </h2>
            <div className="gd-section-body">
              {sec.content.split(/(\*\*.*?\*\*)/).map((part, j) =>
                part.startsWith("**") && part.endsWith("**")
                  ? <strong key={j} style={{ fontWeight: 700, color: "var(--text-primary)" }}>{part.slice(2, -2)}</strong>
                  : part
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Formulas */}
      {lesson.formulas.length > 0 && (
        <div style={{ marginBottom: 32 }}>
          <h2 className="gd-label">📐 Công thức</h2>
          <div className="gd-formulas">
            {lesson.formulas.map((f, i) => (
              <div key={i} className="gd-formula-card">
                <p className="gd-formula-name">{f.name}</p>
                <p className="gd-formula-text">{f.formula}</p>
                <p style={{ fontSize: 12, color: "var(--text-secondary)", fontStyle: "italic", margin: "8px 0 0" }}>✏️ {f.example}</p>
                <p style={{ fontSize: 11, color: "var(--text-tertiary)", margin: "2px 0 0" }}>→ {f.exampleVi}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Exercise toggle */}
      {!showExercise ? (
        <button className="gd-start-btn" onClick={() => setShowExercise(true)}>
          ✍️ Làm bài tập ({lesson.exercises.length} câu)
        </button>
      ) : (
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>✍️ Bài tập</h2>
            <button className="gd-hide-btn" onClick={() => setShowExercise(false)}>Ẩn bài tập</button>
          </div>

          {checked && (
            <div className="gd-score-box">
              <div className="gd-score-num" style={{ color: score10 >= 8 ? "#10b981" : score10 >= 6 ? "#f59e0b" : "#ef4444" }}>
                {score10}<span style={{ fontSize: 20, color: "var(--text-tertiary)" }}>/10</span>
              </div>
              <p style={{ fontSize: 13, color: "var(--text-secondary)", margin: 0 }}>{correctCount}/{lesson.exercises.length} câu đúng</p>
            </div>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {lesson.exercises.map((ex, i) => {
              const selected = answers[i];
              const isCorrect = selected === ex.correct;
              const itemCls = checked ? (isCorrect ? "gd-ex correct" : "gd-ex wrong") : "gd-ex";
              return (
                <div key={i} className={itemCls}>
                  <div className="gd-ex-header">
                    <span className={`gd-ex-num ${checked ? (isCorrect ? "correct" : "wrong") : ""}`}>{i + 1}</span>
                    <p className="gd-ex-question">{ex.question}</p>
                  </div>
                  <div className="gd-ex-options">
                    {ex.options.map((opt, j) => {
                      let cls = "gd-ex-opt";
                      if (checked) {
                        if (j === ex.correct) cls += " correct";
                        else if (j === selected) cls += " wrong";
                        else cls += " dim";
                      } else if (j === selected) cls += " selected";
                      return (
                        <button key={j} onClick={() => !checked && setAnswers(prev => ({ ...prev, [i]: j }))} disabled={checked} className={cls}>
                          <span className={`gd-ex-key ${checked && j === ex.correct ? "correct" : checked && j === selected ? "wrong" : j === selected ? "selected" : ""}`}>
                            {String.fromCharCode(65 + j)}
                          </span>
                          {opt}
                        </button>
                      );
                    })}
                  </div>
                  {checked && (
                    <div className="gd-ex-explain">💡 {ex.explanation}</div>
                  )}
                </div>
              );
            })}
          </div>

          <div style={{ display: "flex", gap: 12, marginTop: 20 }}>
            {!checked ? (
              <button className="gd-start-btn" onClick={() => setChecked(true)} disabled={Object.keys(answers).length < lesson.exercises.length}
                style={{ opacity: Object.keys(answers).length < lesson.exercises.length ? 0.4 : 1 }}>
                ✅ Kiểm tra ({Object.keys(answers).length}/{lesson.exercises.length})
              </button>
            ) : (
              <button className="gd-start-btn" onClick={() => { setAnswers({}); setChecked(false); }}>
                🔄 Làm lại
              </button>
            )}
          </div>
        </div>
      )}

      <style jsx global>{`
        .gd-page { max-width: 700px; margin: 0 auto; padding: 24px 16px; }
        .gd-breadcrumb { font-size: 13px; color: var(--text-tertiary); margin-bottom: 16px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
        .gd-breadcrumb a { color: var(--text-tertiary); text-decoration: none; }
        .gd-breadcrumb a:hover { color: var(--action-primary); }
        .gd-breadcrumb span:last-child { color: var(--text-primary); }
        .gd-title { font-size: 24px; font-weight: 900; color: var(--text-primary); margin: 0; }
        .gd-label { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; color: var(--text-tertiary); margin-bottom: 12px; }

        .gd-section { background: var(--bg-surface); border: 1px solid var(--border-default); border-radius: 12px; padding: 20px; box-shadow: var(--shadow-sm); }
        @media (max-width: 480px) { .gd-section { padding: 16px; } }
        .gd-section-heading { font-size: 15px; font-weight: 700; color: var(--text-primary); margin: 0 0 12px; display: flex; align-items: center; gap: 8px; }
        .gd-accent-bar { width: 4px; height: 20px; background: var(--action-primary); border-radius: 99px; flex-shrink: 0; }
        .gd-section-body { font-size: 13px; color: var(--text-secondary); line-height: 1.7; white-space: pre-line; }

        .gd-formulas { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
        @media (max-width: 640px) { .gd-formulas { grid-template-columns: 1fr; } }
        .gd-formula-card { background: var(--bg-interactive); border: 1px solid var(--border-default); border-radius: 12px; padding: 16px; }
        .gd-formula-name { font-size: 11px; font-weight: 700; color: var(--action-primary); text-transform: uppercase; letter-spacing: .04em; margin: 0 0 4px; }
        .gd-formula-text { font-size: 14px; font-weight: 900; color: var(--text-primary); font-family: monospace; margin: 0; }

        .gd-start-btn { width: 100%; border-radius: 12px; background: linear-gradient(135deg, #3b82f6, #6366f1); padding: 16px; color: white; font-weight: 700; font-size: 15px; border: none; cursor: pointer; transition: all 0.3s; }
        .gd-start-btn:hover { box-shadow: 0 6px 20px rgba(59,130,246,0.3); }
        .gd-start-btn:active { transform: scale(0.98); }
        .gd-start-btn:disabled { cursor: not-allowed; }
        .gd-hide-btn { font-size: 12px; color: var(--text-tertiary); background: none; border: none; cursor: pointer; }
        .gd-hide-btn:hover { color: var(--action-primary); }

        .gd-score-box { text-align: center; padding: 16px; margin-bottom: 16px; background: var(--bg-surface); border: 1px solid var(--border-default); border-radius: 12px; box-shadow: var(--shadow-sm); animation: gdScaleIn 0.3s ease; }
        .gd-score-num { font-size: 40px; font-weight: 900; margin-bottom: 4px; }

        .gd-ex { border-radius: 12px; border: 1px solid var(--border-default); background: var(--bg-surface); padding: 16px; transition: all 0.3s; }
        .gd-ex.correct { border-color: #22c55e; background: rgba(34,197,94,0.06); }
        .gd-ex.wrong { border-color: #ef4444; background: rgba(239,68,68,0.06); }
        .gd-ex-header { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 12px; }
        .gd-ex-num { flex-shrink: 0; width: 28px; height: 28px; border-radius: 50%; font-size: 12px; font-weight: 700; display: flex; align-items: center; justify-content: center; background: var(--bg-interactive); color: var(--text-secondary); }
        .gd-ex-num.correct { background: #22c55e; color: white; }
        .gd-ex-num.wrong { background: #ef4444; color: white; }
        .gd-ex-question { font-size: 14px; font-weight: 500; color: var(--text-primary); flex: 1; margin: 0; line-height: 1.5; }

        .gd-ex-options { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-left: 36px; }
        @media (max-width: 480px) { .gd-ex-options { grid-template-columns: 1fr; margin-left: 0; } }
        .gd-ex-opt { display: flex; align-items: center; gap: 8px; border-radius: 8px; border: 1px solid var(--border-default); background: var(--bg-surface); padding: 8px 12px; font-size: 13px; text-align: left; color: var(--text-primary); cursor: pointer; transition: all 0.2s; }
        .gd-ex-opt:hover { border-color: var(--action-primary); }
        .gd-ex-opt.selected { border-color: var(--action-primary); background: var(--bg-interactive); color: var(--action-primary); font-weight: 500; }
        .gd-ex-opt.correct { border-color: #22c55e; background: rgba(34,197,94,0.08); color: #15803d; font-weight: 600; }
        .gd-ex-opt.wrong { border-color: #ef4444; background: rgba(239,68,68,0.08); color: #dc2626; }
        .gd-ex-opt.dim { color: var(--text-disabled); }

        .gd-ex-key { flex-shrink: 0; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 700; border: 1px solid var(--border-default); color: var(--text-tertiary); }
        .gd-ex-key.selected { background: var(--action-primary); color: white; border-color: var(--action-primary); }
        .gd-ex-key.correct { background: #22c55e; color: white; border-color: #22c55e; }
        .gd-ex-key.wrong { background: #ef4444; color: white; border-color: #ef4444; }

        .gd-ex-explain { margin-left: 36px; margin-top: 8px; font-size: 12px; color: var(--text-secondary); background: var(--bg-interactive); border: 1px solid var(--border-default); border-radius: 8px; padding: 8px 12px; }
        @media (max-width: 480px) { .gd-ex-explain { margin-left: 0; } }

        @keyframes gdScaleIn { from { transform: scale(0.95); opacity: 0; } to { transform: scale(1); opacity: 1; } }
      `}</style>
    </div>
  );
}
