"use client";

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { apiFetch, apiUrl } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

/* ── Types ── */
type QuizType = "all" | "meaning" | "reading" | "kanji";

/* ── Kanji Quiz Progress (localStorage) ── */
interface KanjiQuizProgress {
  currentIdx: number;
  score: { correct: number; wrong: number };
  quizType: QuizType;
  answers: Record<number, number>;  // questionIdx → selectedOptionIdx
  finished: boolean;
  cachedQuestions?: QuizQuestion[];  // prevent randomization issues on reload
  lessonLabel?: string;
}

const PROGRESS_KEY = (id: string) => `kanji_quiz_${id}`;

function loadKanjiProgress(lessonId: string): KanjiQuizProgress | null {
  try {
    const raw = localStorage.getItem(PROGRESS_KEY(lessonId));
    if (!raw) return null;
    return JSON.parse(raw);
  } catch { return null; }
}

function saveKanjiProgress(lessonId: string, progress: KanjiQuizProgress) {
  try {
    localStorage.setItem(PROGRESS_KEY(lessonId), JSON.stringify(progress));
  } catch { /* ignore */ }
}

function clearKanjiProgress(lessonId: string) {
  try { localStorage.removeItem(PROGRESS_KEY(lessonId)); } catch { /* ignore */ }
}

interface QuizOption {
  text: string;
  is_correct: boolean;
}

interface QuizQuestion {
  kanji_id: number;
  char: string;
  sino_vi: string;
  onyomi: string;
  kunyomi: string;
  meaning_vi: string;
  question_type: "meaning" | "reading" | "kanji";
  options: QuizOption[];
}

interface QuizData {
  lesson_id: number;
  lesson_label: string;
  questions: QuizQuestion[];
  total: number;
}

interface StatusItem {
  id: number;
  char: string;
  sino_vi: string;
  has_quiz: boolean;
}

interface StatusData {
  lesson_id: number;
  lesson_label: string;
  items: StatusItem[];
  total: number;
  ready: number;
}

type PagePhase = "checking" | "generating" | "ready" | "quiz" | "finished";

const TYPE_LABELS: Record<string, string> = {
  all: "Tất cả",
  meaning: "Nghĩa",
  reading: "Cách đọc",
  kanji: "Hán tự",
};

const TYPE_PROMPTS: Record<string, string> = {
  meaning: "Chọn nghĩa đúng của chữ Kanji:",
  reading: "Chọn cách đọc đúng của chữ Kanji:",
  kanji: "Chọn chữ Kanji đúng:",
};

