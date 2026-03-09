"use client";

import { useState, useCallback, useEffect } from "react";
import {
  Steps,
  Upload,
  Button,
  Select,
  InputNumber,
  Table,
  Input,
  Tag,
  Typography,
  Card,
  Row,
  Col,
  Space,
  message,
  Spin,
  Alert,
  Tooltip,
  Image,
  Popconfirm,
  Result,
  Statistic,
  Collapse,
  Modal,
  Divider,
  Badge,
} from "antd";
import {
  UploadOutlined,
  RobotOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  DeleteOutlined,
  PlusOutlined,
  ArrowLeftOutlined,
  ArrowRightOutlined,
  ImportOutlined,
  FileImageOutlined,
  CopyOutlined,
  EditOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
  DownloadOutlined,
  CloseCircleOutlined,
  SafetyCertificateOutlined,
  HistoryOutlined,
} from "@ant-design/icons";
import { adminUpload, adminPost, adminGet } from "@/lib/admin-api";

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Dragger } = Upload;

const JLPT_LEVELS = ["N5", "N4", "N3", "N2", "N1"];

/* ── Types ────────────────────────────────────────────────── */

interface KanjiExample {
  word: string;
  hiragana: string;
  meaning: string;
  jlpt: string;
}

interface KanjiItem {
  character: string;
  han_viet: string;
  onyomi: string[];
  kunyomi: string[];
  meaning_vi: string;
  formation: string;
  uncertain: boolean;
  uncertain_note: string;
  examples: KanjiExample[];
}

interface PageData {
  kanji_list: KanjiItem[];
  topic: string;
  extracted: boolean;
  extracting: boolean;
  error: string;
}

/* ── Main Component ───────────────────────────────────────── */

