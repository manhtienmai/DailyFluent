"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { setUserPref } from "@/lib/user-prefs";

interface SidebarContextType {
  collapsed: boolean;
  mobileOpen: boolean;
  userModalOpen: boolean;
  theme: "light" | "dark";
  toggleCollapse: () => void;
  toggleMobile: () => void;
  closeMobile: () => void;
  openUserModal: () => void;
  closeUserModal: () => void;
  toggleTheme: () => void;
}

const SidebarContext = createContext<SidebarContextType | null>(null);

export function useSidebar() {
  const ctx = useContext(SidebarContext);
  if (!ctx) throw new Error("useSidebar must be used within SidebarProvider");
  return ctx;
}

export function SidebarProvider({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [userModalOpen, setUserModalOpen] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");

  // Restore persisted state
  useEffect(() => {
    if (localStorage.getItem("sidebar-collapsed") === "true") {
      setCollapsed(true);
    }
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
      setTheme("dark");
    } else if (
      !savedTheme &&
      window.matchMedia?.("(prefers-color-scheme: dark)").matches
    ) {
      setTheme("dark");
    }
  }, []);

  // Sync theme to DOM
  useEffect(() => {
    if (theme === "dark") {
      document.documentElement.setAttribute("data-theme", "dark");
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
  }, [theme]);

  // Sync collapsed class to body
  useEffect(() => {
    document.body.classList.toggle("sidebar-collapsed", collapsed);
  }, [collapsed]);

  const toggleCollapse = useCallback(() => {
    setCollapsed((prev) => {
      localStorage.setItem("sidebar-collapsed", String(!prev));
      return !prev;
    });
  }, []);

  const toggleMobile = useCallback(() => setMobileOpen((p) => !p), []);
  const closeMobile = useCallback(() => setMobileOpen(false), []);
  const openUserModal = useCallback(() => setUserModalOpen(true), []);
  const closeUserModal = useCallback(() => setUserModalOpen(false), []);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => {
      const next = prev === "dark" ? "light" : "dark";
      localStorage.setItem("theme", next);
      setUserPref("theme", next).catch(() => {});
      return next;
    });
  }, []);

  // Close modal on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeUserModal();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [closeUserModal]);

  return (
    <SidebarContext.Provider
      value={{
        collapsed,
        mobileOpen,
        userModalOpen,
        theme,
        toggleCollapse,
        toggleMobile,
        closeMobile,
        openUserModal,
        closeUserModal,
        toggleTheme,
      }}
    >
      {children}
    </SidebarContext.Provider>
  );
}
