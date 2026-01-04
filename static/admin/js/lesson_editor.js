/**
 * Rich Text Editor for Lesson Content
 * Simple, beautiful, and feature-rich editor
 */
(function() {
  'use strict';
  
  // Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initEditor);
  } else {
    initEditor();
  }
  
  function initEditor() {
    const contentField = document.getElementById('id_content');
    if (!contentField) return;
    
    const editor = new RichTextEditor(contentField);
    editor.init();
  }
  
  /**
   * Rich Text Editor Class
   */
  class RichTextEditor {
    constructor(textarea) {
      this.textarea = textarea;
      this.wrapper = null;
      this.toolbar = null;
      this.content = null;
      this.commands = this.initCommands();
      this.savedRange = null; // Store cursor position for table insertion
    }
    
    init() {
      this.createEditor();
      this.setupEventListeners();
      this.syncContent();
    }
    
    /**
     * Initialize command definitions
     */
    initCommands() {
      return [
        {
          id: 'bold',
          cmd: 'bold',
          icon: this.getIcon('bold'),
          title: 'In đậm',
          shortcut: 'b',
          state: true
        },
        {
          id: 'italic',
          cmd: 'italic',
          icon: this.getIcon('italic'),
          title: 'In nghiêng',
          shortcut: 'i',
          state: true
        },
        {
          id: 'underline',
          cmd: 'underline',
          icon: this.getIcon('underline'),
          title: 'Gạch chân',
          shortcut: 'u',
          state: true
        },
        { type: 'divider' },
        {
          id: 'heading1',
          cmd: 'formatBlock',
          value: '<h1>',
          icon: this.getIcon('h1'),
          title: 'Tiêu đề 1',
          shortcut: '1'
        },
        {
          id: 'heading2',
          cmd: 'formatBlock',
          value: '<h2>',
          icon: this.getIcon('h2'),
          title: 'Tiêu đề 2',
          shortcut: '2'
        },
        {
          id: 'heading3',
          cmd: 'formatBlock',
          value: '<h3>',
          icon: this.getIcon('h3'),
          title: 'Tiêu đề 3',
          shortcut: '3'
        },
        { type: 'divider' },
        {
          id: 'unorderedList',
          cmd: 'insertUnorderedList',
          icon: this.getIcon('ul'),
          title: 'Danh sách không đánh số',
          shortcut: 'l'
        },
        {
          id: 'orderedList',
          cmd: 'insertOrderedList',
          icon: this.getIcon('ol'),
          title: 'Danh sách đánh số',
          shortcut: 'o'
        },
        {
          id: 'blockquote',
          cmd: 'formatBlock',
          value: '<blockquote>',
          icon: this.getIcon('quote'),
          title: 'Trích dẫn',
          shortcut: 'q'
        },
        { type: 'divider' },
        {
          id: 'link',
          cmd: 'createLink',
          icon: this.getIcon('link'),
          title: 'Chèn liên kết',
          shortcut: 'k',
          custom: true
        },
        {
          id: 'code',
          cmd: 'formatBlock',
          value: '<pre>',
          icon: this.getIcon('code'),
          title: 'Code block',
          shortcut: 'c'
        },
        {
          id: 'table',
          cmd: 'insertTable',
          icon: this.getIcon('table'),
          title: 'Chèn bảng',
          shortcut: 't',
          custom: true
        },
        { type: 'divider' },
        {
          id: 'alignLeft',
          cmd: 'justifyLeft',
          icon: this.getIcon('alignLeft'),
          title: 'Căn trái',
          shortcut: null
        },
        {
          id: 'alignCenter',
          cmd: 'justifyCenter',
          icon: this.getIcon('alignCenter'),
          title: 'Căn giữa',
          shortcut: null
        },
        {
          id: 'alignRight',
          cmd: 'justifyRight',
          icon: this.getIcon('alignRight'),
          title: 'Căn phải',
          shortcut: null
        },
        { type: 'divider' },
        {
          id: 'removeFormat',
          cmd: 'removeFormat',
          icon: this.getIcon('removeFormat'),
          title: 'Xóa định dạng',
          shortcut: null
        },
        {
          id: 'undo',
          cmd: 'undo',
          icon: this.getIcon('undo'),
          title: 'Hoàn tác (Ctrl+Z)',
          shortcut: 'z'
        },
        {
          id: 'redo',
          cmd: 'redo',
          icon: this.getIcon('redo'),
          title: 'Làm lại (Ctrl+Y)',
          shortcut: 'y'
        }
      ];
    }
    
    /**
     * Get SVG icon
     */
    getIcon(type) {
      const icons = {
        bold: '<path d="M6 4h8a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"></path><path d="M6 12h9a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"></path>',
        italic: '<path d="M11 4h3"></path><path d="M7 20h3"></path><path d="M14 4l-4 16"></path>',
        underline: '<path d="M6 3v7a6 6 0 0 0 6 6 6 6 0 0 0 6-6V3"></path><path d="M4 21h16"></path>',
        h1: '<path d="M4 12h8"></path><path d="M4 18V6"></path><path d="M12 18V6"></path><path d="M17 18l3-4.5V6"></path>',
        h2: '<path d="M4 6v12"></path><path d="M4 12h7"></path><path d="M4 18h7"></path><path d="M11 4l7 5-7 5"></path>',
        h3: '<path d="M4 6v12"></path><path d="M4 12h8"></path><path d="M4 18h8"></path><path d="M12 6l4 3-4 3 4 3-4 3"></path>',
        ul: '<path d="M8 6h13"></path><path d="M8 12h13"></path><path d="M8 18h13"></path><path d="M3 6h.01"></path><path d="M3 12h.01"></path><path d="M3 18h.01"></path>',
        ol: '<path d="M11 6h10"></path><path d="M11 12h10"></path><path d="M11 18h10"></path><path d="M4 6h1v1H4z"></path><path d="M4 12h1v1H4z"></path><path d="M4 18h1v1H4z"></path>',
        quote: '<path d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V20c0 1 0 1 1 1z"></path><path d="M15 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2h.75c0 2.25.25 4-2.75 4v3c0 1 0 1 1 1z"></path>',
        link: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>',
        code: '<path d="m16 18 6-6-6-6"></path><path d="m8 6-6 6 6 6"></path>',
        table: '<path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"></path>',
        alignLeft: '<path d="M21 10H3"></path><path d="M21 6H3"></path><path d="M21 14H3"></path><path d="M21 18H3"></path>',
        alignCenter: '<path d="M18 10H6"></path><path d="M21 6H3"></path><path d="M21 14H3"></path><path d="M18 18H6"></path>',
        alignRight: '<path d="M21 10h-4"></path><path d="M21 6H3"></path><path d="M21 14h-4"></path><path d="M21 18h-4"></path>',
        removeFormat: '<path d="M4 7V4h16v3"></path><path d="M5 20h6"></path><path d="M13 4 9 20"></path><path d="M14 11l6-7"></path><path d="M14 18l6-7"></path>',
        undo: '<path d="M3 7v6h6"></path><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"></path>',
        redo: '<path d="M21 7v6h-6"></path><path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3L21 13"></path>'
      };
      
      const path = icons[type] || '';
      return `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${path}</svg>`;
    }
    
    /**
     * Create editor structure
     */
    createEditor() {
      // Create wrapper
      this.wrapper = document.createElement('div');
      this.wrapper.className = 'df-rich-editor-wrapper';
      
      // Create toolbar
      this.toolbar = document.createElement('div');
      this.toolbar.className = 'df-rich-editor-toolbar';
      this.createToolbar();
      
      // Create content area
      this.content = document.createElement('div');
      this.content.className = 'df-rich-editor-content';
      this.content.contentEditable = true;
      this.content.innerHTML = this.textarea.value || '';
      this.content.setAttribute('data-placeholder', 'Nhập nội dung bài học...');
      
      // Create status bar
      const statusBar = this.createStatusBar();
      
      // Assemble
      this.wrapper.appendChild(this.toolbar);
      this.wrapper.appendChild(this.content);
      this.wrapper.appendChild(statusBar);
      
      // Insert into DOM
      const fieldContent = this.textarea.closest('.field-content') || this.textarea.parentElement;
      if (fieldContent) {
        fieldContent.appendChild(this.wrapper);
      } else {
        this.textarea.parentElement.insertBefore(this.wrapper, this.textarea.nextSibling);
      }
    }
    
    /**
     * Create toolbar buttons
     */
    createToolbar() {
      this.commands.forEach(cmd => {
        if (cmd.type === 'divider') {
          const divider = document.createElement('div');
          divider.className = 'df-rich-editor-divider';
          this.toolbar.appendChild(divider);
        } else {
          const button = this.createButton(cmd);
          this.toolbar.appendChild(button);
        }
      });
    }
    
    /**
     * Create toolbar button
     */
    createButton(cmd) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'df-rich-editor-btn';
      button.innerHTML = cmd.icon;
      button.title = cmd.title + (cmd.shortcut ? ` (Ctrl+${cmd.shortcut.toUpperCase()})` : '');
      button.setAttribute('data-cmd', cmd.id);
      
      button.addEventListener('click', (e) => {
        e.preventDefault();
        this.handleCommand(cmd);
      });
      
      return button;
    }
    
    /**
     * Create status bar with character count
     */
    createStatusBar() {
      const statusBar = document.createElement('div');
      statusBar.className = 'df-rich-editor-status';
      
      const charCount = document.createElement('div');
      charCount.className = 'df-rich-editor-charcount';
      charCount.textContent = '0 ký tự';
      
      statusBar.appendChild(charCount);
      
      // Store reference for update function
      this.charCountElement = charCount;
      
      return statusBar;
    }
    
    /**
     * Update character count
     */
    updateCharCount() {
      if (!this.charCountElement) return;
      const text = this.content.innerText || '';
      const count = text.length;
      this.charCountElement.textContent = `${count.toLocaleString()} ký tự`;
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
      // Content sync
      this.content.addEventListener('input', () => {
        this.syncContent();
        this.updateCharCount();
        this.updateToolbar();
      });
      
      // Paste handling - strip formatting by default
      this.content.addEventListener('paste', (e) => {
        e.preventDefault();
        const text = (e.clipboardData || window.clipboardData).getData('text/plain');
        document.execCommand('insertText', false, text);
        this.syncContent();
        this.updateCharCount();
      });
      
      // Keyboard shortcuts
      this.content.addEventListener('keydown', (e) => {
        this.handleKeyboardShortcuts(e);
      });
      
      // Selection change
      this.content.addEventListener('mouseup', () => this.updateToolbar());
      this.content.addEventListener('keyup', () => this.updateToolbar());
      
      // Form submit
      const form = this.textarea.closest('form');
      if (form) {
        form.addEventListener('submit', () => {
          this.syncContent();
        });
      }
      
      // Initial character count
      this.updateCharCount();
    }
    
    /**
     * Handle keyboard shortcuts
     */
    handleKeyboardShortcuts(e) {
      const ctrl = e.ctrlKey || e.metaKey;
      
      if (!ctrl) {
        setTimeout(() => {
          this.syncContent();
          this.updateCharCount();
        }, 0);
        return;
      }
      
      // Find command by shortcut
      const cmd = this.commands.find(c => c.shortcut === e.key.toLowerCase());
      if (cmd && !cmd.custom) {
        e.preventDefault();
        this.handleCommand(cmd);
        return;
      }
      
      // Special shortcuts
      if (e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        document.execCommand('undo');
        this.syncContent();
        this.updateCharCount();
      } else if ((e.key === 'y') || (e.key === 'z' && e.shiftKey)) {
        e.preventDefault();
        document.execCommand('redo');
        this.syncContent();
        this.updateCharCount();
      } else if (e.key === 'k') {
        e.preventDefault();
        this.insertLink();
      } else if (e.key === 't') {
        e.preventDefault();
        this.insertTable();
      }
    }
    
    /**
     * Handle command execution
     */
    handleCommand(cmd) {
      if (cmd.custom) {
        if (cmd.id === 'link') {
          this.insertLink();
        } else if (cmd.id === 'table') {
          this.insertTable();
        }
      } else {
        document.execCommand(cmd.cmd, false, cmd.value || null);
        this.content.focus();
        this.syncContent();
        this.updateCharCount();
        this.updateToolbar();
      }
    }
    
    /**
     * Insert link
     */
    insertLink() {
      const url = prompt('Nhập URL:', 'https://');
      if (url && url.trim()) {
        document.execCommand('createLink', false, url.trim());
        this.syncContent();
        this.updateCharCount();
      }
    }
    
    /**
     * Insert table
     */
    insertTable() {
      // Save current cursor position before opening dialog
      // First, ensure content is focused to get accurate cursor position
      this.content.focus();
      
      // Small delay to ensure focus is set
      setTimeout(() => {
        const selection = window.getSelection();
        let savedRange = null;
        
        if (selection.rangeCount > 0) {
          const currentRange = selection.getRangeAt(0);
          // Check if range is within content area
          let container = currentRange.commonAncestorContainer;
          if (container.nodeType === Node.TEXT_NODE) {
            container = container.parentNode;
          }
          
          if (this.content.contains(container) || container === this.content) {
            savedRange = currentRange.cloneRange();
          }
        }
        
        // If no valid selection, create range at current cursor position
        if (!savedRange) {
          const range = document.createRange();
          // Try to find the current position by checking if there's a text node
          const walker = document.createTreeWalker(
            this.content,
            NodeFilter.SHOW_TEXT,
            null,
            false
          );
          
          let textNode = walker.nextNode();
          if (textNode) {
            range.setStart(textNode, textNode.textContent.length);
            range.collapse(true);
          } else {
            // No text node, set at end of content
            range.selectNodeContents(this.content);
            range.collapse(false);
          }
          savedRange = range;
        }
        
        // Store saved range for later use
        this.savedRange = savedRange;
        
        // Create modal dialog
        const modal = this.createTableDialog();
        document.body.appendChild(modal);
        
        // Show modal
        modal.style.display = 'flex';
        modal.querySelector('.df-table-dialog-input-rows').focus();
        
        // Handle form submission
        const form = modal.querySelector('.df-table-dialog-form');
        form.addEventListener('submit', (e) => {
          e.preventDefault();
          const rows = parseInt(modal.querySelector('.df-table-dialog-input-rows').value) || 3;
          const cols = parseInt(modal.querySelector('.df-table-dialog-input-cols').value) || 3;
          
          if (rows > 0 && cols > 0 && rows <= 20 && cols <= 20) {
            const tableHTML = this.generateTableHTML(rows, cols);
            this.insertHTMLAtSavedPosition(tableHTML);
            setTimeout(() => {
              if (document.body.contains(modal)) {
                document.body.removeChild(modal);
              }
            }, 100);
          } else {
            alert('Vui lòng nhập số hàng và cột từ 1 đến 20');
          }
        });
        
        // Handle cancel
        const cancelBtn = modal.querySelector('.df-table-dialog-cancel');
        cancelBtn.addEventListener('click', () => {
          this.savedRange = null; // Clear saved range
          if (document.body.contains(modal)) {
            document.body.removeChild(modal);
          }
        });
        
        // Close on backdrop click
        modal.addEventListener('click', (e) => {
          if (e.target === modal) {
            this.savedRange = null; // Clear saved range
            if (document.body.contains(modal)) {
              document.body.removeChild(modal);
            }
          }
        });
        
        // Close on Escape
        const handleEscape = (e) => {
          if (e.key === 'Escape') {
            this.savedRange = null; // Clear saved range
            if (document.body.contains(modal)) {
              document.body.removeChild(modal);
            }
            document.removeEventListener('keydown', handleEscape);
          }
        };
        document.addEventListener('keydown', handleEscape);
      }, 10);
      
      // Create modal dialog
      const modal = this.createTableDialog();
      document.body.appendChild(modal);
      
      // Show modal
      modal.style.display = 'flex';
      modal.querySelector('.df-table-dialog-input-rows').focus();
      
      // Handle form submission
      const form = modal.querySelector('.df-table-dialog-form');
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        const rows = parseInt(modal.querySelector('.df-table-dialog-input-rows').value) || 3;
        const cols = parseInt(modal.querySelector('.df-table-dialog-input-cols').value) || 3;
        
        if (rows > 0 && cols > 0 && rows <= 20 && cols <= 20) {
          const tableHTML = this.generateTableHTML(rows, cols);
          this.insertHTMLAtSavedPosition(tableHTML);
          setTimeout(() => {
            if (document.body.contains(modal)) {
              document.body.removeChild(modal);
            }
          }, 100);
        } else {
          alert('Vui lòng nhập số hàng và cột từ 1 đến 20');
        }
      });
      
      // Handle cancel
      const cancelBtn = modal.querySelector('.df-table-dialog-cancel');
      cancelBtn.addEventListener('click', () => {
        this.savedRange = null; // Clear saved range
        if (document.body.contains(modal)) {
          document.body.removeChild(modal);
        }
      });
      
      // Close on backdrop click
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          this.savedRange = null; // Clear saved range
          if (document.body.contains(modal)) {
            document.body.removeChild(modal);
          }
        }
      });
      
      // Close on Escape
      const handleEscape = (e) => {
        if (e.key === 'Escape') {
          this.savedRange = null; // Clear saved range
          if (document.body.contains(modal)) {
            document.body.removeChild(modal);
          }
          document.removeEventListener('keydown', handleEscape);
        }
      };
      document.addEventListener('keydown', handleEscape);
    }
    
    /**
     * Create table dialog
     */
    createTableDialog() {
      const modal = document.createElement('div');
      modal.className = 'df-table-dialog-overlay';
      
      modal.innerHTML = `
        <div class="df-table-dialog">
          <div class="df-table-dialog-header">
            <h3>Chèn bảng</h3>
            <button type="button" class="df-table-dialog-close" aria-label="Đóng">×</button>
          </div>
          <form class="df-table-dialog-form">
            <div class="df-table-dialog-body">
              <div class="df-table-dialog-field">
                <label>Số hàng:</label>
                <input type="number" class="df-table-dialog-input-rows" min="1" max="20" value="3" required>
              </div>
              <div class="df-table-dialog-field">
                <label>Số cột:</label>
                <input type="number" class="df-table-dialog-input-cols" min="1" max="20" value="3" required>
              </div>
            </div>
            <div class="df-table-dialog-footer">
              <button type="button" class="df-table-dialog-cancel">Hủy</button>
              <button type="submit" class="df-table-dialog-submit">Chèn</button>
            </div>
          </form>
        </div>
      `;
      
      // Close button
      modal.querySelector('.df-table-dialog-close').addEventListener('click', () => {
        document.body.removeChild(modal);
      });
      
      return modal;
    }
    
    /**
     * Generate table HTML
     */
    generateTableHTML(rows, cols) {
      let html = '<table>';
      
      // Header row
      html += '<thead><tr>';
      for (let i = 0; i < cols; i++) {
        html += '<th>&nbsp;</th>';
      }
      html += '</tr></thead>';
      
      // Body rows
      html += '<tbody>';
      for (let i = 0; i < rows - 1; i++) {
        html += '<tr>';
        for (let j = 0; j < cols; j++) {
          html += '<td>&nbsp;</td>';
        }
        html += '</tr>';
      }
      html += '</tbody>';
      
      html += '</table>';
      return html;
    }
    
    /**
     * Insert HTML at saved cursor position
     */
    insertHTMLAtSavedPosition(html) {
      // Ensure content is focused
      this.content.focus();
      
      // Use saved range if available
      let range = null;
      if (this.savedRange) {
        try {
          // Check if saved range is still valid
          const container = this.savedRange.commonAncestorContainer;
          if (container && (this.content.contains(container) || container === this.content)) {
            range = this.savedRange;
          }
        } catch (e) {
          // Range is no longer valid, will use current selection
        }
      }
      
      // If no saved range or invalid, try to get current selection
      if (!range) {
        const selection = window.getSelection();
        if (selection.rangeCount > 0) {
          range = selection.getRangeAt(0);
        }
      }
      
      // If still no range, create one at cursor position
      if (!range) {
        range = document.createRange();
        range.selectNodeContents(this.content);
        range.collapse(false);
      }
      
      // Ensure range is within content area
      let container = range.commonAncestorContainer;
      if (container.nodeType === Node.TEXT_NODE) {
        container = container.parentNode;
      }
      
      if (!this.content.contains(container) && container !== this.content) {
        // Fallback: append to end
        this.insertHTMLAtEnd(html);
        return;
      }
      
      // Delete any selected content
      range.deleteContents();
      
      // Create a temporary container to parse HTML
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = html;
      
      // Insert all nodes from tempDiv
      const nodes = Array.from(tempDiv.childNodes);
      let lastNode = null;
      
      nodes.forEach((node) => {
        const clonedNode = node.cloneNode(true);
        try {
          range.insertNode(clonedNode);
          lastNode = clonedNode;
          // Move range after inserted node
          range.setStartAfter(clonedNode);
          range.collapse(false);
        } catch (e) {
          console.warn('Error inserting node:', e);
        }
      });
      
      // Update selection
      const selection = window.getSelection();
      if (lastNode) {
        const newRange = document.createRange();
        newRange.setStartAfter(lastNode);
        newRange.collapse(false);
        selection.removeAllRanges();
        selection.addRange(newRange);
      }
      
      // Clear saved range
      this.savedRange = null;
      
      this.syncContent();
      this.updateCharCount();
      this.content.focus();
    }
    
    /**
     * Insert HTML at cursor position (legacy method, kept for compatibility)
     */
    insertHTML(html) {
      this.insertHTMLAtSavedPosition(html);
    }
    
    /**
     * Insert HTML at end of content
     */
    insertHTMLAtEnd(html) {
      // Add a paragraph break if content exists
      const currentHTML = this.content.innerHTML.trim();
      if (currentHTML) {
        this.content.innerHTML = currentHTML + '<p><br></p>' + html;
      } else {
        this.content.innerHTML = html;
      }
      
      // Move cursor to end after a short delay
      setTimeout(() => {
        const range = document.createRange();
        const selection = window.getSelection();
        
        // Find the last table or last element
        const tables = this.content.querySelectorAll('table');
        if (tables.length > 0) {
          const lastTable = tables[tables.length - 1];
          range.setStartAfter(lastTable);
          range.collapse(false);
        } else {
          range.selectNodeContents(this.content);
          range.collapse(false);
        }
        
        selection.removeAllRanges();
        selection.addRange(range);
        this.content.focus();
        this.syncContent();
        this.updateCharCount();
      }, 10);
    }
    
    /**
     * Update toolbar button states
     */
    updateToolbar() {
      this.commands.forEach(cmd => {
        if (cmd.type === 'divider' || cmd.custom) return;
        
        const button = this.toolbar.querySelector(`[data-cmd="${cmd.id}"]`);
        if (!button) return;
        
        if (cmd.state) {
          const isActive = document.queryCommandState(cmd.cmd);
          button.classList.toggle('active', isActive);
        }
      });
    }
    
    /**
     * Sync content to hidden textarea
     */
    syncContent() {
      this.textarea.value = this.content.innerHTML;
    }
  }
})();