export default function KanjiQuizPage() {
  const params = useParams();
  const router = useRouter();
  const lessonId = params.lessonId as string;

  // Restore saved progress on mount
  const savedProgress = useRef(loadKanjiProgress(lessonId));

  const [phase, setPhase] = useState<PagePhase>("checking");
  const [statusData, setStatusData] = useState<StatusData | null>(null);

  const [genDone, setGenDone] = useState(0);
  const [genTotal, setGenTotal] = useState(0);
  const [genCurrent, setGenCurrent] = useState("");
  const [genLogs, setGenLogs] = useState<string[]>([]);

  const [quizData, setQuizData] = useState<QuizData | null>(null);
  const [quizType, setQuizType] = useState<QuizType>(savedProgress.current?.quizType || "meaning");
  const [currentIdx, setCurrentIdx] = useState(savedProgress.current?.currentIdx || 0);
  const [selected, setSelected] = useState<number | null>(null);
  const [score, setScore] = useState(savedProgress.current?.score || { correct: 0, wrong: 0 });
  const [showNext, setShowNext] = useState(false);
  const answersRef = useRef<Record<number, number>>(savedProgress.current?.answers || {});
  // Track per-kanji results: { kanji_id: { correct: n, total: n } }
  const kanjiResultsRef = useRef<Record<number, { correct: number; total: number }>>({});

  const checkStatus = useCallback(async () => {
    setPhase("checking");
    try {
      const res = await fetch(`/api/v1/kanji/quiz/${lessonId}/status`, { credentials: "include" });
      const data: StatusData = await res.json();
      setStatusData(data);

      const needGen = data.items.filter(i => !i.has_quiz);
      if (needGen.length === 0) {
        setPhase("ready");
        loadQuiz(quizType, true);  // restore progress on initial load
      } else {
        setPhase("generating");
        await generateAll(data, needGen);
      }
    } catch {
      setPhase("ready");
    }
  }, [lessonId]);

  const generateAll = async (status: StatusData, needGen: StatusItem[]) => {
    setGenTotal(needGen.length);
    setGenDone(0);
    setGenLogs([]);

    for (let i = 0; i < needGen.length; i++) {
      const item = needGen[i];
      setGenCurrent(item.char);
      setGenDone(i);
      setGenLogs(prev => [...prev, `⏳ ${item.char} (${item.sino_vi || "..."})...`]);

      try {
        const res = await fetch(`/api/v1/kanji/quiz/generate-one`, {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ kanji_id: item.id }),
        });
        const data = await res.json();
        if (data.status === "success") {
          setGenLogs(prev => [...prev, `✅ ${item.char}: OK`]);
        } else {
          setGenLogs(prev => [...prev, `⚠️ ${item.char}: ${data.message || "Failed"}`]);
        }
      } catch (err) {
        setGenLogs(prev => [...prev, `❌ ${item.char}: ${String(err)}`]);
      }

      await new Promise(r => setTimeout(r, 300));
    }

    setGenDone(needGen.length);
    setGenCurrent("Hoàn tất!");

    await new Promise(r => setTimeout(r, 500));
    setPhase("ready");
    loadQuiz(quizType);
  };

  const loadQuiz = async (type: QuizType, restoreProgress = false) => {
    // Check for saved progress with cached questions — read directly from localStorage
    if (restoreProgress) {
      const sp = loadKanjiProgress(lessonId);
      if (sp && sp.quizType === type && !sp.finished && sp.cachedQuestions?.length) {
        // Restore from cache — use exact same questions as before
        setQuizData({
          lesson_id: parseInt(lessonId, 10),
          lesson_label: sp.lessonLabel || "",
          questions: sp.cachedQuestions,
          total: sp.cachedQuestions.length,
        });
        setCurrentIdx(sp.currentIdx);
        setScore(sp.score);
        answersRef.current = sp.answers || {};
        // If the current question was already answered, show the selection
        const prevAnswer = sp.answers[sp.currentIdx];
        if (prevAnswer !== undefined) {
          setSelected(prevAnswer);
          setShowNext(true);
        } else {
          setSelected(null);
          setShowNext(false);
        }
        setPhase("quiz");
        return;
      }
    }

    // Fresh load from API
    try {
      const res = await fetch(`/api/v1/kanji/quiz/${lessonId}?quiz_type=${type}`, { credentials: "include" });
      const data: QuizData = await res.json();
      setQuizData(data);
      setCurrentIdx(0);
      setSelected(null);
      setScore({ correct: 0, wrong: 0 });
      setShowNext(false);
      answersRef.current = {};
      savedProgress.current = null;

      // Cache the fresh questions for later restore
      saveKanjiProgress(lessonId, {
        currentIdx: 0,
        score: { correct: 0, wrong: 0 },
        quizType: type,
        answers: {},
        finished: false,
        cachedQuestions: data.questions,
        lessonLabel: data.lesson_label,
      });

      setPhase("quiz");
    } catch {
      setPhase("quiz");
    }
  };

  useEffect(() => {
    checkStatus();
  }, []);

  const handleTypeChange = (type: QuizType) => {
    setQuizType(type);
    loadQuiz(type);
  };

  const questions = quizData?.questions || [];
  const currentQ = questions[currentIdx];
  const totalQ = questions.length;

  /** Aggregate per-kanji results and send to backend */
  const syncProgressToBackend = () => {
    const results = kanjiResultsRef.current;
    for (const kanjiId of Object.keys(results)) {
      const r = results[Number(kanjiId)];
      // passed = answered ALL questions for this kanji correctly
      const passed = r.correct === r.total;
      apiFetch(apiUrl("/kanji/progress"), {
        method: "POST",
        body: JSON.stringify({ kanji_id: Number(kanjiId), passed }),
      }).catch(() => {});
    }
  };

  const handleSelect = (optIndex: number) => {
    if (selected !== null) return;
    setSelected(optIndex);

    const isCorrect = currentQ.options[optIndex].is_correct;
    const newScore = isCorrect
      ? { ...score, correct: score.correct + 1 }
      : { ...score, wrong: score.wrong + 1 };
    setScore(newScore);

    // Aggregate results per kanji (send at quiz end, not per question)
    const kid = currentQ.kanji_id;
    if (!kanjiResultsRef.current[kid]) {
      kanjiResultsRef.current[kid] = { correct: 0, total: 0 };
    }
    kanjiResultsRef.current[kid].total += 1;
    if (isCorrect) kanjiResultsRef.current[kid].correct += 1;

    // Save progress to localStorage
    answersRef.current[currentIdx] = optIndex;
    saveKanjiProgress(lessonId, {
      currentIdx,
      score: newScore,
      quizType,
      answers: answersRef.current,
      finished: currentIdx + 1 >= totalQ,
      cachedQuestions: questions,
      lessonLabel: quizData?.lesson_label,
    });

    setTimeout(() => {
      if (currentIdx + 1 >= totalQ) {
        setPhase("finished");
        clearKanjiProgress(lessonId);
        syncProgressToBackend();
      } else {
        setShowNext(true);
      }
    }, 1200);
  };

  const nextQuestion = () => {
    const nextIdx = currentIdx + 1;
    setCurrentIdx(nextIdx);
    setSelected(null);
    setShowNext(false);
    setAutoProgress(0);

    // Update progress with new index
    saveKanjiProgress(lessonId, {
      currentIdx: nextIdx,
      score,
      quizType,
      answers: answersRef.current,
      finished: false,
      cachedQuestions: questions,
      lessonLabel: quizData?.lesson_label,
    });
  };

  const [autoProgress, setAutoProgress] = useState(0);
  const autoTimerRef = useRef<ReturnType<typeof setInterval>>(null);

  useEffect(() => {
    if (showNext) {
      setAutoProgress(0);
      const start = Date.now();
      const duration = 1800;
      autoTimerRef.current = setInterval(() => {
        const elapsed = Date.now() - start;
        const pct = Math.min((elapsed / duration) * 100, 100);
        setAutoProgress(pct);
        if (elapsed >= duration) {
          clearInterval(autoTimerRef.current!);
          nextQuestion();
        }
      }, 30);
      return () => { if (autoTimerRef.current) clearInterval(autoTimerRef.current); };
    }
  }, [showNext]);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
      if (phase !== "quiz" || !currentQ) return;

      const num = parseInt(e.key);
      if (num >= 1 && num <= 4 && selected === null && currentQ.options[num - 1]) {
        e.preventDefault();
        handleSelect(num - 1);
      }

      if ((e.key === "Enter" || e.key === " ") && showNext) {
        e.preventDefault();
        if (autoTimerRef.current) clearInterval(autoTimerRef.current);
        nextQuestion();
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [phase, currentQ, selected, showNext]);

  const retry = () => {
    clearKanjiProgress(lessonId);
    answersRef.current = {};
    kanjiResultsRef.current = {};
    loadQuiz(quizType);
  };

  const resultEmoji = useMemo(() => {
    if (phase !== "finished") return "";
    const pct = totalQ > 0 ? score.correct / totalQ : 0;
    if (pct >= 0.9) return "🎉";
    if (pct >= 0.7) return "👏";
    if (pct >= 0.5) return "💪";
    return "📚";
  }, [phase, score, totalQ]);

  const resultMessage = useMemo(() => {
    if (phase !== "finished") return "";
    const pct = totalQ > 0 ? score.correct / totalQ : 0;
    if (pct >= 0.9) return "Xuất sắc! Bạn nắm rất vững!";
    if (pct >= 0.7) return "Tốt lắm! Cũng gần thành thạo rồi!";
    if (pct >= 0.5) return "Khá tốt! Cần ôn thêm một chút!";
    return "Hãy ôn bài thêm nhé!";
  }, [phase, score, totalQ]);

  const lessonLabel = statusData?.lesson_label || quizData?.lesson_label || "";

  /* ── Type selector buttons ── */
  const TypeSelector = () => (
    <div className="flex flex-wrap justify-center gap-1.5 my-2">
      {(["all", "meaning", "reading", "kanji"] as QuizType[]).map(t => (
        <Button key={t} size="xs"
          variant={quizType === t ? "default" : "outline"}
          className={cn(
            "rounded-full text-xs font-semibold",
            quizType === t && "bg-gradient-to-br from-indigo-500 to-violet-500 text-white shadow-[0_2px_8px_rgba(99,102,241,0.3)]"
          )}
          onClick={() => handleTypeChange(t)}
        >
          {TYPE_LABELS[t]}
        </Button>
      ))}
    </div>
  );

  // ── PHASE: Checking ──
  if (phase === "checking") {
    return (
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="text-center animate-[fadeIn_0.3s_ease]">
          <div className="text-5xl mb-3 animate-bounce">🔍</div>
          <div className="text-lg font-bold text-[var(--text-primary)]">Đang kiểm tra dữ liệu quiz...</div>
          <div className="text-sm text-[var(--text-tertiary)] mt-1">Vui lòng đợi trong giây lát</div>
        </div>
      </div>
    );
  }

  // ── PHASE: Generating ──
  if (phase === "generating") {
    const pct = genTotal > 0 ? (genDone / genTotal) * 100 : 0;
    return (
      <div className="flex min-h-screen flex-col items-center p-4 pt-8">
        <div className="w-full max-w-[500px]">
          <div className="mb-3 flex items-center gap-3">
            <Button variant="ghost" size="sm" onClick={() => router.back()} className="text-[var(--text-tertiary)]">← Quay lại</Button>
            {lessonLabel && <Badge variant="outline" className="text-xs">{lessonLabel}</Badge>}
          </div>
          <h1 className="text-center text-lg font-bold text-[var(--text-primary)] mb-4">Đang tạo Quiz bằng AI</h1>

          <Card className="text-center py-6">
            <CardContent className="px-6">
              <div className="text-[4rem] leading-none mb-2" style={{ fontFamily: "'Noto Sans JP', sans-serif" }}>
                {genCurrent || "..."}
              </div>
              <div className="text-sm text-[var(--text-tertiary)] mb-5">
                Gemini AI đang tạo đáp án nhiễu...
              </div>

              <div className="mb-4">
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="font-semibold text-[var(--text-primary)]">{genDone}/{genTotal} chữ Kanji</span>
                  <span className="text-[var(--text-tertiary)]">{Math.round(pct)}%</span>
                </div>
                <Progress value={pct} className="h-2" />
              </div>

              {statusData && (
                <div className="flex flex-wrap justify-center gap-1.5 my-5">
                  {statusData.items.map((item, idx) => {
                    const isGenerated = item.has_quiz || idx < genDone;
                    const isActive = idx === genDone && !item.has_quiz;
                    return (
                      <div key={item.id}
                        className={cn(
                          "flex h-10 w-10 items-center justify-center rounded-[10px] text-lg transition-all",
                          isGenerated && "border-emerald-500/30 bg-emerald-500/10 text-emerald-500",
                          isActive && "border-2 border-amber-500 bg-amber-500/[0.08] text-[var(--text-primary)] animate-[fadeIn_0.3s_ease]",
                          !isGenerated && !isActive && "border-[1.5px] border-[var(--border-subtle)] text-[var(--text-primary)]"
                        )}
                        style={{ fontFamily: "'Noto Sans JP', sans-serif" }}
                      >
                        {isGenerated ? "✓" : item.char}
                      </div>
                    );
                  })}
                </div>
              )}

              {genLogs.length > 0 && (
                <div className="mt-2 max-h-[120px] overflow-y-auto rounded-[10px] bg-[var(--bg-app)] p-2 px-3 text-left text-xs font-mono">
                  {genLogs.slice(-8).map((l, i) => (
                    <div key={i} className={cn("py-0.5", i < genLogs.slice(-8).length - 1 && "opacity-60")}>{l}</div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // ── PHASE: Ready ──
  if (phase === "ready") {
    return (
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="text-center animate-[fadeIn_0.3s_ease]">
          <div className="text-5xl mb-3">✨</div>
          <div className="text-lg font-bold text-[var(--text-primary)]">Đang tải câu hỏi...</div>
        </div>
      </div>
    );
  }

  // ── PHASE: No data ──
  if (!quizData || totalQ === 0) {
    return (
      <div className="flex min-h-screen flex-col items-center p-4 pt-8">
        <div className="w-full max-w-[500px]">
          <div className="mb-3 flex items-center gap-3">
            <Button variant="ghost" size="sm" onClick={() => router.back()} className="text-[var(--text-tertiary)]">← Quay lại</Button>
            <h1 className="text-lg font-bold text-[var(--text-primary)]">Quiz Kanji</h1>
          </div>
          <div className="text-center py-10 animate-[fadeIn_0.3s_ease]">
            <div className="text-5xl mb-3">📭</div>
            <div className="text-lg font-bold text-[var(--text-primary)]">Chưa có câu hỏi quiz</div>
            <div className="text-sm text-[var(--text-tertiary)] mt-1">
              Không thể tạo quiz cho bài học này.
              {quizType !== "all" && " Thử chọn loại quiz khác."}
            </div>
            <TypeSelector />
            <Button variant="outline" asChild className="mt-4 rounded-full">
              <Link href="/kanji">← Danh sách bài học</Link>
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // ── PHASE: Finished ──
  if (phase === "finished") {
    return (
      <div className="flex min-h-screen flex-col items-center p-4 pt-8">
        <div className="w-full max-w-[500px]">
          <div className="mb-3 text-center">
            {quizData.lesson_label && <Badge variant="outline" className="text-xs">{quizData.lesson_label}</Badge>}
            <h1 className="text-lg font-bold text-[var(--text-primary)] mt-2">Kết quả Quiz</h1>
          </div>
          <Card className="text-center py-8 animate-[fadeIn_0.5s_ease]">
            <CardContent className="px-6">
              <div className="text-6xl mb-3 animate-bounce">{resultEmoji}</div>
              <div className="text-4xl font-extrabold text-[var(--text-primary)]">{score.correct}/{totalQ}</div>
              <div className="text-sm text-[var(--text-secondary)] mt-2">{resultMessage}</div>
              <div className="flex justify-center gap-3 mt-4 mb-6">
                <Badge className="bg-emerald-500/10 text-emerald-600 border-emerald-500/20">✓ {score.correct} đúng</Badge>
                <Badge className="bg-red-500/10 text-red-600 border-red-500/20">✗ {score.wrong} sai</Badge>
              </div>
              <div className="flex flex-col items-center gap-2.5 sm:flex-row sm:justify-center">
                <Button onClick={retry} className="rounded-full bg-gradient-to-br from-indigo-500 to-violet-500 text-white shadow-[0_3px_12px_rgba(99,102,241,0.3)]">
                  🔄 Làm lại
                </Button>
                <Button variant="outline" asChild className="rounded-full">
                  <Link href="/kanji">← Danh sách</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // ── PHASE: Active Quiz ──
  const correctIdx = currentQ.options.findIndex(o => o.is_correct);

  return (
    <div className="flex min-h-screen flex-col items-center p-4 pt-6 max-sm:pt-4 max-sm:p-3">
      <div className="w-full max-w-[500px]">
        <div className="mb-2 flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => router.back()} className="text-[var(--text-tertiary)]">← Quay lại</Button>
          {quizData.lesson_label && <Badge variant="outline" className="text-xs">{quizData.lesson_label}</Badge>}
          <h1 className="ml-auto text-sm font-bold text-[var(--text-primary)]">Quiz Nhận diện Kanji</h1>
        </div>

        {/* Type selector */}
        <TypeSelector />

        {/* Progress */}
        <div className="mb-3">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <div className="flex gap-2">
              <Badge variant="outline" className="text-xs bg-emerald-500/10 text-emerald-600 border-emerald-500/20">✓ {score.correct}</Badge>
              <Badge variant="outline" className="text-xs bg-red-500/10 text-red-600 border-red-500/20">✗ {score.wrong}</Badge>
            </div>
            <span className="text-[var(--text-tertiary)] font-medium">{currentIdx + 1} / {totalQ}</span>
          </div>
          <Progress value={((currentIdx + 1) / totalQ) * 100} className="h-1.5" />
        </div>

        {/* Question Card */}
        <Card key={currentIdx} className="animate-[slideUp_0.3s_ease] py-0">
          <CardContent className="p-5 max-sm:p-4">
            <Badge variant="secondary" className="text-xs mb-3">{TYPE_LABELS[currentQ.question_type] || TYPE_LABELS.meaning}</Badge>

            <div className="text-center mb-4">
              {currentQ.question_type === "kanji" ? (
                <>
                  <div className="text-base text-[var(--text-primary)] font-medium mb-1">
                    {currentQ.sino_vi || "?"}
                  </div>
                  <div className="text-xs text-[var(--text-tertiary)]">Chọn chữ Kanji đúng</div>
                </>
              ) : (
                <>
                  <div className="text-6xl font-bold text-[var(--text-primary)] mb-2 animate-[fadeIn_0.3s_ease]" style={{ fontFamily: "var(--font-jp-user, 'Noto Sans JP'), sans-serif" }}>
                    {currentQ.char}
                  </div>
                  {currentQ.question_type === "meaning" ? null : (
                    selected !== null ? (
                      <div className="text-sm text-[var(--text-tertiary)] animate-[revealIn_0.3s_ease]">{currentQ.sino_vi}</div>
                    ) : null
                  )}
                </>
              )}

              {selected !== null && (currentQ.onyomi || currentQ.kunyomi) && (
                <div className="flex flex-wrap justify-center gap-2 mt-2 animate-[fadeIn_0.4s_ease]">
                  {currentQ.onyomi && (
                    <Badge variant="outline" className="text-xs bg-emerald-500/[0.08] text-emerald-500 border-emerald-500/20" style={{ fontFamily: "var(--font-jp-user, 'Noto Sans JP'), sans-serif" }}>
                      音 {currentQ.onyomi}
                    </Badge>
                  )}
                  {currentQ.kunyomi && (
                    <Badge variant="outline" className="text-xs bg-emerald-500/[0.08] text-emerald-500 border-emerald-500/20" style={{ fontFamily: "var(--font-jp-user, 'Noto Sans JP'), sans-serif" }}>
                      訓 {currentQ.kunyomi}
                    </Badge>
                  )}
                </div>
              )}
            </div>

            <div className="text-sm text-[var(--text-secondary)] text-center mb-3 font-medium">{TYPE_PROMPTS[currentQ.question_type]}</div>

            <div className="flex flex-col gap-2">
              {currentQ.options.map((opt, idx) => {
                const isSelected = selected === idx;
                const isCorrectOpt = opt.is_correct;
                const isWrongSelection = isSelected && !isCorrectOpt;
                const showAsCorrect = selected !== null && isCorrectOpt;

                return (
                  <button key={idx}
                    className={cn(
                      "group flex w-full items-center gap-3 rounded-[14px] border-[1.5px] border-l-[3px] border-l-transparent px-4 py-3 text-left transition-all",
                      "border-[var(--border-default)] bg-[var(--bg-surface)] cursor-pointer",
                      selected === null && "hover:border-indigo-300 hover:border-l-indigo-500 hover:bg-indigo-500/[0.03] hover:translate-x-1",
                      showAsCorrect && "!border-emerald-400 !border-l-emerald-500 !bg-emerald-500/[0.05] animate-[pulseOk_0.6s_ease]",
                      isWrongSelection && "!border-red-300 !border-l-red-500 !bg-red-500/[0.04] animate-[shake_0.4s_ease]",
                      selected !== null && !showAsCorrect && !isWrongSelection && "opacity-50",
                      selected !== null && "cursor-default"
                    )}
                    onClick={() => handleSelect(idx)}
                    disabled={selected !== null}
                    style={currentQ.question_type === "kanji" ? { fontFamily: "var(--font-jp-user, 'Noto Sans JP'), sans-serif", fontSize: "1.4rem", textAlign: "center" } : undefined}
                  >
                    <span className={cn(
                      "flex h-5 w-5 shrink-0 items-center justify-center rounded text-[0.65rem] font-bold transition-all",
                      "bg-[var(--border-subtle)] text-[var(--text-tertiary)]",
                      selected === null && "group-hover:bg-indigo-500 group-hover:text-white",
                      showAsCorrect && "!bg-emerald-500 !text-white",
                      isWrongSelection && "!bg-red-500 !text-white"
                    )}>{idx + 1}</span>
                    <span className="flex-1">{opt.text}</span>
                  </button>
                );
              })}
            </div>

            {showNext && (
              <>
                <div className="mt-3 h-[3px] w-full overflow-hidden rounded-sm bg-[var(--border-subtle)]">
                  <div className="h-full rounded-sm bg-gradient-to-r from-indigo-500 to-violet-500" style={{ width: `${autoProgress}%`, transition: "width linear" }} />
                </div>
                <div className="mt-2 text-center">
                  <Button onClick={() => {
                    if (autoTimerRef.current) clearInterval(autoTimerRef.current);
                    nextQuestion();
                  }}
                    className="rounded-full bg-gradient-to-br from-indigo-500 to-violet-500 text-white shadow-[0_3px_12px_rgba(99,102,241,0.3)] animate-[revealIn_0.3s_ease]"
                  >
                    Câu tiếp theo →
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
