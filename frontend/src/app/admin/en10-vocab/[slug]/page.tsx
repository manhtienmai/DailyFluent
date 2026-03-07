"use client";

import { useEffect, useState } from "react";
import {
  Card, Table, Button, Space, Tag, Typography, Breadcrumb,
  Popconfirm, message, Input, Spin,
} from "antd";
import {
  DeleteOutlined, SoundOutlined, SearchOutlined, ArrowLeftOutlined,
} from "@ant-design/icons";
import { useParams, useRouter } from "next/navigation";

const { Title, Text } = Typography;
const API = process.env.NEXT_PUBLIC_API_URL || "";

interface VocabWord {
  word: string;
  pos: string;
  ipa: string;
  meaning: string;
  audio_us?: string;
  audio_uk?: string;
}

interface TopicData {
  slug: string;
  title: string;
  title_vi: string;
  emoji: string;
  word_count: number;
  words: VocabWord[];
}

export default function AdminEN10VocabDetailPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  const [topic, setTopic] = useState<TopicData | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const fetchTopic = async () => {
    try {
      const res = await fetch(`${API}/api/v1/exam/english/vocab-topics/${slug}`, { credentials: "include" });
      if (res.ok) {
        setTopic(await res.json());
      }
    } catch {
      message.error("Không thể tải dữ liệu");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchTopic(); }, [slug]);

  const handleDelete = async (word: string) => {
    setDeleting(word);
    try {
      const res = await fetch(
        `${API}/api/v1/exam/english/vocab-topics/${slug}/words/${encodeURIComponent(word)}`,
        { method: "DELETE", credentials: "include" },
      );
      if (res.ok) {
        message.success(`Đã xóa "${word}"`);
        // Update state locally without reload
        setTopic((prev) => {
          if (!prev) return prev;
          const updatedWords = prev.words.filter((w) => w.word !== word);
          return { ...prev, words: updatedWords, word_count: updatedWords.length };
        });
      } else {
        const data = await res.json().catch(() => ({}));
        message.error(data.detail || "Không thể xóa từ này");
      }
    } catch {
      message.error("Lỗi kết nối");
    } finally {
      setDeleting(null);
    }
  };

  const playAudio = (w: VocabWord) => {
    const url = w.audio_us || w.audio_uk;
    if (url) {
      new Audio(url).play().catch(() => {});
    } else if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(w.word);
      u.lang = "en-US";
      u.rate = 0.9;
      window.speechSynthesis.speak(u);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!topic) {
    return <Text type="danger">Không tìm thấy chủ đề</Text>;
  }

  const filteredWords = topic.words.filter((w) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return w.word.toLowerCase().includes(q) || w.meaning.toLowerCase().includes(q);
  });

  const columns = [
    {
      title: "STT",
      key: "stt",
      width: 60,
      render: (_: unknown, __: unknown, idx: number) => idx + 1,
    },
    {
      title: "Từ vựng",
      dataIndex: "word",
      key: "word",
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: "Loại",
      dataIndex: "pos",
      key: "pos",
      width: 120,
      render: (pos: string) => <Tag>{pos}</Tag>,
    },
    {
      title: "Phiên âm",
      dataIndex: "ipa",
      key: "ipa",
      render: (ipa: string) => <Text type="secondary" italic>{ipa}</Text>,
    },
    {
      title: "Nghĩa",
      dataIndex: "meaning",
      key: "meaning",
    },
    {
      title: "",
      key: "actions",
      width: 100,
      render: (_: unknown, record: VocabWord) => (
        <Space>
          <Button
            type="text"
            icon={<SoundOutlined />}
            size="small"
            onClick={() => playAudio(record)}
          />
          <Popconfirm
            title={`Xóa "${record.word}"?`}
            description="Từ sẽ bị gỡ khỏi chủ đề này"
            onConfirm={() => handleDelete(record.word)}
            okText="Xóa"
            cancelText="Hủy"
            okButtonProps={{ danger: true }}
          >
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              size="small"
              loading={deleting === record.word}
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Breadcrumb
        style={{ marginBottom: 16 }}
        items={[
          { title: "Admin" },
          { title: <a onClick={() => router.push("/admin/en10-vocab")}>EN10 Vocab Topics</a> },
          { title: topic.title },
        ]}
      />

      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => router.push("/admin/en10-vocab")}
        />
        <Title level={3} style={{ margin: 0 }}>
          {topic.emoji} {topic.title}
          <Text type="secondary" style={{ fontSize: 16, marginLeft: 8 }}>
            ({topic.title_vi} — {topic.word_count} từ)
          </Text>
        </Title>
      </div>

      <Card>
        <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <Input
            placeholder="Tìm từ vựng..."
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ maxWidth: 300 }}
            allowClear
          />
          <Text type="secondary">
            {filteredWords.length} / {topic.words.length} từ
          </Text>
        </div>

        <Table
          columns={columns}
          dataSource={filteredWords}
          rowKey="word"
          size="middle"
          pagination={{ pageSize: 50, showSizeChanger: false }}
        />
      </Card>
    </div>
  );
}
