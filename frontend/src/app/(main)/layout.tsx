"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/sidebar/Sidebar";
import Topbar from "@/components/sidebar/Topbar";
import UserModal from "@/components/sidebar/UserModal";
import NotificationToast from "@/components/notifications/NotificationToast";
import { SidebarProvider, useSidebar } from "@/hooks/useSidebar";
import { AuthProvider, useAuth } from "@/lib/auth";
import { LanguageModeProvider } from "@/hooks/useLanguageMode";
import { NotificationProvider } from "@/hooks/useNotifications";

function AuthGate({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh", color: "var(--text-tertiary)" }}>
        Đang tải...
      </div>
    );
  }

  if (!user) return null;
  return <>{children}</>;
}

function MainLayoutInner({ children }: { children: React.ReactNode }) {
  const { mobileOpen, closeMobile } = useSidebar();

  return (
    <AuthGate>
      <NotificationProvider>
        <div className="df-sidebar-body">
          {/* Sidebar */}
          <Sidebar />

          {/* Mobile Overlay */}
          <div
            className={`df-sidebar-overlay ${mobileOpen ? "active" : ""}`}
            onClick={closeMobile}
          />

          {/* Main Wrapper */}
          <div className="df-main-wrapper">
            {/* Top Header */}
            <Topbar />

            {/* Main Content */}
            <main className="df-content-area">{children}</main>
          </div>

          {/* User Profile Modal */}
          <UserModal />

          {/* Toast Notifications */}
          <NotificationToast />
        </div>
      </NotificationProvider>
    </AuthGate>
  );
}

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthProvider>
      <LanguageModeProvider>
        <SidebarProvider>
          <MainLayoutInner>{children}</MainLayoutInner>
        </SidebarProvider>
      </LanguageModeProvider>
    </AuthProvider>
  );
}

