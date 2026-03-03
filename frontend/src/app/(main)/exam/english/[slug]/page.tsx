"use client";
import { useEffect, useState, useRef, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useSidebar } from "@/hooks/useSidebar";

/* ── Types ── */
interface Choice { key: string; text: string; }
interface Question {
  id: number; num: number; text: string; text_vi: string;
  choices: Choice[]; correct_answer: string;
  explanation_json: Record<string, string>;
  section_type: string;
}
interface Passage { id: number; title: string; text: string; instruction: string; }
interface Section { type: string; title: string; passage: Passage | null; questions: Question[]; }
interface ExamData {
  id: number; title: string; slug: string; description: string;
  total_questions: number; time_limit_minutes: number; sections: Section[];
  is_vip?: boolean;
}

/* ── localStorage helpers ── */
const PROGRESS_KEY = (slug: string) => `en10_exam_${slug}`;
const HISTORY_KEY = (slug: string) => `en10_history_${slug}`;
interface ExamProgress {
  answers: Record<number, string>;
  flagged: number[];
}
interface AttemptRecord {
  correct: number;
  total: number;
  percent: number;
  date: string; // ISO string
}
function loadProgress(slug: string): ExamProgress | null {
  try { const r = localStorage.getItem(PROGRESS_KEY(slug)); return r ? JSON.parse(r) : null; } catch { return null; }
}
function saveProgress(slug: string, p: ExamProgress) {
  try { localStorage.setItem(PROGRESS_KEY(slug), JSON.stringify(p)); } catch {}
}
function clearProgress(slug: string) {
  try { localStorage.removeItem(PROGRESS_KEY(slug)); } catch {}
}
function loadHistory(slug: string): AttemptRecord[] {
  try { const r = localStorage.getItem(HISTORY_KEY(slug)); return r ? JSON.parse(r) : []; } catch { return []; }
}
function saveHistory(slug: string, records: AttemptRecord[]) {
  try { localStorage.setItem(HISTORY_KEY(slug), JSON.stringify(records)); } catch {}
}

