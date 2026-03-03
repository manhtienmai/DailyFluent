import Link from "next/link";

export default function LandingPage() {
  return (
    <div style={{ fontFamily: "'Inter', sans-serif" }}>
      {/* Hero */}
      <section style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%)", color: "white", textAlign: "center", padding: "4rem 1.5rem", position: "relative", overflow: "hidden" }}>
        <div style={{ position: "absolute", inset: 0, background: "radial-gradient(circle at 30% 50%, rgba(99,102,241,.15), transparent 60%), radial-gradient(circle at 70% 30%, rgba(139,92,246,.1), transparent 50%)" }} />
        <div style={{ position: "relative", maxWidth: 800, zIndex: 1 }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "0.5rem 1rem", borderRadius: "9999px", background: "rgba(99,102,241,.15)", border: "1px solid rgba(99,102,241,.3)", fontSize: "0.75rem", fontWeight: 600, marginBottom: "2rem" }}>
            ⚡ Nền tảng học ngoại ngữ #1 Việt Nam
          </div>
          <h1 style={{ fontSize: "clamp(2rem, 5vw, 3.5rem)", fontWeight: 800, lineHeight: 1.1, marginBottom: "1.5rem", letterSpacing: "-0.02em" }}>
            Học tiếng Anh & tiếng Nhật <br />
            <span style={{ background: "linear-gradient(135deg, #818cf8, #c084fc)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>Thông minh hơn mỗi ngày</span>
          </h1>
          <p style={{ fontSize: "1.125rem", color: "rgba(255,255,255,.7)", maxWidth: 600, margin: "0 auto 2rem", lineHeight: 1.6 }}>
            DailyFluent kết hợp AI, spaced repetition và lộ trình cá nhân hóa để giúp bạn chinh phục TOEIC, JLPT và giao tiếp tự tin.
          </p>
          <div style={{ display: "flex", gap: "1rem", justifyContent: "center", flexWrap: "wrap" }}>
            <Link href="/signup" style={{ padding: "1rem 2.5rem", borderRadius: "0.75rem", background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "white", fontWeight: 700, fontSize: "1rem", textDecoration: "none", boxShadow: "0 4px 20px rgba(99,102,241,.4)" }}>Bắt đầu miễn phí →</Link>
            <Link href="/login" style={{ padding: "1rem 2.5rem", borderRadius: "0.75rem", background: "rgba(255,255,255,.1)", border: "1px solid rgba(255,255,255,.2)", color: "white", fontWeight: 600, fontSize: "1rem", textDecoration: "none" }}>Đăng nhập</Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section style={{ padding: "5rem 1.5rem", background: "#fafafa" }}>
        <div style={{ maxWidth: 1000, margin: "0 auto" }}>
          <h2 style={{ textAlign: "center", fontSize: "2rem", fontWeight: 800, marginBottom: "3rem", color: "#1e293b" }}>Tính năng nổi bật</h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1.5rem" }}>
            {[
              { icon: "🎯", title: "Placement Test", desc: "Đánh giá trình độ chính xác với bài test thông minh, tạo lộ trình phù hợp." },
              { icon: "📚", title: "Flashcards & SRS", desc: "Ghi nhớ từ vựng lâu dài với phương pháp Spaced Repetition." },
              { icon: "🎮", title: "Game học tập", desc: "5+ trò chơi tương tác: MCQ, Matching, Listening, Fill, Dictation." },
              { icon: "📝", title: "Luyện thi TOEIC", desc: "Bộ đề thi thực chiến với phân tích kết quả chi tiết." },
              { icon: "🈲", title: "Kanji & Ngữ pháp", desc: "Học Kanji theo tần suất, ngữ pháp theo level JLPT." },
              { icon: "🎧", title: "Choukai & Dokkai", desc: "Luyện nghe, đọc hiểu với audio và bài đọc thực tế." },
            ].map((f) => (
              <div key={f.title} style={{ padding: "2rem", borderRadius: "1rem", background: "white", border: "1px solid #e2e8f0", transition: "transform 0.2s, box-shadow 0.2s" }}>
                <div style={{ fontSize: "2.5rem", marginBottom: "1rem" }}>{f.icon}</div>
                <h3 style={{ fontSize: "1.125rem", fontWeight: 700, marginBottom: "0.5rem", color: "#1e293b" }}>{f.title}</h3>
                <p style={{ fontSize: "0.875rem", color: "#64748b", lineHeight: 1.6 }}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Steps */}
      <section style={{ padding: "5rem 1.5rem", background: "white" }}>
        <div style={{ maxWidth: 800, margin: "0 auto", textAlign: "center" }}>
          <h2 style={{ fontSize: "2rem", fontWeight: 800, marginBottom: "3rem", color: "#1e293b" }}>3 bước bắt đầu</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
            {[
              { step: "1", title: "Đăng ký miễn phí", desc: "Tạo tài khoản chỉ trong 30 giây." },
              { step: "2", title: "Làm bài Placement Test", desc: "Hệ thống đánh giá trình độ và tạo lộ trình cá nhân hóa." },
              { step: "3", title: "Học mỗi ngày", desc: "Hoàn thành bài học hàng ngày, theo dõi tiến độ và giữ streak." },
            ].map((s) => (
              <div key={s.step} style={{ display: "flex", alignItems: "center", gap: "1.5rem", textAlign: "left" }}>
                <div style={{ width: 56, height: 56, borderRadius: "50%", background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "white", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.25rem", fontWeight: 800, flexShrink: 0 }}>{s.step}</div>
                <div>
                  <h3 style={{ fontWeight: 700, color: "#1e293b", marginBottom: "0.25rem" }}>{s.title}</h3>
                  <p style={{ color: "#64748b", fontSize: "0.875rem" }}>{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{ padding: "5rem 1.5rem", background: "linear-gradient(135deg, #312e81, #1e1b4b)", textAlign: "center", color: "white" }}>
        <h2 style={{ fontSize: "2rem", fontWeight: 800, marginBottom: "1rem" }}>Sẵn sàng chinh phục ngoại ngữ?</h2>
        <p style={{ color: "rgba(255,255,255,.7)", marginBottom: "2rem", maxWidth: 500, margin: "0 auto 2rem" }}>Tham gia cùng hàng nghìn học viên đang cải thiện mỗi ngày.</p>
        <Link href="/signup" style={{ padding: "1rem 3rem", borderRadius: "0.75rem", background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "white", fontWeight: 700, fontSize: "1.125rem", textDecoration: "none", display: "inline-block", boxShadow: "0 4px 20px rgba(99,102,241,.4)" }}>Đăng ký ngay — Miễn phí</Link>
      </section>

      {/* Footer */}
      <footer style={{ padding: "2rem 1.5rem", background: "#0f172a", textAlign: "center" }}>
        <p style={{ color: "rgba(255,255,255,.4)", fontSize: "0.75rem" }}>© 2026 DailyFluent. All rights reserved.</p>
      </footer>
    </div>
  );
}
