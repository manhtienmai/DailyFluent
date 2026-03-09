"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Table, Button, Typography, Space, Tag, Select, InputNumber,
  message, Progress, Switch, Tooltip, Slider, Card, Input, Divider
} from "antd";
import {
  SoundOutlined, PlayCircleOutlined, ThunderboltOutlined,
  ReloadOutlined, AudioOutlined
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { adminGet, adminPost } from "@/lib/admin-api";

const { Title, Text } = Typography;

interface Stats {
  total: number;
  has_audio_us: number;
  has_audio_uk: number;
  missing: number;
  language: string;
}

interface MissingEntry {
  id: number;
  word: string;
  pos: string;
  ipa: string;
  audio_us: string;
  audio_uk: string;
}

interface BatchProgress {
  running: boolean;
  total: number;
  done: number;
  success: number;
  errors: number;
  current_word: string;
  error_list: string[];
}

interface VoiceOption {
  name: string;
  gender: string;
  quality: string;
  note: string;
}

export default function TtsPage() {
  const [language, setLanguage] = useState("en");
  const [stats, setStats] = useState<Stats | null>(null);
  const [items, setItems] = useState<MissingEntry[]>([]);
  const [totalMissing, setTotalMissing] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [batchLimit, setBatchLimit] = useState(50);
  const [batchForce, setBatchForce] = useState(false);
  const [progress, setProgress] = useState<BatchProgress | null>(null);
  const [generatingId, setGeneratingId] = useState<number | null>(null);
  const [playingUrl, setPlayingUrl] = useState<string | null>(null);
  const [batchRunning, setBatchRunning] = useState(false);

  // Voice & speed settings
  const [voices, setVoices] = useState<Record<string, VoiceOption[]>>({});
  const [selectedVoiceUS, setSelectedVoiceUS] = useState("en-US-Studio-Q");
  const [selectedVoiceUK, setSelectedVoiceUK] = useState("en-GB-Studio-B");
  const [speakingRate, setSpeakingRate] = useState(0.92);

  // EN10 preview
  const [en10Word, setEN10Word] = useState("");
  const [en10Loading, setEN10Loading] = useState(false);
  const [en10Audio, setEN10Audio] = useState<string | null>(null);

  // Grammar TTS
  interface GrammarTopic { topic_id: string; title: string; title_vi: string; exercise_count: number; total_words: number; words_with_audio: number; }
  const [grammarTopics, setGrammarTopics] = useState<GrammarTopic[]>([]);
  const [selectedGrammarTopic, setSelectedGrammarTopic] = useState<string>("");
  const [grammarGenerating, setGrammarGenerating] = useState(false);
  const [grammarResult, setGrammarResult] = useState<{ success: boolean; message: string; generated?: number; errors?: number; total_words?: number } | null>(null);

  const fetchGrammarTopics = useCallback(() => {
    adminGet<{ items: GrammarTopic[] }>("/crud/tts/grammar-topics/")
      .then((d) => setGrammarTopics(d.items || []))
      .catch(() => {});
  }, []);

  const fetchStats = useCallback(() => {
    adminGet<Stats>(`/crud/tts/stats/?language=${language}`)
      .then(setStats)
      .catch(() => setStats(null));
  }, [language]);

  const fetchMissing = useCallback(() => {
    setLoading(true);
    adminGet<{ items: MissingEntry[]; count: number }>(
      `/crud/tts/missing/?language=${language}&page=${page}`
    )
      .then((d) => {
        setItems(d.items || []);
        setTotalMissing(d.count || 0);
      })
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [language, page]);

  const fetchProgress = useCallback(() => {
    adminGet<BatchProgress>("/crud/tts/progress/")
      .then(setProgress)
      .catch(() => {});
  }, []);

  const fetchVoices = useCallback(() => {
    adminGet<{ voices: Record<string, VoiceOption[]>; default_speaking_rate: number }>("/crud/tts/voices/")
      .then((d) => {
        setVoices(d.voices || {});
        setSpeakingRate(d.default_speaking_rate || 0.92);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetchStats();
    fetchMissing();
    fetchVoices();
    fetchGrammarTopics();
  }, [fetchStats, fetchMissing, fetchVoices, fetchGrammarTopics]);

  // Poll progress while batch is running
  useEffect(() => {
    if (!batchRunning) return;
    const interval = setInterval(() => {
      adminGet<BatchProgress>("/crud/tts/progress/")
        .then((p) => {
          setProgress(p);
          // Batch finished: stop polling, refresh data
          if (!p.running) {
            setBatchRunning(false);
            fetchStats();
            fetchMissing();
          }
        })
        .catch(() => {});
    }, 1500);
    return () => clearInterval(interval);
  }, [batchRunning, fetchStats, fetchMissing]);

  const startBatch = async () => {
    try {
      const resp = await adminPost<{ success: boolean; message: string }>(
        "/crud/tts/generate-batch/",
        { language, limit: batchLimit, force: batchForce, voice_us: selectedVoiceUS, voice_uk: selectedVoiceUK, speaking_rate: speakingRate }
      );
      if (resp.success) {
        message.success(resp.message);
        setBatchRunning(true); // Start polling immediately
        fetchProgress();
      } else {
        message.warning(resp.message);
      }
    } catch {
      message.error("Lỗi khi khởi chạy batch");
    }
  };

  const generateSingle = async (entryId: number) => {
    setGeneratingId(entryId);
    try {
      const resp = await adminPost<{ success: boolean; result?: any; message?: string }>(
        "/crud/tts/generate-single/",
        { entry_id: entryId, force: true }
      );
      if (resp.success) {
        message.success(`Đã tạo audio cho "${resp.result?.word}"`);
        fetchMissing();
        fetchStats();
      } else {
        message.error(resp.message || "Lỗi");
      }
    } catch {
      message.error("Lỗi khi tạo audio");
    } finally {
      setGeneratingId(null);
    }
  };

  const playAudio = (url: string) => {
    if (playingUrl) return;
    setPlayingUrl(url);
    const audio = new Audio(url);
    audio.onended = () => setPlayingUrl(null);
    audio.onerror = () => { setPlayingUrl(null); message.error("Không phát được audio"); };
    audio.play();
  };

  const previewEN10 = async () => {
    if (!en10Word.trim()) return;
    setEN10Loading(true);
    setEN10Audio(null);
    try {
      const accent = selectedVoiceUS.startsWith("en-GB") ? "en-GB" : "en-US";
      const resp = await adminPost<{ success: boolean; audio_base64?: string; message?: string }>(
        "/crud/tts/en10-synthesize/",
        { word: en10Word.trim(), voice_name: selectedVoiceUS, language_code: accent, speaking_rate: speakingRate }
      );
      if (resp.success && resp.audio_base64) {
        const audioUrl = `data:audio/mp3;base64,${resp.audio_base64}`;
        setEN10Audio(audioUrl);
        const audio = new Audio(audioUrl);
        audio.play();
      } else {
        message.error(resp.message || "Lỗi");
      }
    } catch {
      message.error("Lỗi khi synthesize");
    } finally {
      setEN10Loading(false);
    }
  };

  const generateGrammarTts = async () => {
    if (!selectedGrammarTopic) { message.warning("Chọn topic trước"); return; }
    setGrammarGenerating(true);
    setGrammarResult(null);
    try {
      const accent = selectedVoiceUS.startsWith("en-GB") ? "en-GB" : "en-US";
      const resp = await adminPost<{ success: boolean; message: string; generated?: number; errors?: number; total_words?: number; error_list?: string[] }>(
        "/crud/tts/grammar-batch-synthesize/",
        { topic_id: selectedGrammarTopic, voice_name: selectedVoiceUS, language_code: accent, speaking_rate: speakingRate }
      );
      setGrammarResult(resp);
      if (resp.success) {
        message.success(resp.message);
        fetchGrammarTopics();
      } else {
        message.error(resp.message);
      }
    } catch {
      message.error("Lỗi khi tạo Grammar TTS");
    } finally {
      setGrammarGenerating(false);
    }
  };

  const pctHasAudio = stats ? Math.round(((stats.total - stats.missing) / Math.max(stats.total, 1)) * 100) : 0;

  const columns: ColumnsType<MissingEntry> = [
    {
      title: "ID", dataIndex: "id", width: 60,
      render: (id) => <Text type="secondary" style={{ fontSize: 12 }}>{id}</Text>,
    },
    {
      title: "Từ vựng", dataIndex: "word",
      render: (word, r) => (
        <div>
          <Text strong>{word}</Text>
          {r.pos && <Tag style={{ marginLeft: 6, fontSize: 10 }}>{r.pos}</Tag>}
          {r.ipa && <div><Text type="secondary" style={{ fontSize: 11, fontFamily: "monospace" }}>{r.ipa}</Text></div>}
        </div>
      ),
    },
    {
      title: "US", dataIndex: "audio_us", width: 70, align: "center",
      render: (url) => url ? (
        <Tooltip title="Phát">
          <Button
            size="small" type="text"
            icon={<PlayCircleOutlined style={{ color: "#10b981" }} />}
            onClick={() => playAudio(url)}
            loading={playingUrl === url}
          />
        </Tooltip>
      ) : <Tag color="default">—</Tag>,
    },
    {
      title: "UK", dataIndex: "audio_uk", width: 70, align: "center",
      render: (url) => url ? (
        <Tooltip title="Phát">
          <Button
            size="small" type="text"
            icon={<PlayCircleOutlined style={{ color: "#3b82f6" }} />}
            onClick={() => playAudio(url)}
            loading={playingUrl === url}
          />
        </Tooltip>
      ) : <Tag color="default">—</Tag>,
    },
    {
      title: "", key: "actions", width: 100, align: "center",
      render: (_, r) => (
        <Button
          size="small" type="primary"
          icon={<SoundOutlined />}
          loading={generatingId === r.id}
          onClick={() => generateSingle(r.id)}
        >
          Generate
        </Button>
      ),
    },
  ];

  const usVoices = voices["en-US"] || [];
  const ukVoices = voices["en-GB"] || [];
  const jpVoices = voices["ja-JP"] || [];

  return (
    <div>
      <Space direction="vertical" size="large" style={{ width: "100%" }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <Title level={3} style={{ margin: 0 }}>🔊 TTS Audio Generator</Title>
            <Text type="secondary">Google Cloud TTS → Azure → DB</Text>
          </div>
          <Select
            value={language}
            onChange={(v) => { setLanguage(v); setPage(1); }}
            style={{ width: 150 }}
            options={[
              { value: "en", label: "🇬🇧 English" },
              { value: "jp", label: "🇯🇵 Japanese" },
            ]}
          />
        </div>

        {/* ── Voice & Speed Settings ── */}
        <Card size="small" title="🎙️ Cài đặt giọng đọc & tốc độ" style={{ borderColor: "#d1d5db" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
            {/* US Voice */}
            <div>
              <Text strong style={{ fontSize: 12, display: "block", marginBottom: 6 }}>🇺🇸 Giọng US</Text>
              <Select
                value={selectedVoiceUS}
                onChange={setSelectedVoiceUS}
                style={{ width: "100%" }}
                optionLabelProp="label"
              >
                {usVoices.map((v) => (
                  <Select.Option key={v.name} value={v.name} label={`${v.name} (${v.gender})`}>
                    <div>
                      <Text strong style={{ fontSize: 12 }}>{v.name}</Text>
                      <Tag
                        style={{ marginLeft: 6, fontSize: 10 }}
                        color={v.quality === "Studio" ? "gold" : v.quality === "Neural2" ? "blue" : "default"}
                      >
                        {v.quality}
                      </Tag>
                      <Tag style={{ fontSize: 10 }}>{v.gender}</Tag>
                    </div>
                    <div style={{ fontSize: 11, color: "#888" }}>{v.note}</div>
                  </Select.Option>
                ))}
              </Select>
            </div>

            {/* UK Voice */}
            <div>
              <Text strong style={{ fontSize: 12, display: "block", marginBottom: 6 }}>🇬🇧 Giọng UK</Text>
              <Select
                value={selectedVoiceUK}
                onChange={setSelectedVoiceUK}
                style={{ width: "100%" }}
                optionLabelProp="label"
              >
                {ukVoices.map((v) => (
                  <Select.Option key={v.name} value={v.name} label={`${v.name} (${v.gender})`}>
                    <div>
                      <Text strong style={{ fontSize: 12 }}>{v.name}</Text>
                      <Tag
                        style={{ marginLeft: 6, fontSize: 10 }}
                        color={v.quality === "Studio" ? "gold" : v.quality === "Neural2" ? "blue" : "default"}
                      >
                        {v.quality}
                      </Tag>
                      <Tag style={{ fontSize: 10 }}>{v.gender}</Tag>
                    </div>
                    <div style={{ fontSize: 11, color: "#888" }}>{v.note}</div>
                  </Select.Option>
                ))}
              </Select>
            </div>
          </div>

          {/* Speaking Rate */}
          <div>
            <Text strong style={{ fontSize: 12 }}>⏱️ Tốc độ nói: <Text code>{speakingRate.toFixed(2)}x</Text></Text>
            <div style={{ fontSize: 11, color: "#888", marginBottom: 4 }}>
              0.5 = rất chậm · 0.8 = chậm rõ · <b>0.92 = chuẩn từ điển</b> · 1.0 = bình thường · 1.2 = nhanh
            </div>
            <Slider
              min={0.5} max={1.5} step={0.02}
              value={speakingRate}
              onChange={setSpeakingRate}
              marks={{ 0.5: "0.5", 0.8: "0.8", 0.92: "0.92", 1.0: "1.0", 1.2: "1.2", 1.5: "1.5" }}
            />
          </div>

          <Divider style={{ margin: "12px 0" }} />

          {/* EN10 Preview */}
          <div>
            <Text strong style={{ fontSize: 12, display: "block", marginBottom: 6 }}>🔤 Preview phát âm (nhập từ bất kỳ)</Text>
            <div style={{ display: "flex", gap: 8 }}>
              <Input
                placeholder="Nhập từ tiếng Anh, vd: opportunity"
                value={en10Word}
                onChange={(e) => setEN10Word(e.target.value)}
                onPressEnter={previewEN10}
                style={{ flex: 1 }}
              />
              <Button
                type="primary"
                icon={<AudioOutlined />}
                onClick={previewEN10}
                loading={en10Loading}
              >
                Nghe thử
              </Button>
              {en10Audio && (
                <Button
                  icon={<PlayCircleOutlined />}
                  onClick={() => { const a = new Audio(en10Audio); a.play(); }}
                >
                  Phát lại
                </Button>
              )}
            </div>
          </div>
        </Card>

        {/* ── Grammar TTS Section ── */}
        <Card size="small" title="📝 Grammar Exercises TTS" style={{ borderColor: "#a78bfa" }}>
          <Text type="secondary" style={{ fontSize: 12, display: "block", marginBottom: 12 }}>
            Tạo audio phát âm cho các từ trong bài tập trọng âm / pronunciation. Học viên sẽ nghe được phát âm ngay trên trang bài tập.
          </Text>
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            <Select
              placeholder="Chọn Grammar Topic"
              value={selectedGrammarTopic || undefined}
              onChange={setSelectedGrammarTopic}
              style={{ minWidth: 280 }}
              options={grammarTopics.map(t => ({
                value: t.topic_id,
                label: `${t.title} — ${t.exercise_count} bài, ${t.total_words} từ (${t.words_with_audio} có audio)`,
              }))}
            />
            <Button
              type="primary"
              icon={<SoundOutlined />}
              onClick={generateGrammarTts}
              loading={grammarGenerating}
              disabled={!selectedGrammarTopic || grammarGenerating}
              style={{ background: "#7c3aed" }}
            >
              Generate Audio
            </Button>
            <Button
              icon={<ReloadOutlined />}
              size="small"
              onClick={fetchGrammarTopics}
            >
              Refresh
            </Button>
          </div>

          {/* Grammar coverage table */}
          {grammarTopics.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #e5e7eb" }}>
                    <th style={{ textAlign: "left", padding: "6px 8px", color: "#6b7280" }}>Topic</th>
                    <th style={{ textAlign: "center", padding: "6px 8px", color: "#6b7280", width: 80 }}>Bài tập</th>
                    <th style={{ textAlign: "center", padding: "6px 8px", color: "#6b7280", width: 80 }}>Tổng từ</th>
                    <th style={{ textAlign: "center", padding: "6px 8px", color: "#6b7280", width: 100 }}>Có Audio</th>
                  </tr>
                </thead>
                <tbody>
                  {grammarTopics.map(t => {
                    const pct = t.total_words > 0 ? Math.round(t.words_with_audio / t.total_words * 100) : 0;
                    return (
                      <tr key={t.topic_id} style={{ borderBottom: "1px solid #f3f4f6", cursor: "pointer", background: selectedGrammarTopic === t.topic_id ? "#f5f3ff" : undefined }} onClick={() => setSelectedGrammarTopic(t.topic_id)}>
                        <td style={{ padding: "6px 8px", fontWeight: 500 }}>{t.title} <span style={{ color: "#9ca3af" }}>({t.title_vi})</span></td>
                        <td style={{ textAlign: "center", padding: "6px 8px" }}>{t.exercise_count}</td>
                        <td style={{ textAlign: "center", padding: "6px 8px" }}>{t.total_words}</td>
                        <td style={{ textAlign: "center", padding: "6px 8px" }}>
                          <Tag color={pct === 100 ? "success" : pct > 0 ? "processing" : "default"}>
                            {t.words_with_audio}/{t.total_words} ({pct}%)
                          </Tag>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Generation result */}
          {grammarResult && (
            <div style={{ marginTop: 12, padding: 12, borderRadius: 8, background: grammarResult.success ? "#f0fdf4" : "#fef2f2", border: `1px solid ${grammarResult.success ? "#bbf7d0" : "#fecaca"}` }}>
              <Text strong style={{ color: grammarResult.success ? "#15803d" : "#dc2626", fontSize: 13 }}>
                {grammarResult.success ? "✅" : "❌"} {grammarResult.message}
              </Text>
            </div>
          )}
        </Card>

        {/* Stats */}
        {stats && (
          <div style={{
            display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12,
          }}>
            <div style={{ background: "var(--bg-surface, #fff)", borderRadius: 10, padding: 16, border: "1px solid var(--border-default, #eee)" }}>
              <Text type="secondary" style={{ fontSize: 11 }}>Tổng WordEntry</Text>
              <div style={{ fontSize: 24, fontWeight: 700 }}>{stats.total}</div>
            </div>
            <div style={{ background: "var(--bg-surface, #fff)", borderRadius: 10, padding: 16, border: "1px solid var(--border-default, #eee)" }}>
              <Text type="secondary" style={{ fontSize: 11 }}>Có Audio (US)</Text>
              <div style={{ fontSize: 24, fontWeight: 700, color: "#10b981" }}>{stats.has_audio_us}</div>
            </div>
            <div style={{ background: "var(--bg-surface, #fff)", borderRadius: 10, padding: 16, border: "1px solid var(--border-default, #eee)" }}>
              <Text type="secondary" style={{ fontSize: 11 }}>Có Audio (UK)</Text>
              <div style={{ fontSize: 24, fontWeight: 700, color: "#3b82f6" }}>{stats.has_audio_uk}</div>
            </div>
            <div style={{ background: "var(--bg-surface, #fff)", borderRadius: 10, padding: 16, border: "1px solid var(--border-default, #eee)" }}>
              <Text type="secondary" style={{ fontSize: 11 }}>Thiếu Audio</Text>
              <div style={{ fontSize: 24, fontWeight: 700, color: stats.missing > 0 ? "#ef4444" : "#10b981" }}>{stats.missing}</div>
            </div>
          </div>
        )}

        {/* Coverage bar */}
        {stats && (
          <div>
            <Text type="secondary" style={{ fontSize: 12 }}>Phủ sóng audio: {pctHasAudio}%</Text>
            <Progress
              percent={pctHasAudio}
              status={pctHasAudio === 100 ? "success" : "active"}
              strokeColor={{ "0%": "#6366f1", "100%": "#10b981" }}
            />
          </div>
        )}

        {/* Batch controls */}
        <div style={{
          display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap",
          background: "var(--bg-surface, #fff)", borderRadius: 10, padding: 16,
          border: "1px solid var(--border-default, #eee)"
        }}>
          <Text strong style={{ fontSize: 13 }}>⚡ Batch Generate:</Text>
          <InputNumber
            size="small" min={1} max={500}
            value={batchLimit}
            onChange={(v) => setBatchLimit(v || 50)}
            addonAfter="từ"
            style={{ width: 120 }}
          />
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <Switch
              size="small"
              checked={batchForce}
              onChange={setBatchForce}
            />
            <Text style={{ fontSize: 12 }}>Ghi đè</Text>
          </div>
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            onClick={startBatch}
            loading={batchRunning || progress?.running}
            disabled={batchRunning || progress?.running}
          >
            {(batchRunning || progress?.running) ? "Đang chạy..." : "Bắt đầu"}
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => { fetchStats(); fetchMissing(); fetchProgress(); }}
            size="small"
          >
            Refresh
          </Button>
        </div>

        {/* Batch progress */}
        {progress?.running && (
          <div style={{
            background: "var(--bg-surface, #fff)", borderRadius: 10, padding: 16,
            border: "1px solid #6366f1"
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
              <Text strong>🔄 Đang xử lý: <Text code>{progress.current_word}</Text></Text>
              <Text>{progress.done}/{progress.total} ({progress.success} ✓ · {progress.errors} ✗)</Text>
            </div>
            <Progress
              percent={Math.round((progress.done / Math.max(progress.total, 1)) * 100)}
              status="active"
              strokeColor="#6366f1"
            />
          </div>
        )}

        {/* Last batch errors */}
        {progress && !progress.running && progress.error_list && progress.error_list.length > 0 && (
          <div style={{
            background: "#fef2f2", borderRadius: 10, padding: 12,
            border: "1px solid #fecaca", fontSize: 12
          }}>
            <Text strong style={{ color: "#ef4444" }}>⚠️ Lỗi ({progress.errors}):</Text>
            <ul style={{ margin: "4px 0 0 16px", padding: 0 }}>
              {progress.error_list.slice(0, 10).map((err, i) => (
                <li key={i} style={{ color: "#991b1b" }}>{err}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Missing entries table */}
        <div>
          <Text strong style={{ fontSize: 13 }}>📋 Từ vựng chưa có audio ({totalMissing})</Text>
          <Table<MissingEntry>
            columns={columns}
            dataSource={items}
            rowKey="id"
            loading={loading}
            size="small"
            style={{ marginTop: 8 }}
            pagination={{
              current: page,
              total: totalMissing,
              pageSize: 50,
              onChange: (p) => setPage(p),
              showSizeChanger: false,
              showTotal: (total, range) => `${range[0]}-${range[1]} / ${total}`,
            }}
          />
        </div>
      </Space>
    </div>
  );
}
