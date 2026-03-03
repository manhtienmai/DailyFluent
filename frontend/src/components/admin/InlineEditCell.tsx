"use client";

import { useState, useRef, useEffect } from "react";

interface InlineEditCellProps {
  value: string;
  onSave: (newValue: string) => Promise<void> | void;
  style?: React.CSSProperties;
  inputStyle?: React.CSSProperties;
  placeholder?: string;
}

/**
 * Double-click-to-edit table cell.
 * - Double-click → input field (auto-focused)
 * - Enter or blur → save
 * - Escape → cancel
 */
export default function InlineEditCell({ value, onSave, style, inputStyle, placeholder }: InlineEditCellProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editing]);

  const handleSave = async () => {
    const trimmed = draft.trim();
    if (trimmed && trimmed !== value) {
      await onSave(trimmed);
    }
    setEditing(false);
  };

  return (
    <td
      onDoubleClick={() => { setDraft(value); setEditing(true); }}
      style={{ cursor: "text", ...style }}
      title="Double-click để sửa"
    >
      {editing ? (
        <input
          ref={inputRef}
          value={draft}
          onChange={e => setDraft(e.target.value)}
          onBlur={handleSave}
          onKeyDown={e => {
            if (e.key === "Enter") handleSave();
            if (e.key === "Escape") setEditing(false);
          }}
          placeholder={placeholder}
          style={{
            width: "100%",
            padding: "4px 8px",
            fontSize: 13,
            borderRadius: 6,
            border: "1.5px solid var(--action-primary)",
            background: "var(--bg-app-subtle)",
            color: "var(--text-primary)",
            outline: "none",
            ...inputStyle,
          }}
        />
      ) : (
        value || <span style={{ color: "var(--text-quaternary)" }}>—</span>
      )}
    </td>
  );
}
