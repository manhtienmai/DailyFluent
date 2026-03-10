"use client";

import { useMemo } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { Layout, Menu } from "antd";
import type { MenuProps } from "antd";
import {
  DashboardOutlined,
  BookOutlined,
  FormOutlined,
  QuestionCircleOutlined,
  FileTextOutlined,
  VideoCameraOutlined,
  ReadOutlined,
  ThunderboltOutlined,
  ImportOutlined,
  BuildOutlined,
  AudioOutlined,
  EditOutlined,
  UploadOutlined,
  PictureOutlined,
  UserOutlined,
  CreditCardOutlined,
  WalletOutlined,
  CommentOutlined,
  ShopOutlined,
  AppstoreOutlined,
  AimOutlined,
  GlobalOutlined,
  SettingOutlined,
  RobotOutlined,
  SwapOutlined,
  BlockOutlined,
  CrownFilled,
  SoundOutlined,
  LockOutlined,
  BarChartOutlined,
  ScheduleOutlined,
  FilePdfOutlined,
} from "@ant-design/icons";

const { Sider } = Layout;

type MenuItem = Required<MenuProps>["items"][number];

function item(
  label: React.ReactNode,
  key: string,
  icon?: React.ReactNode,
  children?: MenuItem[],
): MenuItem {
  return { key, icon, children, label } as MenuItem;
}

/* Helper to create a colored icon */
const ci = (Icon: React.ComponentType<any>, color: string) => <Icon style={{ color, fontSize: 16 }} />;

const MENU_ITEMS: MenuItem[] = [
  item(<Link href="/admin/dashboard">Dashboard</Link>, "/admin/dashboard", ci(DashboardOutlined, "#6366f1")),

  {
    type: "group",
    label: "Nội dung",
    children: [
      item(<Link href="/admin/vocab">Từ vựng</Link>, "/admin/vocab", ci(BookOutlined, "#10b981")),
      item(<Link href="/admin/vocab/sets">Bộ từ vựng</Link>, "/admin/vocab/sets", ci(AppstoreOutlined, "#06b6d4")),
      item(<Link href="/admin/exam/templates">Bài thi</Link>, "/admin/exam/templates", ci(FormOutlined, "#8b5cf6")),
      item(<Link href="/admin/exam/books">Sách thi</Link>, "/admin/exam/books", ci(ReadOutlined, "#f59e0b")),
      item(<Link href="/admin/exam/questions">Câu hỏi</Link>, "/admin/exam/questions", ci(QuestionCircleOutlined, "#3b82f6")),
      item(<Link href="/admin/kanji">Kanji</Link>, "/admin/kanji", ci(FileTextOutlined, "#ef4444")),
      item(<Link href="/admin/grammar">Ngữ pháp</Link>, "/admin/grammar", ci(BlockOutlined, "#ec4899")),
      item(<Link href="/admin/videos">Video</Link>, "/admin/videos", ci(VideoCameraOutlined, "#f97316")),
      item(<Link href="/admin/books">Thư viện Ebook</Link>, "/admin/books", ci(ReadOutlined, "#14b8a6")),
    ],
  },

  {
    type: "group",
    label: "Công cụ",
    children: [
      item(<Link href="/admin/vocab/bulk-add">Thêm từ hàng loạt</Link>, "/admin/vocab/bulk-add", ci(ThunderboltOutlined, "#f59e0b")),
      item(<Link href="/admin/vocab/import-jp">Import JP</Link>, "/admin/vocab/import-jp", ci(ImportOutlined, "#ef4444")),
      item(<Link href="/admin/vocab/quiz-generate">Quiz Generator</Link>, "/admin/vocab/quiz-generate", ci(BuildOutlined, "#8b5cf6")),
      item(<Link href="/admin/vocab/example-generate">Sinh ví dụ JP</Link>, "/admin/vocab/example-generate", ci(RobotOutlined, "#10b981")),
      item(<Link href="/admin/kanji/quiz-generate">Kanji Quiz</Link>, "/admin/kanji/quiz-generate", ci(BuildOutlined, "#ec4899")),
      item(<Link href="/admin/kanji/pdf-import">Kanji PDF Import</Link>, "/admin/kanji/pdf-import", ci(FilePdfOutlined, "#ef4444")),
      item(<Link href="/admin/vocab/choukai-tool">Choukai Tool</Link>, "/admin/vocab/choukai-tool", ci(AudioOutlined, "#06b6d4")),
      item(<Link href="/admin/vocab/tts">TTS Generator</Link>, "/admin/vocab/tts", ci(SoundOutlined, "#10b981")),
      item(<Link href="/admin/exam/dokkai-editor">Dokkai Tool</Link>, "/admin/exam/dokkai-editor", ci(EditOutlined, "#10b981")),
      item(<Link href="/admin/exam/import-toeic">Import TOEIC</Link>, "/admin/exam/import-toeic", ci(UploadOutlined, "#3b82f6")),
      item(<Link href="/admin/exam/import-usage">AI Import 用法</Link>, "/admin/exam/import-usage", ci(RobotOutlined, "#8b5cf6")),
      item(<Link href="/admin/exam/import-grammar">AI Import 文法</Link>, "/admin/exam/import-grammar", ci(RobotOutlined, "#6366f1")),
      item(<Link href="/admin/exam/import-sentence-order">AI Import 並べ替え</Link>, "/admin/exam/import-sentence-order", ci(SwapOutlined, "#14b8a6")),
      item(<Link href="/admin/exam/import-english">Import English</Link>, "/admin/exam/import-english", ci(GlobalOutlined, "#3b82f6")),
      item(<Link href="/admin/exam/upload-images">Upload ảnh</Link>, "/admin/exam/upload-images", ci(PictureOutlined, "#f97316")),
    ],
  },

  {
    type: "group",
    label: "Giáo viên",
    children: [
      item(<Link href="/admin/teacher-dashboard">Dashboard GV</Link>, "/admin/teacher-dashboard", ci(BarChartOutlined, "#10b981")),
      item(<Link href="/admin/assignments">Giao bài tập</Link>, "/admin/assignments", ci(ScheduleOutlined, "#f59e0b")),
    ],
  },

  {
    type: "group",
    label: "Quản lý",
    children: [
      item(<Link href="/admin/courses">Khoá học</Link>, "/admin/courses", ci(ReadOutlined, "#6366f1")),
      item(<Link href="/admin/placement">Placement</Link>, "/admin/placement", ci(AimOutlined, "#ef4444")),
      item(<Link href="/admin/users">Người dùng</Link>, "/admin/users", ci(UserOutlined, "#3b82f6")),
      item(<Link href="/admin/vip">VIP</Link>, "/admin/vip", ci(CrownFilled, "#faad14")),
      item(<Link href="/admin/exams">Đề thi</Link>, "/admin/exams", ci(LockOutlined, "#8b5cf6")),
      item(<Link href="/admin/payment">Thanh toán</Link>, "/admin/payment", ci(CreditCardOutlined, "#10b981")),
      item(<Link href="/admin/wallet">Ví & Coin</Link>, "/admin/wallet", ci(WalletOutlined, "#f59e0b")),
      item(<Link href="/admin/feedback">Feedback</Link>, "/admin/feedback", ci(CommentOutlined, "#06b6d4")),
      item(<Link href="/admin/shop">Shop</Link>, "/admin/shop", ci(ShopOutlined, "#ec4899")),
    ],
  },
];

