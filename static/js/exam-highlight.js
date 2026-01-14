/**
 * Exam Highlight feature (TOEIC take page)
 * - Shows popup toolbar when selecting text
 * - Saves highlights to localStorage per template/session
 */
(function () {
  function ready(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  ready(function () {
    const containerEl = document.querySelector(".df-toeic-exam-container");
    const highlightToggle = document.getElementById("highlight-toggle");
    const highlightToolbar = document.getElementById("highlight-toolbar");

    if (!containerEl || !highlightToggle || !highlightToolbar) return;

    const templateId = containerEl.getAttribute("data-template-id") || "";
    const sessionId = containerEl.getAttribute("data-session-id") || "";
    const storageKey = `df_highlights_${templateId}_${sessionId}`;

    let highlights = [];
    let currentSelection = null;
    let tempMarkEl = null;

    function clearTempMark() {
      if (!tempMarkEl) return;
      try {
        const parent = tempMarkEl.parentNode;
        if (parent) {
          parent.replaceChild(document.createTextNode(tempMarkEl.textContent), tempMarkEl);
          parent.normalize();
        }
      } catch (e) {
        // ignore
      }
      tempMarkEl = null;
    }

    function loadHighlights() {
      try {
        const saved = localStorage.getItem(storageKey);
        if (saved) {
          highlights = JSON.parse(saved);
          applyHighlights();
        }
      } catch (e) {
        console.error("[highlight] load error:", e);
      }
    }

    function saveHighlights() {
      try {
        localStorage.setItem(storageKey, JSON.stringify(highlights));
      } catch (e) {
        console.error("[highlight] save error:", e);
      }
    }

    function generateHighlightId() {
      return "hl_" + Date.now() + "_" + Math.random().toString(36).slice(2, 11);
    }

    function getTextNodes(root) {
      const nodes = [];
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null, false);
      let n;
      while ((n = walker.nextNode())) nodes.push(n);
      return nodes;
    }

    // Compute absolute text offset (within root.textContent) for a DOM Range
    function rangeToOffsets(root, range) {
      const nodes = getTextNodes(root);
      let pos = 0;
      let start = null;
      let end = null;

      for (const node of nodes) {
        const len = (node.textContent || "").length;
        if (node === range.startContainer) start = pos + range.startOffset;
        if (node === range.endContainer) end = pos + range.endOffset;
        pos += len;
      }
      if (start === null || end === null) return null;
      return { start, end };
    }

    // Create a DOM Range from absolute offsets within root.textContent
    function offsetsToRange(root, start, end) {
      const nodes = getTextNodes(root);
      let pos = 0;
      const r = document.createRange();

      let startSet = false;
      for (const node of nodes) {
        const len = (node.textContent || "").length;
        const next = pos + len;

        if (!startSet && start >= pos && start <= next) {
          r.setStart(node, Math.max(0, Math.min(len, start - pos)));
          startSet = true;
        }
        if (startSet && end >= pos && end <= next) {
          r.setEnd(node, Math.max(0, Math.min(len, end - pos)));
          return r;
        }
        pos = next;
      }
      return null;
    }

    function applyHighlights() {
      // unwrap existing marks
      document.querySelectorAll("mark.df-user-highlight").forEach((mark) => {
        const parent = mark.parentNode;
        parent.replaceChild(document.createTextNode(mark.textContent), mark);
        parent.normalize();
      });

      highlights.forEach((hl) => applyHighlightToDOM(hl));
    }

    function applyHighlightToDOM(hl) {
      const content = document.querySelector(".df-toeic-content");
      if (!content || !hl || !hl.text) return;

      let range = null;
      if (typeof hl.start === "number" && typeof hl.end === "number") {
        range = offsetsToRange(content, hl.start, hl.end);
      }

      // fallback: old highlights saved by text only
      if (!range) {
        const walker = document.createTreeWalker(content, NodeFilter.SHOW_TEXT, null, false);
        let node;
        while ((node = walker.nextNode())) {
          const text = node.textContent || "";
          const idx = text.indexOf(hl.text);
          if (idx === -1) continue;
          range = document.createRange();
          range.setStart(node, idx);
          range.setEnd(node, idx + hl.text.length);
          break;
        }
      }

      if (!range) return;

      const mark = document.createElement("mark");
      mark.className = "df-user-highlight";
      mark.dataset.highlightId = hl.id;

      if (hl.color === "underline") {
        mark.style.background = "transparent";
        mark.style.textDecoration = "underline";
        mark.style.textDecorationColor = "#2563eb";
        mark.style.textDecorationThickness = "2px";
      } else {
        mark.style.background = hl.color || "#fde047";
      }

      if (hl.note) {
        mark.title = hl.note;
        mark.style.cursor = "help";
      }

      try {
        range.surroundContents(mark);
      } catch (e) {
        // spans multiple nodes; skip
      }
    }

    function showToolbarAtViewportPoint(x, y) {
      const pad = 8;
      const approxWidth = 260;
      // Nudge a bit to the right to avoid covering the selection start
      const nudgeRight = 16;
      const clampedX = Math.max(
        pad + approxWidth / 2,
        Math.min(window.innerWidth - pad - approxWidth / 2, x + nudgeRight)
      );
      const clampedY = Math.max(pad + 10, y);

      highlightToolbar.style.display = "flex";
      highlightToolbar.style.left = clampedX + "px";
      highlightToolbar.style.top = clampedY + "px";
    }

    function hideToolbar() {
      highlightToolbar.style.display = "none";
      currentSelection = null;
      clearTempMark();
    }

    // Selection handler
    document.addEventListener("mouseup", function (e) {
      if (!highlightToggle.checked) return;
      if (e.target.closest(".df-highlight-toolbar")) return;

      const selection = window.getSelection();
      const selectedText = (selection ? selection.toString() : "").trim();

      // If user clicked elsewhere, clear any temp highlight
      if (!e.target.closest("mark.df-highlight-temp") && !e.target.closest("mark.df-user-highlight")) {
        clearTempMark();
      }

      // If selection/click is inside an existing highlight, prefer editing that highlight
      const anchorNode = selection && selection.anchorNode ? selection.anchorNode : null;
      const anchorEl =
        anchorNode && anchorNode.nodeType === 3 ? anchorNode.parentElement : (anchorNode && anchorNode.nodeType === 1 ? anchorNode : null);
      const existingMarkFromSelection = anchorEl ? anchorEl.closest("mark.df-user-highlight") : null;

      if (existingMarkFromSelection) {
        currentSelection = { highlightId: existingMarkFromSelection.dataset.highlightId };
        const rect = existingMarkFromSelection.getBoundingClientRect();
        const x = rect.left + rect.width / 2;
        const y = rect.top - 8;
        showToolbarAtViewportPoint(x, y < 40 ? rect.bottom + 8 : y);
        // Prevent browser selection UI (Edge/Chrome mini menu)
        if (selection) selection.removeAllRanges();
        return;
      }

      if (selectedText.length > 0) {
        const range = selection.getRangeAt(0);
        const container = range.commonAncestorContainer;
        const content = document.querySelector(".df-toeic-content");

        const anchor = container.nodeType === 3 ? container.parentNode : container;
        if (content && anchor && content.contains(anchor)) {
          const offsets = rangeToOffsets(content, range);
          currentSelection = offsets
            ? { text: selectedText, start: offsets.start, end: offsets.end }
            : { text: selectedText };
          const rect = range.getBoundingClientRect();
          const x = rect.left + rect.width / 2;
          const y = rect.top - 8;
          showToolbarAtViewportPoint(x, y < 40 ? rect.bottom + 8 : y);
          // Keep a visible selection by wrapping a temporary mark, then clear selection
          clearTempMark();
          let wrapped = false;
          try {
            const tmp = document.createElement("mark");
            tmp.className = "df-highlight-temp";
            tmp.dataset.temp = "1";
            range.surroundContents(tmp);
            tempMarkEl = tmp;
            wrapped = true;
          } catch (e) {
            wrapped = false;
          }
          if (wrapped && selection) selection.removeAllRanges();
          return;
        }
      }

      // click existing highlight
      const highlightMark = e.target.closest("mark.df-user-highlight");
      if (highlightMark) {
        currentSelection = { highlightId: highlightMark.dataset.highlightId };
        const rect = highlightMark.getBoundingClientRect();
        const x = rect.left + rect.width / 2;
        const y = rect.top - 8;
        showToolbarAtViewportPoint(x, y < 40 ? rect.bottom + 8 : y);
        if (selection) selection.removeAllRanges();
        return;
      }

      hideToolbar();
    });

    // Toolbar actions
    highlightToolbar.addEventListener("click", function (e) {
      const btn = e.target.closest(".df-highlight-btn");
      if (!btn) return;
      const action = btn.dataset.color;

      if (action === "remove") {
        if (currentSelection && currentSelection.highlightId) {
          highlights = highlights.filter((h) => h.id !== currentSelection.highlightId);
          saveHighlights();
          applyHighlights();
        } else if (currentSelection && currentSelection.text) {
          // fallback: remove all highlights matching selected text
          const t = currentSelection.text;
          highlights = highlights.filter((h) => h.text !== t);
          saveHighlights();
          applyHighlights();
        }
        clearTempMark();
      } else if (action === "edit" || action === "note") {
        if (!currentSelection) return;
        let existingNote = "";
        if (currentSelection.highlightId) {
          const hl = highlights.find((h) => h.id === currentSelection.highlightId);
          existingNote = hl ? hl.note || "" : "";
        }
        const note = prompt("Nhập ghi chú:", existingNote);
        if (note === null) return;

        if (currentSelection.highlightId) {
          const hl = highlights.find((h) => h.id === currentSelection.highlightId);
          if (hl) {
            hl.note = note;
            saveHighlights();
            applyHighlights();
          }
        } else if (currentSelection.text) {
          highlights.push({
            id: generateHighlightId(),
            text: currentSelection.text,
            color: "#fde047",
            note: note,
          });
          saveHighlights();
          applyHighlights();
        }
        clearTempMark();
      } else {
        // colors / underline
        if (currentSelection && currentSelection.highlightId) {
          const hl = highlights.find((h) => h.id === currentSelection.highlightId);
          if (hl) {
            hl.color = action;
            saveHighlights();
            applyHighlights();
          }
        } else if (currentSelection && currentSelection.text) {
          highlights.push({
            id: generateHighlightId(),
            text: currentSelection.text,
            start: typeof currentSelection.start === "number" ? currentSelection.start : undefined,
            end: typeof currentSelection.end === "number" ? currentSelection.end : undefined,
            color: action,
          });
          saveHighlights();
          applyHighlights();
        }
        clearTempMark();
      }

      hideToolbar();
      const sel = window.getSelection();
      if (sel) sel.removeAllRanges();
    });

    loadHighlights();
  });
})();


