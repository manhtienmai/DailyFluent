"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Table, Input, Tag, Button, Typography, Space, Popconfirm,
  Select, InputNumber, message, Tooltip
} from "antd";
import { SearchOutlined, CrownFilled, LockOutlined, GiftOutlined, StopOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { adminGet, adminPost } from "@/lib/admin-api";

const { Title, Text } = Typography;

interface VipUser {
  id: number;
  username: string;
  email: string;
  full_name: string;
  is_vip: boolean;
  sub_active: boolean;
  end_date: string | null;
  plan_name: string;
  date_joined: string;
}

const DURATION_OPTIONS = [
  { value: 30, label: "30 ngày" },
  { value: 90, label: "90 ngày" },
  { value: 180, label: "6 tháng" },
  { value: 365, label: "1 năm" },
  { value: 730, label: "2 năm" },
  { value: 3650, label: "10 năm (vĩnh viễn)" },
];

export default function VipManagementPage() {
  const [items, setItems] = useState<VipUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [granting, setGranting] = useState<number | null>(null);
  const [grantDays, setGrantDays] = useState(365);

  const fetchData = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    params.set("filter", filter);
    params.set("page", String(page));
    adminGet<{ items: VipUser[]; count: number }>(`/crud/vip/users/?${params}`)
      .then((d) => {
        setItems(d.items || []);
        setTotalCount(d.count || 0);
      })
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [search, filter, page]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const grantVip = async (userId: number, days: number) => {
    try {
      await adminPost(`/crud/vip/grant/${userId}/`, { duration_days: days });
      message.success(`Đã cấp VIP ${days} ngày thành công!`);
      setGranting(null);
      fetchData();
    } catch {
      message.error("Lỗi khi cấp VIP");
    }
  };

  const revokeVip = async (userId: number) => {
    try {
      await adminPost(`/crud/vip/revoke/${userId}/`, {});
      message.success("Đã thu hồi VIP");
      fetchData();
    } catch {
      message.error("Lỗi khi thu hồi VIP");
    }
  };

  const vipCount = items.filter(u => u.is_vip).length;

  const columns: ColumnsType<VipUser> = [
    {
      title: "ID", dataIndex: "id", width: 55,
      render: (id) => <Text type="secondary" style={{ fontSize: 12 }}>{id}</Text>,
    },
    {
      title: "User", dataIndex: "username",
      render: (_, u) => (
        <div>
          <Text strong style={{ fontSize: 13 }}>{u.username}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 11 }}>{u.email}</Text>
        </div>
      ),
    },
    {
      title: "Họ tên", dataIndex: "full_name", width: 140,
      render: (name) => <Text style={{ fontSize: 12 }}>{name}</Text>,
    },
    {
      title: "VIP", dataIndex: "is_vip", width: 90, align: "center",
      render: (isVip) =>
        isVip ? (
          <Tag icon={<CrownFilled />} color="gold" style={{ fontWeight: 600 }}>VIP</Tag>
        ) : (
          <Tag icon={<LockOutlined />} color="default">Free</Tag>
        ),
    },
    {
      title: "Hết hạn", dataIndex: "end_date", width: 110,
      render: (d) => {
        if (!d) return <Text type="secondary" style={{ fontSize: 11 }}>—</Text>;
        const endDate = new Date(d);
        const today = new Date();
        const daysLeft = Math.ceil((endDate.getTime() - today.getTime()) / (1000 * 86400));
        const isExpired = daysLeft < 0;
        return (
          <Tooltip title={`${daysLeft > 0 ? `Còn ${daysLeft} ngày` : `Hết hạn ${Math.abs(daysLeft)} ngày trước`}`}>
            <Text
              style={{ fontSize: 12 }}
              type={isExpired ? "danger" : daysLeft < 7 ? "warning" : undefined}
            >
              {endDate.toLocaleDateString("vi-VN")}
            </Text>
          </Tooltip>
        );
      },
    },
    {
      title: "Gói", dataIndex: "plan_name", width: 130,
      render: (p) => <Text style={{ fontSize: 11 }} type="secondary">{p}</Text>,
    },
    {
      title: "Thao tác", key: "actions", width: 200, align: "center",
      render: (_, u) => {
        if (granting === u.id) {
          return (
            <Space size="small" wrap>
              <InputNumber
                size="small"
                value={grantDays}
                onChange={(v) => setGrantDays(v || 365)}
                min={1}
                max={3650}
                style={{ width: 70 }}
                addonAfter="d"
              />
              <Button
                size="small" type="primary"
                onClick={() => grantVip(u.id, grantDays)}
                icon={<GiftOutlined />}
              >
                Cấp
              </Button>
              <Button size="small" onClick={() => setGranting(null)}>Hủy</Button>
            </Space>
          );
        }

        return (
          <Space size="small">
            {u.is_vip ? (
              <>
                <Button
                  size="small" type="default"
                  icon={<GiftOutlined />}
                  onClick={() => { setGranting(u.id); setGrantDays(365); }}
                >
                  Gia hạn
                </Button>
                <Popconfirm
                  title="Thu hồi VIP?"
                  description={`${u.username} sẽ mất quyền truy cập đề thi`}
                  onConfirm={() => revokeVip(u.id)}
                  okText="Thu hồi"
                  cancelText="Hủy"
                  okButtonProps={{ danger: true }}
                >
                  <Button size="small" danger icon={<StopOutlined />}>
                    Thu hồi
                  </Button>
                </Popconfirm>
              </>
            ) : (
              <Button
                size="small" type="primary"
                icon={<CrownFilled />}
                onClick={() => { setGranting(u.id); setGrantDays(365); }}
                style={{ backgroundColor: "#faad14", borderColor: "#faad14" }}
              >
                Cấp VIP
              </Button>
            )}
          </Space>
        );
      },
    },
  ];

  return (
    <div>
      <Space direction="vertical" size="large" style={{ width: "100%" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <Title level={3} style={{ margin: 0 }}>👑 Quản lý VIP</Title>
            <Text type="secondary">
              {totalCount} tài khoản · <Text strong style={{ color: "#faad14" }}>{vipCount} VIP</Text>
            </Text>
          </div>

          {/* Quick grant presets */}
          <Space size="small">
            {DURATION_OPTIONS.slice(0, 4).map(opt => (
              <Tooltip key={opt.value} title={`Cấp VIP ${opt.label} cho user đã chọn`}>
                <Button
                  size="small"
                  type="default"
                  style={{ fontSize: 11 }}
                  onClick={() => setGrantDays(opt.value)}
                  className={grantDays === opt.value ? "ant-btn-primary" : ""}
                >
                  {opt.label}
                </Button>
              </Tooltip>
            ))}
          </Space>
        </div>

        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <Input.Search
            placeholder="Tìm user (username, email, tên)..."
            allowClear
            onSearch={(v) => { setSearch(v); setPage(1); }}
            onChange={(e) => { if (!e.target.value) { setSearch(""); setPage(1); } }}
            style={{ maxWidth: 350 }}
            prefix={<SearchOutlined />}
          />
          <Select
            value={filter}
            onChange={(v) => { setFilter(v); setPage(1); }}
            style={{ width: 150 }}
            options={[
              { value: "all", label: "Tất cả" },
              { value: "vip", label: "👑 Chỉ VIP" },
              { value: "non_vip", label: "🔒 Chưa VIP" },
            ]}
          />
        </div>

        <Table<VipUser>
          columns={columns}
          dataSource={items}
          rowKey="id"
          loading={loading}
          size="middle"
          rowClassName={(u) => u.is_vip ? "vip-row" : ""}
          pagination={{
            current: page,
            total: totalCount,
            pageSize: 50,
            onChange: (p) => setPage(p),
            showSizeChanger: false,
            showTotal: (total, range) => `${range[0]}-${range[1]} / ${total}`,
          }}
        />
      </Space>

      <style jsx global>{`
        .vip-row {
          background: linear-gradient(90deg, rgba(250,173,20,0.04) 0%, transparent 100%) !important;
        }
        .vip-row:hover > td {
          background: rgba(250,173,20,0.08) !important;
        }
      `}</style>
    </div>
  );
}
