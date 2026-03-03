/**
 * Auth utilities for DailyFluent.
 *
 * Uses JWT tokens in httpOnly cookies.
 * Provides AuthProvider context and useAuth() hook.
 */

"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { apiFetch, apiUrl } from "./api";

// ── Types ──────────────────────────────────────────────────

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  avatar_url?: string;
}

interface AuthResult {
  success: boolean;
  message: string;
  user?: User;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<AuthResult>;
  signup: (email: string, password1: string, password2: string) => Promise<AuthResult>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

// ── API Functions ──────────────────────────────────────────

export async function getCurrentUser(): Promise<User | null> {
  try {
    return await apiFetch<User>(apiUrl("/auth/me"));
  } catch {
    return null;
  }
}

export async function loginAPI(email: string, password: string): Promise<AuthResult> {
  try {
    return await apiFetch<AuthResult>(apiUrl("/auth/login"), {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  } catch (e: unknown) {
    return { success: false, message: (e as Error).message || "Đăng nhập thất bại." };
  }
}

export async function signupAPI(
  email: string,
  password1: string,
  password2: string
): Promise<AuthResult> {
  try {
    return await apiFetch<AuthResult>(apiUrl("/auth/signup"), {
      method: "POST",
      body: JSON.stringify({ email, password1, password2 }),
    });
  } catch (e: unknown) {
    return { success: false, message: (e as Error).message || "Đăng ký thất bại." };
  }
}

export async function logoutAPI(): Promise<void> {
  try {
    await apiFetch(apiUrl("/auth/logout"), { method: "POST" });
  } catch {
    // Best effort
  }
}

// ── Context ────────────────────────────────────────────────

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  login: async () => ({ success: false, message: "" }),
  signup: async () => ({ success: false, message: "" }),
  logout: async () => {},
  refreshUser: async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const u = await getCurrentUser();
    setUser(u);
    setLoading(false);
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = useCallback(
    async (email: string, password: string): Promise<AuthResult> => {
      const result = await loginAPI(email, password);
      if (result.success && result.user) {
        setUser(result.user);
      }
      return result;
    },
    []
  );

  const signup = useCallback(
    async (email: string, password1: string, password2: string): Promise<AuthResult> => {
      const result = await signupAPI(email, password1, password2);
      if (result.success && result.user) {
        setUser(result.user);
      }
      return result;
    },
    []
  );

  const logout = useCallback(async () => {
    await logoutAPI();
    setUser(null);
    window.location.href = "/login";
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  return useContext(AuthContext);
}
