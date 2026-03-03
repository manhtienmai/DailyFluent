"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

/* ── Load choukai.css from public ── */
function useChoukaiCSS() {
  useEffect(() => {
    const id = "choukai-css";
    if (document.getElementById(id)) return;
    const link = document.createElement("link");
    link.id = id;
    link.rel = "stylesheet";
    link.href = "/css/choukai.css";
    document.head.appendChild(link);
    return () => { link.remove(); };
  }, []);
}

/* ── Types ── */
interface QidItem { id: number; num: number; correct: string }
interface MondaiGroup { key: string; label: string; count: number; qids: QidItem[] }
interface BookData {
  id: number; slug: string; title: string; level: string;
  description: string; cover_url: string;
  mondai_groups: MondaiGroup[]; total_questions: number;
  first_key: string; initial_answers: Record<string, string>;
}
interface ChoiceData { key: string; html: string }
interface LineData { speaker: string; html: string; vi: string }
interface QuestionData {
  id: number; num: number; audio_url: string; image_url: string;
  text: string; correct: string; choices: ChoiceData[]; lines: LineData[];
}

/* ── Audio Player Hook ── */
function useAudioPlayer() {
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [bufferedPct, setBufferedPct] = useState(0);
  const [speed, setSpeedState] = useState(1);
  const [volume, setVolumeState] = useState(1);
  const [activeUrl, setActiveUrl] = useState("");
  const [muted, setMuted] = useState(false);
  const speeds = [0.5, 0.75, 1, 1.25, 1.5, 2];
  const audioElRef = useRef<HTMLAudioElement | null>(null);
  const listenersAttached = useRef(false);

  /* Callback ref — attaches listeners when audio element appears */
  const setAudioRef = useCallback((el: HTMLAudioElement | null) => {
    // Clean up old listeners
    if (audioElRef.current && listenersAttached.current) {
      const old = audioElRef.current;
      old.removeEventListener("timeupdate", onTimeUpdate);
      old.removeEventListener("durationchange", onDurationChange);
      old.removeEventListener("progress", onProgress);
      old.removeEventListener("play", onPlay);
      old.removeEventListener("pause", onPause);
      old.removeEventListener("ended", onEnded);
      listenersAttached.current = false;
    }
    audioElRef.current = el;
    if (el) {
      el.addEventListener("timeupdate", onTimeUpdate);
      el.addEventListener("durationchange", onDurationChange);
      el.addEventListener("progress", onProgress);
      el.addEventListener("play", onPlay);
      el.addEventListener("pause", onPause);
      el.addEventListener("ended", onEnded);
      listenersAttached.current = true;
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function onTimeUpdate() { const a = audioElRef.current; if (a) setCurrentTime(a.currentTime); }
  function onDurationChange() { const a = audioElRef.current; if (a) setDuration(a.duration || 0); }
  function onProgress() {
    const a = audioElRef.current;
    if (a && a.buffered.length > 0 && a.duration) {
      setBufferedPct((a.buffered.end(a.buffered.length - 1) / a.duration) * 100);
    }
  }
  function onPlay() { setPlaying(true); }
  function onPause() { setPlaying(false); }
  function onEnded() { setPlaying(false); setCurrentTime(0); }

  const prevUrlRef = useRef("");

  const play = useCallback((url: string) => {
    const a = audioElRef.current;
    if (!a) return;
    if (prevUrlRef.current !== url && url) {
      a.src = url;
      a.load();
    }
    prevUrlRef.current = url;
    setActiveUrl(url);
    a.play().catch(() => {});
  }, []);

  const togglePlay = useCallback(() => {
    const a = audioElRef.current;
    if (!a) return;
    if (a.paused) a.play().catch(() => {}); else a.pause();
  }, []);

  const skip = useCallback((sec: number) => {
    const a = audioElRef.current;
    if (!a) return;
    a.currentTime = Math.max(0, Math.min(a.duration || 0, a.currentTime + sec));
  }, []);

  const seek = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const a = audioElRef.current;
    if (!a || !a.duration) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    a.currentTime = pct * a.duration;
  }, []);

  const setSpeed = useCallback((s: number) => {
    const a = audioElRef.current;
    if (a) a.playbackRate = s;
    setSpeedState(s);
  }, []);

  const setVolume = useCallback((v: number) => {
    const a = audioElRef.current;
    if (a) { a.volume = v; a.muted = false; }
    setVolumeState(v);
    setMuted(false);
  }, []);

  const toggleMute = useCallback(() => {
    const a = audioElRef.current;
    if (a) a.muted = !a.muted;
    setMuted((m) => !m);
  }, []);

  const progressPct = duration ? (currentTime / duration) * 100 : 0;
  const fmtTime = (t: number) => {
    if (!t || !isFinite(t)) return "0:00";
    const m = Math.floor(t / 60);
    const s = Math.floor(t % 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  return { setAudioRef, activeUrl, playing, currentTime, duration, bufferedPct, progressPct, speed, speeds, volume, muted, play, togglePlay, skip, seek, setSpeed, setVolume, toggleMute, fmtTime };
}

/* ── Main Page ── */
export default function ChoukaiBookDetailPage() {
  useChoukaiCSS();
  const params = useParams();
  const slug = params.slug as string;
  const player = useAudioPlayer();

  const [book, setBook] = useState<BookData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeMondai, setActiveMondai] = useState("");
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [answered, setAnswered] = useState<Record<number, boolean>>({});
  const [currentQuestions, setCurrentQuestions] = useState<QuestionData[]>([]);
  const [questionsLoading, setQuestionsLoading] = useState(false);
  const [viOpen, setViOpen] = useState<Record<number, boolean>>({});
  const [transcriptOpen, setTranscriptOpen] = useState<Record<number, boolean>>({});
  const [showSpeed, setShowSpeed] = useState<Record<number, boolean>>({});
  const [qmapCollapsed, setQmapCollapsed] = useState(false);
  const cacheRef = useRef<Record<string, QuestionData[]>>({});

  /* Load book data */
  useEffect(() => {
    fetch(`/api/v1/exam/choukai/${slug}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d: BookData) => {
        setBook(d);
        setActiveMondai(d.first_key);
        // Restore previous answers
        const ans: Record<number, string> = {};
        const ansd: Record<number, boolean> = {};
        for (const [qid, key] of Object.entries(d.initial_answers || {})) {
          const id = parseInt(qid);
          if (key) { ans[id] = key; ansd[id] = true; }
        }
        setAnswers(ans);
        setAnswered(ansd);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [slug]);

  /* Load questions for a mondai group */
  const loadMondai = useCallback(async (key: string) => {
    if (cacheRef.current[key]) {
      setCurrentQuestions(cacheRef.current[key]);
      return;
    }
    setQuestionsLoading(true);
    setCurrentQuestions([]);
    try {
      const res = await fetch(`/api/v1/exam/choukai/${slug}/mondai/${key}`, { credentials: "include" });
      const data = await res.json();
      const qs = data.questions || [];
      cacheRef.current[key] = qs;
      setCurrentQuestions(qs);
    } catch {
      setCurrentQuestions([]);
    }
    setQuestionsLoading(false);
  }, [slug]);

  /* Auto-load first mondai */
  useEffect(() => {
    if (activeMondai) loadMondai(activeMondai);
  }, [activeMondai, loadMondai]);

  /* Switch mondai */
  const switchMondai = (key: string) => setActiveMondai(key);

  /* Select a choice */
  const selectChoice = (qId: number, choiceKey: string, correctKey: string) => {
    if (answered[qId]) return;
    setAnswers((prev) => ({ ...prev, [qId]: choiceKey }));
    setAnswered((prev) => ({ ...prev, [qId]: true }));
    // Auto-open transcript after answering
    setTranscriptOpen((prev) => ({ ...prev, [qId]: true }));
    // Save to server
    fetch("/api/v1/exam/choukai/save-answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ question_id: qId, selected_key: choiceKey }),
    }).catch(() => {});
  };

  /* Question map helpers */
  const allQids = book?.mondai_groups.flatMap((g) => g.qids) || [];
  const qmapCorrect = allQids.filter((q) => answered[q.id] && answers[q.id] === q.correct).length;
  const qmapWrong = allQids.filter((q) => answered[q.id] && answers[q.id] !== q.correct).length;
  const qmapPending = allQids.filter((q) => !answered[q.id]).length;

  /* Mondai qids map */
  const mondaiQids: Record<string, number[]> = {};
  book?.mondai_groups.forEach((g) => { mondaiQids[g.key] = g.qids.map((q) => q.id); });
  const activeQids = mondaiQids[activeMondai] || [];
  const answeredCount = activeQids.filter((id) => answered[id]).length;
  const progressPct = activeQids.length ? Math.round((answeredCount / activeQids.length) * 100) : 0;

  /* Jump to question */
  const jumpToQuestion = async (mondaiKey: string, qId: number) => {
    if (activeMondai !== mondaiKey) {
      setActiveMondai(mondaiKey);
      await loadMondai(mondaiKey);
    }
    setTimeout(() => {
      const el = document.getElementById("ck-q-" + qId);
      if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 100);
  };

  return (
    <div className="choukai-page">
      {/* Audio element — always rendered so event listeners attach immediately */}
      <audio ref={player.setAudioRef} preload="none" style={{ display: "none", position: "absolute", pointerEvents: "none" }} />

      {loading ? (
        <div className="choukai-container">
          <div className="ck-glass" style={{ padding: "3rem", textAlign: "center" }}>
            <div className="ck-loading-spinner" />
            <p style={{ color: "var(--text-secondary)", marginTop: "0.75rem", fontSize: "0.875rem" }}>Đang tải...</p>
          </div>
        </div>
      ) : !book ? (
        <div className="choukai-container">
          <div className="ck-glass" style={{ padding: "2rem", textAlign: "center", color: "var(--text-secondary)" }}>Không tìm thấy sách.</div>
        </div>
      ) : (
      <div className="choukai-container">

        {/* ── Breadcrumb ── */}
        <div className="ck-breadcrumb">
          <Link href="/exam/choukai">Luyện nghe</Link>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M9 18l6-6-6-6" /></svg>
          <span>{book.title}</span>
        </div>

        {/* ── Book Header ── */}
        <div className="ck-glass ck-detail-header">
          <div className="ck-detail-cover">
            {book.cover_url ? (
              <img src={book.cover_url} alt={book.title} />
            ) : (
              <div className={`ck-detail-cover-placeholder ck-book-placeholder--${book.level.toLowerCase()}`}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ width: 48, height: 48, opacity: 0.4 }}>
                  <path d="M3 18v-6a9 9 0 0118 0v6" />
                  <path d="M21 19a2 2 0 01-2 2h-1a2 2 0 01-2-2v-3a2 2 0 012-2h3zM3 19a2 2 0 002 2h1a2 2 0 002-2v-3a2 2 0 00-2-2H3z" />
                </svg>
              </div>
            )}
          </div>
          <div className="ck-detail-info">
            <h1>{book.title}</h1>
            <div className="ck-book-meta">
              <span className={`ck-level-badge ck-level-badge--${book.level.toLowerCase()}`}>{book.level}</span>
            </div>
            {book.description && <p className="ck-book-desc">{book.description}</p>}
            <div className="ck-detail-stats">
              <div className="ck-detail-stat">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: 16, height: 16 }}>
                  <path d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01" />
                </svg>
                <strong>{book.total_questions}</strong> câu hỏi
              </div>
              <div className="ck-detail-stat">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: 16, height: 16 }}>
                  <rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" />
                  <rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" />
                </svg>
                <strong>{book.mondai_groups.length}</strong> もんだい
              </div>
            </div>
          </div>
        </div>

        {/* ── Question Map ── */}
        {book.mondai_groups.length > 0 && (
          <div className="ck-glass ck-qmap">
            <div className="ck-qmap-header">
              <div className="ck-qmap-title">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" />
                  <rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" />
                </svg>
                Bản đồ câu hỏi
              </div>
              <div className="ck-qmap-legend">
                <span className="ck-qmap-legend-item">
                  <span className="ck-qmap-legend-dot ck-qmap-legend-dot--correct" />
                  Đúng ({qmapCorrect})
                </span>
                <span className="ck-qmap-legend-item">
                  <span className="ck-qmap-legend-dot ck-qmap-legend-dot--wrong" />
                  Sai ({qmapWrong})
                </span>
                <span className="ck-qmap-legend-item">
                  <span className="ck-qmap-legend-dot ck-qmap-legend-dot--pending" />
                  Chưa làm ({qmapPending})
                </span>
                <button className="ck-qmap-toggle" onClick={() => setQmapCollapsed(!qmapCollapsed)}>
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
                    style={qmapCollapsed ? {} : { transform: "rotate(180deg)" }}>
                    <path d="M19 9l-7 7-7-7" />
                  </svg>
                  <span>{qmapCollapsed ? "Xem" : "Thu gọn"}</span>
                </button>
              </div>
            </div>

            {!qmapCollapsed && (
              <div className="ck-qmap-body">
                {book.mondai_groups.map((group) => (
                  <div className="ck-qmap-group" key={group.key}>
                    <div className={`ck-qmap-group-label ck-qmap-group-label--${group.key}`}>
                      {group.label} — {group.count} câu
                    </div>
                    <div className="ck-qmap-grid">
                      {group.qids.map((q) => {
                        const isAnswered = answered[q.id];
                        const isCorrect = isAnswered && answers[q.id] === q.correct;
                        const isWrong = isAnswered && answers[q.id] !== q.correct;
                        let cls = "ck-qmap-cell";
                        if (isCorrect) cls += " ck-qmap-cell--correct";
                        else if (isWrong) cls += " ck-qmap-cell--wrong";
                        else cls += " ck-qmap-cell--pending";
                        if (q.num >= 100) cls += " ck-qmap-cell--sm";
                        const title = isAnswered
                          ? (isCorrect ? `Câu ${q.num}: Đúng ✓` : `Câu ${q.num}: Sai ✗ — ĐA: ${q.correct}`)
                          : `Câu ${q.num}: Chưa làm`;
                        return (
                          <button key={q.id} type="button" className={cls} title={title}
                            onClick={() => jumpToQuestion(group.key, q.id)}>
                            {q.num}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── Mondai Tabs ── */}
        {book.mondai_groups.length > 0 && (
          <>
            <div className="ck-glass ck-mondai-tabs">
              {book.mondai_groups.map((group) => (
                <button key={group.key}
                  className={`ck-mondai-tab ${activeMondai === group.key ? `ck-mondai-tab--active-${group.key}` : ""}`}
                  onClick={() => switchMondai(group.key)}>
                  <span>{group.label}</span>
                  <span className="ck-tab-count">{group.count}</span>
                </button>
              ))}
            </div>

            {/* ── Questions Container ── */}
            <div id="ck-questions-container">
              {questionsLoading ? (
                <div className="ck-glass" style={{ padding: "2rem", textAlign: "center" }}>
                  <div className="ck-loading-spinner" />
                  <p style={{ color: "var(--text-secondary)", marginTop: "0.75rem", fontSize: "0.875rem" }}>Đang tải câu hỏi...</p>
                </div>
              ) : currentQuestions.length > 0 ? (
                <div>
                  {/* Progress bar */}
                  <div className="ck-glass ck-progress">
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span className="ck-progress-text">{answeredCount} / {activeQids.length} đã trả lời</span>
                      <span className="ck-progress-text">{progressPct}%</span>
                    </div>
                    <div className="ck-progress-bar">
                      <div className={`ck-progress-fill ck-progress-fill--${activeMondai}`}
                        style={{ width: `${progressPct}%` }} />
                    </div>
                  </div>

                  {/* Question cards */}
                  {currentQuestions.map((q) => (
                    <div key={q.id} id={`ck-q-${q.id}`} className="ck-glass ck-question-card">
                      {/* Header: number + player */}
                      <div className="ck-q-header">
                        <span className={`ck-q-number ck-q-number--${activeMondai}`}>{q.num}</span>

                        {/* Audio player */}
                        {q.audio_url && (
                          <AudioPlayer player={player} audioUrl={q.audio_url} qId={q.id} qNum={q.num}
                            showSpeed={showSpeed} setShowSpeed={setShowSpeed} />
                        )}
                      </div>

                      {/* Image + Choices layout */}
                      <div className={`ck-split-layout ${q.image_url ? "ck-split-layout--has-image" : ""}`}>
                        {q.image_url && (
                          <div className="ck-split-image">
                            <img src={q.image_url} alt={`Q${q.num}`} loading="lazy" />
                          </div>
                        )}
                        <div className="ck-split-choices">
                          <div className="ck-choices">
                            {q.choices.map((c) => {
                              const isAns = answered[q.id];
                              let cls = "ck-choice-btn";
                              if (answers[q.id] === c.key && !isAns) cls += " ck-choice--selected";
                              if (isAns && c.key === q.correct) cls += " ck-choice--correct";
                              if (isAns && answers[q.id] === c.key && c.key !== q.correct) cls += " ck-choice--wrong";
                              if (isAns) cls += " ck-choice--answered";
                              return (
                                <button key={c.key} className={cls}
                                  onClick={() => selectChoice(q.id, c.key, q.correct)}>
                                  <span className="ck-choice-key">{c.key}</span>
                                  <span className="ck-choice-text ck-ruby" dangerouslySetInnerHTML={{ __html: c.html }} />
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      </div>

                      {/* Transcript toggle + section */}
                      {answered[q.id] && q.lines && q.lines.length > 0 && (
                        <div className="ck-transcript-section">
                          <div className="ck-transcript-toolbar">
                            <button className="ck-transcript-toggle" onClick={() => setTranscriptOpen((prev) => ({ ...prev, [q.id]: !prev[q.id] }))}>
                              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: 14, height: 14 }}>
                                <path d="M4 6h16M4 12h16M4 18h10" />
                              </svg>
                              <span>{transcriptOpen[q.id] ? "Ẩn hội thoại" : "Xem hội thoại"}</span>
                            </button>
                            {transcriptOpen[q.id] && (
                              <button className="ck-transcript-toggle" onClick={() => setViOpen((prev) => ({ ...prev, [q.id]: !prev[q.id] }))}>
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: 14, height: 14 }}>
                                  <path d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                                </svg>
                                <span>{viOpen[q.id] ? "Ẩn bản dịch" : "Hiện bản dịch"}</span>
                              </button>
                            )}
                          </div>
                          {transcriptOpen[q.id] && (
                            <div className="ck-transcript-lines">
                              {q.lines.map((ln, lnIdx) => (
                                <div key={lnIdx} className="ck-transcript-line">
                                  <div className="ck-transcript-line-jp">
                                    {ln.speaker === "F" && <span className="ck-speaker-tag ck-speaker-f">F</span>}
                                    {ln.speaker === "M" && <span className="ck-speaker-tag ck-speaker-m">M</span>}
                                    {ln.speaker === "N" && <span className="ck-narrator-tag">▶</span>}
                                    <span className="ck-line-text ck-ruby" dangerouslySetInnerHTML={{ __html: ln.html }} />
                                  </div>
                                  {ln.vi && viOpen[q.id] && (
                                    <div className="ck-transcript-line-vi">{ln.vi}</div>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="ck-glass" style={{ padding: "2rem", textAlign: "center", color: "var(--text-secondary)" }}>
                  Chưa có câu hỏi nào trong nhóm này.
                </div>
              )}
            </div>
          </>
        )}

        {book.mondai_groups.length === 0 && (
          <div className="ck-glass" style={{ padding: "2rem", textAlign: "center", color: "#64748b" }}>
            Chưa có câu hỏi nào trong sách này.
          </div>
        )}
      </div>
      )}
    </div>
  );
}

/* ── Audio Player Component ── */
function AudioPlayer({ player, audioUrl, qId, qNum, showSpeed, setShowSpeed }: {
  player: ReturnType<typeof useAudioPlayer>;
  audioUrl: string; qId: number; qNum: number;
  showSpeed: Record<number, boolean>;
  setShowSpeed: React.Dispatch<React.SetStateAction<Record<number, boolean>>>;
}) {
  const isActive = player.activeUrl === audioUrl;

  return (
    <div className="ck-card-player">
      <div className="ck-cp-body">
        <div className="ck-cp-row">
          {/* Skip -5s */}
          <button className="ck-cp-btn ck-cp-skip" onClick={() => player.skip(-5)} title="-5s">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: 17, height: 17 }}>
              <path d="M1 4v6h6" /><path d="M3.51 15a9 9 0 105.64-8.36L1 10" />
            </svg>
            <span className="ck-cp-skip5">5</span>
          </button>

          {/* Play/Pause */}
          <button className="ck-cp-btn ck-cp-playpause"
            onClick={() => isActive ? player.togglePlay() : player.play(audioUrl)}>
            {(!isActive || !player.playing) ? (
              <svg viewBox="0 0 24 24" fill="currentColor" style={{ width: 15, height: 15 }}><path d="M8 5v14l11-7z" /></svg>
            ) : (
              <svg viewBox="0 0 24 24" fill="currentColor" style={{ width: 15, height: 15 }}>
                <rect x="6" y="4" width="4" height="16" rx="1" /><rect x="14" y="4" width="4" height="16" rx="1" />
              </svg>
            )}
          </button>

          {/* Skip +5s */}
          <button className="ck-cp-btn ck-cp-skip" onClick={() => player.skip(5)} title="+5s">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: 17, height: 17 }}>
              <path d="M23 4v6h-6" /><path d="M20.49 15a9 9 0 11-5.64-8.36L23 10" />
            </svg>
            <span className="ck-cp-skip5">5</span>
          </button>

          {/* Progress bar */}
          <div className="ck-cp-progress"
            onClick={(e) => isActive ? player.seek(e) : player.play(audioUrl)}>
            <div className="ck-cp-buf" style={{ width: isActive ? `${player.bufferedPct}%` : "0" }} />
            <div className="ck-cp-fill" style={{ width: isActive ? `${player.progressPct}%` : "0" }} />
          </div>

          {/* Time */}
          <span className="ck-cp-time">
            {isActive ? `${player.fmtTime(player.currentTime)} / ${player.fmtTime(player.duration)}` : "—"}
          </span>

          {/* Speed */}
          <div style={{ position: "relative" }}>
            <button className="ck-cp-speed-btn" onClick={() => setShowSpeed((prev) => ({ ...prev, [qId]: !prev[qId] }))}>
              {player.speed === 1 ? "1x" : `${player.speed}x`}
            </button>
            {showSpeed[qId] && (
              <div className="ck-cp-speed-menu" onClick={(e) => e.stopPropagation()}>
                {player.speeds.map((s) => (
                  <button key={s} className={`ck-cp-speed-opt ${player.speed === s ? "active" : ""}`}
                    onClick={() => { player.setSpeed(s); setShowSpeed((prev) => ({ ...prev, [qId]: false })); }}>
                    {s}x
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Volume */}
          <VolumeSlider player={player} />
        </div>
      </div>
    </div>
  );
}

/* ── Volume Slider with Drag Support ── */
function VolumeSlider({ player }: { player: ReturnType<typeof useAudioPlayer> }) {
  const trackRef = useRef<HTMLDivElement>(null);
  const draggingRef = useRef(false);

  const calcVolume = useCallback((clientX: number) => {
    if (!trackRef.current) return;
    const rect = trackRef.current.getBoundingClientRect();
    const pct = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
    player.setVolume(pct);
  }, [player]);

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    draggingRef.current = true;
    calcVolume(e.clientX);

    const onMouseMove = (ev: MouseEvent) => {
      if (draggingRef.current) calcVolume(ev.clientX);
    };
    const onMouseUp = () => {
      draggingRef.current = false;
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };
    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
  }, [calcVolume]);

  return (
    <div className="ck-cp-vol">
      <button className="ck-cp-btn ck-cp-vol-btn" onClick={() => player.toggleMute()}
        title={player.muted ? "Bật âm" : "Tắt âm"}>
        {(player.muted || player.volume === 0) ? (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: 16, height: 16 }}>
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
            <line x1="23" y1="9" x2="17" y2="15" /><line x1="17" y1="9" x2="23" y2="15" />
          </svg>
        ) : player.volume <= 0.5 ? (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: 16, height: 16 }}>
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
            <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: 16, height: 16 }}>
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
            <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
          </svg>
        )}
      </button>
      <div ref={trackRef} className="ck-cp-vol-track"
        style={{ '--vol-pct': `${(player.muted ? 0 : player.volume) * 100}%` } as React.CSSProperties}
        onMouseDown={onMouseDown}>
        <div className="ck-cp-vol-fill" />
        <div className="ck-cp-vol-thumb" />
      </div>
    </div>
  );
}
