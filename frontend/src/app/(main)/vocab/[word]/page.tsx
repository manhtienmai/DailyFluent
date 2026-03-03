"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

/* ── Types ── */
interface KanjiBreakdown {
  char: string;
  sino_vi: string;
  meaning_vi: string;
  formation: string;
}

interface RelatedVocab {
  id: number;
  word: string;
  reading: string;
  meaning: string;
}

interface VocabDetail {
  word: string;
  reading: string;
  meaning: string;
  kanji_breakdown: KanjiBreakdown[];
  related_vocab: RelatedVocab[];
}

export default function VocabWordPage() {
  const params = useParams();
  const word = decodeURIComponent(params.word as string);

  const [data, setData] = useState<VocabDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!data) setLoading(true);
    setError(null);
    fetch(`/api/v1/kanji/vocab/word/${encodeURIComponent(word)}`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((d: VocabDetail) => {
        setData(d);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [word]);

  /* Loading */
  if (loading && !data) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="w-7 h-7 border-3 border-df-border border-t-indigo-500 rounded-full animate-spin" />
      </div>
    );
  }

  /* Error */
  if (error || !data) {
    return (
      <div className="flex items-center justify-center min-h-[50vh] text-df-error text-sm">
        Không tìm thấy từ vựng: <strong className="ml-1">{word}</strong>
      </div>
    );
  }

  const hasBreakdown = data.kanji_breakdown.length > 0;
  const hasMultiKanji = data.kanji_breakdown.length >= 2;

  return (
    <div className="max-w-2xl mx-auto px-4 pt-6 pb-14">

      {/* ── Breadcrumb ── */}
      <nav className="flex items-center gap-1.5 text-xs text-df-tertiary mb-5">
        <Link href="/kanji" className="hover:text-df-primary transition-colors">
          Hán tự
        </Link>
        <span className="opacity-40">/</span>
        <span className="text-df-primary font-semibold">{data.word}</span>
      </nav>

      {/* ── Hero Card ── */}
      <div className="bg-df-surface border border-df-border rounded-2xl shadow-df-sm overflow-hidden mb-6">
        <div className="pt-10 pb-8 px-6 text-center">
          {/* Reading + Word */}
          <p className="text-df-secondary text-sm font-medium tracking-wide mb-1 font-jp">
            {data.reading}
          </p>
          <h1 className="font-jp text-5xl font-extrabold text-df-primary leading-tight tracking-wide">
            {data.word}
          </h1>
          <p className="text-df-secondary text-lg font-medium mt-3">
            {data.meaning}
          </p>
        </div>

        {/* Formula bar */}
        {hasMultiKanji && (
          <div className="border-t border-df-border-subtle bg-indigo-50/40 dark:bg-indigo-950/20 px-5 py-3">
            <div className="flex items-center justify-center gap-2 flex-wrap">
              {data.kanji_breakdown.map((k, i) => (
                <span key={k.char} className="inline-flex items-center gap-1">
                  {i > 0 && <span className="text-df-tertiary text-xs font-semibold mx-0.5">+</span>}
                  <Link
                    href={`/kanji/${encodeURIComponent(k.char)}`}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/70 dark:bg-white/5 border border-indigo-200/50 dark:border-indigo-500/20 hover:border-indigo-400 hover:shadow-sm transition-all text-sm no-underline group"
                  >
                    <span className="font-jp text-base font-bold text-df-primary group-hover:text-indigo-600 transition-colors">
                      {k.char}
                    </span>
                    <span className="text-indigo-500 dark:text-indigo-400 text-xs font-semibold">
                      {k.sino_vi}
                    </span>
                  </Link>
                </span>
              ))}
              <span className="text-df-tertiary text-sm mx-1">→</span>
              <span className="text-df-primary text-sm font-semibold">{data.meaning}</span>
            </div>
          </div>
        )}
      </div>

      {/* ── Kanji Breakdown Cards ── */}
      {hasBreakdown && (
        <section className="mb-6">
          <h2 className="text-[11px] font-bold text-df-tertiary uppercase tracking-widest mb-3 ml-1">
            Thành phần Kanji
          </h2>
          <div className="flex flex-col gap-3">
            {data.kanji_breakdown.map((k) => (
              <Link
                key={k.char}
                href={`/kanji/${encodeURIComponent(k.char)}`}
                className="group flex items-start gap-4 p-4 bg-df-surface border border-df-border rounded-2xl hover:border-indigo-300 dark:hover:border-indigo-500/40 hover:shadow-df-md transition-all no-underline"
              >
                {/* Kanji icon */}
                <div className="shrink-0 w-14 h-14 rounded-xl bg-gradient-to-br from-indigo-50 to-indigo-100 dark:from-indigo-950/50 dark:to-indigo-900/30 flex items-center justify-center border border-indigo-100 dark:border-indigo-800/30">
                  <span className="font-jp text-2xl font-extrabold text-df-primary group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors leading-none">
                    {k.char}
                  </span>
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline gap-2 mb-1">
                    <span className="text-indigo-500 dark:text-indigo-400 font-bold text-[15px]">
                      {k.sino_vi}
                    </span>
                    <span className="text-df-tertiary text-xs">·</span>
                    <span className="text-df-secondary text-sm">{k.meaning_vi}</span>
                  </div>
                  {k.formation && (
                    <p className="text-df-tertiary text-xs leading-relaxed line-clamp-2 m-0">
                      {k.formation}
                    </p>
                  )}
                </div>

                {/* Arrow */}
                <svg className="w-4 h-4 text-df-tertiary opacity-0 group-hover:opacity-100 group-hover:text-indigo-500 transition-all mt-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* ── Related Vocab ── */}
      {data.related_vocab.length > 0 && (
        <section className="mb-6">
          <h2 className="text-[11px] font-bold text-df-tertiary uppercase tracking-widest mb-3 ml-1">
            Từ vựng cùng Kanji
          </h2>
          <div className="bg-df-surface border border-df-border rounded-2xl overflow-hidden divide-y divide-df-border-subtle">
            {data.related_vocab.map((rv) => (
              <Link
                key={rv.id}
                href={`/vocab/${encodeURIComponent(rv.word)}`}
                className="group flex items-center gap-3 px-4 py-3 hover:bg-indigo-50/40 dark:hover:bg-indigo-950/20 transition-colors no-underline"
              >
                <span className="font-jp text-base font-semibold text-df-primary group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors shrink-0">
                  {rv.word}
                </span>
                <span className="font-jp text-sm text-df-tertiary shrink-0">
                  {rv.reading}
                </span>
                <span className="text-sm text-df-secondary ml-auto text-right truncate">
                  {rv.meaning}
                </span>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
