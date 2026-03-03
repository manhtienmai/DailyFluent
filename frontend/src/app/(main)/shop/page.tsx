"use client";

import { useState, useEffect } from "react";

interface Frame {
  id: number;
  name: string;
  slug: string;
  rarity: string;
  price: number;
  css_gradient?: string;
  image_url?: string;
  owned: boolean;
  equipped: boolean;
}

interface Wallet { coins: number; }

const RARITY_COLORS: Record<string, string> = { COMMON: "#6B7280", RARE: "#3B82F6", EPIC: "#8B5CF6", LEGENDARY: "#EC4899" };
const RARITY_LABELS: Record<string, string> = { COMMON: "Thường", RARE: "Hiếm", EPIC: "Sử thi", LEGENDARY: "Huyền thoại" };

export default function ShopPage() {
  const [frames, setFrames] = useState<Frame[]>([]);
  const [wallet, setWallet] = useState<Wallet>({ coins: 0 });
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"shop" | "inventory">("shop");
  const [toast, setToast] = useState("");

  useEffect(() => {
    fetch("/api/v1/shop/frames", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: { frames: Frame[]; wallet: Wallet }) => { setFrames(d.frames || []); setWallet(d.wallet || { coins: 0 }); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(""), 3000); };

  const buyFrame = async (id: number) => {
    try {
      const r = await fetch(`/api/v1/shop/frames/${id}/buy`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" } });
      const d = await r.json();
      if (d.success) {
        setFrames((p) => p.map((f) => f.id === id ? { ...f, owned: true } : f));
        setWallet({ coins: d.coins ?? wallet.coins - (frames.find((f) => f.id === id)?.price || 0) });
        showToast("Mua thành công! 🎉");
      } else { showToast(d.error || "Không đủ xu"); }
    } catch { showToast("Lỗi kết nối"); }
  };

  const equipFrame = async (id: number) => {
    try {
      const r = await fetch(`/api/v1/shop/frames/${id}/equip`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" } });
      const d = await r.json();
      if (d.success) {
        setFrames((p) => p.map((f) => ({ ...f, equipped: f.id === id })));
        showToast("Đã trang bị! ✨");
      }
    } catch { showToast("Lỗi kết nối"); }
  };

  const display = tab === "inventory" ? frames.filter((f) => f.owned) : frames;

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <div className="text-center mb-6">
        <h1 className="text-2xl font-extrabold" style={{ color: "var(--text-primary)" }}>Cửa hàng</h1>
      </div>

      {/* Top nav */}
      <div className="flex justify-between items-center flex-wrap gap-4 mb-6">
        <div className="flex gap-2">
          {(["shop", "inventory"] as const).map((t) => (
            <button key={t} onClick={() => setTab(t)} className="px-5 py-2.5 rounded-full text-sm font-semibold transition-all" style={{
              background: tab === t ? "linear-gradient(135deg, #7C3AED, #A855F7)" : "var(--bg-surface)",
              color: tab === t ? "white" : "var(--text-secondary)",
              border: tab === t ? "none" : "1px solid var(--border-default)",
              cursor: "pointer",
            }}>{t === "shop" ? "Vật phẩm" : "Kho đồ"}</button>
          ))}
        </div>
        <div className="flex items-center gap-3 px-5 py-2.5 rounded-full font-bold" style={{ background: "linear-gradient(135deg, #fbbf24, #f59e0b)", color: "#1c1917", boxShadow: "0 4px 15px rgba(245,158,11,.3)" }}>
          <div className="w-5 h-5 rounded-full" style={{ background: "linear-gradient(135deg, #FCD34D, #F59E0B)", border: "2px solid rgba(255,255,255,.5)" }} />
          <span>{wallet.coins.toLocaleString()}</span>
        </div>
      </div>

      {/* Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))", gap: "1.5rem" }}>
        {display.map((f) => (
          <div key={f.id} className="p-6 rounded-2xl text-center transition-all" style={{
            background: f.rarity === "LEGENDARY" ? "linear-gradient(135deg, rgba(139,92,246,.1), rgba(236,72,153,.1))" : "var(--bg-surface)",
            border: f.rarity === "LEGENDARY" ? "2px solid rgba(139,92,246,.3)" : "1px solid var(--border-default)",
          }}>
            {/* Preview */}
            <div className="w-40 h-40 mx-auto mb-5 relative">
              {f.image_url ? (
                <img src={f.image_url} alt={f.name} className="w-full h-full object-contain" />
              ) : (
                <div className="w-full h-full rounded-full" style={{ background: f.css_gradient || "linear-gradient(135deg, #6366f1, #8b5cf6)", opacity: 0.3 }} />
              )}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-24 h-24 rounded-full flex items-center justify-center text-4xl" style={{ background: "var(--bg-surface)" }}>👤</div>
            </div>

            <h3 className="font-bold mb-1" style={{ color: "var(--text-primary)" }}>{f.name}</h3>
            <div className="text-xs mb-4 flex items-center justify-center gap-1" style={{ color: RARITY_COLORS[f.rarity] || "#6B7280" }}>
              {f.rarity === "LEGENDARY" ? "⭐" : f.rarity === "EPIC" ? "🏆" : f.rarity === "RARE" ? "✨" : "📦"} {RARITY_LABELS[f.rarity] || f.rarity}
            </div>

            <div className="flex items-center justify-between mt-3">
              <div className="flex items-center gap-1.5 font-bold" style={{ color: "#F59E0B" }}>
                <div className="w-5 h-5 rounded-full" style={{ background: "linear-gradient(135deg, #FBBF24, #F59E0B)" }} />
                {f.price.toLocaleString()}
              </div>
              {f.owned ? (
                f.equipped ? (
                  <span className="px-4 py-2 rounded-lg text-xs font-semibold" style={{ background: "var(--bg-interactive)", color: "var(--text-tertiary)" }}>✓ Đang dùng</span>
                ) : (
                  <button onClick={() => equipFrame(f.id)} className="px-4 py-2 rounded-lg text-xs font-semibold text-white" style={{ background: "linear-gradient(135deg, #10B981, #059669)", border: "none", cursor: "pointer" }}>Trang bị</button>
                )
              ) : (
                <button onClick={() => buyFrame(f.id)} className="px-4 py-2 rounded-lg text-xs font-semibold text-white" style={{
                  background: f.rarity === "LEGENDARY" ? "linear-gradient(135deg, #8B5CF6, #EC4899)" : "linear-gradient(135deg, #7C3AED, #A855F7)", border: "none", cursor: "pointer",
                }}>Mua</button>
              )}
            </div>
          </div>
        ))}
        {!display.length && <p className="col-span-full text-center py-8" style={{ color: "var(--text-tertiary)" }}>{tab === "inventory" ? "Bạn chưa có vật phẩm nào." : "Không có vật phẩm."}</p>}
      </div>

      {/* Toast */}
      {toast && (
        <div style={{ position: "fixed", bottom: "2rem", left: "50%", transform: "translateX(-50%)", padding: "1rem 1.5rem", background: "var(--bg-surface)", border: "1px solid var(--border-default)", borderRadius: "0.75rem", boxShadow: "0 10px 30px rgba(0,0,0,.15)", zIndex: 1000, color: "var(--text-primary)", fontWeight: 600 }}>{toast}</div>
      )}
    </div>
  );
}
