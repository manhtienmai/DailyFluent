"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";

export type StudyLanguage = "en" | "jp";

interface LanguageModeContextType {
  mode: StudyLanguage;
  setMode: (m: StudyLanguage) => void;
  toggleMode: () => void;
}

const LanguageModeContext = createContext<LanguageModeContextType | null>(null);

const STORAGE_KEY = "study-language";

export function useLanguageMode() {
  const ctx = useContext(LanguageModeContext);
  if (!ctx)
    throw new Error("useLanguageMode must be used within LanguageModeProvider");
  return ctx;
}

export function LanguageModeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<StudyLanguage>("en");

  // Restore from localStorage
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "jp" || saved === "en") {
      setModeState(saved);
    }
  }, []);

  const setMode = useCallback((m: StudyLanguage) => {
    setModeState(m);
    localStorage.setItem(STORAGE_KEY, m);
  }, []);

  const toggleMode = useCallback(() => {
    setModeState((prev) => {
      const next = prev === "en" ? "jp" : "en";
      localStorage.setItem(STORAGE_KEY, next);
      return next;
    });
  }, []);

  return (
    <LanguageModeContext.Provider value={{ mode, setMode, toggleMode }}>
      {children}
    </LanguageModeContext.Provider>
  );
}