/* ── Resolve active key ──────────────────────────────────── */

const ALL_KEYS = [
  "/admin/dashboard",
  "/admin/vocab", "/admin/vocab/sets", "/admin/vocab/bulk-add",
  "/admin/vocab/import-jp", "/admin/vocab/quiz-generate", "/admin/vocab/example-generate", "/admin/vocab/choukai-tool",
  "/admin/exam/templates", "/admin/exam/books", "/admin/exam/questions",
  "/admin/exam/dokkai-editor", "/admin/exam/import-toeic",
  "/admin/exam/import-usage", "/admin/exam/import-grammar",
  "/admin/exam/import-sentence-order", "/admin/exam/import-english", "/admin/exam/upload-images",
  "/admin/vocab/tts",
  "/admin/kanji", "/admin/kanji/quiz-generate", "/admin/kanji/pdf-import",
  "/admin/grammar", "/admin/videos", "/admin/books", "/admin/courses",
  "/admin/teacher-dashboard", "/admin/assignments",
  "/admin/placement", "/admin/users", "/admin/vip", "/admin/exams", "/admin/payment", "/admin/wallet",
  "/admin/feedback", "/admin/shop",
];

function resolveActiveKey(pathname: string): string[] {
  // Exact match first
  if (ALL_KEYS.includes(pathname)) return [pathname];
  // Check for parent match with children in nav
  const sorted = [...ALL_KEYS].sort((a, b) => b.length - a.length);
  for (const key of sorted) {
    if (pathname.startsWith(key + "/") || pathname === key) return [key];
  }
  // Default
  if (pathname === "/admin" || pathname === "/admin/") return ["/admin/dashboard"];
  return [];
}

/* ── Component ───────────────────────────────────────────── */

interface SidebarProps {
  collapsed: boolean;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

export default function AdminSidebar({ collapsed, mobileOpen, onCloseMobile }: SidebarProps) {
  const pathname = usePathname();
  const selectedKeys = useMemo(() => resolveActiveKey(pathname), [pathname]);

  return (
    <Sider
      width={240}
      collapsedWidth={80}
      collapsed={collapsed}
      breakpoint="lg"
      style={{
        overflow: "auto",
        height: "100vh",
        position: "fixed",
        left: 0,
        top: 0,
        bottom: 0,
        zIndex: 200,
      }}
    >
      {/* Brand header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          padding: collapsed ? "16px 20px" : "16px 20px",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
        }}
      >
        <img
          src="/logo_official.png"
          alt="DailyFluent"
          style={{ width: 36, height: 36, borderRadius: 10, flexShrink: 0 }}
        />
        {!collapsed && (
          <div style={{ overflow: "hidden" }}>
            <div style={{ fontWeight: 700, fontSize: 16, lineHeight: 1.2, color: "inherit" }}>
              DailyFluent
            </div>
            <div style={{ fontSize: 11, fontWeight: 600, color: "#6366f1", textTransform: "uppercase", letterSpacing: 0.5 }}>
              Admin Panel
            </div>
          </div>
        )}
      </div>

      {/* Menu */}
      <Menu
        mode="inline"
        selectedKeys={selectedKeys}
        items={MENU_ITEMS}
        onClick={onCloseMobile}
        style={{ borderRight: 0, paddingTop: 8 }}
      />

      {/* Footer links */}
      <div style={{ padding: "12px 8px", borderTop: "1px solid rgba(255,255,255,0.06)", marginTop: "auto" }}>
        <Menu
          mode="inline"
          selectable={false}
          items={[
            item(<Link href="/">Về trang chính</Link>, "home", ci(GlobalOutlined, "#14b8a6")),
            item(<a href="/django-admin/">Django Admin</a>, "django", ci(SettingOutlined, "#64748b")),
          ]}
          style={{ borderRight: 0 }}
        />
      </div>
    </Sider>
  );
}
