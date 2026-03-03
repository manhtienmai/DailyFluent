"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Table, Button, Typography, Space, Tag, Select, InputNumber,
  message, Progress, Switch, Tooltip, Input
} from "antd";
import {
  SoundOutlined, PlayCircleOutlined, ThunderboltOutlined,
  ReloadOutlined, SearchOutlined
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

  useEffect(() => {
    fetchStats();
    fetchMissing();
  }, [fetchStats, fetchMissing]);

  // Poll progress while batch is running
  useEffect(() => {
    if (!progress?.running) return;
    const interval = setInterval(() => {
      fetchProgress();
    }, 2000);
    return () => clearInterval(interval);
  }, [progress?.running, fetchProgress]);

  const startBatch = async () => {
    try {
      const resp = await adminPost<{ success: boolean; message: string }>(
        "/crud/tts/generate-batch/",
        { language, limit: batchLimit, force: batchForce }
      );
      if (resp.success) {
        message.success(resp.message);
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
            loading={progress?.running}
            disabled={progress?.running}
          >
            {progress?.running ? "Đang chạy..." : "Bắt đầu"}
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
