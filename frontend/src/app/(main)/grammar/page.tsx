"use client";

import { Suspense, useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import s from "./grammar.module.css";

interface GrammarPoint {
  id: number;
  slug: string;
  title: string;
  meaning: string;
  structure: string;
  level: string;
}

const LEVELS = ["N5", "N4", "N3", "N2", "N1"];

const levelConfig: Record<string, { gradient: string; glow: string; icon: string; label: string }> = {
  N5: { gradient: "linear-gradient(135deg, #34d399, #10b981)", glow: "rgba(16,185,129,0.2)", icon: "🌱", label: "Sơ cấp" },
  N4: { gradient: "linear-gradient(135deg, #2dd4bf, #14b8a6)", glow: "rgba(20,184,166,0.2)", icon: "🌿", label: "Cơ bản" },
  N3: { gradient: "linear-gradient(135deg, #60a5fa, #3b82f6)", glow: "rgba(59,130,246,0.2)", icon: "📘", label: "Trung cấp" },
  N2: { gradient: "linear-gradient(135deg, #a78bfa, #8b5cf6)", glow: "rgba(139,92,246,0.2)", icon: "📕", label: "Nâng cao" },
  N1: { gradient: "linear-gradient(135deg, #fbbf24, #f59e0b)", glow: "rgba(245,158,11,0.2)", icon: "👑", label: "Cao cấp" },
};

function GrammarHomeInner() {
  const searchParams = useSearchParams();
  const levelParam = searchParams.get("level")?.toUpperCase() || "";
  const activeLevel = LEVELS.includes(levelParam) ? levelParam : "";

  const [points, setPoints] = useState<GrammarPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const url = `/api/v1/grammar/points${activeLevel ? `?level=${activeLevel}` : ""}`;
    fetch(url, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((data) => {
        setPoints(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(() => {
        setPoints([]);
        setLoading(false);
      });
  }, [activeLevel]);

  const filtered = useMemo(() => {
    if (!search.trim()) return points;
    const q = search.trim().toLowerCase();
    return points.filter(
      (p) =>
        p.title.toLowerCase().includes(q) ||
        (p.meaning || "").toLowerCase().includes(q) ||
        (p.structure || "").toLowerCase().includes(q)
    );
  }, [points, search]);

  const grouped = useMemo(() => {
    if (activeLevel) return { [activeLevel]: filtered };
    const g: Record<string, GrammarPoint[]> = {};
    for (const p of filtered) {
      if (!g[p.level]) g[p.level] = [];
      g[p.level].push(p);
    }
    return g;
  }, [filtered, activeLevel]);

  const totalCount = points.length;

  return (
    <div className={s.page}>
      {/* Hero */}
      <div className={s.hero}>
        <div className={s.heroContent}>
          <div className={s.heroIcon}>文</div>
          <div>
            <h1 className={s.heroTitle}>Ngữ pháp JLPT</h1>
            <p className={s.heroSub}>{totalCount} mẫu ngữ pháp · N5 → N1</p>
          </div>
        </div>
        <div className={s.searchWrap}>
          <svg className={s.searchIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
          </svg>
          <input
            type="text"
            placeholder="Tìm ngữ pháp... vd: ために, tại vì..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className={s.searchInput}
          />
          {search && <button onClick={() => setSearch("")} className={s.searchClear}>✕</button>}
        </div>
      </div>

      {/* Tabs */}
      <div className={s.tabsRow}>
        <div className={s.tabs}>
          <Link href="/grammar" className={`${s.tab} ${!activeLevel ? s.tabActive : ""}`}>
            Tất cả<span className={s.tabCount}>{totalCount}</span>
          </Link>
          {LEVELS.map((lv) => {
            const config = levelConfig[lv];
            const count = points.filter((p) => p.level === lv).length;
            return (
              <Link
                key={lv}
                href={`/grammar?level=${lv}`}
                className={`${s.tab} ${activeLevel === lv ? s.tabActive : ""}`}
                style={activeLevel === lv ? { background: config.gradient, color: "#fff" } : {}}
              >
                <span className={s.tabEmoji}>{config.icon}</span>
                {lv}
                {count > 0 && <span className={s.tabCount}>{count}</span>}
              </Link>
            );
          })}
        </div>
        <Link href="/grammar/books" className={s.booksLink}>📚 Theo sách</Link>
      </div>

      {/* Content */}
      {loading ? (
        <div className={s.loading}>
          <div className={s.spinner} />
          <span>Đang tải...</span>
        </div>
      ) : filtered.length > 0 ? (
        <div>
          {Object.entries(grouped).map(([level, pts]) => {
            const config = levelConfig[level] || levelConfig.N3;
            return (
              <div key={level} className={s.levelSection}>
                {!activeLevel && (
                  <div className={s.levelHeader}>
                    <div className={s.levelBadge} style={{ background: config.gradient }}>
                      {config.icon} {level}
                    </div>
                    <span className={s.levelLabel}>{config.label} · {pts.length} mẫu</span>
                    <div className={s.levelLine} />
                  </div>
                )}
                <div className={s.grid}>
                  {pts.map((point, i) => (
                    <Link
                      key={point.id}
                      href={`/grammar/${point.slug}`}
                      className={s.card}
                      style={{ animationDelay: `${i * 30}ms` }}
                    >
                      <div className={s.cardTop}>
                        <h3 className={s.cardTitle}>{point.title}</h3>
                        <span className={s.cardLevel} style={{ background: config.gradient }}>
                          {point.level}
                        </span>
                      </div>
                      {point.meaning && <p className={s.cardMeaning}>{point.meaning}</p>}
                      {point.structure && <p className={s.cardStructure}>{point.structure}</p>}
                      <div className={s.cardArrow}>→</div>
                    </Link>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className={s.empty}>
          <div className={s.emptyIcon}>🔍</div>
          <p className={s.emptyTitle}>
            {search ? `Không tìm thấy "${search}"` : "Chưa có ngữ pháp nào"}
          </p>
          <p className={s.emptySub}>Thử tìm bằng tiếng Nhật hoặc tiếng Việt</p>
        </div>
      )}
    </div>
  );
}

export default function GrammarHomePage() {
  return (
    <Suspense fallback={<div style={{ padding: '60px 24px', textAlign: 'center', color: 'var(--text-tertiary)' }}>Đang tải...</div>}>
      <GrammarHomeInner />
    </Suspense>
  );
}
