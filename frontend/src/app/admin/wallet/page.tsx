"use client";
import { useState, useEffect, useCallback } from "react";
import { Table, Button, Tag, Modal, InputNumber, Tabs, Typography, Space } from "antd";
import { EditOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { adminGet, adminPut } from "@/lib/admin-api";

const { Title, Text } = Typography;

interface Wallet { id: number; username: string; coins: number; }
interface Transaction { id: number; username: string; amount: number; balance_after: number; transaction_type: string; description: string; created_at: string; }

export default function WalletPage() {
  const [tab, setTab] = useState<"wallets" | "transactions">("wallets");
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [showEdit, setShowEdit] = useState(false);
  const [editingWallet, setEditingWallet] = useState<Wallet | null>(null);
  const [coins, setCoins] = useState(0);

  const fetchWallets = useCallback(() => { setLoading(true); adminGet<{ items: Wallet[] }>("/crud/wallet/wallets/").then(d => setWallets(d.items || [])).catch(() => setWallets([])).finally(() => setLoading(false)); }, []);
  const fetchTransactions = useCallback(() => { setLoading(true); adminGet<{ items: Transaction[] }>("/crud/wallet/transactions/").then(d => setTransactions(d.items || [])).catch(() => setTransactions([])).finally(() => setLoading(false)); }, []);
  useEffect(() => { if (tab === "wallets") fetchWallets(); else fetchTransactions(); }, [tab, fetchWallets, fetchTransactions]);

  const openEdit = (w: Wallet) => { setEditingWallet(w); setCoins(w.coins); setShowEdit(true); };
  const saveCoins = async () => { if (!editingWallet) return; await adminPut(`/crud/wallet/wallets/${editingWallet.id}/`, { coins }); setShowEdit(false); fetchWallets(); };

  const walletCols: ColumnsType<Wallet> = [
    { title: "ID", dataIndex: "id", width: 60, render: (id) => <Text type="secondary" style={{ fontSize: 12 }}>{id}</Text> },
    { title: "User", dataIndex: "username", render: (u) => <Text strong>{u}</Text> },
    { title: "Coins", dataIndex: "coins", width: 120, render: (c) => <Tag color={c >= 100 ? "success" : c >= 50 ? "warning" : "error"}>🪙 {c}</Tag> },
    { title: "", key: "actions", width: 120, render: (_, w) => <Button size="small" type="text" icon={<EditOutlined />} onClick={() => openEdit(w)}>Sửa coins</Button> },
  ];

  const txCols: ColumnsType<Transaction> = [
    { title: "ID", dataIndex: "id", width: 60, render: (id) => <Text type="secondary" style={{ fontSize: 12 }}>{id}</Text> },
    { title: "User", dataIndex: "username", render: (u) => <Text strong>{u}</Text> },
    { title: "Số lượng", dataIndex: "amount", width: 90, render: (a) => <Text strong style={{ color: a > 0 ? "#10b981" : "#ef4444" }}>{a > 0 ? "+" : ""}{a}</Text> },
    { title: "Sau GD", dataIndex: "balance_after", width: 80 },
    { title: "Loại", dataIndex: "transaction_type", width: 100, render: (t) => <Tag color="processing">{t}</Tag> },
    { title: "Mô tả", dataIndex: "description", ellipsis: true, render: (d) => <Text style={{ fontSize: 12 }}>{d}</Text> },
    { title: "Ngày", dataIndex: "created_at", width: 100, render: (d) => <Text style={{ fontSize: 12 }}>{new Date(d).toLocaleDateString("vi-VN")}</Text> },
  ];

  return (
    <div>
      <Space orientation="vertical" size="large" style={{ width: "100%" }}>
        <div><Title level={3} style={{ margin: 0 }}>🪙 Ví & Coin</Title><Text type="secondary">Quản lý ví</Text></div>
        <Tabs activeKey={tab} onChange={(k) => setTab(k as "wallets" | "transactions")} items={[
          { key: "wallets", label: "🪙 Ví" },
          { key: "transactions", label: "📋 Lịch sử" },
        ]} />
        {tab === "wallets" && <Table<Wallet> columns={walletCols} dataSource={wallets} rowKey="id" loading={loading} size="middle" pagination={false} />}
        {tab === "transactions" && <Table<Transaction> columns={txCols} dataSource={transactions} rowKey="id" loading={loading} size="middle" pagination={{ pageSize: 50, showSizeChanger: false }} />}
      </Space>
      <Modal title={`✏️ Sửa coins — ${editingWallet?.username || ""}`} open={showEdit} onCancel={() => setShowEdit(false)} onOk={saveCoins} okText="💾 Lưu" width={360}>
        <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Số coins</Text><InputNumber value={coins} onChange={v => setCoins(v || 0)} style={{ width: "100%" }} /></div>
      </Modal>
    </div>
  );
}
