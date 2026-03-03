"use client";

import { useState, useEffect } from "react";

interface Todo { id: number; title: string; is_completed: boolean; created_at: string; }

export default function TodosPage() {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [loading, setLoading] = useState(true);
  const [newTodo, setNewTodo] = useState("");

  useEffect(() => {
    fetch("/todos/api/", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: Todo[]) => { setTodos(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const add = async () => {
    if (!newTodo.trim()) return;
    try {
      const r = await fetch("/todos/create/", {
        method: "POST", credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: newTodo }),
      });
      const d = await r.json();
      if (d.id) { setTodos((p) => [d, ...p]); setNewTodo(""); }
    } catch { /* ignore */ }
  };

  const toggle = async (id: number) => {
    try {
      await fetch(`/todos/${id}/toggle/`, { method: "POST", credentials: "include" });
      setTodos((p) => p.map((t) => t.id === id ? { ...t, is_completed: !t.is_completed } : t));
    } catch { /* ignore */ }
  };

  const remove = async (id: number) => {
    try {
      await fetch(`/todos/${id}/delete/`, { method: "POST", credentials: "include" });
      setTodos((p) => p.filter((t) => t.id !== id));
    } catch { /* ignore */ }
  };

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;

  const done = todos.filter((t) => t.is_completed).length;

  return (
    <div style={{ maxWidth: 600, margin: "0 auto", padding: "2rem 1rem" }}>
      <h1 className="text-2xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>📝 Công việc</h1>
      <p className="text-sm mb-6" style={{ color: "var(--text-tertiary)" }}>{done}/{todos.length} hoàn thành</p>

      {/* Add */}
      <div className="flex gap-3 mb-6">
        <input value={newTodo} onChange={(e) => setNewTodo(e.target.value)} onKeyDown={(e) => e.key === "Enter" && add()} placeholder="Thêm công việc mới..." className="flex-1 p-3 rounded-xl text-sm border" style={{ background: "var(--bg-interactive)", borderColor: "var(--border-default)", color: "var(--text-primary)" }} />
        <button onClick={add} disabled={!newTodo.trim()} className="px-5 py-3 rounded-xl text-sm font-semibold text-white" style={{ background: "#6366f1", opacity: newTodo.trim() ? 1 : 0.5, border: "none", cursor: "pointer" }}>Thêm</button>
      </div>

      <div className="space-y-2">
        {todos.map((t) => (
          <div key={t.id} className="flex items-center gap-3 p-3 rounded-xl transition-all" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)", opacity: t.is_completed ? 0.6 : 1 }}>
            <button onClick={() => toggle(t.id)} className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-xs" style={{
              background: t.is_completed ? "#10b981" : "transparent",
              border: t.is_completed ? "none" : "2px solid var(--border-default)",
              color: "white", cursor: "pointer",
            }}>{t.is_completed ? "✓" : ""}</button>
            <span className="flex-1 text-sm" style={{ color: "var(--text-primary)", textDecoration: t.is_completed ? "line-through" : "none" }}>{t.title}</span>
            <button onClick={() => remove(t.id)} className="text-xs px-2 py-1 rounded-lg transition-all" style={{ background: "transparent", border: "none", color: "var(--text-tertiary)", cursor: "pointer" }}>✕</button>
          </div>
        ))}
        {!todos.length && <p className="text-center py-8" style={{ color: "var(--text-tertiary)" }}>Chưa có công việc nào.</p>}
      </div>
    </div>
  );
}
