"use client";

import { Layout, Button, Avatar, Dropdown, Switch, Space, Typography } from "antd";
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SunOutlined,
  MoonOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuOutlined,
} from "@ant-design/icons";
import { useAuth } from "@/lib/auth";

const { Header } = Layout;
const { Text } = Typography;

interface TopbarProps {
  collapsed: boolean;
  isDark: boolean;
  onToggleCollapsed: () => void;
  onToggleMobile: () => void;
  onToggleDark: () => void;
}

export default function AdminTopbar({
  collapsed,
  isDark,
  onToggleCollapsed,
  onToggleMobile,
  onToggleDark,
}: TopbarProps) {
  const { user, logout } = useAuth();

  const initials = user
    ? (user.first_name?.[0] || user.username?.[0] || "A").toUpperCase()
    : "A";

  return (
    <Header
      style={{
        position: "fixed",
        top: 0,
        right: 0,
        left: collapsed ? 80 : 240,
        zIndex: 150,
        display: "flex",
        alignItems: "center",
        padding: "0 24px",
        gap: 16,
        transition: "left 0.2s",
        boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
        borderBottom: "1px solid rgba(0,0,0,0.06)",
      }}
    >
      {/* Desktop toggle */}
      <Button
        type="text"
        icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
        onClick={onToggleCollapsed}
        className="desktop-toggle"
      />

      {/* Mobile toggle */}
      <Button
        type="text"
        icon={<MenuOutlined />}
        onClick={onToggleMobile}
        className="mobile-toggle"
        style={{ display: "none" }}
      />

      <div style={{ flex: 1 }} />

      <Space size="middle">
        {/* Theme toggle */}
        <Switch
          checked={isDark}
          onChange={onToggleDark}
          checkedChildren={<MoonOutlined />}
          unCheckedChildren={<SunOutlined />}
        />

        {/* User menu */}
        <Dropdown
          menu={{
            items: [
              {
                key: "logout",
                icon: <LogoutOutlined />,
                label: "Đăng xuất",
                danger: true,
                onClick: logout,
              },
            ],
          }}
          trigger={["click"]}
        >
          <Space style={{ cursor: "pointer" }}>
            <Avatar
              src={user?.avatar_url || undefined}
              icon={!user?.avatar_url ? <UserOutlined /> : undefined}
              style={{ background: "#6366f1" }}
            >
              {!user?.avatar_url && initials}
            </Avatar>
            <Text strong style={{ fontSize: 13 }}>
              {user?.first_name || user?.username || "Admin"}
            </Text>
          </Space>
        </Dropdown>
      </Space>
    </Header>
  );
}
