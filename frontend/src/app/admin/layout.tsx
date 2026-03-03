"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter, usePathname } from "next/navigation";
import { AntdRegistry } from "@ant-design/nextjs-registry";
import { ConfigProvider, theme as antTheme, Layout, Spin } from "antd";
import { AuthProvider, useAuth } from "@/lib/auth";
import AdminSidebar from "@/components/admin/Sidebar";
import AdminTopbar from "@/components/admin/Topbar";
import "./admin.css"; // kept for backward compat during migration

const { Content } = Layout;

/* ── Brand colour tokens ─────────────────────────────────── */
const BRAND = {
  primary: "#6366f1",       // indigo-500
  primaryHover: "#4f46e5",  // indigo-600
  info: "#3b82f6",
  success: "#10b981",
  warning: "#f59e0b",
  error: "#ef4444",
  borderRadius: 10,
  fontFamily:
    '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
};

/* ── Admin Auth Gate ─────────────────────────────────────── */

function AdminGuard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>
        <Spin size="large" tip="Đang tải…" />
      </div>
    );
  }

  if (!user) return null;
  return <>{children}</>;
}

/* ── Admin Layout Inner ──────────────────────────────────── */

function AdminLayoutInner({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isDark, setIsDark] = useState(false);

  // Persist sidebar state
  useEffect(() => {
    const saved = localStorage.getItem("admin-sidebar");
    if (saved === "closed") setCollapsed(true);
  }, []);

  // Sync dark mode from document
  useEffect(() => {
    const check = () =>
      setIsDark(document.documentElement.getAttribute("data-theme") === "dark");
    check();
    const observer = new MutationObserver(check);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });
    return () => observer.disconnect();
  }, []);

  const toggleCollapsed = () => {
    setCollapsed((prev) => {
      localStorage.setItem("admin-sidebar", !prev ? "closed" : "open");
      return !prev;
    });
  };

  const toggleDark = () => {
    const next = isDark ? "light" : "dark";
    if (next === "dark") {
      document.documentElement.setAttribute("data-theme", "dark");
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
    localStorage.setItem("theme", next);
    setIsDark(next === "dark");
  };

  const themeConfig = useMemo(
    () => ({
      algorithm: isDark ? antTheme.darkAlgorithm : antTheme.defaultAlgorithm,
      token: {
        colorPrimary: BRAND.primary,
        colorInfo: BRAND.info,
        colorSuccess: BRAND.success,
        colorWarning: BRAND.warning,
        colorError: BRAND.error,
        borderRadius: BRAND.borderRadius,
        fontFamily: BRAND.fontFamily,
      },
      components: {
        Layout: {
          headerBg: isDark ? "#141414" : "#ffffff",
          siderBg: isDark ? "#141414" : "#001529",
        },
      },
    }),
    [isDark],
  );

  return (
    <ConfigProvider theme={themeConfig}>
      <Layout style={{ minHeight: "100vh" }}>
        <AdminSidebar
          collapsed={collapsed}
          mobileOpen={mobileOpen}
          onCloseMobile={() => setMobileOpen(false)}
        />

        <Layout
          style={{
            marginLeft: collapsed ? 80 : 240,
            transition: "margin-left 0.2s",
          }}
        >
          <AdminTopbar
            collapsed={collapsed}
            isDark={isDark}
            onToggleCollapsed={toggleCollapsed}
            onToggleMobile={() => setMobileOpen((p) => !p)}
            onToggleDark={toggleDark}
          />

          <Content
            style={{
              padding: "88px 24px 24px",
              maxWidth: 1440,
            }}
          >
            {children}
          </Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  );
}

/* ── Export ───────────────────────────────────────────────── */

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AntdRegistry>
      <AuthProvider>
        <AdminLayoutInner>{children}</AdminLayoutInner>
      </AuthProvider>
    </AntdRegistry>
  );
}
