"use client";
import { useEffect, useState, useCallback, useMemo, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useSidebar } from "@/hooks/useSidebar";
import { getUserPrefSync, setUserPref } from "@/lib/user-prefs";

/* ── Types ── */
interface Choice { key: string; text: string; }
interface Word { word: string; ipa: string; underline?: string; sound?: string; stress_pos?: number; }
interface Pair { left: string; right: string; }

interface ReviewItem {
  type: string;
  source_q?: number;
  front?: string; front_ipa?: string; back?: string; example?: string; example_vi?: string;
  instruction?: string; words?: Word[]; correct_answer?: string; rule?: string; explanation?: string;
  question?: string; choices?: Choice[];
  original?: string; keyword?: string;
  pairs?: Pair[]; distractors?: string[];
}

interface ReviewData {
  exam_slug: string; exam_title: string;
  items: ReviewItem[]; total: number; types: string[];
}

/* ── review progress helpers ── */
interface ReviewProgress {
  activeType: string | null;
  currentIdx: number;
  answers: Record<string, string>;
  score: { correct: number; total: number };
}
function loadReviewProgress(slug: string): ReviewProgress | null {
  return getUserPrefSync<ReviewProgress>(`review-progress-${slug}`);
}
function saveReviewProgress(slug: string, p: ReviewProgress) {
  setUserPref(`review-progress-${slug}`, p).catch(() => {});
}

const TYPE_LABELS: Record<string, { label: string; icon: string; desc: string }> = {
  vocab_flashcard: { label: "Từ vựng", icon: "📝", desc: "Flashcard từ vựng" },
  pronunciation_ipa: { label: "Phát âm", icon: "🔊", desc: "IPA & quy tắc phát âm" },
  stress_drill: { label: "Trọng âm", icon: "🎯", desc: "Quy tắc trọng âm" },
  grammar_drill: { label: "Ngữ pháp", icon: "📖", desc: "Cấu trúc & công thức" },
  fill_in_blank: { label: "Điền từ", icon: "✏️", desc: "Điền từ vào chỗ trống" },
  match_collocation: { label: "Collocation", icon: "🔗", desc: "Nối cặp từ" },
  sentence_transform: { label: "Viết lại câu", icon: "🔄", desc: "Chuyển đổi câu" },
};

