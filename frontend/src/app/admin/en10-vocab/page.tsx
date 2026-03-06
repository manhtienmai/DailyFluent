"use client";

import { useEffect, useState } from "react";
import { Card, Table, Typography, Spin, Button } from "antd";
import { EyeOutlined } from "@ant-design/icons";
import { useRouter } from "next/navigation";

const { Title, Text } = Typography;
const API = process.env.NEXT_PUBLIC_API_URL || "";

interface VocabTopic {
  slug: string;
  title: string;
  title_vi: string;
  emoji: string;
  word_count: number;
}

export default function AdminEN10VocabListPage() {
  const router = useRouter();
  const [topics, setTopics] = useState<VocabTopic[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/v1/exam/english/vocab-topics`, { credentials: "include" })
      .then((r) => r.json())
      .then((data) => setTopics(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  const columns = [
    {
      title: "",
      dataIndex: "emoji",
      key: "emoji",
      width: 50,
      render: (emoji: string) => <span style={{ fontSize: 20 }}>{emoji}</span>,
    },
    {
      title: "Chủ đề",
      dataIndex: "title",
      key: "title",
      render: (title: string, record: VocabTopic) => (
        <div>
          <Text strong>{title}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>{record.title_vi}</Text>
        </div>
      ),
    },
    {
      title: "Slug",
      dataIndex: "slug",
      key: "slug",
      render: (slug: string) => <Text code>{slug}</Text>,
    },
    {
      title: "Số từ",
      dataIndex: "word_count",
      key: "word_count",
      width: 80,
      align: "center" as const,
    },
    {
      title: "",
      key: "actions",
      width: 100,
      render: (_: unknown, record: VocabTopic) => (
        <Button
          type="primary"
          icon={<EyeOutlined />}
          size="small"
          onClick={() => router.push(`/admin/en10-vocab/${record.slug}`)}
        >
          Quản lý
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Title level={3} style={{ marginBottom: 24 }}>
        📚 EN10 Vocab Topics
        <Text type="secondary" style={{ fontSize: 14, marginLeft: 8 }}>
          ({topics.length} chủ đề)
        </Text>
      </Title>

      <Card>
        <Table
          columns={columns}
          dataSource={topics}
          rowKey="slug"
          size="middle"
          pagination={false}
        />
      </Card>
    </div>
  );
}