export default function KanjiPdfImportPage() {
  const [currentStep, setCurrentStep] = useState(0);

  // Step 1 state
  const [sessionId, setSessionId] = useState("");
  const [pageCount, setPageCount] = useState(0);
  const [thumbnails, setThumbnails] = useState<string[]>([]);
  const [jlptLevel, setJlptLevel] = useState("N3");
  const [startingLesson, setStartingLesson] = useState(1);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");

  // Page range for heavy PDFs
  const [pageFrom, setPageFrom] = useState(1);
  const [pageTo, setPageTo] = useState(1);

  // Session history
  const [savedSessions, setSavedSessions] = useState<any[]>([]);
  const [loadingSession, setLoadingSession] = useState(false);

  // Step 2 state
  const [currentPage, setCurrentPage] = useState(0);
  const [pagesData, setPagesData] = useState<PageData[]>([]);
  const [pageImages, setPageImages] = useState<Record<number, string>>({});

  // JSON paste modal (single page)
  const [jsonModalOpen, setJsonModalOpen] = useState(false);
  const [jsonText, setJsonText] = useState("");
  const [jsonError, setJsonError] = useState("");

  // Batch JSON paste modal (all pages at once)
  const [batchModalOpen, setBatchModalOpen] = useState(false);
  const [batchJsonText, setBatchJsonText] = useState("");
  const [batchJsonError, setBatchJsonError] = useState("");

  // Auto-load from server
  const [loadingAiData, setLoadingAiData] = useState(false);

  // Step 3 state
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<any>(null);
  const [importError, setImportError] = useState("");

  /* ── Step 1: Upload PDF ──────────────────────────────────── */

  const handleUpload = useCallback(async (file: File) => {
    setUploading(true);
    setUploadError("");
    const formData = new FormData();
    formData.append("pdf_file", file);

    try {
      const res = await adminUpload<any>("/crud/kanji-pdf/upload/", formData);
      if (res.success) {
        setSessionId(res.session_id);
        setPageCount(res.page_count);
        setThumbnails(res.thumbnails);
        setPageFrom(1);
        setPageTo(res.page_count);
        message.success(
          `Upload thành công: ${res.page_count} trang — Session: ${res.session_id}`
        );
        message.info(
          `Hãy nói với Antigravity: "session_id: ${res.session_id}, xử lý trang 1-${res.page_count}"`,
          8
        );
      } else {
        setUploadError(res.message || "Upload thất bại");
      }
    } catch (e: any) {
      setUploadError("Upload lỗi: " + e.message);
    } finally {
      setUploading(false);
    }
    return false;
  }, []);

  /* ── Load saved sessions on mount ──────────────────────── */

  useEffect(() => {
    adminGet<any>("/crud/kanji-pdf/sessions/").then((res) => {
      if (res.success) setSavedSessions(res.sessions || []);
    }).catch(() => {});
  }, []);

  const loadSession = async (sid: string) => {
    setLoadingSession(true);
    try {
      const res = await adminGet<any>(`/crud/kanji-pdf/session/${sid}/`);
      if (res.success) {
        setSessionId(res.session_id);
        setPageCount(res.page_count);
        setThumbnails(res.thumbnails);
        setPageFrom(1);
        setPageTo(res.page_count);
        message.success(`Đã load session: ${res.filename} (${res.page_count} trang)`);
      } else {
        message.error(res.message || "Không load được session");
      }
    } catch (e: any) {
      message.error("Lỗi: " + e.message);
    } finally {
      setLoadingSession(false);
    }
  };

  // Number of working pages based on selected range
  const workingPageCount = Math.max(0, pageTo - pageFrom + 1);

  // Map working page index → real page index
  const realPageIndex = (workIdx: number) => pageFrom - 1 + workIdx;

  const startWorking = () => {
    setPagesData(
      Array.from({ length: workingPageCount }, () => ({
        kanji_list: [],
        topic: "",
        extracted: false,
        extracting: false,
        error: "",
      }))
    );
    setCurrentPage(0);
    setCurrentStep(1);
  };

  /* ── Step 2: Download page image ─────────────────────────── */

  const downloadPageImage = (workIdx: number) => {
    const realIdx = realPageIndex(workIdx);
    const imgSrc = pageImages[realIdx] || thumbnails[realIdx];
    if (!imgSrc) return;
    const link = document.createElement("a");
    link.href = imgSrc;
    link.download = `kanji_page_${realIdx + 1}.png`;
    link.click();
  };

  /* ── Step 2: Paste JSON ──────────────────────────────────── */

  const openJsonModal = (pageIdx: number) => {
    setJsonText("");
    setJsonError("");
    setJsonModalOpen(true);
  };

  const applyJsonData = () => {
    setJsonError("");
    let text = jsonText.trim();

    // Strip markdown code fences if present
    if (text.startsWith("```")) {
      const lines = text.split("\n");
      text = lines.slice(1, -1).join("\n");
    }

    try {
      const data = JSON.parse(text);

      // Support multiple formats:
      // 1. Full format: { kanji_list: [...] }
      // 2. Array format: [{ character: "...", ... }]
      // 3. Single lesson format: { jlpt_level: ..., kanji_list: [...] }
      let kanjiList: KanjiItem[] = [];

      if (Array.isArray(data)) {
        kanjiList = data;
      } else if (data.kanji_list && Array.isArray(data.kanji_list)) {
        kanjiList = data.kanji_list;
      } else {
        setJsonError(
          "JSON format không đúng. Cần: { kanji_list: [...] } hoặc [{ character: ... }]"
        );
        return;
      }

      // Validate basic structure
      if (kanjiList.length === 0) {
        setJsonError("kanji_list rỗng");
        return;
      }

      const first = kanjiList[0];
      if (!first.character) {
        setJsonError(
          'Mỗi kanji cần có trường "character". VD: {"character": "日", "han_viet": "Nhật", ...}'
        );
        return;
      }

      // Ensure all items have required defaults
      kanjiList = kanjiList.map((k) => ({
        character: k.character || "",
        han_viet: k.han_viet || "",
        onyomi: Array.isArray(k.onyomi) ? k.onyomi : [],
        kunyomi: Array.isArray(k.kunyomi) ? k.kunyomi : [],
        meaning_vi: k.meaning_vi || "",
        formation: k.formation || "",
        uncertain: k.uncertain || false,
        uncertain_note: k.uncertain_note || "",
        examples: Array.isArray(k.examples)
          ? k.examples.map((ex: any) => ({
              word: ex.word || "",
              hiragana: ex.hiragana || "",
              meaning: ex.meaning || "",
              jlpt: ex.jlpt || "N3",
            }))
          : [],
      }));

      setPagesData((prev) => {
        const copy = [...prev];
        copy[currentPage] = {
          ...copy[currentPage],
          kanji_list: kanjiList,
          topic:
            data.topic ||
            copy[currentPage].topic ||
            `Bài ${startingLesson + currentPage}`,
          extracted: true,
          extracting: false,
          error: "",
        };
        return copy;
      });

      setJsonModalOpen(false);
      message.success(`Đã nhập ${kanjiList.length} kanji cho trang ${realPageIndex(currentPage) + 1}`);
    } catch (e: any) {
      setJsonError(`JSON parse error: ${e.message}`);
    }
  };

  /* ── Batch paste (all pages at once) ──────────────────────── */

  const openBatchModal = () => {
    setBatchJsonText("");
    setBatchJsonError("");
    setBatchModalOpen(true);
  };

  const applyBatchJsonData = () => {
    setBatchJsonError("");
    let text = batchJsonText.trim();

    // Strip markdown code fences
    if (text.startsWith("```")) {
      const lines = text.split("\n");
      text = lines.slice(1, -1).join("\n");
    }

    try {
      const data = JSON.parse(text);

      // Support formats:
      // 1. { pages: [ { kanji_list: [...], topic: "..." }, ... ] }
      // 2. [ { kanji_list: [...], topic: "..." }, ... ]
      // 3. [ { character: "...", ... }, ... ]  (single page, same as single paste)
      let pages: Array<{ kanji_list: KanjiItem[]; topic?: string }> = [];

      if (Array.isArray(data)) {
        if (data.length > 0 && data[0].kanji_list) {
          // Array of page objects
          pages = data;
        } else if (data.length > 0 && data[0].character) {
          // Single flat array → treat as one page
          pages = [{ kanji_list: data }];
        }
      } else if (data.pages && Array.isArray(data.pages)) {
        pages = data.pages;
      } else if (data.kanji_list) {
        // Single page object
        pages = [data];
      } else {
        setBatchJsonError(
          'Format: { pages: [ { kanji_list: [...], topic: "..." } ] } hoặc [ { kanji_list: [...] } ]'
        );
        return;
      }

      if (pages.length === 0) {
        setBatchJsonError("Không có dữ liệu trang nào");
        return;
      }

      if (pages.length > workingPageCount) {
        setBatchJsonError(
          `JSON có ${pages.length} trang nhưng chỉ đang xử lý ${workingPageCount} trang. Giảm số trang trong JSON hoặc mở rộng phạm vi.`
        );
        return;
      }

      // Normalize and apply
      setPagesData((prev) => {
        const copy = [...prev];
        pages.forEach((pageObj, i) => {
          if (i >= copy.length) return;
          const kanjiList = (pageObj.kanji_list || []).map((k: any) => ({
            character: k.character || "",
            han_viet: k.han_viet || "",
            onyomi: Array.isArray(k.onyomi) ? k.onyomi : [],
            kunyomi: Array.isArray(k.kunyomi) ? k.kunyomi : [],
            meaning_vi: k.meaning_vi || "",
            formation: k.formation || "",
            uncertain: k.uncertain || false,
            uncertain_note: k.uncertain_note || "",
            examples: Array.isArray(k.examples)
              ? k.examples.map((ex: any) => ({
                  word: ex.word || "",
                  hiragana: ex.hiragana || "",
                  meaning: ex.meaning || "",
                  jlpt: ex.jlpt || "N3",
                }))
              : [],
          }));
          copy[i] = {
            kanji_list: kanjiList,
            topic: pageObj.topic || `Bài ${startingLesson + i}`,
            extracted: kanjiList.length > 0,
            extracting: false,
            error: "",
          };
        });
        return copy;
      });

      const totalK = pages.reduce(
        (s, p) => s + (p.kanji_list?.length || 0),
        0
      );
      setBatchModalOpen(false);
      message.success(
        `Đã nhập ${totalK} kanji cho ${pages.length} trang!`
      );
    } catch (e: any) {
      setBatchJsonError(`JSON parse error: ${e.message}`);
    }
  };

  /* ── AI Verify: copy data + prompt for Antigravity ────────── */

  const copyForAiVerify = () => {
    const pagesWithData = pagesData
      .map((p, i) => ({ ...p, pageNum: realPageIndex(i) + 1 }))
      .filter((p) => p.extracted && p.kanji_list.length > 0);

    if (pagesWithData.length === 0) {
      message.warning("Chưa có dữ liệu kanji nào để kiểm tra");
      return;
    }

    const dataForVerify = {
      pages: pagesWithData.map((p) => ({
        topic: p.topic,
        kanji_list: p.kanji_list.map((k) => ({
          character: k.character,
          han_viet: k.han_viet,
          onyomi: k.onyomi,
          kunyomi: k.kunyomi,
          meaning_vi: k.meaning_vi,
          formation: k.formation,
          examples: k.examples,
        })),
      })),
    };

    const prompt = `Hãy kiểm tra và sửa lại dữ liệu kanji sau. Với mỗi kanji, kiểm tra:
1. Âm Hán Việt có CHÍNH XÁC không (ví dụ: 日=Nhật, 月=Nguyệt, 火=Hỏa)
2. Onyomi (katakana) và Kunyomi (hiragana) có đúng không
3. Nghĩa tiếng Việt có chính xác không
4. Từ vựng mẫu: từ, cách đọc, nghĩa có đúng không
5. Cấp JLPT của từ vựng có hợp lý không

Nếu phát hiện lỗi, hãy sửa trực tiếp. Đánh dấu "uncertain": true và "uncertain_note" cho từ nào bạn không chắc chắn 100%.

Trả về JSON THUẦN (không markdown) cùng format, chỉ sửa những chỗ sai:

${JSON.stringify(dataForVerify, null, 2)}`;

    navigator.clipboard.writeText(prompt).then(() => {
      message.success(
        "Đã copy dữ liệu + prompt kiểm tra. Paste cho Antigravity để verify!",
        5
      );
    }).catch(() => {
      setBatchJsonText(prompt);
      setBatchModalOpen(true);
      message.info("Không thể copy tự động. Hãy copy thủ công từ modal.");
    });
  };

  /* ── Auto-load extracted data from server ───────────────── */

  const loadAiExtractedData = async () => {
    if (!sessionId) {
      message.error("Không có session_id");
      return;
    }
    setLoadingAiData(true);
    try {
      const res = await adminGet<any>(
        `/crud/kanji-pdf/load-extracted/${sessionId}/`
      );
      if (res.success && res.data) {
        const data = res.data;
        let pages: Array<{ kanji_list: any[]; topic?: string }> = [];

        if (Array.isArray(data)) {
          if (data.length > 0 && data[0].kanji_list) pages = data;
          else if (data.length > 0 && data[0].character)
            pages = [{ kanji_list: data }];
        } else if (data.pages) {
          pages = data.pages;
        } else if (data.kanji_list) {
          pages = [data];
        }

        if (pages.length === 0) {
          message.warning("File extracted.json rỗng");
          setLoadingAiData(false);
          return;
        }

        setPagesData((prev) => {
          const copy = [...prev];
          pages.forEach((pageObj, i) => {
            if (i >= copy.length) return;
            const kanjiList = (pageObj.kanji_list || []).map((k: any) => ({
              character: k.character || "",
              han_viet: k.han_viet || "",
              onyomi: Array.isArray(k.onyomi) ? k.onyomi : [],
              kunyomi: Array.isArray(k.kunyomi) ? k.kunyomi : [],
              meaning_vi: k.meaning_vi || "",
              formation: k.formation || "",
              uncertain: k.uncertain || false,
              uncertain_note: k.uncertain_note || "",
              examples: Array.isArray(k.examples)
                ? k.examples.map((ex: any) => ({
                    word: ex.word || "",
                    hiragana: ex.hiragana || "",
                    meaning: ex.meaning || "",
                    jlpt: ex.jlpt || "N3",
                  }))
                : [],
            }));
            copy[i] = {
              kanji_list: kanjiList,
              topic: pageObj.topic || `Bài ${startingLesson + i}`,
              extracted: kanjiList.length > 0,
              extracting: false,
              error: "",
            };
          });
          return copy;
        });

        const totalK = pages.reduce(
          (s, p) => s + (p.kanji_list?.length || 0),
          0
        );
        message.success(
          `✨ Đã tự động load ${totalK} kanji cho ${pages.length} trang!`
        );
      } else {
        message.warning(
          res.message ||
            "Chưa có dữ liệu. Hãy nói với Antigravity để trích xuất."
        );
      }
    } catch (e: any) {
      message.error("Lỗi load: " + e.message);
    } finally {
      setLoadingAiData(false);
    }
  };

  /* ── Step 2: Edit helpers ────────────────────────────────── */

  const updateKanji = (
    pageIdx: number,
    kanjiIdx: number,
    field: string,
    value: any
  ) => {
    setPagesData((prev) => {
      const copy = [...prev];
      const kanji = { ...copy[pageIdx].kanji_list[kanjiIdx] };
      (kanji as any)[field] = value;
      copy[pageIdx] = {
        ...copy[pageIdx],
        kanji_list: [
          ...copy[pageIdx].kanji_list.slice(0, kanjiIdx),
          kanji,
          ...copy[pageIdx].kanji_list.slice(kanjiIdx + 1),
        ],
      };
      return copy;
    });
  };

  const updateExample = (
    pageIdx: number,
    kanjiIdx: number,
    exIdx: number,
    field: string,
    value: string
  ) => {
    setPagesData((prev) => {
      const copy = [...prev];
      const kanji = { ...copy[pageIdx].kanji_list[kanjiIdx] };
      const examples = [...kanji.examples];
      examples[exIdx] = { ...examples[exIdx], [field]: value };
      kanji.examples = examples;
      copy[pageIdx] = {
        ...copy[pageIdx],
        kanji_list: [
          ...copy[pageIdx].kanji_list.slice(0, kanjiIdx),
          kanji,
          ...copy[pageIdx].kanji_list.slice(kanjiIdx + 1),
        ],
      };
      return copy;
    });
  };

  const deleteKanji = (pageIdx: number, kanjiIdx: number) => {
    setPagesData((prev) => {
      const copy = [...prev];
      copy[pageIdx] = {
        ...copy[pageIdx],
        kanji_list: copy[pageIdx].kanji_list.filter((_, i) => i !== kanjiIdx),
      };
      return copy;
    });
  };

  const addExample = (pageIdx: number, kanjiIdx: number) => {
    setPagesData((prev) => {
      const copy = [...prev];
      const kanji = { ...copy[pageIdx].kanji_list[kanjiIdx] };
      kanji.examples = [
        ...kanji.examples,
        { word: "", hiragana: "", meaning: "", jlpt: "N3" },
      ];
      copy[pageIdx] = {
        ...copy[pageIdx],
        kanji_list: [
          ...copy[pageIdx].kanji_list.slice(0, kanjiIdx),
          kanji,
          ...copy[pageIdx].kanji_list.slice(kanjiIdx + 1),
        ],
      };
      return copy;
    });
  };

  const deleteExample = (
    pageIdx: number,
    kanjiIdx: number,
    exIdx: number
  ) => {
    setPagesData((prev) => {
      const copy = [...prev];
      const kanji = { ...copy[pageIdx].kanji_list[kanjiIdx] };
      kanji.examples = kanji.examples.filter((_, i) => i !== exIdx);
      copy[pageIdx] = {
        ...copy[pageIdx],
        kanji_list: [
          ...copy[pageIdx].kanji_list.slice(0, kanjiIdx),
          kanji,
          ...copy[pageIdx].kanji_list.slice(kanjiIdx + 1),
        ],
      };
      return copy;
    });
  };

  const updatePageTopic = (pageIdx: number, topic: string) => {
    setPagesData((prev) => {
      const copy = [...prev];
      copy[pageIdx] = { ...copy[pageIdx], topic };
      return copy;
    });
  };

  const clearPageData = (pageIdx: number) => {
    setPagesData((prev) => {
      const copy = [...prev];
      copy[pageIdx] = {
        kanji_list: [],
        topic: "",
        extracted: false,
        extracting: false,
        error: "",
      };
      return copy;
    });
  };

  /* ── Step 3: Import ──────────────────────────────────────── */

  const handleImport = async () => {
    setImporting(true);
    setImportError("");
    try {
      const validPages = pagesData
        .filter((p) => p.extracted && p.kanji_list.length > 0)
        .map((p, i) => ({
          kanji_list: p.kanji_list,
          topic: p.topic || `Bài ${startingLesson + i}`,
        }));

      if (validPages.length === 0) {
        setImportError("Chưa có trang nào có dữ liệu. Vui lòng nhập ít nhất 1 trang.");
        setImporting(false);
        return;
      }

      const res = await adminPost<any>("/crud/kanji-pdf/import/", {
        jlpt_level: jlptLevel,
        starting_lesson: startingLesson,
        pages_data: validPages,
        session_id: sessionId,
      });

      if (res.success) {
        setImportResult(res);
        message.success("Import thành công!");
      } else {
        setImportError(res.message || "Import thất bại");
      }
    } catch (e: any) {
      setImportError("Lỗi import: " + e.message);
    } finally {
      setImporting(false);
    }
  };

  /* ── Computed ─────────────────────────────────────────────── */

  const totalKanji = pagesData.reduce(
    (sum, p) => sum + p.kanji_list.length,
    0
  );
  const totalExamples = pagesData.reduce(
    (sum, p) =>
      sum + p.kanji_list.reduce((s, k) => s + k.examples.length, 0),
    0
  );
  const extractedPages = pagesData.filter((p) => p.extracted).length;
  const uncertainCount = pagesData.reduce(
    (sum, p) => sum + p.kanji_list.filter((k) => k.uncertain).length,
    0
  );
  const errorPages = pagesData.filter((p) => p.error).length;

  /* ── Render ──────────────────────────────────────────────── */

  return (
    <div>
      <Title level={3} style={{ marginBottom: 24 }}>
        📄 Kanji PDF Import
      </Title>

      <Steps
        current={currentStep}
        items={[
          { title: "Upload PDF", icon: <UploadOutlined /> },
          { title: "Nhập dữ liệu & Review", icon: <EditOutlined /> },
          { title: "Import DB", icon: <CheckCircleOutlined /> },
        ]}
        style={{ marginBottom: 32 }}
      />

      {/* ── Step 1: Upload ──────────────────────────────────── */}
      {currentStep === 0 && (
        <Card>
          {/* Session history */}
          {savedSessions.length > 0 && !sessionId && (
            <div style={{ marginBottom: 20 }}>
              <Text strong><HistoryOutlined /> Phiên làm việc gần đây:</Text>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}>
                {savedSessions.slice(0, 5).map((s) => (
                  <Button
                    key={s.session_id}
                    size="small"
                    loading={loadingSession}
                    onClick={() => loadSession(s.session_id)}
                    icon={s.has_extracted ? <CheckCircleOutlined style={{ color: "#10b981" }} /> : undefined}
                  >
                    {s.filename} ({s.page_count} trang)
                  </Button>
                ))}
              </div>
              <Divider style={{ margin: "16px 0" }} />
            </div>
          )}

          <Row gutter={24}>
            <Col span={16}>
              <Dragger
                accept=".pdf"
                maxCount={1}
                showUploadList={false}
                beforeUpload={(file) => {
                  handleUpload(file);
                  return false;
                }}
                disabled={uploading}
              >
                <div className="ant-upload-drag-icon">
                  {uploading ? (
                    <Spin size="large" />
                  ) : (
                    <UploadOutlined
                      style={{ fontSize: 48, color: "#6366f1" }}
                    />
                  )}
                </div>
                <p className="ant-upload-text">
                  {uploading
                    ? "Đang xử lý PDF..."
                    : "Kéo thả file PDF vào đây"}
                </p>
                <p className="ant-upload-hint">
                  Hỗ trợ file PDF chứa từ vựng Kanji
                </p>
              </Dragger>

              {uploadError && (
                <Alert
                  title="Upload thất bại"
                  description={uploadError}
                  type="error"
                  showIcon
                  closable
                  onClose={() => setUploadError("")}
                  style={{ marginTop: 12 }}
                  action={
                    <Button size="small" onClick={() => setUploadError("")}>
                      Thử lại
                    </Button>
                  }
                />
              )}
            </Col>
            <Col span={8}>
              <div
                style={{ display: "flex", flexDirection: "column", gap: 12, width: "100%" }}
              >
                <div>
                  <Text strong>Cấp JLPT:</Text>
                  <Select
                    value={jlptLevel}
                    onChange={setJlptLevel}
                    style={{ width: "100%", marginTop: 4 }}
                    options={JLPT_LEVELS.map((l) => ({ label: l, value: l }))}
                  />
                </div>
                <div>
                  <Text strong>Bài bắt đầu:</Text>
                  <InputNumber
                    value={startingLesson}
                    onChange={(v) => setStartingLesson(v || 1)}
                    min={1}
                    style={{ width: "100%", marginTop: 4 }}
                  />
                </div>

                <Alert
                  title="Hướng dẫn"
                  description={
                    <ol style={{ margin: 0, paddingLeft: 16, fontSize: 12 }}>
                      <li>Upload file PDF chứa kanji</li>
                      <li>Chọn phạm vi trang + JLPT level</li>
                      <li>Gửi session_id cho Antigravity</li>
                      <li>Nhấn <b>⚡ Load AI Data</b> → review → import</li>
                    </ol>
                  }
                  type="info"
                  showIcon
                />
              </div>
            </Col>
          </Row>

          {/* Thumbnails preview + page range */}
          {thumbnails.length > 0 && (
            <div style={{ marginTop: 24 }}>
              {/* Page range controls */}
              <Card size="small" style={{ marginBottom: 16, background: "#f8fafc" }}>
                <Row align="middle" gutter={16}>
                  <Col>
                    <Text strong>Chọn phạm vi trang:</Text>
                  </Col>
                  <Col>
                    <Space>
                      <Text>Từ trang</Text>
                      <InputNumber
                        value={pageFrom}
                        onChange={(v) => setPageFrom(Math.max(1, Math.min(v || 1, pageTo)))}
                        min={1}
                        max={pageTo}
                        style={{ width: 70 }}
                      />
                      <Text>đến trang</Text>
                      <InputNumber
                        value={pageTo}
                        onChange={(v) => setPageTo(Math.max(pageFrom, Math.min(v || pageCount, pageCount)))}
                        min={pageFrom}
                        max={pageCount}
                        style={{ width: 70 }}
                      />
                      <Text type="secondary">/ {pageCount} trang</Text>
                      <Tag color="blue">{workingPageCount} trang sẽ xử lý</Tag>
                    </Space>
                  </Col>
                </Row>
              </Card>

              <Text strong>
                Xem trước ({pageCount} trang — sẽ xử lý trang {pageFrom}→{pageTo}):
              </Text>
              <div
                style={{
                  display: "flex",
                  gap: 12,
                  overflowX: "auto",
                  marginTop: 8,
                  padding: "8px 0",
                }}
              >
                {thumbnails.map((thumb, i) => {
                  const inRange = i + 1 >= pageFrom && i + 1 <= pageTo;
                  return (
                    <div
                      key={i}
                      style={{
                        border: inRange ? "2px solid #6366f1" : "2px solid #e5e7eb",
                        borderRadius: 8,
                        padding: 4,
                        flexShrink: 0,
                        textAlign: "center",
                        opacity: inRange ? 1 : 0.4,
                        transition: "all 0.2s",
                      }}
                    >
                      <img
                        src={thumb}
                        alt={`Trang ${i + 1}`}
                        style={{ height: 150, borderRadius: 4 }}
                      />
                      <div
                        style={{
                          fontSize: 12,
                          marginTop: 4,
                          color: inRange ? "#6366f1" : "#6b7280",
                          fontWeight: inRange ? 600 : 400,
                        }}
                      >
                        Trang {i + 1}
                      </div>
                    </div>
                  );
                })}
              </div>

              <Button
                type="primary"
                size="large"
                onClick={startWorking}
                style={{ marginTop: 16 }}
                icon={<ArrowRightOutlined />}
                disabled={workingPageCount === 0}
              >
                Xử lý {workingPageCount} trang (trang {pageFrom}→{pageTo})
              </Button>

              {sessionId && (
                <Alert
                  title={<>Session ID: <Text code copyable>{sessionId}</Text></>}
                  description={
                    <div style={{ fontSize: 12 }}>
                      <div style={{ marginBottom: 4 }}>Copy lệnh này gửi cho Antigravity:</div>
                      <Text
                        code
                        copyable={{ text: `session_id: ${sessionId}, xử lý trang ${pageFrom}-${pageTo}, JLPT ${jlptLevel}, bài bắt đầu: ${startingLesson}` }}
                      >
                        session_id: {sessionId}, xử lý trang {pageFrom}-{pageTo}, JLPT {jlptLevel}, bài bắt đầu: {startingLesson}
                      </Text>
                      <div style={{ marginTop: 8, color: "#6b7280" }}>
                        VD: <code>session_id: abc123, xử lý trang 1-5, JLPT N3, bài bắt đầu: 1</code>
                      </div>
                    </div>
                  }
                  type="success"
                  showIcon
                  style={{ marginTop: 12 }}
                />
              )}
            </div>
          )}
        </Card>
      )}

      {/* ── Step 2: Manual Input & Review ──────────────────── */}
      {currentStep === 1 && (
        <div>
          {/* Page navigation header */}
          <Card size="small" style={{ marginBottom: 16 }}>
            <Row align="middle" justify="space-between">
              <Col>
                <Space>
                  <Button
                    icon={<ArrowLeftOutlined />}
                    disabled={currentPage === 0}
                    onClick={() => setCurrentPage((p) => p - 1)}
                  >
                    Trước
                  </Button>
                  <Text strong>
                    Trang {realPageIndex(currentPage) + 1} (#{currentPage + 1}/{workingPageCount})
                  </Text>
                  <Button
                    icon={<ArrowRightOutlined />}
                    disabled={currentPage >= workingPageCount - 1}
                    onClick={() => setCurrentPage((p) => p + 1)}
                  >
                    Sau
                  </Button>
                </Space>
              </Col>
              <Col>
                <Space>
                  <Tag color="blue">
                    {extractedPages}/{workingPageCount} trang có dữ liệu
                  </Tag>
                  <Tag color="green">{totalKanji} từ vựng</Tag>
                  {uncertainCount > 0 && (
                    <Tag color="orange" icon={<WarningOutlined />}>
                      {uncertainCount} cần kiểm tra
                    </Tag>
                  )}
                  {errorPages > 0 && (
                    <Tag color="red" icon={<ExclamationCircleOutlined />}>
                      {errorPages} lỗi
                    </Tag>
                  )}
                </Space>
              </Col>
              <Col>
                <Space>
                  <Button onClick={() => setCurrentStep(0)}>Quay lại</Button>
                  <Button
                    type="primary"
                    icon={<RobotOutlined />}
                    onClick={loadAiExtractedData}
                    loading={loadingAiData}
                    style={{ background: "#059669" }}
                  >
                    ⚡ Load AI Data
                  </Button>
                  <Button
                    icon={<CopyOutlined />}
                    onClick={openBatchModal}
                    style={{ borderColor: "#6366f1", color: "#6366f1" }}
                  >
                    Batch Paste
                  </Button>
                  <Button
                    icon={<SafetyCertificateOutlined />}
                    onClick={copyForAiVerify}
                    disabled={extractedPages === 0}
                    style={{ borderColor: "#10b981", color: "#10b981" }}
                  >
                    AI Verify
                  </Button>
                  <Button
                    type="primary"
                    onClick={() => setCurrentStep(2)}
                    disabled={extractedPages === 0}
                  >
                    Review & Import →
                  </Button>
                </Space>
              </Col>
            </Row>
          </Card>

          {/* Page content */}
          <Row gutter={16}>
            {/* Left: page image */}
            <Col span={8}>
              <Card
                title={
                  <Space>
                    <FileImageOutlined />
                    <span>Trang {realPageIndex(currentPage) + 1}</span>
                  </Space>
                }
                size="small"
                extra={
                  <Space>
                    <Tooltip title="Tải ảnh trang này">
                      <Button
                        size="small"
                        icon={<DownloadOutlined />}
                        onClick={() => downloadPageImage(currentPage)}
                      />
                    </Tooltip>
                  </Space>
                }
                styles={{
                  body: {
                    padding: 8,
                    maxHeight: "70vh",
                    overflow: "auto",
                  },
                }}
              >
                {thumbnails[realPageIndex(currentPage)] && (
                  <Image
                    src={
                      pageImages[realPageIndex(currentPage)] || thumbnails[realPageIndex(currentPage)]
                    }
                    alt={`Trang ${realPageIndex(currentPage) + 1}`}
                    style={{ width: "100%", borderRadius: 4 }}
                    fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
                  />
                )}

                <Divider style={{ margin: "12px 0" }} />

                <Alert
                  title="Cách dùng"
                  type="info"
                  description={
                    <ol
                      style={{
                        margin: 0,
                        paddingLeft: 16,
                        fontSize: 12,
                        lineHeight: 1.8,
                      }}
                    >
                      <li>Tải ảnh trang ↑</li>
                      <li>
                        Gửi ảnh cho Antigravity kèm lệnh{" "}
                        <code>/kanji</code>
                      </li>
                      <li>Copy JSON mà AI trả về</li>
                      <li>
                        Nhấn <b>Paste JSON</b> bên phải →
                      </li>
                    </ol>
                  }
                />
              </Card>
            </Col>

            {/* Right: extracted data */}
            <Col span={16}>
              <Card
                title={
                  <Row justify="space-between" align="middle">
                    <Space>
                      <EditOutlined />
                      <span>Dữ liệu trang {realPageIndex(currentPage) + 1}</span>
                      {pagesData[currentPage]?.extracted && (
                        <Tag color="green" icon={<CheckCircleOutlined />}>
                          {pagesData[currentPage].kanji_list.length} kanji
                        </Tag>
                      )}
                    </Space>
                    <Space>
                      <Input
                        value={pagesData[currentPage]?.topic || ""}
                        onChange={(e) =>
                          updatePageTopic(currentPage, e.target.value)
                        }
                        style={{ width: 180 }}
                        placeholder="Chủ đề bài học..."
                        addonBefore="Chủ đề"
                      />
                      <Button
                        type="primary"
                        icon={<CopyOutlined />}
                        onClick={() => openJsonModal(currentPage)}
                      >
                        Paste JSON
                      </Button>
                      {pagesData[currentPage]?.extracted && (
                        <Popconfirm
                          title="Xóa dữ liệu trang này?"
                          onConfirm={() => clearPageData(currentPage)}
                        >
                          <Button
                            danger
                            icon={<CloseCircleOutlined />}
                            size="small"
                          >
                            Xóa
                          </Button>
                        </Popconfirm>
                      )}
                    </Space>
                  </Row>
                }
                size="small"
                styles={{
                  body: {
                    padding: 8,
                    maxHeight: "70vh",
                    overflow: "auto",
                  },
                }}
              >
                {pagesData[currentPage]?.error && (
                  <Alert
                    title="Lỗi"
                    description={pagesData[currentPage].error}
                    type="error"
                    showIcon
                    closable
                    style={{ marginBottom: 12 }}
                    action={
                      <Button
                        size="small"
                        icon={<ReloadOutlined />}
                        onClick={() => openJsonModal(currentPage)}
                      >
                        Thử lại
                      </Button>
                    }
                  />
                )}

                {!pagesData[currentPage]?.extracted && (
                  <div
                    style={{
                      textAlign: "center",
                      padding: "40px 20px",
                      background: "#fafafa",
                      borderRadius: 8,
                    }}
                  >
                    <FileImageOutlined
                      style={{ fontSize: 48, color: "#d1d5db", marginBottom: 16 }}
                    />
                    <Paragraph type="secondary">
                      Chưa có dữ liệu cho trang này.
                    </Paragraph>
                    <Space direction="vertical">
                      <Button
                        type="primary"
                        icon={<CopyOutlined />}
                        onClick={() => openJsonModal(currentPage)}
                        size="large"
                      >
                        Paste JSON dữ liệu kanji
                      </Button>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Tải ảnh → gửi cho Antigravity → copy JSON → paste vào đây
                      </Text>
                    </Space>
                  </div>
                )}

                {pagesData[currentPage]?.extracted &&
                  pagesData[currentPage].kanji_list.length === 0 && (
                    <Alert
                      title="Không có kanji"
                      description="Chưa có kanji nào trong trang này. Paste JSON để thêm."
                      type="warning"
                      showIcon
                      action={
                        <Button
                          size="small"
                          onClick={() => openJsonModal(currentPage)}
                        >
                          Paste JSON
                        </Button>
                      }
                    />
                  )}

                {pagesData[currentPage]?.extracted &&
                  pagesData[currentPage].kanji_list.length > 0 && (
                    <Collapse
                      accordion
                      items={pagesData[currentPage].kanji_list.map(
                        (kanji, kIdx) => ({
                          key: kIdx.toString(),
                          label: (
                            <Space>
                              <span
                                style={{
                                  fontSize: 24,
                                  fontWeight: 700,
                                  fontFamily: "serif",
                                }}
                              >
                                {kanji.character}
                              </span>
                              <Tag>{kanji.han_viet}</Tag>
                              <Text type="secondary">
                                {kanji.meaning_vi}
                              </Text>
                              <Text type="secondary" style={{ fontSize: 12 }}>
                                ({kanji.examples.length} từ)
                              </Text>
                              {kanji.uncertain && (
                                <Tooltip title={kanji.uncertain_note}>
                                  <Tag
                                    color="orange"
                                    icon={<WarningOutlined />}
                                  >
                                    Cần kiểm tra
                                  </Tag>
                                </Tooltip>
                              )}
                            </Space>
                          ),
                          extra: (
                            <Popconfirm
                              title="Xóa kanji này?"
                              onConfirm={(e) => {
                                e?.stopPropagation();
                                deleteKanji(currentPage, kIdx);
                              }}
                              onCancel={(e) => e?.stopPropagation()}
                            >
                              <Button
                                size="small"
                                danger
                                icon={<DeleteOutlined />}
                                onClick={(e) => e.stopPropagation()}
                              />
                            </Popconfirm>
                          ),
                          children: (
                            <div>
                              {kanji.uncertain && kanji.uncertain_note && (
                                <Alert
                                  title={kanji.uncertain_note}
                                  type="warning"
                                  showIcon
                                  style={{ marginBottom: 12 }}
                                />
                              )}
                              <Row gutter={[12, 12]}>
                                <Col span={8}>
                                  <Text
                                    type="secondary"
                                    style={{ fontSize: 12 }}
                                  >
                                    Hán Việt
                                  </Text>
                                  <Input
                                    value={kanji.han_viet}
                                    onChange={(e) =>
                                      updateKanji(
                                        currentPage,
                                        kIdx,
                                        "han_viet",
                                        e.target.value
                                      )
                                    }
                                  />
                                </Col>
                                <Col span={8}>
                                  <Text
                                    type="secondary"
                                    style={{ fontSize: 12 }}
                                  >
                                    Âm On (katakana)
                                  </Text>
                                  <Input
                                    value={kanji.onyomi?.join("・")}
                                    onChange={(e) =>
                                      updateKanji(
                                        currentPage,
                                        kIdx,
                                        "onyomi",
                                        e.target.value
                                          .split(/[・,、]/)
                                          .map((s: string) => s.trim())
                                          .filter(Boolean)
                                      )
                                    }
                                  />
                                </Col>
                                <Col span={8}>
                                  <Text
                                    type="secondary"
                                    style={{ fontSize: 12 }}
                                  >
                                    Âm Kun (hiragana)
                                  </Text>
                                  <Input
                                    value={kanji.kunyomi?.join("・")}
                                    onChange={(e) =>
                                      updateKanji(
                                        currentPage,
                                        kIdx,
                                        "kunyomi",
                                        e.target.value
                                          .split(/[・,、]/)
                                          .map((s: string) => s.trim())
                                          .filter(Boolean)
                                      )
                                    }
                                  />
                                </Col>
                                <Col span={12}>
                                  <Text
                                    type="secondary"
                                    style={{ fontSize: 12 }}
                                  >
                                    Nghĩa tiếng Việt
                                  </Text>
                                  <Input
                                    value={kanji.meaning_vi}
                                    onChange={(e) =>
                                      updateKanji(
                                        currentPage,
                                        kIdx,
                                        "meaning_vi",
                                        e.target.value
                                      )
                                    }
                                  />
                                </Col>
                                <Col span={12}>
                                  <Text
                                    type="secondary"
                                    style={{ fontSize: 12 }}
                                  >
                                    Hình thành
                                  </Text>
                                  <Input
                                    value={kanji.formation}
                                    onChange={(e) =>
                                      updateKanji(
                                        currentPage,
                                        kIdx,
                                        "formation",
                                        e.target.value
                                      )
                                    }
                                  />
                                </Col>
                              </Row>

                              {/* Examples table */}
                              <div style={{ marginTop: 16 }}>
                                <Row
                                  justify="space-between"
                                  align="middle"
                                  style={{ marginBottom: 8 }}
                                >
                                  <Text strong style={{ fontSize: 13 }}>
                                    Từ vựng mẫu ({kanji.examples.length})
                                  </Text>
                                  <Button
                                    size="small"
                                    icon={<PlusOutlined />}
                                    onClick={() =>
                                      addExample(currentPage, kIdx)
                                    }
                                  >
                                    Thêm
                                  </Button>
                                </Row>
                                <Table
                                  size="small"
                                  pagination={false}
                                  dataSource={kanji.examples.map(
                                    (ex, i) => ({
                                      ...ex,
                                      key: i,
                                    })
                                  )}
                                  columns={[
                                    {
                                      title: "Từ",
                                      dataIndex: "word",
                                      width: 120,
                                      render: (
                                        v: string,
                                        _: any,
                                        i: number
                                      ) => (
                                        <Input
                                          size="small"
                                          value={v}
                                          onChange={(e) =>
                                            updateExample(
                                              currentPage,
                                              kIdx,
                                              i,
                                              "word",
                                              e.target.value
                                            )
                                          }
                                        />
                                      ),
                                    },
                                    {
                                      title: "Hiragana",
                                      dataIndex: "hiragana",
                                      width: 140,
                                      render: (
                                        v: string,
                                        _: any,
                                        i: number
                                      ) => (
                                        <Input
                                          size="small"
                                          value={v}
                                          onChange={(e) =>
                                            updateExample(
                                              currentPage,
                                              kIdx,
                                              i,
                                              "hiragana",
                                              e.target.value
                                            )
                                          }
                                        />
                                      ),
                                    },
                                    {
                                      title: "Nghĩa",
                                      dataIndex: "meaning",
                                      render: (
                                        v: string,
                                        _: any,
                                        i: number
                                      ) => (
                                        <Input
                                          size="small"
                                          value={v}
                                          onChange={(e) =>
                                            updateExample(
                                              currentPage,
                                              kIdx,
                                              i,
                                              "meaning",
                                              e.target.value
                                            )
                                          }
                                        />
                                      ),
                                    },
                                    {
                                      title: "JLPT",
                                      dataIndex: "jlpt",
                                      width: 80,
                                      render: (
                                        v: string,
                                        _: any,
                                        i: number
                                      ) => (
                                        <Select
                                          size="small"
                                          value={v}
                                          onChange={(val) =>
                                            updateExample(
                                              currentPage,
                                              kIdx,
                                              i,
                                              "jlpt",
                                              val
                                            )
                                          }
                                          style={{ width: 70 }}
                                          options={JLPT_LEVELS.map((l) => ({
                                            label: l,
                                            value: l,
                                          }))}
                                        />
                                      ),
                                    },
                                    {
                                      title: "",
                                      width: 40,
                                      render: (
                                        _: any,
                                        __: any,
                                        i: number
                                      ) => (
                                        <Button
                                          size="small"
                                          danger
                                          icon={<DeleteOutlined />}
                                          onClick={() =>
                                            deleteExample(
                                              currentPage,
                                              kIdx,
                                              i
                                            )
                                          }
                                        />
                                      ),
                                    },
                                  ]}
                                />
                              </div>
                            </div>
                          ),
                        })
                      )}
                    />
                  )}
              </Card>
            </Col>
          </Row>

          {/* Quick page navigation bar */}
          <Card size="small" style={{ marginTop: 16 }}>
            <Row justify="space-between" align="middle">
              <Text strong style={{ fontSize: 13 }}>Nhảy đến trang:</Text>
              <Space wrap>
                {Array.from({ length: workingPageCount }, (_, i) => {
                  const page = pagesData[i];
                  const hasData = page?.extracted && page.kanji_list.length > 0;
                  const hasError = !!page?.error;
                  return (
                    <Badge
                      key={i}
                      count={hasError ? "!" : 0}
                      size="small"
                      offset={[-2, 0]}
                    >
                      <Button
                        type={i === currentPage ? "primary" : "default"}
                        size="small"
                        onClick={() => setCurrentPage(i)}
                        style={{
                          background: hasData
                            ? i === currentPage
                              ? undefined
                              : "#f0fdf4"
                            : hasError
                              ? "#fef2f2"
                              : undefined,
                          borderColor: hasData
                            ? "#10b981"
                            : hasError
                              ? "#ef4444"
                              : undefined,
                          minWidth: 36,
                        }}
                      >
                        {realPageIndex(i) + 1}
                      </Button>
                    </Badge>
                  );
                })}
              </Space>
            </Row>
          </Card>
        </div>
      )}

      {/* ── Step 3: Final Review & Import ──────────────────── */}
      {currentStep === 2 && (
        <div>
          {importResult ? (
            <Result
              status="success"
              title="Import thành công!"
              subTitle={importResult.message}
              extra={[
                <Button
                  key="kanji"
                  type="primary"
                  onClick={() =>
                    (window.location.href = "/admin/kanji")
                  }
                >
                  Xem từ vựng
                </Button>,
                <Button
                  key="new"
                  onClick={() => window.location.reload()}
                >
                  Import PDF mới
                </Button>,
              ]}
            >
              <Card size="small">
                <Row gutter={16}>
                  <Col span={6}>
                    <Statistic
                      title="Bài học"
                      value={importResult.stats?.lessons || 0}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="Từ vựng"
                      value={importResult.stats?.kanji || 0}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="Ví dụ"
                      value={importResult.stats?.vocab || 0}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="Đã liên kết"
                      value={importResult.stats?.vocab_linked || 0}
                    />
                  </Col>
                </Row>
              </Card>
            </Result>
          ) : (
            <>
              <Row gutter={16} style={{ marginBottom: 24 }}>
                <Col span={6}>
                  <Card size="small">
                    <Statistic
                      title="Trang có dữ liệu"
                      value={extractedPages}
                      suffix={`/ ${pageCount}`}
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card size="small">
                    <Statistic title="Tổng từ vựng" value={totalKanji} />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card size="small">
                    <Statistic
                      title="Tổng ví dụ"
                      value={totalExamples}
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card size="small">
                    <Statistic
                      title="Cần kiểm tra"
                      value={uncertainCount}
                      valueStyle={{
                        color:
                          uncertainCount > 0 ? "#f59e0b" : "#10b981",
                      }}
                    />
                  </Card>
                </Col>
              </Row>

              {importError && (
                <Alert
                  title="Lỗi Import"
                  description={importError}
                  type="error"
                  showIcon
                  closable
                  onClose={() => setImportError("")}
                  style={{ marginBottom: 16 }}
                  action={
                    <Button
                      size="small"
                      icon={<ReloadOutlined />}
                      onClick={() => {
                        setImportError("");
                        handleImport();
                      }}
                    >
                      Thử lại
                    </Button>
                  }
                />
              )}

              {uncertainCount > 0 && (
                <Alert
                  title={`Có ${uncertainCount} kanji được đánh dấu không chắc chắn`}
                  description="Bạn nên quay lại Step 2 để kiểm tra lại những item có dấu cảnh báo vàng."
                  type="warning"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
              )}

              <Card
                title={`Tổng hợp: ${jlptLevel} — Bài ${startingLesson} đến ${startingLesson + extractedPages - 1}`}
                size="small"
                style={{ marginBottom: 16 }}
              >
                <Table
                  size="small"
                  pagination={false}
                  dataSource={pagesData
                    .map((p, i) => ({ ...p, originalIdx: i }))
                    .filter(
                      (p) => p.extracted && p.kanji_list.length > 0
                    )
                    .map((p, i) => ({
                      key: i,
                      lesson: startingLesson + p.originalIdx,
                      topic: p.topic,
                      kanjiCount: p.kanji_list.length,
                      vocabCount: p.kanji_list.reduce(
                        (s, k) => s + k.examples.length,
                        0
                      ),
                      uncertainCount: p.kanji_list.filter(
                        (k) => k.uncertain
                      ).length,
                      kanjiChars: p.kanji_list
                        .map((k) => k.character)
                        .join(" "),
                    }))}
                  columns={[
                    {
                      title: "Bài",
                      dataIndex: "lesson",
                      width: 60,
                    },
                    { title: "Chủ đề", dataIndex: "topic" },
                    {
                      title: "Từ vựng",
                      dataIndex: "kanjiCount",
                      width: 70,
                    },
                    {
                      title: "Ví dụ",
                      dataIndex: "vocabCount",
                      width: 80,
                    },
                    {
                      title: "⚠️",
                      dataIndex: "uncertainCount",
                      width: 50,
                      render: (v: number) =>
                        v > 0 ? (
                          <Tag color="orange">{v}</Tag>
                        ) : (
                          <Tag color="green">✓</Tag>
                        ),
                    },
                    {
                      title: "Các chữ",
                      dataIndex: "kanjiChars",
                      render: (v: string) => (
                        <span
                          style={{ fontFamily: "serif", fontSize: 16 }}
                        >
                          {v}
                        </span>
                      ),
                    },
                  ]}
                />
              </Card>

              <Row justify="space-between">
                <Button
                  icon={<ArrowLeftOutlined />}
                  onClick={() => setCurrentStep(1)}
                >
                  Quay lại chỉnh sửa
                </Button>
                <Popconfirm
                  title="Xác nhận import?"
                  description={`Import ${totalKanji} từ vựng, ${totalExamples} ví dụ vào DB?`}
                  onConfirm={handleImport}
                  okText="Import"
                  cancelText="Hủy"
                >
                  <Button
                    type="primary"
                    size="large"
                    icon={<ImportOutlined />}
                    loading={importing}
                  >
                    Import vào Database
                  </Button>
                </Popconfirm>
              </Row>
            </>
          )}
        </div>
      )}

      {/* ── JSON Paste Modal ──────────────────────────────── */}
      <Modal
        title={`Paste JSON — Trang ${currentPage + 1}`}
        open={jsonModalOpen}
        onCancel={() => setJsonModalOpen(false)}
        width={700}
        footer={[
          <Button key="cancel" onClick={() => setJsonModalOpen(false)}>
            Hủy
          </Button>,
          <Button
            key="apply"
            type="primary"
            onClick={applyJsonData}
            disabled={!jsonText.trim()}
          >
            Áp dụng
          </Button>,
        ]}
      >
        <Alert
          title="Paste JSON dữ liệu kanji vào đây"
          description={
            <span>
              Hỗ trợ format: <code>{"{ kanji_list: [...] }"}</code> hoặc{" "}
              <code>{"[{ character: ... }]"}</code>. Có thể paste cả
              markdown code block.
            </span>
          }
          type="info"
          showIcon
          style={{ marginBottom: 12 }}
        />

        <TextArea
          value={jsonText}
          onChange={(e) => {
            setJsonText(e.target.value);
            setJsonError("");
          }}
          placeholder={`Paste JSON từ Antigravity vào đây...\n\nVD:\n{\n  "kanji_list": [\n    {\n      "character": "日",\n      "han_viet": "Nhật",\n      "onyomi": ["ニチ", "ジツ"],\n      "kunyomi": ["ひ", "か"],\n      "meaning_vi": "Ngày, mặt trời",\n      "formation": "Tượng hình: Hình mặt trời",\n      "examples": [\n        {"word": "日本", "hiragana": "にほん", "meaning": "Nhật Bản", "jlpt": "N5"}\n      ]\n    }\n  ]\n}`}
          rows={16}
          style={{ fontFamily: "monospace", fontSize: 13 }}
        />

        {jsonError && (
          <Alert
            title="Lỗi JSON"
            description={jsonError}
            type="error"
            showIcon
            style={{ marginTop: 12 }}
          />
        )}
      </Modal>
      {/* ── Batch JSON Paste Modal ────────────────────────── */}
      <Modal
        title="Batch Paste — Tất cả trang"
        open={batchModalOpen}
        onCancel={() => setBatchModalOpen(false)}
        width={800}
        footer={[
          <Button key="cancel" onClick={() => setBatchModalOpen(false)}>
            Hủy
          </Button>,
          <Button
            key="apply"
            type="primary"
            onClick={applyBatchJsonData}
            disabled={!batchJsonText.trim()}
          >
            Áp dụng tất cả
          </Button>,
        ]}
      >
        <Alert
          title="Paste JSON cho TẤT CẢ các trang cùng lúc"
          description={
            <span>
              Format: <code>{'{"pages": [ {"kanji_list": [...], "topic": "Bài 1"}, ... ]}'}</code>
              <br />
              Hoặc: <code>{'[{"kanji_list": [...]}, ...]'}</code>
              <br />
              Antigravity sẽ tạo JSON này khi bạn gửi ảnh trang + session_id.
            </span>
          }
          type="info"
          showIcon
          style={{ marginBottom: 12 }}
        />

        <TextArea
          value={batchJsonText}
          onChange={(e) => {
            setBatchJsonText(e.target.value);
            setBatchJsonError("");
          }}
          placeholder={`Paste JSON từ Antigravity vào đây...\n\nVD:\n{\n  "pages": [\n    {\n      "topic": "Bài 1",\n      "kanji_list": [\n        {\n          "character": "日",\n          "han_viet": "Nhật",\n          "onyomi": ["ニチ"],\n          "kunyomi": ["ひ"],\n          "meaning_vi": "Ngày",\n          "formation": "Tượng hình",\n          "examples": [{"word": "日本", "hiragana": "にほん", "meaning": "Nhật Bản", "jlpt": "N5"}]\n        }\n      ]\n    },\n    {\n      "topic": "Bài 2",\n      "kanji_list": [...]\n    }\n  ]\n}`}
          rows={18}
          style={{ fontFamily: "monospace", fontSize: 13 }}
        />

        {batchJsonError && (
          <Alert
            title="Lỗi JSON"
            description={batchJsonError}
            type="error"
            showIcon
            style={{ marginTop: 12 }}
          />
        )}
      </Modal>
    </div>
  );
}
