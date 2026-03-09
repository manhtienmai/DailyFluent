"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSidebar } from "@/hooks/useSidebar";
import { useLanguageMode, type StudyLanguage } from "@/hooks/useLanguageMode";
import { useRef, useCallback } from "react";

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
  iconClass: string;
  matchPaths: string[];
  lang: StudyLanguage | "both";
}

const navItems: NavItem[] = [
  {
    href: "/",
    label: "Trang chủ",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
        <polyline points="9 22 9 12 15 12 15 22" />
      </svg>
    ),
    iconClass: "df-icon-home",
    matchPaths: ["/"],
    lang: "both",
  },
  {
    href: "/vocab/courses",
    label: "Bộ từ vựng",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 14l9-5-9-5-9 5 9 5z" />
        <path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
      </svg>
    ),
    iconClass: "df-icon-exam",
    matchPaths: ["/vocab/courses", "/toeic"],
    lang: "both",
  },

  {
    href: "/vocab/flashcards",
    label: "Flashcard",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="2" y="6" width="20" height="12" rx="2" />
        <path d="M12 6v12M2 12h20" />
      </svg>
    ),
    iconClass: "df-icon-flashcard",
    matchPaths: ["/vocab/flashcards"],
    lang: "both",
  },
  {
    href: "/vocab/my-words",
    label: "Từ vựng của tôi",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
      </svg>
    ),
    iconClass: "df-icon-book",
    matchPaths: ["/vocab/my-words", "/vocab/games"],
    lang: "both",
  },
  {
    href: "/exam",
    label: "Đề thi",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M9 11l3 3L22 4" />
        <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
      </svg>
    ),
    iconClass: "df-icon-exam",
    matchPaths: ["/exam"],
    lang: "both",
  },
  {
    href: "/exam/english",
    label: "Tiếng Anh 10",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z" />
      </svg>
    ),
    iconClass: "df-icon-english",
    matchPaths: ["/exam/english"],
    lang: "en",
  },
  {
    href: "/exam/study",
    label: "Kho Học Tập",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z" />
        <path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z" />
      </svg>
    ),
    iconClass: "df-icon-study",
    matchPaths: ["/exam/study"],
    lang: "jp",
  },
  {
    href: "/kanji",
    label: "Kanji",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <path d="M8 8h8M8 12h8M8 16h5" />
        <path d="M15 12v4" />
      </svg>
    ),
    iconClass: "df-icon-kanji",
    matchPaths: ["/kanji"],
    lang: "jp",
  },
  {
    href: "/jlpt/n1/vocabulary",
    label: "JLPT N1",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M4 6h16M4 10h16M4 14h10M4 18h12" />
      </svg>
    ),
    iconClass: "df-icon-jlpt",
    matchPaths: ["/jlpt"],
    lang: "jp",
  },
  {
    href: "/grammar",
    label: "Ngữ pháp",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 20h9" />
        <path d="M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z" />
      </svg>
    ),
    iconClass: "df-icon-grammar",
    matchPaths: ["/grammar"],
    lang: "jp",
  },
  {
    href: "/exam/choukai",
    label: "Luyện nghe",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M3 18v-6a9 9 0 0118 0v6" />
        <path d="M21 19a2 2 0 01-2 2h-1a2 2 0 01-2-2v-3a2 2 0 012-2h3zM3 19a2 2 0 002 2h1a2 2 0 002-2v-3a2 2 0 00-2-2H3z" />
      </svg>
    ),
    iconClass: "df-icon-choukai",
    matchPaths: ["/exam/choukai"],
    lang: "jp",
  },
  {
    href: "/dictation",
    label: "Nghe chép chính tả",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z" />
        <path d="M19 10v2a7 7 0 01-14 0v-2" />
        <line x1="12" y1="19" x2="12" y2="23" />
        <line x1="8" y1="23" x2="16" y2="23" />
      </svg>
    ),
    iconClass: "df-icon-dictation",
    matchPaths: ["/dictation"],
    lang: "jp",
  },
  {
    href: "/streak",
    label: "Xếp hạng",
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 23a7.5 7.5 0 0 1-5.138-12.963C8.204 8.774 11.5 6.5 11 1.5c6 4 9 8 3 14 1 0 2.5 0 5-2.47.27.773.5 1.604.5 2.47A7.5 7.5 0 0 1 12 23z" />
      </svg>
    ),
    iconClass: "df-icon-streak",
    matchPaths: ["/streak"],
    lang: "both",
  },
  {
    href: "/feedback",
    label: "Góc Cải Tiến",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
    iconClass: "df-sidebar-icon-feedback",
    matchPaths: ["/feedback"],
    lang: "both",
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { collapsed, toggleCollapse, mobileOpen } = useSidebar();
  const { mode } = useLanguageMode();
  const tooltipRef = useRef<HTMLDivElement | null>(null);

  // Filter nav items based on language mode
  const filteredItems = navItems.filter(
    (item) => item.lang === "both" || item.lang === mode
  );

  const isActive = useCallback(
    (item: NavItem) => {
      if (item.href === "/") return pathname === "/";
      return item.matchPaths.some(
        (p) => pathname === p || pathname.startsWith(p + "/")
      );
    },
    [pathname]
  );

  const showTooltip = useCallback(
    (e: React.MouseEvent<HTMLAnchorElement>, label: string) => {
      if (!collapsed) return;
      const tip = tooltipRef.current;
      if (!tip) return;
      tip.textContent = label;
      tip.classList.add("active");
      const rect = e.currentTarget.getBoundingClientRect();
      tip.style.top = `${rect.top + (rect.height - tip.offsetHeight) / 2}px`;
      tip.style.left = `${rect.right + 10}px`;
    },
    [collapsed]
  );

  const hideTooltip = useCallback(() => {
    tooltipRef.current?.classList.remove("active");
  }, []);

  return (
    <>
      <aside className={`df-sidebar ${mobileOpen ? "mobile-open" : ""}`} id="df-sidebar">
        <nav className="df-sidebar-nav">
          {filteredItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              data-title={item.label}
              className={`df-sidebar-item ${isActive(item) ? "active" : ""}`}
              onMouseEnter={(e) => showTooltip(e, item.label)}
              onMouseLeave={hideTooltip}
            >
              <span className={`df-sidebar-icon ${item.iconClass}`}>
                {item.icon}
              </span>
              <span className="df-sidebar-label">{item.label}</span>
            </Link>
          ))}
        </nav>

        <button
          className="df-sidebar-collapse-btn"
          onClick={toggleCollapse}
          title="Thu gọn"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="11 17 6 12 11 7" />
            <polyline points="18 17 13 12 18 7" />
          </svg>
        </button>
      </aside>

      {/* Tooltip */}
      <div ref={tooltipRef} className="df-sidebar-tooltip" />
    </>
  );
}