export default function ReviewPage() {
  const params = useParams();
  const slug = params.slug as string;
  const { collapsed, toggleCollapse } = useSidebar();

  const [data, setData] = useState<ReviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeType, setActiveType] = useState<string | null>(null);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [showAnswer, setShowAnswer] = useState(false);
  const [flipped, setFlipped] = useState(false);
  const [matchSelections, setMatchSelections] = useState<Record<string, string>>({});
  const [matchSubmitted, setMatchSubmitted] = useState(false);
  const [score, setScore] = useState({ correct: 0, total: 0 });
  const [dbResults, setDbResults] = useState<Record<string, { correct_count: number; total_count: number; completed: boolean }>>({});
  const [slideDir, setSlideDir] = useState<"left" | "right">("left");
  const [animating, setAnimating] = useState(false);
  const [mounted, setMounted] = useState(false);
  const wasCollapsedRef = useRef(collapsed);

  useEffect(() => {
    wasCollapsedRef.current = collapsed;
    if (!collapsed) toggleCollapse();
    setTimeout(() => setMounted(true), 50);
    return () => { if (!wasCollapsedRef.current) toggleCollapse(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    fetch(`/api/v1/exam/english/${slug}/review`, { credentials: "include" })
      .then(r => r.json())
      .then(d => {
        setData(d);
        const saved = loadReviewProgress(slug);
        if (saved) {
          setActiveType(saved.activeType);
          setCurrentIdx(saved.currentIdx);
          setAnswers(saved.answers);
          setScore(saved.score);
          if (saved.activeType && saved.answers[`${saved.activeType}_${saved.currentIdx}`]) {
            setShowAnswer(true);
          }
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));

    fetch(`/api/v1/exam/english/${slug}/review/my-results`, { credentials: "include" })
      .then(r => { if (r.ok) return r.json(); throw new Error(); })
      .then(d => {
        const map: Record<string, { correct_count: number; total_count: number; completed: boolean }> = {};
        for (const r of d.results || []) {
          map[r.quiz_type] = { correct_count: r.correct_count, total_count: r.total_count, completed: r.completed };
        }
        setDbResults(map);
      })
      .catch(() => {});
  }, [slug]);

  useEffect(() => {
    if (!data) return;
    saveReviewProgress(slug, { activeType, currentIdx, answers, score });
  }, [activeType, currentIdx, answers, score, slug, data]);

  const saveToDb = useCallback((quizType: string, correct: number, total: number, ans: Record<string, string>, completed: boolean) => {
    fetch(`/api/v1/exam/english/${slug}/review/save`, {
      method: "POST", credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ quiz_type: quizType, correct_count: correct, total_count: total, answers_json: ans, completed }),
    })
      .then(r => { if (r.ok) return r.json(); })
      .then(() => { setDbResults(prev => ({ ...prev, [quizType]: { correct_count: correct, total_count: total, completed } })); })
      .catch(() => {});
  }, [slug]);

  const filteredItems = useMemo(() => {
    if (!data || !activeType) return [];
    return data.items.filter(i => i.type === activeType);
  }, [data, activeType]);

  const currentItem = filteredItems[currentIdx] || null;

  const animateTransition = useCallback((dir: "left" | "right", cb: () => void) => {
    setSlideDir(dir);
    setAnimating(true);
    setTimeout(() => {
      cb();
      setAnimating(false);
    }, 200);
  }, []);

  const goNext = useCallback(() => {
    animateTransition("left", () => {
      setShowAnswer(false);
      setFlipped(false);
      setMatchSelections({});
      setMatchSubmitted(false);
      if (currentIdx < filteredItems.length - 1) {
        setCurrentIdx(prev => prev + 1);
      }
    });
  }, [currentIdx, filteredItems.length, animateTransition]);

  const goPrev = useCallback(() => {
    animateTransition("right", () => {
      setShowAnswer(false);
      setFlipped(false);
      if (currentIdx > 0) setCurrentIdx(prev => prev - 1);
    });
  }, [currentIdx, animateTransition]);

  const handleSelectAnswer = useCallback((key: string) => {
    if (showAnswer) return;
    const itemKey = `${activeType}_${currentIdx}`;
    const newAnswers = { ...answers, [itemKey]: key };
    setAnswers(newAnswers);
    setShowAnswer(true);
    const newScore = currentItem?.correct_answer === key
      ? { correct: score.correct + 1, total: score.total + 1 }
      : { correct: score.correct, total: score.total + 1 };
    setScore(newScore);
    if (activeType && filteredItems.length > 0) {
      const answeredInType = Object.keys(newAnswers).filter(k => k.startsWith(`${activeType}_`)).length;
      if (answeredInType % 5 === 0 || answeredInType === filteredItems.length) {
        saveToDb(activeType, newScore.correct, newScore.total, newAnswers, answeredInType === filteredItems.length);
      }
    }
  }, [showAnswer, activeType, currentIdx, currentItem, answers, score, filteredItems.length, saveToDb]);

  const startQuizType = useCallback((type: string) => {
    setActiveType(type);
    setCurrentIdx(0);
    setShowAnswer(false);
    setFlipped(false);
    setMatchSelections({});
    setMatchSubmitted(false);
    setScore({ correct: 0, total: 0 });
    const typeAnswers: Record<string, string> = {};
    Object.entries(answers).forEach(([k, v]) => { if (k.startsWith(`${type}_`)) typeAnswers[k] = v; });
    setAnswers(typeAnswers);
    if (data) {
      const items = data.items.filter(i => i.type === type);
      let correct = 0, total = 0;
      items.forEach((item, idx) => {
        const key = `${type}_${idx}`;
        if (typeAnswers[key]) { total++; if (item.correct_answer === typeAnswers[key]) correct++; }
      });
      setScore({ correct, total });
      setCurrentIdx(total);
      if (total > 0 && total < items.length && typeAnswers[`${type}_${total}`]) setShowAnswer(true);
    }
  }, [answers, data]);

  const backToMenu = useCallback(() => {
    if (activeType && score.total > 0) {
      saveToDb(activeType, score.correct, score.total, answers, currentIdx >= filteredItems.length);
    }
    setActiveType(null);
    setCurrentIdx(0);
    setShowAnswer(false);
  }, [activeType, score, answers, currentIdx, filteredItems.length, saveToDb]);

  const handleRetryType = useCallback((type: string) => {
    const newAnswers: Record<string, string> = {};
    Object.entries(answers).forEach(([k, v]) => { if (!k.startsWith(`${type}_`)) newAnswers[k] = v; });
    setAnswers(newAnswers);
    setScore({ correct: 0, total: 0 });
    setCurrentIdx(0);
    setShowAnswer(false);
    setFlipped(false);
    setMatchSelections({});
    setMatchSubmitted(false);
  }, [answers]);

  if (loading) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="relative">
        <div className="h-10 w-10 animate-spin rounded-full border-3 border-blue-500 border-t-transparent" />
        <div className="absolute inset-0 h-10 w-10 animate-ping rounded-full border border-blue-300 opacity-20" />
      </div>
    </div>
  );

  if (!data || data.items.length === 0) return (
    <div className="p-8 text-center animate-[fadeIn_0.4s_ease]">
      <p className="text-gray-500 text-base">Chưa có bài ôn tập cho đề này.</p>
      <Link href={`/exam/english/${slug}`} className="text-blue-500 text-sm mt-2 inline-block">← Quay lại đề thi</Link>
    </div>
  );

  // Menu view
  if (!activeType) {
    const typeCounts: Record<string, number> = {};
    data.items.forEach(i => { typeCounts[i.type] = (typeCounts[i.type] || 0) + 1; });

    return (
      <div className={`max-w-[700px] mx-auto px-4 py-6 transition-all duration-500 ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}>
        <nav className="mb-4 text-sm text-gray-400 flex items-center gap-1">
          <Link href={`/exam/english/${slug}`} className="hover:text-blue-500 transition-colors duration-200">← {data.exam_title}</Link>
        </nav>

        <h1 className="text-xl font-bold text-gray-800 dark:text-gray-100 mb-1 relative inline-block">
          📚 Ôn tập kiến thức
          <span className={`absolute bottom-0 left-0 h-[2px] bg-blue-500 rounded-full transition-all duration-700 ease-out ${mounted ? "w-full" : "w-0"}`} />
        </h1>
        <p className="text-sm text-gray-400 mb-6">Chọn dạng bài muốn luyện tập</p>

        <div className="grid gap-3">
          {Object.entries(TYPE_LABELS).map(([type, info], idx) => {
            const count = typeCounts[type] || 0;
            if (count === 0) return null;
            const dbResult = dbResults[type];
            return (
              <button
                key={type}
                onClick={() => startQuizType(type)}
                className="flex items-center gap-4 bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm hover:shadow-md transition-all duration-300 text-left group hover:-translate-y-0.5 active:scale-[0.98]"
                style={{ animation: `slideUp 0.4s ease-out ${idx * 0.07}s both` }}
              >
                <span className="text-2xl transition-transform duration-300 group-hover:scale-125 group-hover:rotate-6">{info.icon}</span>
                <div className="flex-1">
                  <p className="font-semibold text-base text-gray-800 dark:text-gray-100 transition-colors duration-200 group-hover:text-blue-500">{info.label}</p>
                  <p className="text-sm text-gray-400">{info.desc}</p>
                  {dbResult && (
                    <p className="text-xs text-emerald-500 mt-0.5 flex items-center gap-1">
                      {dbResult.completed ? <><span className="animate-[popIn_0.3s_ease]">✓</span> Hoàn thành</> : `${dbResult.correct_count}/${dbResult.total_count} đúng`}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm bg-blue-50 dark:bg-blue-900/30 text-blue-500 px-2.5 py-0.5 rounded-full font-medium">
                    {count} câu
                  </span>
                  <span className="text-gray-300 transition-transform duration-200 group-hover:translate-x-1">→</span>
                </div>
              </button>
            );
          })}
        </div>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-300">Tổng: {data.total} câu ôn tập từ đề thi</p>
        </div>

        <style jsx global>{`
          @keyframes slideUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
          @keyframes popIn { 0% { transform: scale(0); } 60% { transform: scale(1.2); } 100% { transform: scale(1); } }
        `}</style>
      </div>
    );
  }

  // Completed screen
  if (currentIdx >= filteredItems.length) {
    const pct = score.total ? Math.round(score.correct / score.total * 100) : 0;
    return (
      <div className="max-w-[600px] mx-auto px-4 py-12 text-center animate-[scaleIn_0.4s_ease]">
        <div className="text-6xl mb-4 animate-bounce">🎉</div>
        <p className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-2">Hoàn thành!</p>
        <div className="text-4xl font-black mb-2" style={{ color: pct >= 80 ? "#10b981" : pct >= 60 ? "#f59e0b" : "#ef4444" }}>
          {pct}%
        </div>
        <p className="text-base text-gray-500 mb-6">{score.correct}/{score.total} câu đúng</p>
        <div className="flex gap-3 justify-center">
          <button onClick={backToMenu}
            className="rounded-lg bg-gray-200 dark:bg-gray-700 px-5 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-300 transition-all duration-200 hover:-translate-y-0.5 active:scale-[0.97]">
            ← Menu
          </button>
          <button onClick={() => handleRetryType(activeType)}
            className="rounded-lg bg-blue-500 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-600 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md hover:shadow-blue-500/25 active:scale-[0.97]">
            🔄 Làm lại
          </button>
        </div>
        <style jsx global>{`
          @keyframes scaleIn { from { opacity: 0; transform: scale(0.85); } to { opacity: 1; transform: scale(1); } }
        `}</style>
      </div>
    );
  }

  const typeInfo = TYPE_LABELS[activeType] || { label: activeType, icon: "📝" };

  return (
    <div className="max-w-[700px] mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <button onClick={backToMenu}
          className="text-sm text-gray-400 hover:text-blue-500 transition-all duration-200 hover:-translate-x-0.5 active:scale-95">
          ← Menu
        </button>
        <span className="text-sm text-gray-400 tabular-nums font-medium">
          {currentIdx + 1}/{filteredItems.length}
        </span>
        <span className="text-sm bg-blue-50 dark:bg-blue-900/30 text-blue-500 px-2.5 py-0.5 rounded-full font-medium">
          {typeInfo.icon} {typeInfo.label}
        </span>
      </div>

      {/* Animated progress bar */}
      <div className="h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full mb-6 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-blue-400 to-blue-600 transition-all duration-500 ease-out rounded-full relative"
          style={{ width: `${((currentIdx + 1) / filteredItems.length) * 100}%` }}
        >
          <div className="absolute right-0 top-0 bottom-0 w-3 bg-white/30 rounded-full animate-pulse" />
        </div>
      </div>

      {/* Quiz content with slide transition */}
      <div className={`min-h-[300px] transition-all duration-200 ${
        animating
          ? slideDir === "left"
            ? "opacity-0 -translate-x-6"
            : "opacity-0 translate-x-6"
          : "opacity-100 translate-x-0"
      }`}>
        {currentItem && renderQuizItem(
          currentItem, activeType, showAnswer, flipped, setFlipped,
          handleSelectAnswer, answers[`${activeType}_${currentIdx}`],
          matchSelections, setMatchSelections, matchSubmitted, setMatchSubmitted
        )}
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between mt-6">
        <button
          onClick={goPrev}
          disabled={currentIdx === 0}
          className="rounded-lg bg-gray-100 dark:bg-gray-700 px-4 py-2.5 text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-200 transition-all duration-200 disabled:opacity-30 hover:-translate-x-0.5 active:scale-[0.97]"
        >
          ← Trước
        </button>

        {/* Live score */}
        {score.total > 0 && (
          <span className="text-sm text-emerald-500 font-medium animate-[fadeIn_0.3s_ease]">
            ✓ {score.correct}/{score.total}
          </span>
        )}

        {activeType === "vocab_flashcard" ? (
          <button
            onClick={() => {
              if (currentIdx >= filteredItems.length - 1) {
                setCurrentIdx(filteredItems.length);
                saveToDb(activeType, score.correct, score.total, answers, true);
              } else {
                goNext();
              }
            }}
            className="rounded-lg bg-blue-500 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-600 transition-all duration-200 hover:translate-x-0.5 hover:shadow-md hover:shadow-blue-500/25 active:scale-[0.97]"
          >
            {currentIdx >= filteredItems.length - 1 ? "Kết quả ✨" : "Tiếp →"}
          </button>
        ) : showAnswer || (activeType === "match_collocation" && matchSubmitted) ? (
          <button
            onClick={() => {
              if (currentIdx >= filteredItems.length - 1) {
                setCurrentIdx(filteredItems.length);
                saveToDb(activeType, score.correct, score.total, answers, true);
              } else {
                goNext();
              }
            }}
            className="rounded-lg bg-blue-500 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-600 transition-all duration-200 hover:translate-x-0.5 hover:shadow-md hover:shadow-blue-500/25 active:scale-[0.97] animate-[slideIn_0.3s_ease]"
          >
            {currentIdx >= filteredItems.length - 1 ? "Kết quả ✨" : "Tiếp →"}
          </button>
        ) : <div />}
      </div>

      <style jsx global>{`
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes slideIn { from { opacity: 0; transform: translateX(8px); } to { opacity: 1; transform: translateX(0); } }
      `}</style>
    </div>
  );
}

/* ── Render individual quiz item ── */
function renderQuizItem(
  item: ReviewItem, type: string, showAnswer: boolean,
  flipped: boolean, setFlipped: (v: boolean) => void,
  onSelect: (key: string) => void, selectedKey: string | undefined,
  matchSelections: Record<string, string>,
  setMatchSelections: (v: Record<string, string>) => void,
  matchSubmitted: boolean,
  setMatchSubmitted: (v: boolean) => void,
) {
  switch (type) {
    case "vocab_flashcard":
      return <VocabFlashcard item={item} flipped={flipped} setFlipped={setFlipped} />;
    case "pronunciation_ipa":
      return <PronunciationQuiz item={item} showAnswer={showAnswer} onSelect={onSelect} selectedKey={selectedKey} />;
    case "stress_drill":
      return <StressDrill item={item} showAnswer={showAnswer} onSelect={onSelect} selectedKey={selectedKey} />;
    case "grammar_drill":
    case "fill_in_blank":
    case "sentence_transform":
      return <MCQQuiz item={item} showAnswer={showAnswer} onSelect={onSelect} selectedKey={selectedKey} type={type} />;
    case "match_collocation":
      return <MatchCollocation item={item} selections={matchSelections} setSelections={setMatchSelections} submitted={matchSubmitted} setSubmitted={setMatchSubmitted} />;
    default:
      return <p className="text-gray-400">Unsupported quiz type: {type}</p>;
  }
}

/* ── Vocab Flashcard with 3D flip ── */
function VocabFlashcard({ item, flipped, setFlipped }: { item: ReviewItem; flipped: boolean; setFlipped: (v: boolean) => void }) {
  return (
    <div className="perspective-1000" onClick={() => setFlipped(!flipped)}>
      <div className={`relative min-h-[280px] transition-all duration-500 cursor-pointer select-none [transform-style:preserve-3d] ${flipped ? "[transform:rotateY(180deg)]" : ""}`}>
        {/* Front */}
        <div className="absolute inset-0 bg-white dark:bg-gray-800 rounded-xl shadow-sm flex flex-col items-center justify-center p-8 [backface-visibility:hidden] hover:shadow-lg transition-shadow duration-300">
          <p className="text-3xl font-bold text-gray-800 dark:text-gray-100 mb-2">{item.front}</p>
          {item.front_ipa && <p className="text-base text-blue-400 font-mono mb-4">{item.front_ipa}</p>}
          <p className="text-sm text-gray-300 mt-4 flex items-center gap-1.5">
            <span className="animate-[wiggle_1s_ease_infinite]">👆</span> Nhấn để lật
          </p>
        </div>
        {/* Back */}
        <div className="absolute inset-0 bg-white dark:bg-gray-800 rounded-xl shadow-sm flex flex-col items-center justify-center p-8 [backface-visibility:hidden] [transform:rotateY(180deg)] hover:shadow-lg transition-shadow duration-300">
          <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mb-3">{item.back}</p>
          {item.example && (
            <div className="mt-2 text-center">
              <p className="text-base text-gray-600 dark:text-gray-300 italic">"{item.example}"</p>
              {item.example_vi && <p className="text-sm text-gray-400 mt-1">{item.example_vi}</p>}
            </div>
          )}
          <p className="text-sm text-gray-300 mt-4 flex items-center gap-1.5">
            <span className="animate-[wiggle_1s_ease_infinite]">👆</span> Nhấn để lật lại
          </p>
        </div>
      </div>
      <style jsx global>{`
        .perspective-1000 { perspective: 1000px; }
        @keyframes wiggle { 0%,100% { transform: rotate(0deg); } 25% { transform: rotate(-6deg); } 75% { transform: rotate(6deg); } }
      `}</style>
    </div>
  );
}

/* ── Pronunciation IPA Quiz ── */
function PronunciationQuiz({ item, showAnswer, onSelect, selectedKey }: {
  item: ReviewItem; showAnswer: boolean; onSelect: (k: string) => void; selectedKey?: string;
}) {
  const keys = ["A", "B", "C", "D"];
  return (
    <div>
      <p className="text-base text-gray-600 dark:text-gray-300 mb-4 italic">{item.instruction}</p>
      <div className="grid grid-cols-2 gap-3 mb-4">
        {item.words?.map((w, i) => {
          const key = keys[i];
          const isCorrect = key === item.correct_answer;
          const isSelected = key === selectedKey;
          let cls = "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:border-blue-300 hover:shadow-sm hover:-translate-y-0.5";
          if (showAnswer) {
            if (isCorrect) cls = "bg-emerald-50 dark:bg-emerald-900/30 border border-emerald-400 ring-1 ring-emerald-300 shadow-sm shadow-emerald-500/10 scale-[1.02]";
            else if (isSelected) cls = "bg-red-50 dark:bg-red-900/20 border border-red-400 animate-[wrongShake_0.4s_ease]";
            else cls = "bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 opacity-40";
          } else if (isSelected) {
            cls = "bg-blue-50 dark:bg-blue-900/30 border border-blue-400 ring-1 ring-blue-300 scale-[1.02]";
          }
          return (
            <button
              key={key}
              onClick={() => onSelect(key)}
              disabled={showAnswer}
              className={`rounded-xl p-4 text-center transition-all duration-300 active:scale-[0.97] ${cls}`}
            >
              <span className="text-sm text-gray-400 font-bold">{key}.</span>
              <p className="text-xl font-bold text-gray-800 dark:text-gray-100">
                {w.underline ? (
                  <>
                    {w.word.split(w.underline)[0]}
                    <span className="underline decoration-2 decoration-blue-400">{w.underline}</span>
                    {w.word.split(w.underline).slice(1).join(w.underline)}
                  </>
                ) : w.word}
              </p>
              <p className="text-sm text-blue-400 font-mono mt-1">{w.ipa}</p>
              {w.sound && <p className="text-xs text-gray-400 mt-0.5">{w.underline} → {w.sound}</p>}
            </button>
          );
        })}
      </div>
      {showAnswer && (
        <div className="rounded-xl bg-blue-50 dark:bg-blue-900/20 p-4 mt-3 animate-[slideDown_0.3s_ease] border border-blue-100 dark:border-blue-800/30">
          <p className="text-sm font-semibold text-blue-600 dark:text-blue-400 mb-1">💡 {item.rule}</p>
          <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">{item.explanation}</p>
        </div>
      )}
      <style jsx global>{`
        @keyframes wrongShake { 0%,100% { transform: translateX(0); } 20% { transform: translateX(-5px); } 40% { transform: translateX(5px); } 60% { transform: translateX(-3px); } 80% { transform: translateX(3px); } }
        @keyframes slideDown { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
}

/* ── Stress Drill ── */
function StressDrill({ item, showAnswer, onSelect, selectedKey }: {
  item: ReviewItem; showAnswer: boolean; onSelect: (k: string) => void; selectedKey?: string;
}) {
  const keys = ["A", "B", "C", "D"];
  return (
    <div>
      <p className="text-base text-gray-600 dark:text-gray-300 mb-4 italic">{item.instruction}</p>
      <div className="grid grid-cols-2 gap-3 mb-4">
        {item.words?.map((w, i) => {
          const key = keys[i];
          const isCorrect = key === item.correct_answer;
          const isSelected = key === selectedKey;
          let cls = "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:border-blue-300 hover:shadow-sm hover:-translate-y-0.5";
          if (showAnswer) {
            if (isCorrect) cls = "bg-emerald-50 dark:bg-emerald-900/30 border border-emerald-400 ring-1 ring-emerald-300 shadow-sm shadow-emerald-500/10 scale-[1.02]";
            else if (isSelected) cls = "bg-red-50 dark:bg-red-900/20 border border-red-400 animate-[wrongShake_0.4s_ease]";
            else cls = "bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 opacity-40";
          } else if (isSelected) {
            cls = "bg-blue-50 dark:bg-blue-900/30 border border-blue-400 ring-1 ring-blue-300 scale-[1.02]";
          }
          return (
            <button
              key={key}
              onClick={() => onSelect(key)}
              disabled={showAnswer}
              className={`rounded-xl p-4 text-center transition-all duration-300 active:scale-[0.97] ${cls}`}
            >
              <span className="text-sm text-gray-400 font-bold">{key}.</span>
              <p className="text-xl font-bold text-gray-800 dark:text-gray-100">{w.word}</p>
              <p className="text-sm text-blue-400 font-mono mt-1">{w.ipa}</p>
              <p className="text-xs text-gray-400 mt-0.5">Trọng âm: {w.stress_pos}</p>
            </button>
          );
        })}
      </div>
      {showAnswer && (
        <div className="rounded-xl bg-blue-50 dark:bg-blue-900/20 p-4 mt-3 animate-[slideDown_0.3s_ease] border border-blue-100 dark:border-blue-800/30">
          <p className="text-sm font-semibold text-blue-600 dark:text-blue-400 mb-1">💡 {item.rule}</p>
          <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">{item.explanation}</p>
        </div>
      )}
    </div>
  );
}

/* ── MCQ Quiz ── */
function MCQQuiz({ item, showAnswer, onSelect, selectedKey, type }: {
  item: ReviewItem; showAnswer: boolean; onSelect: (k: string) => void; selectedKey?: string; type: string;
}) {
  return (
    <div>
      {item.rule && (
        <div className="text-sm bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 px-3 py-2 rounded-lg mb-3 inline-block font-medium animate-[fadeIn_0.3s_ease]">
          📌 {item.rule}
        </div>
      )}

      {type === "sentence_transform" && item.original && (
        <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4 mb-3 border border-gray-100 dark:border-gray-700">
          <p className="text-sm text-gray-400 mb-1">Câu gốc:</p>
          <p className="text-base text-gray-800 dark:text-gray-100 font-medium">{item.original}</p>
          {item.keyword && (
            <p className="text-sm text-blue-500 mt-1.5">Từ khóa: <strong className="bg-blue-50 dark:bg-blue-900/30 px-1.5 py-0.5 rounded">{item.keyword}</strong></p>
          )}
        </div>
      )}

      {item.question && (
        <p className="text-base text-gray-800 dark:text-gray-100 mb-4 leading-relaxed">{item.question}</p>
      )}

      <div className="grid gap-2">
        {item.choices?.map((c, ci) => {
          const isSelected = selectedKey === c.key;
          const isCorrect = c.key === item.correct_answer;
          let cls = "bg-gray-50 dark:bg-gray-700/40 hover:bg-gray-100 dark:hover:bg-gray-700/60 text-gray-700 dark:text-gray-200 hover:shadow-sm hover:-translate-y-px";
          if (showAnswer) {
            if (isCorrect) cls = "bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 ring-1 ring-emerald-400 shadow-sm shadow-emerald-500/10";
            else if (isSelected) cls = "bg-red-50 dark:bg-red-900/20 text-red-400 line-through animate-[wrongShake_0.4s_ease]";
            else cls = "bg-gray-50/50 dark:bg-gray-700/10 text-gray-400";
          } else if (isSelected) {
            cls = "bg-blue-50 dark:bg-blue-900/30 text-blue-600 ring-1 ring-blue-400";
          }
          return (
            <button
              key={c.key}
              onClick={() => onSelect(c.key)}
              disabled={showAnswer}
              className={`flex items-center gap-2.5 rounded-xl px-4 py-3 text-left text-[15px] transition-all duration-200 active:scale-[0.98] ${cls}`}
              style={{ animationDelay: `${ci * 0.05}s` }}
            >
              <span className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border transition-all duration-200 ${
                showAnswer && isCorrect ? "bg-emerald-500 text-white border-emerald-500 shadow-sm animate-[popIn_0.3s_ease]" :
                showAnswer && isSelected ? "bg-red-400 text-white border-red-400" :
                isSelected ? "bg-blue-500 text-white border-blue-500" :
                "border-gray-300 dark:border-gray-500 text-gray-400"
              }`}>{c.key}</span>
              <span className="flex-1">{c.text}</span>
              {showAnswer && isCorrect && <span className="text-emerald-500 text-base animate-[popIn_0.3s_ease]">✓</span>}
              {showAnswer && isSelected && !isCorrect && <span className="text-red-400 text-base">✗</span>}
            </button>
          );
        })}
      </div>

      {showAnswer && item.explanation && (
        <div className="rounded-xl bg-blue-50 dark:bg-blue-900/20 p-4 mt-3 animate-[slideDown_0.3s_ease] border border-blue-100 dark:border-blue-800/30">
          <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">💡 {item.explanation}</p>
        </div>
      )}

      <style jsx global>{`
        @keyframes popIn { 0% { transform: scale(0); } 60% { transform: scale(1.2); } 100% { transform: scale(1); } }
        @keyframes wrongShake { 0%,100% { transform: translateX(0); } 20% { transform: translateX(-5px); } 40% { transform: translateX(5px); } 60% { transform: translateX(-3px); } 80% { transform: translateX(3px); } }
        @keyframes slideDown { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
      `}</style>
    </div>
  );
}

/* ── Match Collocation ── */
function MatchCollocation({ item, selections, setSelections, submitted, setSubmitted }: {
  item: ReviewItem;
  selections: Record<string, string>;
  setSelections: (v: Record<string, string>) => void;
  submitted: boolean;
  setSubmitted: (v: boolean) => void;
}) {
  const pairs = item.pairs || [];
  const allRightOptions = useMemo(() => {
    const rights = pairs.map(p => p.right);
    const dists = item.distractors || [];
    return [...rights, ...dists].sort(() => Math.random() - 0.5);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const [activeLeft, setActiveLeft] = useState<string | null>(null);

  const handleSelectRight = (right: string) => {
    if (submitted || !activeLeft) return;
    setSelections({ ...selections, [activeLeft]: right });
    setActiveLeft(null);
  };

  const correctCount = pairs.filter(p => selections[p.left] === p.right).length;

  return (
    <div>
      <p className="text-base text-gray-600 dark:text-gray-300 mb-4 italic">{item.instruction}</p>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          {pairs.map((p, pi) => {
            const isActive = activeLeft === p.left;
            const hasSelection = !!selections[p.left];
            const isCorrect = submitted && selections[p.left] === p.right;
            const isWrong = submitted && selections[p.left] && selections[p.left] !== p.right;
            let cls = "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:border-blue-300";
            if (isActive) cls = "bg-blue-50 dark:bg-blue-900/30 border border-blue-400 ring-2 ring-blue-300/50 shadow-sm shadow-blue-500/10 scale-[1.02]";
            else if (isCorrect) cls = "bg-emerald-50 dark:bg-emerald-900/30 border border-emerald-400 shadow-sm shadow-emerald-500/10";
            else if (isWrong) cls = "bg-red-50 dark:bg-red-900/20 border border-red-400 animate-[wrongShake_0.4s_ease]";
            else if (hasSelection) cls = "bg-blue-50 dark:bg-blue-900/20 border border-blue-300";
            return (
              <button
                key={p.left}
                onClick={() => !submitted && setActiveLeft(isActive ? null : p.left)}
                className={`w-full rounded-xl px-4 py-3 text-[15px] font-medium text-left transition-all duration-300 active:scale-[0.97] ${cls}`}
                style={{ animation: `slideUp 0.3s ease-out ${pi * 0.05}s both` }}
              >
                <span className="text-gray-800 dark:text-gray-100">{p.left}</span>
                {hasSelection && (
                  <span className="ml-2 text-sm text-blue-400 animate-[fadeIn_0.2s_ease]">→ {selections[p.left]}</span>
                )}
                {submitted && isCorrect && <span className="ml-1 animate-[popIn_0.3s_ease]">✅</span>}
                {submitted && isWrong && <span className="ml-1">❌</span>}
              </button>
            );
          })}
        </div>

        <div className="space-y-2">
          {allRightOptions.map((right, ri) => {
            const isUsed = Object.values(selections).includes(right);
            return (
              <button
                key={right}
                onClick={() => handleSelectRight(right)}
                disabled={submitted || !activeLeft || isUsed}
                className={`w-full rounded-xl px-4 py-3 text-[15px] text-left transition-all duration-300 active:scale-[0.97] ${
                  isUsed
                    ? "bg-gray-100 dark:bg-gray-700/30 text-gray-400 opacity-40 scale-95"
                    : activeLeft
                      ? "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:border-blue-400 hover:shadow-sm hover:-translate-y-0.5 cursor-pointer"
                      : "bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-500"
                }`}
                style={{ animation: `slideUp 0.3s ease-out ${ri * 0.05}s both` }}
              >
                {right}
              </button>
            );
          })}
        </div>
      </div>

      {!submitted && Object.keys(selections).length === pairs.length && (
        <button
          onClick={() => setSubmitted(true)}
          className="mt-4 rounded-xl bg-blue-500 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-600 w-full transition-all duration-200 hover:shadow-lg hover:shadow-blue-500/25 hover:-translate-y-0.5 active:scale-[0.98] animate-[slideUp_0.3s_ease]"
        >
          Kiểm tra
        </button>
      )}

      {submitted && (
        <div className="rounded-xl bg-blue-50 dark:bg-blue-900/20 p-4 mt-4 text-center animate-[scaleIn_0.3s_ease]">
          <p className="text-base font-medium text-gray-700 dark:text-gray-200">
            {correctCount}/{pairs.length} cặp đúng
            {correctCount === pairs.length ? " 🎉" : ""}
          </p>
        </div>
      )}

      <style jsx global>{`
        @keyframes slideUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes scaleIn { from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: scale(1); } }
        @keyframes popIn { 0% { transform: scale(0); } 60% { transform: scale(1.2); } 100% { transform: scale(1); } }
        @keyframes wrongShake { 0%,100% { transform: translateX(0); } 20% { transform: translateX(-5px); } 40% { transform: translateX(5px); } 60% { transform: translateX(-3px); } 80% { transform: translateX(3px); } }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
      `}</style>
    </div>
  );
}
