"use client";

import { useState, type FormEvent } from "react";
import { useAuth } from "@/lib/auth";
import { apiFetch, apiUrl } from "@/lib/api";
import Link from "next/link";

export default function SettingsPage() {
  const { user, refreshUser } = useAuth();

  // Account form
  const [firstName, setFirstName] = useState(user?.first_name || "");
  const [lastName, setLastName] = useState(user?.last_name || "");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Password modal
  const [pwOpen, setPwOpen] = useState(false);
  const [oldPw, setOldPw] = useState("");
  const [newPw1, setNewPw1] = useState("");
  const [newPw2, setNewPw2] = useState("");
  const [pwError, setPwError] = useState("");
  const [pwSuccess, setPwSuccess] = useState(false);
  const [pwLoading, setPwLoading] = useState(false);

  // Notification toggles
  const [dailyReminder, setDailyReminder] = useState(true);
  const [examNotif, setExamNotif] = useState(true);
  const [marketing, setMarketing] = useState(false);

  // Font selection
  const JP_FONTS = [
    { id: "noto-sans", label: "Noto Sans JP", family: "'Noto Sans JP', sans-serif", desc: "Mặc định — rõ ràng, hiện đại" },
    { id: "noto-serif", label: "Noto Serif JP", family: "'Noto Serif JP', serif", desc: "Chân phương, cổ điển" },
    { id: "zen-maru", label: "Zen Maru Gothic", family: "'Zen Maru Gothic', sans-serif", desc: "Bo tròn, thân thiện" },
    { id: "kosugi-maru", label: "Kosugi Maru", family: "'Kosugi Maru', sans-serif", desc: "Tròn dễ thương, nhẹ nhàng" },
    { id: "sawarabi", label: "Sawarabi Mincho", family: "'Sawarabi Mincho', serif", desc: "Mincho thanh lịch" },
    { id: "mplus-rounded", label: "M PLUS Rounded 1c", family: "'M PLUS Rounded 1c', sans-serif", desc: "Tròn hiện đại, dễ đọc" },
  ];
  const [jpFont, setJpFont] = useState(() => {
    if (typeof window !== "undefined") return localStorage.getItem("df-jp-font") || "noto-sans";
    return "noto-sans";
  });

  const handleFontChange = (fontId: string) => {
    setJpFont(fontId);
    localStorage.setItem("df-jp-font", fontId);
    const font = JP_FONTS.find(f => f.id === fontId);
    if (font) document.documentElement.style.setProperty("--font-jp-user", font.family);
  };

  const handleSaveAccount = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await apiFetch(apiUrl("/profile/update/"), {
        method: "POST",
        body: JSON.stringify({ first_name: firstName, last_name: lastName }),
      });
      await refreshUser();
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch { /* ignore */ }
    setSaving(false);
  };

  const handleChangePassword = async (e: FormEvent) => {
    e.preventDefault();
    setPwError("");
    if (newPw1 !== newPw2) { setPwError("Mật khẩu xác nhận không khớp."); return; }
    if (newPw1.length < 8) { setPwError("Mật khẩu mới phải có ít nhất 8 ký tự."); return; }
    setPwLoading(true);
    try {
      await apiFetch(apiUrl("/auth/change-password/"), {
        method: "POST",
        body: JSON.stringify({ old_password: oldPw, new_password1: newPw1, new_password2: newPw2 }),
      });
      setPwSuccess(true);
      setOldPw(""); setNewPw1(""); setNewPw2("");
      setTimeout(() => { setPwOpen(false); setPwSuccess(false); }, 2000);
    } catch {
      setPwError("Mật khẩu hiện tại không đúng hoặc có lỗi xảy ra.");
    }
    setPwLoading(false);
  };

  const inputStyle = { background: "var(--bg-interactive)", borderColor: "var(--border-default)", color: "var(--text-primary)" };

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "2rem 1rem" }}>
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-1" style={{ color: "var(--text-primary)" }}>Cài đặt tài khoản</h1>
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Quản lý thông tin và tùy chọn cá nhân của bạn</p>
      </div>

      {/* Account Section */}
      <div className="rounded-2xl overflow-hidden mb-5" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
        <div className="px-5 py-3" style={{ background: "var(--bg-interactive)", borderBottom: "1px solid var(--border-default)" }}>
          <h2 className="text-sm font-semibold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>👤 Thông tin tài khoản</h2>
        </div>
        <div className="p-5">
          {/* User info */}
          <div className="flex items-center gap-4 mb-5 pb-5" style={{ borderBottom: "1px solid var(--border-default)" }}>
            <div className="w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold text-white" style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }}>
              {(user?.username || "U").slice(0, 1).toUpperCase()}
            </div>
            <div className="flex-1">
              <div className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>{user?.username}</div>
              <div className="text-sm" style={{ color: "var(--text-secondary)" }}>{user?.email || "Chưa có email"}</div>
            </div>
            <Link href="/profile" className="text-sm px-4 py-2 rounded-xl font-semibold no-underline" style={{ background: "var(--bg-interactive)", color: "var(--text-primary)", border: "1px solid var(--border-default)" }}>
              Xem trang cá nhân
            </Link>
          </div>

          <form onSubmit={handleSaveAccount}>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: "var(--text-primary)" }}>Họ (Last Name)</label>
                <input value={lastName} onChange={(e) => setLastName(e.target.value)} placeholder="Nhập họ" className="w-full p-2.5 rounded-xl text-sm border" style={inputStyle} />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1" style={{ color: "var(--text-primary)" }}>Tên (First Name)</label>
                <input value={firstName} onChange={(e) => setFirstName(e.target.value)} placeholder="Nhập tên" className="w-full p-2.5 rounded-xl text-sm border" style={inputStyle} />
              </div>
            </div>
            <div className="flex items-center justify-end gap-3">
              {saved && <span className="text-sm text-green-500 font-semibold">✓ Đã lưu!</span>}
              <button type="submit" disabled={saving} className="px-5 py-2 rounded-xl text-sm font-semibold text-white" style={{ background: "#3b82f6", opacity: saving ? 0.6 : 1 }}>
                {saving ? "Đang lưu..." : "Lưu thông tin"}
              </button>
            </div>
          </form>

          <div className="mt-5">
            <label className="block text-sm font-medium mb-1" style={{ color: "var(--text-primary)" }}>Tên đăng nhập</label>
            <input value={user?.username || ""} disabled className="w-full p-2.5 rounded-xl text-sm border opacity-60" style={inputStyle} />
            <p className="text-xs mt-1" style={{ color: "var(--text-tertiary)" }}>Tên đăng nhập không thể thay đổi</p>
          </div>
        </div>
      </div>

      {/* Notifications Section */}
      <div className="rounded-2xl overflow-hidden mb-5" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
        <div className="px-5 py-3" style={{ background: "var(--bg-interactive)", borderBottom: "1px solid var(--border-default)" }}>
          <h2 className="text-sm font-semibold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>🔔 Thông báo</h2>
        </div>
        <div className="p-5 space-y-0">
          {[
            { label: "Nhắc nhở học hàng ngày", desc: "Nhận thông báo nhắc bạn học mỗi ngày", value: dailyReminder, set: setDailyReminder },
            { label: "Thông báo kết quả thi", desc: "Nhận thông báo khi có kết quả thi mới", value: examNotif, set: setExamNotif },
            { label: "Email marketing", desc: "Nhận email về khóa học và ưu đãi mới", value: marketing, set: setMarketing },
          ].map((t) => (
            <div key={t.label} className="flex items-center justify-between py-3" style={{ borderBottom: "1px solid var(--border-default)" }}>
              <div className="flex-1">
                <div className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>{t.label}</div>
                <div className="text-xs" style={{ color: "var(--text-tertiary)" }}>{t.desc}</div>
              </div>
              <button onClick={() => t.set(!t.value)} className="w-11 h-6 rounded-full relative transition-all" style={{ background: t.value ? "#3b82f6" : "var(--border-default)" }}>
                <span className="absolute top-[3px] w-[18px] h-[18px] rounded-full bg-white shadow transition-all" style={{ left: t.value ? "calc(100% - 21px)" : "3px" }} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Japanese Font Section */}
      <div className="rounded-2xl overflow-hidden mb-5" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
        <div className="px-5 py-3" style={{ background: "var(--bg-interactive)", borderBottom: "1px solid var(--border-default)" }}>
          <h2 className="text-sm font-semibold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>🔤 Font chữ tiếng Nhật</h2>
        </div>
        <div className="p-5">
          <p className="text-xs mb-4" style={{ color: "var(--text-tertiary)" }}>Chọn font hiển thị cho kanji, câu hỏi quiz, flashcard và các trang học tiếng Nhật</p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "10px" }}>
            {JP_FONTS.map((f) => {
              const active = jpFont === f.id;
              return (
                <button
                  key={f.id}
                  onClick={() => handleFontChange(f.id)}
                  className="text-left"
                  style={{
                    padding: "14px 16px",
                    borderRadius: "14px",
                    border: active ? "2px solid #6366f1" : "1.5px solid var(--border-default)",
                    background: active ? "rgba(99,102,241,.06)" : "var(--bg-surface)",
                    cursor: "pointer",
                    transition: "all .15s",
                    position: "relative",
                  }}
                >
                  {active && (
                    <span style={{ position: "absolute", top: 8, right: 10, fontSize: 14, color: "#6366f1", fontWeight: 700 }}>✓</span>
                  )}
                  <div style={{ fontFamily: f.family, fontSize: 22, fontWeight: 700, color: "var(--text-primary)", lineHeight: 1.4, marginBottom: 4 }}>
                    漢字の練習
                  </div>
                  <div style={{ fontFamily: f.family, fontSize: 13, color: "var(--text-secondary)", marginBottom: 6 }}>
                    日本語を勉強する
                  </div>
                  <div className="text-xs font-semibold" style={{ color: active ? "#6366f1" : "var(--text-primary)" }}>{f.label}</div>
                  <div className="text-xs" style={{ color: "var(--text-tertiary)" }}>{f.desc}</div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Security Section */}
      <div className="rounded-2xl overflow-hidden mb-5" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
        <div className="px-5 py-3" style={{ background: "var(--bg-interactive)", borderBottom: "1px solid var(--border-default)" }}>
          <h2 className="text-sm font-semibold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>🔒 Bảo mật</h2>
        </div>
        <div className="p-5">
          <label className="block text-sm font-medium mb-1" style={{ color: "var(--text-primary)" }}>Đổi mật khẩu</label>
          <p className="text-xs mb-3" style={{ color: "var(--text-tertiary)" }}>Cập nhật mật khẩu để bảo vệ tài khoản của bạn</p>
          <button onClick={() => setPwOpen(true)} className="px-4 py-2 rounded-xl text-sm font-semibold" style={{ background: "var(--bg-interactive)", color: "var(--text-primary)", border: "1px solid var(--border-default)" }}>
            🔑 Đổi mật khẩu
          </button>
        </div>
      </div>

      {/* Password Modal */}
      {pwOpen && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,.5)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center" }} onClick={() => setPwOpen(false)}>
          <div style={{ background: "var(--bg-surface)", borderRadius: "1rem", maxWidth: 420, width: "90%" }} onClick={(e) => e.stopPropagation()}>
            <div className="p-4 flex justify-between items-center" style={{ borderBottom: "1px solid var(--border-default)" }}>
              <span className="font-bold text-lg" style={{ color: "var(--text-primary)" }}>Đổi mật khẩu</span>
              <button onClick={() => setPwOpen(false)} className="text-xl" style={{ background: "none", border: "none", color: "var(--text-secondary)", cursor: "pointer" }}>×</button>
            </div>
            <form onSubmit={handleChangePassword}>
              <div className="p-5 space-y-4">
                {pwError && <div className="p-3 rounded-xl text-sm" style={{ background: "rgba(254,226,226,.7)", color: "#dc2626", border: "1px solid rgba(252,165,165,.5)" }}>{pwError}</div>}
                {pwSuccess && <div className="p-3 rounded-xl text-sm" style={{ background: "rgba(220,252,231,.7)", color: "#16a34a", border: "1px solid rgba(187,247,208,.5)" }}>Mật khẩu đã được đổi thành công!</div>}
                <div>
                  <label className="block text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Mật khẩu hiện tại</label>
                  <input type="password" value={oldPw} onChange={(e) => setOldPw(e.target.value)} required className="w-full p-3 rounded-xl text-sm border" style={inputStyle} />
                </div>
                <div>
                  <label className="block text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Mật khẩu mới</label>
                  <input type="password" value={newPw1} onChange={(e) => setNewPw1(e.target.value)} required minLength={8} className="w-full p-3 rounded-xl text-sm border" style={inputStyle} />
                  <p className="text-xs mt-1" style={{ color: "var(--text-tertiary)" }}>Tối thiểu 8 ký tự</p>
                </div>
                <div>
                  <label className="block text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Xác nhận mật khẩu mới</label>
                  <input type="password" value={newPw2} onChange={(e) => setNewPw2(e.target.value)} required className="w-full p-3 rounded-xl text-sm border" style={inputStyle} />
                </div>
              </div>
              <div className="p-4 flex justify-end gap-3" style={{ borderTop: "1px solid var(--border-default)" }}>
                <button type="button" onClick={() => setPwOpen(false)} className="px-5 py-2 rounded-xl text-sm font-semibold" style={{ background: "var(--bg-interactive)", color: "var(--text-primary)" }}>Hủy</button>
                <button type="submit" disabled={pwLoading} className="px-5 py-2 rounded-xl text-sm font-semibold text-white" style={{ background: "#3b82f6", opacity: pwLoading ? 0.6 : 1 }}>
                  {pwLoading ? "Đang xử lý..." : "Đổi mật khẩu"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
