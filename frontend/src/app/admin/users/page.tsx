"use client";

import { useState, useEffect, useCallback } from "react";
import { Table, Input, Tag, Typography, Space, Switch, Popconfirm, Segmented } from "antd";
import { SearchOutlined, CrownFilled, UserOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { adminGet, adminPut } from "@/lib/admin-api";
import InlineEditCell from "@/components/admin/InlineEditCell";

const { Title, Text } = Typography;

interface User {
  id: number; username: string; email: string;
  first_name: string; last_name: string;
  date_joined: string; is_active: boolean; is_staff: boolean;
}

type RoleFilter = "all" | "teacher" | "student";

export default function UsersPage() {
  const [items, setItems] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [roleFilter, setRoleFilter] = useState<RoleFilter>("all");

  const fetchData = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    params.set("page", String(page));
    adminGet<{ items: User[]; count: number }>(`/crud/users/?${params}`)
      .then((d) => { setItems(d.items || []); setTotalCount(d.count || 0); })
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [search, page]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const toggleUser = async (u: User, field: "is_active" | "is_staff") => {
    const payload = { is_active: u.is_active, is_staff: u.is_staff, [field]: !u[field] };
    await adminPut(`/crud/users/${u.id}/`, payload);
    fetchData();
  };

  // Filter by role
  const filteredItems = roleFilter === "all"
    ? items
    : roleFilter === "teacher"
      ? items.filter((u) => u.is_staff)
      : items.filter((u) => !u.is_staff);

  const teacherCount = items.filter((u) => u.is_staff).length;

  const columns: ColumnsType<User> = [
    { title: "ID", dataIndex: "id", width: 60, render: (id) => <Text type="secondary" style={{ fontSize: 12 }}>{id}</Text> },
    {
      title: "Username", dataIndex: "username",
      render: (_, u) => (
        <Space>
          <InlineEditCell
            value={u.username}
            style={{ fontWeight: 600 }}
            onSave={async (v) => { await adminPut(`/crud/users/${u.id}/`, { is_active: u.is_active, is_staff: u.is_staff, username: v }); fetchData(); }}
          />
          {u.is_staff && (
            <Tag icon={<CrownFilled />} color="gold" style={{ borderRadius: 20, fontWeight: 600, fontSize: 11 }}>
              Giáo viên
            </Tag>
          )}
        </Space>
      ),
    },
    {
      title: "Email", dataIndex: "email",
      render: (_, u) => (
        <InlineEditCell
          value={u.email}
          style={{ fontSize: 12 }}
          onSave={async (v) => { await adminPut(`/crud/users/${u.id}/`, { is_active: u.is_active, is_staff: u.is_staff, email: v }); fetchData(); }}
        />
      ),
    },
    {
      title: "Họ tên", key: "name",
      render: (_, u) => (
        <InlineEditCell
          value={`${u.first_name} ${u.last_name}`.trim()}
          onSave={async (v) => {
            const parts = v.split(" ");
            await adminPut(`/crud/users/${u.id}/`, { is_active: u.is_active, is_staff: u.is_staff, first_name: parts[0] || "", last_name: parts.slice(1).join(" ") || "" });
            fetchData();
          }}
        />
      ),
    },
    { title: "Ngày tham gia", dataIndex: "date_joined", width: 120, render: (d) => <Text style={{ fontSize: 12 }}>{new Date(d).toLocaleDateString("vi-VN")}</Text> },
    {
      title: "Giáo viên", dataIndex: "is_staff", width: 110, align: "center",
      render: (_, u) => (
        <Popconfirm
          title={u.is_staff ? "Thu hồi quyền giáo viên?" : "Gán quyền giáo viên?"}
          description={u.is_staff
            ? `${u.username} sẽ không còn quyền giáo viên (staff).`
            : `${u.username} sẽ được cấp quyền giáo viên (staff).`
          }
          okText={u.is_staff ? "Thu hồi" : "Gán quyền"}
          okType={u.is_staff ? "danger" : "primary"}
          cancelText="Huỷ"
          onConfirm={() => toggleUser(u, "is_staff")}
        >
          <Switch
            size="small"
            checked={u.is_staff}
            checkedChildren={<CrownFilled />}
            unCheckedChildren={<UserOutlined />}
          />
        </Popconfirm>
      ),
    },
    {
      title: "Active", dataIndex: "is_active", width: 80, align: "center",
      render: (_, u) => <Switch size="small" checked={u.is_active} onChange={() => toggleUser(u, "is_active")} />,
    },
  ];

  return (
    <div>
      <Space direction="vertical" size="large" style={{ width: "100%" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16 }}>
          <div>
            <Title level={3} style={{ margin: 0 }}>👤 Người dùng</Title>
            <Space style={{ marginTop: 4 }}>
              <Text type="secondary">{totalCount} tài khoản</Text>
              <Tag icon={<CrownFilled />} color="gold">{teacherCount} giáo viên</Tag>
            </Space>
          </div>

          <Segmented
            value={roleFilter}
            onChange={(v) => { setRoleFilter(v as RoleFilter); setPage(1); }}
            options={[
              { label: `Tất cả (${items.length})`, value: "all" },
              { label: `👨‍🏫 Giáo viên (${teacherCount})`, value: "teacher" },
              { label: `👨‍🎓 Học sinh (${items.length - teacherCount})`, value: "student" },
            ]}
          />
        </div>

        <Input.Search
          placeholder="Tìm user..."
          allowClear
          onSearch={(v) => { setSearch(v); setPage(1); }}
          onChange={(e) => { if (!e.target.value) { setSearch(""); setPage(1); } }}
          style={{ maxWidth: 400 }}
          prefix={<SearchOutlined />}
        />

        <Table<User>
          columns={columns}
          dataSource={filteredItems}
          rowKey="id"
          loading={loading}
          size="middle"
          pagination={{
            current: page,
            total: roleFilter === "all" ? totalCount : filteredItems.length,
            pageSize: 50,
            onChange: (p) => setPage(p),
            showSizeChanger: false,
            showTotal: (total, range) => `${range[0]}-${range[1]} / ${total}`,
          }}
        />
      </Space>
    </div>
  );
}