export default function EnglishExamDetailPage() {
  const params = useParams();
  const slug = params.slug as string;
  const { collapsed, toggleCollapse } = useSidebar();

  const [exam, setExam] = useState<ExamData | null>(null);
  const [loading, setLoading] = useState(true);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [showNav, setShowNav] = useState(false);
  const [flagged, setFlagged] = useState<Set<number>>(new Set());
  const [justAnswered, setJustAnswered] = useState<number | null>(null);
  const [attemptHistory, setAttemptHistory] = useState<AttemptRecord[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [showSentenceChoices, setShowSentenceChoices] = useState(false);
  const [mounted, setMounted] = useState(false);
  const questionRefs = useRef<Record<number, HTMLDivElement | null>>({});
  const wasCollapsedRef = useRef(collapsed);

  const allQuestions = exam?.sections.flatMap(s => s.questions) || [];

  // Auto-collapse sidebar on mount, restore on unmount
  useEffect(() => {
    wasCollapsedRef.current = collapsed;
    if (!collapsed) toggleCollapse();
    setTimeout(() => setMounted(true), 50);
    return () => {
      if (!wasCollapsedRef.current) toggleCollapse();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    fetch(`/api/v1/exam/english/${slug}`, { credentials: "include" })
      .then(r => r.json())
      .then((d: ExamData) => {
        setExam(d);
        const saved = loadProgress(slug);
        if (saved) {
          setAnswers(saved.answers || {});
          if (saved.flagged) setFlagged(new Set(saved.flagged));
        }
        setAttemptHistory(loadHistory(slug));
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [slug]);

  // Auto-save
  useEffect(() => {
    if (!exam) return;
    saveProgress(slug, { answers, flagged: Array.from(flagged) });
  }, [answers, slug, exam, flagged]);

  const handleSelect = useCallback((qNum: number, key: string) => {
    if (answers[qNum]) return;
    setAnswers(prev => ({ ...prev, [qNum]: key }));
    setJustAnswered(qNum);
    setTimeout(() => setJustAnswered(null), 800);
  }, [answers]);

  const toggleFlag = useCallback((qNum: number) => {
    setFlagged(prev => {
      const next = new Set(prev);
      if (next.has(qNum)) next.delete(qNum); else next.add(qNum);
      return next;
    });
  }, []);

  const correctCount = allQuestions.filter(q => answers[q.num] === q.correct_answer).length;
  const answeredCount = Object.keys(answers).length;
  const totalQ = allQuestions.length;
  const allDone = answeredCount === totalQ && totalQ > 0;
  const scorePercent = totalQ ? Math.round(correctCount / totalQ * 100) : 0;
  const score10 = totalQ ? Math.round(correctCount / totalQ * 100) / 10 : 0;

  const handleRetry = useCallback(() => {
    // Archive current attempt if completed
    if (allDone && totalQ > 0) {
      const record: AttemptRecord = {
        correct: correctCount,
        total: totalQ,
        percent: scorePercent,
        date: new Date().toISOString(),
      };
      const history = loadHistory(slug);
      history.push(record);
      saveHistory(slug, history);
      setAttemptHistory(history);
    }
    clearProgress(slug);
    setAnswers({});
    setFlagged(new Set());
    setShowHistory(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [slug, allDone, totalQ, correctCount, scorePercent]);

  const scrollToQuestion = (num: number) => {
    questionRefs.current[num]?.scrollIntoView({ behavior: "smooth", block: "center" });
    setShowNav(false);
  };

  if (loading) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="relative">
        <div className="h-10 w-10 animate-spin rounded-full border-3 border-blue-500 border-t-transparent" />
        <div className="absolute inset-0 h-10 w-10 animate-ping rounded-full border border-blue-300 opacity-20" />
      </div>
    </div>
  );
  if (!exam) return (
    <div className="p-8 text-center animate-[fadeIn_0.4s_ease]">
      <p className="text-gray-500 text-base">Không tìm thấy đề thi.</p>
      <Link href="/exam/english/" className="text-blue-500 text-sm mt-2 inline-block hover:underline">← Quay lại</Link>
    </div>
  );

  // VIP gate
  if (exam.is_vip === false) {
    return (
      <div className="max-w-[500px] mx-auto px-4 py-12 text-center animate-[fadeIn_0.5s_ease]">
        <div className="text-6xl mb-4 animate-bounce">🔒</div>
        <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100 mb-2">{exam.title}</h2>
        <p className="text-sm text-gray-500 mb-1">{exam.total_questions} câu · {exam.time_limit_minutes} phút</p>
        <p className="text-sm text-gray-400 mb-6">Bạn cần tài khoản VIP để truy cập đề thi này.</p>
        <div className="flex flex-col gap-3 items-center">
          <a href="https://zalo.me/0962715898" target="_blank" rel="noopener noreferrer"
            className="inline-block rounded-lg bg-blue-500 px-8 py-2.5 text-sm font-bold text-white hover:bg-blue-600 transition-all duration-200 no-underline hover:shadow-lg hover:shadow-blue-500/30 hover:-translate-y-0.5 active:scale-[0.97]">
            💬 Liên hệ mở khóa qua Zalo
          </a>
          <Link href="/exam/english/" className="text-sm text-gray-400 hover:text-blue-500 transition-colors duration-200">← Quay lại danh sách</Link>
        </div>
      </div>
    );
  }

  return (
    <div className={`px-4 sm:px-6 py-4 pb-24 max-w-[960px] mx-auto transition-all duration-500 ${mounted ? "opacity-100" : "opacity-0"}`}>
      {/* Breadcrumb */}
      <nav className="mb-4 text-sm text-gray-400 flex items-center gap-1">
        <Link href="/exam/english/" className="hover:text-blue-500 transition-colors duration-200">English Lớp 10</Link>
        <span>/</span>
        <span className="text-gray-600 dark:text-gray-300">{exam.title}</span>
      </nav>

      {/* Score summary when all done */}
      {allDone && (
        <div className="mb-5 bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 text-center animate-[scaleIn_0.4s_ease]">
          <div className="text-5xl font-black mb-2 transition-all duration-500" style={{ color: score10 >= 8 ? "#10b981" : score10 >= 6 ? "#f59e0b" : "#ef4444" }}>
            {score10}<span className="text-2xl font-bold text-gray-400">/10</span>
          </div>
          <p className="text-base text-gray-500">{correctCount}/{totalQ} câu đúng</p>
          <p className="text-sm text-gray-400 mt-1 mb-4">
            {score10 >= 8 ? "🎉 Xuất sắc!" : score10 >= 6 ? "👍 Khá tốt!" : "💪 Cần ôn luyện thêm!"}
          </p>
          <div className="flex gap-3 justify-center flex-wrap">
            <button onClick={handleRetry}
              className="rounded-lg bg-gray-200 dark:bg-gray-700 px-5 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-300 transition-all duration-200 hover:-translate-y-0.5 active:scale-[0.97]">
              🔄 Làm lại
            </button>
            <Link href={`/exam/english/${slug}/review`}
              className="rounded-lg bg-blue-500 px-5 py-2 text-sm font-medium text-white hover:bg-blue-600 transition-all duration-200 inline-flex items-center gap-1 hover:-translate-y-0.5 hover:shadow-md hover:shadow-blue-500/25 active:scale-[0.97]">
              📚 Ôn tập kiến thức
            </Link>
            {attemptHistory.length > 0 && (
              <button onClick={() => setShowHistory(!showHistory)}
                className="rounded-lg bg-indigo-100 dark:bg-indigo-900/30 px-5 py-2 text-sm font-medium text-indigo-600 dark:text-indigo-300 hover:bg-indigo-200 transition-all duration-200 hover:-translate-y-0.5 active:scale-[0.97]">
                📊 Lịch sử ({attemptHistory.length})
              </button>
            )}
          </div>

          {/* Attempt History */}
          {showHistory && attemptHistory.length > 0 && (
            <div className="mt-4 text-left animate-[slideDown_0.3s_ease]">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-semibold text-gray-600 dark:text-gray-300">📋 Lịch sử làm bài</p>
                <button
                  onClick={() => { saveHistory(slug, []); setAttemptHistory([]); setShowHistory(false); }}
                  className="text-xs text-red-400 hover:text-red-500 transition-colors"
                >Xóa lịch sử</button>
              </div>
              <div className="space-y-2">
                {[...attemptHistory].reverse().map((a, i) => {
                  const attemptNum = attemptHistory.length - i;
                  return (
                    <div key={i}
                      className="flex items-center justify-between rounded-lg bg-gray-50 dark:bg-gray-700/40 px-4 py-2.5 text-sm"
                      style={{ animation: `slideUp 0.3s ease-out ${i * 0.05}s both` }}
                    >
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-gray-200 dark:bg-gray-600 text-xs font-bold flex items-center justify-center text-gray-500 dark:text-gray-300">
                          {attemptNum}
                        </span>
                        <span className="text-gray-500 dark:text-gray-400">
                          {new Date(a.date).toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-gray-500">{a.correct}/{a.total}</span>
                        <span
                          className="px-2.5 py-0.5 rounded-full text-xs font-bold text-white"
                          style={{ backgroundColor: (a.percent / 10) >= 8 ? "#10b981" : (a.percent / 10) >= 6 ? "#f59e0b" : "#ef4444" }}
                        >
                          {Math.round(a.percent) / 10}/10
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* History badge when not all done but has history */}
      {!allDone && attemptHistory.length > 0 && (
        <div className="mb-4 flex items-center gap-2 text-sm text-indigo-500 animate-[fadeIn_0.4s_ease]">
          <span>📊</span>
          <span>Lần thi trước: <strong>{Math.round(attemptHistory[attemptHistory.length - 1].percent) / 10}/10</strong> ({attemptHistory[attemptHistory.length - 1].correct}/{attemptHistory[attemptHistory.length - 1].total})</span>
          <span className="text-gray-300">·</span>
          <span className="text-gray-400">Đã làm {attemptHistory.length} lần</span>
        </div>
      )}

      {/* Sections */}
      {exam.sections.map((section, si) => (
        <div key={si} className="mb-5" style={{ animation: `slideUp 0.4s ease-out ${si * 0.1}s both` }}>
          {/* Section instruction */}
          <p className="text-[13px] text-gray-500 dark:text-gray-400 leading-relaxed mb-2 italic px-1">
            {section.title}
          </p>

          {/* Passage */}
          {section.passage && (
            <div className="mb-2 bg-gray-50 dark:bg-gray-800/60 rounded-lg p-4 text-[13px] leading-relaxed text-gray-700 dark:text-gray-300 border border-gray-100 dark:border-gray-700/50">
              {section.passage.title && (
                <p className="text-center font-bold text-gray-800 dark:text-gray-100 mb-2 text-[14px]">{section.passage.title}</p>
              )}
              <div className="whitespace-pre-line" dangerouslySetInnerHTML={{ __html: section.passage.text }} />
            </div>
          )}

          {/* Sentence insertion: show shared choices A-D behind toggle */}
          {section.type === 'sentence_insertion' && section.questions.length > 0 && (
            <div className="mb-2">
              <button
                onClick={() => setShowSentenceChoices(!showSentenceChoices)}
                className="w-full flex items-center justify-between bg-white dark:bg-gray-800/40 rounded-xl px-4 py-3 shadow-sm border border-gray-100 dark:border-gray-700/50 text-[13px] font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-all duration-200"
              >
                <span>📋 Xem đáp án A, B, C, D</span>
                <span className={`transition-transform duration-200 ${showSentenceChoices ? 'rotate-180' : ''}`}>▼</span>
              </button>
              <div className={`overflow-hidden transition-all duration-300 ${showSentenceChoices ? 'max-h-[300px] opacity-100 mt-1' : 'max-h-0 opacity-0'}`}>
                <div className="bg-white dark:bg-gray-800/40 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700/50">
                  {section.questions[0].choices.map((c: Choice) => (
                    <p key={c.key} className="text-[13px] text-gray-700 dark:text-gray-200 py-1 leading-relaxed"><strong>{c.key}.</strong> {c.text}</p>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Questions — continuous */}
          <div className="bg-white dark:bg-gray-800/40 rounded-xl overflow-hidden shadow-sm">
            {section.questions.map((q, qi) => {
              const selected = answers[q.num];
              const isCorrect = selected === q.correct_answer;
              const showResult = !!selected;
              const isFlagged = flagged.has(q.num);
              const isShort = q.choices.every(c => c.text.replace(/<[^>]*>/g, "").length <= 30);
              const wasJustAnswered = justAnswered === q.num;
              const isCloze = q.section_type === 'cloze_reading';
              const isSentenceInsertion = q.section_type === 'sentence_insertion';
              const hideQuestionText = isCloze;  // Only hide for fill-in-blank

              return (
                <div
                  key={q.id}
                  ref={(el) => { questionRefs.current[q.num] = el; }}
                  className={`px-5 py-4 transition-all duration-500 ${
                    qi > 0 ? "border-t border-gray-100 dark:border-gray-700/50" : ""
                  } ${
                    showResult
                      ? isCorrect
                        ? `bg-emerald-50/60 dark:bg-emerald-900/15 ${wasJustAnswered ? "animate-[correctPulse_0.6s_ease]" : ""}`
                        : "bg-red-50/40 dark:bg-red-900/10"
                      : isFlagged ? "bg-amber-50/60 dark:bg-amber-900/15" : ""
                  }`}
                >
                  {/* Question header */}
                  <div className={`flex items-start gap-2.5 ${hideQuestionText ? 'mb-1' : 'mb-3'}`}>
                    <span className={`flex-shrink-0 w-7 h-7 rounded-full text-xs font-bold flex items-center justify-center transition-all duration-300 ${
                      showResult
                        ? isCorrect ? "bg-emerald-500 text-white shadow-sm shadow-emerald-500/30 scale-110" : "bg-red-500 text-white shadow-sm shadow-red-500/30"
                        : selected ? "bg-blue-500 text-white" : "bg-gray-200 dark:bg-gray-600 text-gray-500 dark:text-gray-300"
                    }`}>{q.num}</span>
                    {/* Show question text for non-cloze types */}
                    {!hideQuestionText && !isSentenceInsertion && (
                      <p className="text-[13px] text-gray-800 dark:text-gray-100 leading-relaxed flex-1 whitespace-pre-line">{q.text}</p>
                    )}
                    {(hideQuestionText || isSentenceInsertion) && <div className="flex-1" />}
                    {/* Flag button */}
                    {!selected && (
                      <button
                        onClick={() => toggleFlag(q.num)}
                        className={`flex-shrink-0 text-base transition-all duration-200 hover:scale-125 active:scale-90 ${isFlagged ? "text-amber-400" : "text-gray-300 hover:text-amber-400"}`}
                        title="Đánh dấu câu hỏi"
                      >
                        {isFlagged ? "🚩" : "⚑"}
                      </button>
                    )}
                    {/* Correct/wrong indicator */}
                    {showResult && (
                      <span className={`text-base transition-all duration-300 ${wasJustAnswered ? "animate-[popIn_0.3s_ease]" : ""}`}>
                        {isCorrect ? "✅" : "❌"}
                      </span>
                    )}
                  </div>

                  {/* Sentence insertion: dropdown instead of normal choices */}
                  {isSentenceInsertion ? (
                    <div className="ml-9">
                      <select
                        value={selected || ""}
                        onChange={(e) => e.target.value && handleSelect(q.num, e.target.value)}
                        disabled={!!selected}
                        className={`w-full max-w-[200px] rounded-lg border px-3 py-2 text-[13px] transition-all duration-200 appearance-none cursor-pointer ${
                          showResult
                            ? isCorrect
                              ? "border-emerald-400 bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300"
                              : "border-red-400 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-300"
                            : "border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:border-blue-400"
                        }`}
                      >
                        <option value="">-- Chọn --</option>
                        {["A","B","C","D"].map(k => (
                          <option key={k} value={k}>{k}</option>
                        ))}
                      </select>
                      {showResult && (
                        <span className="ml-2 text-[12px] text-gray-500">Đáp án: <strong className="text-emerald-600">{q.correct_answer}</strong></span>
                      )}
                    </div>
                  ) : (
                  /* Normal choices */
                  <div className={`ml-9 gap-2 ${isShort ? "grid grid-cols-2 sm:grid-cols-4" : "grid grid-cols-1"}`}>
                    {q.choices.map((c) => {
                      const isSelected = selected === c.key;
                      const isAnswer = c.key === q.correct_answer;
                      let cls = "hover:bg-gray-100/50 dark:hover:bg-gray-700/30 cursor-pointer text-gray-700 dark:text-gray-200 hover:shadow-sm hover:-translate-y-px";

                      if (showResult) {
                        if (isAnswer) cls = "bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 font-medium ring-1 ring-emerald-300 dark:ring-emerald-600 shadow-sm shadow-emerald-500/10";
                        else cls = "text-gray-700 dark:text-gray-200";
                      } else if (isSelected) {
                        cls = "bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-300 ring-1 ring-blue-300 dark:ring-blue-600";
                      }

                      return (
                        <button
                          key={c.key}
                          onClick={() => handleSelect(q.num, c.key)}
                          disabled={!!selected}
                          className={`flex items-center gap-2 rounded-lg px-3 py-2 text-left text-[13px] transition-all duration-200 active:scale-[0.98] ${cls}`}
                        >
                          <span className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold border transition-all duration-200 ${
                            showResult && isAnswer ? "bg-emerald-500 text-white border-emerald-500 shadow-sm" :
                            showResult && isSelected ? "bg-red-400 text-white border-red-400" :
                            isSelected ? "bg-blue-500 text-white border-blue-500" :
                            "border-gray-300 dark:border-gray-500 text-gray-400 group-hover:border-blue-400"
                          }`}>{c.key}</span>
                          <span className="flex-1 [&_u]:underline [&_u]:decoration-2 [&_u]:decoration-blue-400 [&_u]:font-semibold" dangerouslySetInnerHTML={{ __html: c.text }} />
                          {showResult && isAnswer && <span className="text-emerald-500 text-[13px] animate-[popIn_0.3s_ease]">✓</span>}
                        </button>
                      );
                    })}
                  </div>
                  )}

                  {/* Explanation */}
                  {showResult && q.explanation_json && Object.keys(q.explanation_json).length > 0 && (
                    <div className="mt-3 ml-9 rounded-lg bg-blue-50 dark:bg-blue-900/20 p-3 animate-[slideDown_0.3s_ease] border border-blue-100 dark:border-blue-800/30">
                      <p className="text-sm font-semibold text-blue-600 dark:text-blue-400 mb-1">
                        💡 {q.explanation_json.rule || "Giải thích"}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">{q.explanation_json.detail}</p>
                      {q.explanation_json.tip && (
                        <p className="text-xs text-gray-400 mt-1.5 flex items-center gap-1">
                          <span className="inline-block animate-pulse">📌</span> {q.explanation_json.tip}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}

      {/* Fixed bottom bar */}
      <div className="fixed bottom-0 left-0 right-0 z-50 bg-white/95 dark:bg-gray-900/95 backdrop-blur-md border-t border-gray-200 dark:border-gray-700 transition-all duration-300">
        <div className="max-w-[960px] mx-auto flex items-center justify-between px-4 py-2.5">
          {/* Live score with animation */}
          <div className={`text-sm font-bold px-3 py-1.5 rounded-lg transition-all duration-300 ${
            answeredCount === 0 ? "text-gray-400 bg-gray-100 dark:bg-gray-800" :
            "text-emerald-600 bg-emerald-50 dark:bg-emerald-900/30"
          }`}>
            <span className={justAnswered !== null ? "animate-[popIn_0.3s_ease]" : ""}>✓ {correctCount}/{answeredCount}</span>
          </div>

          <button onClick={() => setShowNav(!showNav)}
            className="text-sm text-gray-400 hover:text-blue-500 transition-all duration-200 flex items-center gap-1.5 hover:scale-105 active:scale-95">
            {answeredCount}/{totalQ} đã trả lời
            {flagged.size > 0 && <span className="text-amber-400 ml-1 animate-pulse">🚩{flagged.size}</span>}
            <span className={`inline-block transition-transform duration-200 ${showNav ? "rotate-180" : ""}`}>▲</span>
          </button>

          {answeredCount > 0 ? (
            <button onClick={handleRetry}
              className="rounded-lg bg-blue-500 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-600 transition-all duration-200 hover:shadow-md hover:shadow-blue-500/25 hover:-translate-y-0.5 active:scale-[0.97]">
              🔄 Làm lại
            </button>
          ) : (
            <span className="text-sm text-gray-300">{totalQ} câu</span>
          )}
        </div>

        {/* Navigation grid with transition */}
        <div className={`border-t border-gray-200 dark:border-gray-700 overflow-hidden transition-all duration-300 ${showNav ? "max-h-40 opacity-100" : "max-h-0 opacity-0"}`}>
          <div className="px-4 py-2">
            <div className="max-w-[960px] mx-auto grid grid-cols-10 gap-1">
              {allQuestions.map(q => {
                const sel = answers[q.num];
                const isRight = sel === q.correct_answer;
                const isFl = flagged.has(q.num);
                let cls = "bg-gray-100 dark:bg-gray-700 text-gray-400";
                if (sel) {
                  cls = isRight
                    ? "bg-emerald-500 text-white shadow-sm shadow-emerald-500/30"
                    : "bg-red-400 text-white shadow-sm shadow-red-500/30";
                } else if (isFl) {
                  cls = "bg-amber-400 text-white shadow-sm shadow-amber-500/30";
                }
                return (
                  <button key={q.num} onClick={() => scrollToQuestion(q.num)}
                    className={`rounded-md text-[11px] font-bold py-1.5 transition-all duration-200 hover:scale-110 hover:-translate-y-0.5 active:scale-95 ${cls}`}>
                    {q.num}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Global keyframes */}
      <style jsx global>{`
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideDown {
          from { opacity: 0; transform: translateY(-8px); max-height: 0; }
          to { opacity: 1; transform: translateY(0); max-height: 200px; }
        }
        @keyframes scaleIn {
          from { opacity: 0; transform: scale(0.9); }
          to { opacity: 1; transform: scale(1); }
        }
        @keyframes popIn {
          0% { transform: scale(0); opacity: 0; }
          60% { transform: scale(1.2); }
          100% { transform: scale(1); opacity: 1; }
        }
        @keyframes correctPulse {
          0% { background-color: rgba(16,185,129,0); }
          30% { background-color: rgba(16,185,129,0.15); }
          100% { background-color: rgba(16,185,129,0.06); }
        }
        @keyframes wrongShake {
          0%, 100% { transform: translateX(0); }
          20% { transform: translateX(-6px); }
          40% { transform: translateX(6px); }
          60% { transform: translateX(-4px); }
          80% { transform: translateX(4px); }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
      `}</style>
    </div>
  );
}
