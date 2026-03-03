"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { apiFetch, apiUrl } from "@/lib/api";

interface ProfileData {
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  avatar_url?: string;
  cover_url?: string;
  bio: string;
  display_title: string;
  subtitle: string;
  social_links: Record<string, string>;
  skills: { languages?: string[]; tools?: string[] };
  certificates: { name: string; score: string }[];
  hobbies: { icon: string; text: string }[];
  info_items: { icon: string; text: string }[];
  streak: { total_study_minutes: number; longest_streak: number; current_streak: number };
  total_vocab: number;
  total_exams: number;
  total_courses: number;
  enrolled_courses: { slug: string; title: string; lessons_count: number; progress: number }[];
  recent_exam_results: { id: number; title: string; score: number; correct_count: number; total_questions: number; submitted_at: string }[];
  badges: { icon: string; name: string }[];
  is_own_profile: boolean;
}

export default function ProfilePage() {
  const params = useParams();
  const username = params?.username as string | undefined;
  const { user } = useAuth();

  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"about" | "courses" | "results">("about");

  // Edit modal
  const [editOpen, setEditOpen] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [editSubtitle, setEditSubtitle] = useState("");
  const [editBio, setEditBio] = useState("");

  useEffect(() => {
    const endpoint = username ? `/profile/${username}` : "/profile/me";
    fetch(`/api/v1${endpoint}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d: ProfileData) => {
        setProfile(d);
        setEditTitle(d.display_title || "");
        setEditSubtitle(d.subtitle || "");
        setEditBio(d.bio || "");
        setLoading(false);
      })
      .catch(() => {
        // Fallback: build from current user
        if (user) {
          setProfile({
            username: user.username, first_name: user.first_name, last_name: user.last_name, email: user.email,
            bio: "", display_title: "", subtitle: "", social_links: {}, skills: {}, certificates: [], hobbies: [],
            info_items: [], streak: { total_study_minutes: 0, longest_streak: 0, current_streak: 0 },
            total_vocab: 0, total_exams: 0, total_courses: 0, enrolled_courses: [], recent_exam_results: [],
            badges: [], is_own_profile: true,
          });
        }
        setLoading(false);
      });
  }, [username, user]);

  const isOwn = profile?.is_own_profile ?? (!username && !!user);

  const saveBio = async () => {
    try {
      await apiFetch(apiUrl("/profile/update/"), {
        method: "POST",
        body: JSON.stringify({ display_title: editTitle, subtitle: editSubtitle, bio: editBio }),
      });
      setProfile((p) => p ? { ...p, display_title: editTitle, subtitle: editSubtitle, bio: editBio } : p);
      setEditOpen(false);
    } catch { /* ignore */ }
  };

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;
  if (!profile) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Không tìm thấy.</div>;

  const displayName = (profile.first_name || profile.last_name)
    ? `${profile.last_name} ${profile.first_name}`.trim()
    : profile.username;

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      {/* Cover */}
      <div style={{
        height: 200, position: "relative", borderRadius: "0 0 1rem 1rem", overflow: "hidden",
        background: profile.cover_url ? `url(${profile.cover_url}) center/cover` : "linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #a18cd1 100%)",
      }}>
        <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: 60, background: "linear-gradient(to top, var(--bg-app), transparent)" }} />
      </div>

      {/* Avatar */}
      <div style={{ display: "flex", justifyContent: "center", marginTop: -70, position: "relative", zIndex: 10, marginBottom: "1rem" }}>
        <div style={{
          width: 130, height: 130, borderRadius: "50%", border: "4px solid var(--bg-surface)",
          boxShadow: "0 8px 24px rgba(0,0,0,.15)", overflow: "hidden", background: "var(--bg-surface)",
        }}>
          {profile.avatar_url ? (
            <img src={profile.avatar_url} alt={profile.username} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          ) : (
            <div style={{ width: "100%", height: "100%", background: "linear-gradient(135deg, #f97316, #ea580c)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "3rem", color: "white", fontWeight: 700 }}>
              {profile.username.slice(0, 1).toUpperCase()}
            </div>
          )}
        </div>
      </div>

      {/* Name */}
      <div className="text-center mb-5 px-6">
        <h1 className="text-2xl font-extrabold inline-flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
          {displayName}
          {isOwn && (
            <button onClick={() => setEditOpen(true)} className="text-xs px-2 py-1 rounded-lg" style={{ background: "var(--bg-interactive)", color: "var(--text-secondary)", border: "1px solid var(--border-default)", fontWeight: 600 }}>
              ✏️ Sửa
            </button>
          )}
        </h1>
      </div>

      {/* Bio Card */}
      <div className="px-6 mb-5">
        <div className="rounded-2xl overflow-hidden" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
          <div className="px-5 py-3 flex items-center justify-between" style={{ background: "var(--bg-interactive)", borderBottom: "1px solid var(--border-default)" }}>
            <span className="text-xs font-semibold uppercase" style={{ color: "var(--text-secondary)" }}>GIỚI THIỆU</span>
          </div>
          <div className="p-5">
            <p className="text-sm leading-relaxed" style={{ color: profile.bio ? "var(--text-secondary)" : "var(--text-tertiary)", fontStyle: profile.bio ? "normal" : "italic" }}>
              {profile.bio || "Nhấn chỉnh sửa để thêm giới thiệu..."}
            </p>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="px-6 pb-8" style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: "1.5rem" }}>
        {/* Left: Tabs */}
        <div className="rounded-2xl overflow-hidden" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
          <div className="flex" style={{ borderBottom: "1px solid var(--border-default)", padding: "0 1.25rem" }}>
            {(["about", "courses", "results"] as const).map((tab) => (
              <button key={tab} onClick={() => setActiveTab(tab)} className="py-3 px-4 text-sm font-semibold border-b-2 transition-all" style={{
                color: activeTab === tab ? "var(--action-primary)" : "var(--text-secondary)",
                borderColor: activeTab === tab ? "var(--action-primary)" : "transparent",
                background: "transparent",
              }}>{tab === "about" ? "Giới thiệu" : tab === "courses" ? "Khóa học" : "Kết quả thi"}</button>
            ))}
          </div>

          <div className="p-5">
            {activeTab === "about" && (
              <>
                <h2 className="text-lg font-bold mb-1" style={{ color: "var(--text-primary)" }}>{profile.display_title || "Hello Fellow < Love />! 👋"}</h2>
                <p className="text-sm font-mono mb-5" style={{ color: "#10b981" }}>{profile.subtitle || "Chào mừng đến trang cá nhân"}</p>
                {/* Social links */}
                <div className="flex flex-wrap gap-2 mb-5">
                  {Object.entries(profile.social_links || {}).map(([key, url]) => (
                    <a key={key} href={url} target="_blank" rel="noreferrer" className="text-xs font-bold text-white px-3 py-1.5 rounded-lg no-underline" style={{ background: key === "facebook" ? "#1877F2" : key === "tiktok" ? "#000" : key === "gmail" ? "#EA4335" : key === "linkedin" ? "#0A66C2" : "#6B7280" }}>{key.toUpperCase()}</a>
                  ))}
                </div>
                {/* Info items */}
                <ul className="space-y-2 mb-5">
                  {(profile.info_items?.length ? profile.info_items : [{ icon: "👋", text: `Xin chào, mình là ${profile.username}` }]).map((item, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm" style={{ color: "var(--text-primary)" }}>
                      <span>{item.icon}</span><span>{item.text}</span>
                    </li>
                  ))}
                </ul>
                {/* Skills */}
                {profile.skills?.languages?.length ? (
                  <div className="mb-4">
                    <h3 className="text-sm font-bold mb-2 flex items-center gap-2" style={{ color: "var(--text-primary)" }}>📚 Ngôn ngữ</h3>
                    <div className="flex flex-wrap gap-2">{profile.skills.languages.map((l) => <span key={l} className="text-xs font-bold text-white px-3 py-1 rounded-lg uppercase" style={{ background: "#3B82F6" }}>{l}</span>)}</div>
                  </div>
                ) : null}
                {/* Certificates */}
                <h3 className="text-base font-bold mt-5 mb-2" style={{ color: "var(--text-primary)" }}>📜 Chứng chỉ</h3>
                <ul className="list-disc pl-5 space-y-1">
                  {profile.certificates?.length ? profile.certificates.map((c, i) => (
                    <li key={i} className="text-sm" style={{ color: "var(--text-primary)" }}>{c.name} <span style={{ color: "var(--action-primary)", fontWeight: 700 }}>{c.score}</span></li>
                  )) : <li className="text-sm" style={{ color: "var(--text-tertiary)" }}>Chưa có chứng chỉ nào</li>}
                </ul>
              </>
            )}

            {activeTab === "courses" && (
              profile.enrolled_courses?.length ? profile.enrolled_courses.map((c) => (
                <a key={c.slug} href={`/courses/${c.slug}`} className="flex items-center gap-3 p-3 rounded-xl no-underline hover:bg-[var(--bg-interactive)] transition-all">
                  <div className="w-9 h-9 rounded-lg flex items-center justify-center text-xs font-bold text-white" style={{ background: "linear-gradient(135deg, #6366F1, #8B5CF6)" }}>{c.title.slice(0, 2).toUpperCase()}</div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-semibold truncate" style={{ color: "var(--text-primary)" }}>{c.title}</div>
                    <div className="text-xs" style={{ color: "var(--text-tertiary)" }}>{c.lessons_count} bài học • {c.progress}%</div>
                  </div>
                </a>
              )) : <div className="text-center py-8" style={{ color: "var(--text-tertiary)" }}><div className="text-4xl mb-3">📚</div><p>Chưa tham gia khóa học nào</p></div>
            )}

            {activeTab === "results" && (
              profile.recent_exam_results?.length ? profile.recent_exam_results.map((r) => (
                <a key={r.id} href={`/exam/session/${r.id}/result`} className="flex items-center gap-3 p-3 rounded-xl no-underline hover:bg-[var(--bg-interactive)] transition-all">
                  <div className="w-9 h-9 rounded-lg flex items-center justify-center text-xs font-bold text-white" style={{
                    background: r.score >= 80 ? "#10B981" : r.score >= 60 ? "#F59E0B" : "#EF4444",
                  }}>{r.score}%</div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-semibold truncate" style={{ color: "var(--text-primary)" }}>{r.title}</div>
                    <div className="text-xs" style={{ color: "var(--text-tertiary)" }}>{r.submitted_at} • {r.correct_count}/{r.total_questions} câu đúng</div>
                  </div>
                </a>
              )) : <div className="text-center py-8" style={{ color: "var(--text-tertiary)" }}><div className="text-4xl mb-3">📝</div><p>Chưa có kết quả thi nào</p></div>
            )}
          </div>
        </div>

        {/* Right: Sidebar */}
        <div className="space-y-4">
          {/* Achievements */}
          <div className="rounded-2xl overflow-hidden" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
            <div className="px-4 py-3 font-bold text-sm" style={{ color: "var(--text-primary)", borderBottom: "1px solid var(--border-default)" }}>Thành tích</div>
            <div className="p-2 space-y-1">
              {[
                { value: `${profile.streak.total_study_minutes}m`, label: "thời gian học", bg: "rgba(249,115,22,.08)", color: "#F97316" },
                { value: String(profile.streak.longest_streak), label: "ngày liên tiếp dài nhất", bg: "rgba(239,68,68,.08)", color: "#EF4444" },
                { value: String(profile.total_vocab), label: "từ vựng đã học", bg: "rgba(16,185,129,.08)", color: "#10B981" },
              ].map((a) => (
                <div key={a.label} className="flex items-center gap-1 p-3 rounded-lg" style={{ background: a.bg }}>
                  <span className="text-base font-bold mr-1" style={{ color: a.color }}>{a.value}</span>
                  <span className="text-sm" style={{ color: "var(--text-secondary)" }}>{a.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Badges */}
          <div className="rounded-2xl overflow-hidden" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
            <div className="px-4 py-3 font-bold text-sm" style={{ color: "var(--text-primary)", borderBottom: "1px solid var(--border-default)" }}>Huy hiệu</div>
            {profile.badges?.length ? (
              <div className="grid grid-cols-3 gap-3 p-4">
                {profile.badges.slice(0, 6).map((b, i) => (
                  <div key={i} className="text-center p-2 rounded-lg" style={{ background: "var(--bg-interactive)" }}>
                    <span className="text-2xl block mb-1">{b.icon}</span>
                    <span className="text-[11px]" style={{ color: "var(--text-secondary)" }}>{b.name}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6"><div className="text-4xl mb-2">🐸</div><p className="text-sm" style={{ color: "var(--text-tertiary)" }}>Chưa có thành tích</p></div>
            )}
          </div>

          {/* Quick Stats */}
          <div className="flex gap-4 p-4 rounded-2xl" style={{ background: "var(--bg-interactive)" }}>
            {[
              { value: profile.total_exams, label: "Bài thi" },
              { value: profile.total_courses, label: "Khóa học" },
              { value: profile.streak.current_streak, label: "Chuỗi ngày" },
            ].map((s) => (
              <div key={s.label} className="flex-1 text-center">
                <div className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>{s.value}</div>
                <div className="text-[11px] uppercase" style={{ color: "var(--text-tertiary)" }}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Edit Modal */}
      {editOpen && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,.5)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center" }} onClick={() => setEditOpen(false)}>
          <div style={{ background: "var(--bg-surface)", borderRadius: "1rem", maxWidth: 500, width: "90%", maxHeight: "80vh", overflow: "auto" }} onClick={(e) => e.stopPropagation()}>
            <div className="p-4 flex justify-between items-center" style={{ borderBottom: "1px solid var(--border-default)" }}>
              <span className="font-bold text-lg" style={{ color: "var(--text-primary)" }}>Chỉnh sửa thông tin</span>
              <button onClick={() => setEditOpen(false)} className="text-xl" style={{ background: "none", border: "none", color: "var(--text-secondary)", cursor: "pointer" }}>×</button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Tiêu đề</label>
                <input value={editTitle} onChange={(e) => setEditTitle(e.target.value)} className="w-full p-3 rounded-xl text-sm border" style={{ background: "var(--bg-interactive)", borderColor: "var(--border-default)", color: "var(--text-primary)" }} />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Phụ đề</label>
                <input value={editSubtitle} onChange={(e) => setEditSubtitle(e.target.value)} className="w-full p-3 rounded-xl text-sm border" style={{ background: "var(--bg-interactive)", borderColor: "var(--border-default)", color: "var(--text-primary)" }} />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Bio</label>
                <textarea value={editBio} onChange={(e) => setEditBio(e.target.value)} rows={4} className="w-full p-3 rounded-xl text-sm border resize-y" style={{ background: "var(--bg-interactive)", borderColor: "var(--border-default)", color: "var(--text-primary)" }} />
              </div>
            </div>
            <div className="p-4 flex justify-end gap-3" style={{ borderTop: "1px solid var(--border-default)" }}>
              <button onClick={() => setEditOpen(false)} className="px-5 py-2 rounded-xl text-sm font-semibold" style={{ background: "var(--bg-interactive)", color: "var(--text-primary)" }}>Hủy</button>
              <button onClick={saveBio} className="px-5 py-2 rounded-xl text-sm font-semibold text-white" style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }}>Lưu</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
