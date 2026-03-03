"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/sidebar/Sidebar";
import Topbar from "@/components/sidebar/Topbar";
import UserModal from "@/components/sidebar/UserModal";
import { SidebarProvider, useSidebar } from "@/hooks/useSidebar";
import { AuthProvider, useAuth } from "@/lib/auth";

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
      </div>
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
      <SidebarProvider>
        <MainLayoutInner>{children}</MainLayoutInner>
      </SidebarProvider>
    </AuthProvider>
  );
}
