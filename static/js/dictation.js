/**
 * Dictation Exercise Application
 * Refactored into modular classes for better maintainability
 */

// ==========================================
// Utility Functions
// ==========================================

function formatTime(s) {
  if (isNaN(s)) return "00:00";
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m < 10 ? '0' + m : m}:${sec < 10 ? '0' + sec : sec}`;
}

function diffString(userText, correctText) {
  const u = userText.trim().split(/\s+/);
  const c = correctText.trim().split(/\s+/);
  let html = '';
  const len = Math.max(u.length, c.length);

  for (let i = 0; i < len; i++) {
    const uw = u[i] || '';
    const cw = c[i] || '';
    if (uw.toLowerCase() === cw.toLowerCase()) {
      html += `<span class="text-emerald-600">${cw}</span> `;
    } else {
      if (uw) html += `<del class="text-rose-400 decoration-rose-300 decoration-2">${uw}</del> `;
      if (cw) html += `<ins class="text-blue-600 no-underline font-semibold">${cw}</ins> `;
    }
  }
  return html.trim();
}

// ==========================================
// Audio Seeker Class
// ==========================================

class AudioSeeker {
  constructor(audio) {
    this.audio = audio;
  }

  /**
   * Check if audio is ready for seeking
   */
  checkAudioReady(targetTime) {
    const source = this.audio.querySelector('source');
    const src = source ? source.src : this.audio.src;

    console.log('[AudioSeeker] Audio state check:', {
      src: src || '(empty)',
      readyState: this.audio.readyState,
      networkState: this.audio.networkState,
      duration: this.audio.duration,
      currentTime: this.audio.currentTime,
      error: this.audio.error ? this.audio.error.message : null
    });

    // Check if src is set
    if (!src || src === '') {
      console.error('[AudioSeeker] Audio src is empty!');
      return false;
    }

    // Only set audio.src if it's truly empty
    if (!this.audio.src || this.audio.src === '' || this.audio.src === window.location.href) {
      console.log('[AudioSeeker] Setting audio.src from source element (was empty)');
      this.audio.src = src;
      return false;
    }

    // Check if audio has metadata
    if (!this.audio.duration || isNaN(this.audio.duration) || this.audio.duration === 0) {
      console.warn('[AudioSeeker] Audio duration not available');
      return false;
    }

    // Check if target time is valid
    if (targetTime < 0 || targetTime >= this.audio.duration) {
      console.error('[AudioSeeker] Invalid target time:', targetTime);
      return false;
    }

    // Check readyState
    if (this.audio.readyState < 2) {
      console.warn('[AudioSeeker] Audio readyState too low:', this.audio.readyState);
      return false;
    }

    return true;
  }

  /**
   * Seek to target time and play
   */
  async seekAndPlay(targetTime, endTime, onPlay, onEnd) {
    const seekAndPlayInternal = () => {
      if (!this.checkAudioReady(targetTime)) {
        console.log('[AudioSeeker] Audio not ready, waiting...');
        const onCanPlay = () => {
          console.log('[AudioSeeker] Audio can play');
          this.audio.removeEventListener('canplay', onCanPlay);
          setTimeout(seekAndPlayInternal, 100);
        };
        this.audio.addEventListener('canplay', onCanPlay, { once: true });

        if (this.audio.networkState === 0 || this.audio.networkState === 3) {
          console.log('[AudioSeeker] Forcing audio load');
          this.audio.load();
        }
        return;
      }

      console.log('[AudioSeeker] Attempting to seek to:', targetTime);
      this.audio.currentTime = targetTime;

      // Use seeked event + polling
      let seekCompleted = false;
      const onSeeked = () => {
        const seekedTime = this.audio.currentTime;
        const diff = Math.abs(seekedTime - targetTime);
        console.log('[AudioSeeker] seeked event, diff:', diff);

        seekCompleted = true;
        this.audio.removeEventListener('seeked', onSeeked);

        if (diff < 0.3) {
          console.log('[AudioSeeker] Seek successful!');
          this.startPlayback(endTime, onPlay, onEnd);
        } else {
          console.warn('[AudioSeeker] Seek time wrong, trying play-then-seek...');
          this.playThenSeek(targetTime, endTime, onPlay, onEnd);
        }
      };
      this.audio.addEventListener('seeked', onSeeked, { once: true });

      // Polling backup
      let attempts = 0;
      const maxAttempts = 50;
      const poll = setInterval(() => {
        if (seekCompleted) {
          clearInterval(poll);
          return;
        }

        attempts++;
        const currentTime = this.audio.currentTime;
        const diff = Math.abs(currentTime - targetTime);

        if (diff < 0.3 || attempts >= maxAttempts) {
          clearInterval(poll);
          this.audio.removeEventListener('seeked', onSeeked);

          if (diff < 0.3) {
            seekCompleted = true;
            this.startPlayback(endTime, onPlay, onEnd);
          } else if (attempts >= maxAttempts) {
            console.warn('[AudioSeeker] Seek timeout, forcing...');
            this.audio.currentTime = targetTime;
            setTimeout(() => {
              this.startPlayback(endTime, onPlay, onEnd);
            }, 200);
          }
        }
      }, 50);
    };

    if (this.checkAudioReady(targetTime)) {
      setTimeout(seekAndPlayInternal, 50);
    } else {
      seekAndPlayInternal();
    }
  }

  /**
   * Play-then-seek approach for browsers that need it
   */
  async playThenSeek(targetTime, endTime, onPlay, onEnd) {
    try {
      await this.audio.play();
      this.audio.pause();
      setTimeout(() => {
        this.audio.currentTime = targetTime;
        setTimeout(() => {
          const diff = Math.abs(this.audio.currentTime - targetTime);
          if (diff < 0.5) {
            this.startPlayback(endTime, onPlay, onEnd);
          } else {
            console.error('[AudioSeeker] Play-then-seek failed, proceeding anyway');
            this.startPlayback(endTime, onPlay, onEnd);
          }
        }, 100);
      }, 50);
    } catch (e) {
      console.error('[AudioSeeker] Play error:', e);
      this.startPlayback(endTime, onPlay, onEnd);
    }
  }

  /**
   * Start playback and monitor end time
   */
  startPlayback(endTime, onPlay, onEnd) {
    this.audio.play().then(() => {
      console.log('[AudioSeeker] Playback started at:', this.audio.currentTime);
      if (onPlay) onPlay();

      const checkInterval = setInterval(() => {
        if (!this.audio.paused && this.audio.currentTime >= endTime) {
          console.log('[AudioSeeker] Reached end time');
          this.audio.pause();
          clearInterval(checkInterval);
          if (onEnd) onEnd();
        }
      }, 50);
    }).catch(e => {
      console.error('[AudioSeeker] Play error:', e);
    });
  }
}

// ==========================================
// Dictation Mode Class
// ==========================================

class DictationMode {
  constructor(audio, segments, elements) {
    this.audio = audio;
    this.segments = segments;
    this.elements = elements;
    this.seeker = new AudioSeeker(audio);

    this.currentIndex = 0;
    this.isSlow = false;
    this.isChecked = false;
    this.correctCount = 0;
    this.checkInterval = null;

    this.setupEventListeners();
  }

  setupEventListeners() {
    this.elements.btnPlay.addEventListener('click', () => {
      if (!this.audio.paused) {
        this.audio.pause();
      } else {
        this.playCurrentSegment();
      }
    });

    this.elements.btnSlow.addEventListener('click', () => {
      this.isSlow = !this.isSlow;
      this.elements.btnSlow.classList.toggle('bg-blue-50', this.isSlow);
      this.elements.btnSlow.classList.toggle('border-blue-300', this.isSlow);
      this.elements.btnSlow.classList.toggle('text-blue-600', this.isSlow);
    });

    this.elements.btnCheck.addEventListener('click', () => this.checkAnswer());
    this.elements.btnNext.addEventListener('click', () => this.nextSegment());

    this.elements.userInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!this.isChecked) {
          this.checkAnswer();
        } else {
          this.nextSegment();
        }
      }
    });
  }

  render() {
    if (this.currentIndex >= this.segments.length) {
      this.showSummary();
      return;
    }

    const seg = this.segments[this.currentIndex];

    this.isChecked = false;
    this.elements.userInput.value = '';
    this.elements.userInput.disabled = false;
    this.elements.btnCheck.classList.remove('hidden');
    this.elements.btnNext.classList.add('hidden');
    this.elements.feedback.classList.add('hidden');

    if (seg.hint) {
      this.elements.hintText.textContent = '💡 ' + seg.hint;
      this.elements.hintText.classList.remove('hidden');
    } else {
      this.elements.hintText.classList.add('hidden');
    }

    this.elements.progressText.textContent = `${this.currentIndex + 1} / ${this.segments.length}`;
    this.elements.progressBar.style.width = `${(this.currentIndex / this.segments.length) * 100}%`;
  }

  playCurrentSegment() {
    if (this.currentIndex >= this.segments.length) return;

    const seg = this.segments[this.currentIndex];
    const targetTime = parseFloat(seg.start_time);
    const endTime = parseFloat(seg.end_time);

    console.log('[DictationMode] Playing segment:', this.currentIndex, seg);

    if (this.checkInterval) clearInterval(this.checkInterval);

    this.audio.pause();
    this.audio.playbackRate = this.isSlow ? 0.7 : 1.0;

    this.seeker.seekAndPlay(
      targetTime,
      endTime,
      () => this.updateVisualizer(true),
      () => this.updateVisualizer(false)
    );
  }

  updateVisualizer(playing) {
    if (playing) {
      this.elements.viz.classList.remove('paused');
    } else {
      this.elements.viz.classList.add('paused');
    }
  }

  checkAnswer() {
    if (this.isChecked) return;
    this.isChecked = true;

    const seg = this.segments[this.currentIndex];
    const userText = this.elements.userInput.value.trim();
    const normalize = s => s.toLowerCase().replace(/[.,?!'"]/g, '');
    const isCorrect = normalize(userText) === normalize(seg.correct_text);

    if (isCorrect) this.correctCount++;

    this.elements.feedback.classList.remove('hidden');
    if (isCorrect) {
      this.elements.feedbackContent.innerHTML = `
        <div class="text-emerald-600 font-bold flex items-center gap-2">
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
          </svg>
          Chính xác!
        </div>
        <div class="mt-1 text-slate-800">${seg.correct_text}</div>
      `;
    } else {
      this.elements.feedbackContent.innerHTML = `
        <div class="text-rose-500 font-bold mb-2">Chưa đúng</div>
        <div class="leading-relaxed bg-slate-50 p-2 rounded">${diffString(userText, seg.correct_text)}</div>
      `;
    }

    this.elements.userInput.disabled = true;
    this.elements.btnCheck.classList.add('hidden');
    this.elements.btnNext.classList.remove('hidden');
    this.elements.btnNext.focus();
  }

  nextSegment() {
    this.currentIndex++;
    this.render();
    this.playCurrentSegment();
  }

  showSummary() {
    this.elements.exerciseApp.classList.add('hidden');
    this.elements.summaryScreen.classList.remove('hidden');
    this.elements.progressBar.style.width = '100%';
    this.elements.finalScore.textContent = `${this.correctCount} / ${this.segments.length} câu đúng`;
  }
}

// ==========================================
// Transcript Mode Class
// ==========================================

class TranscriptMode {
  constructor(audio, segments, elements) {
    this.audio = audio;
    this.segments = segments;
    this.elements = elements;
    this.seeker = new AudioSeeker(audio);

    this.activeIndex = -1;
    this.checkInterval = null;

    this.setupEventListeners();
    this.renderList();
  }

  setupEventListeners() {
    this.elements.btnPlay.addEventListener('click', () => {
      if (this.audio.paused) {
        this.audio.play();
      } else {
        this.audio.pause();
      }
    });

    if (this.elements.btnReplay) {
      this.elements.btnReplay.addEventListener('click', () => {
        if (this.activeIndex >= 0) {
          this.playSegment(this.activeIndex);
        }
      });
    }

    this.elements.btnPrev.addEventListener('click', () => {
      let target = this.activeIndex - 1;
      if (target < 0) target = 0;
      this.playSegment(target);
    });

    this.elements.btnNext.addEventListener('click', () => {
      let target = this.activeIndex + 1;
      if (target >= this.segments.length) target = 0;
      this.playSegment(target);
    });

    this.elements.progressContainer.addEventListener('click', (e) => {
      const rect = e.currentTarget.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const pct = x / rect.width;
      this.audio.currentTime = pct * this.audio.duration;
    });

    // Update progress bar on timeupdate
    this.audio.addEventListener('timeupdate', () => {
      const cur = this.audio.currentTime;
      const dur = this.audio.duration;

      if (dur > 0) {
        const pct = (cur / dur) * 100;
        this.elements.progressBar.style.width = `${pct}%`;
        this.elements.currentTime.textContent = formatTime(cur);
      }

      const idx = this.segments.findIndex(s => cur >= s.start_time && cur < s.end_time);
      if (idx !== -1) {
        this.highlightItem(idx);
      }
    });

    this.audio.addEventListener('play', () => this.updatePlayButton(true));
    this.audio.addEventListener('pause', () => this.updatePlayButton(false));
    this.audio.addEventListener('ended', () => {
      this.updatePlayButton(false);
    });

    // Set total time when metadata loads
    const onMeta = () => {
      this.elements.totalTime.textContent = formatTime(this.audio.duration);
    };
    this.audio.addEventListener('loadedmetadata', onMeta);
    if (this.audio.readyState >= 1) onMeta();
  }

  renderList() {
    this.elements.list.innerHTML = '';
    this.segments.forEach((seg, idx) => {
      const div = document.createElement('div');
      div.className = `transcript-item group flex gap-3 rounded-lg cursor-pointer`;
      div.dataset.index = idx;

      div.innerHTML = `
        <div class="flex items-center gap-3 pt-0.5">
          <button class="play-btn w-8 h-8 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center hover:bg-blue-200 hover:scale-105 transition-all" title="Phát">
            <svg class="w-4 h-4 ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          </button>
        </div>
        <div class="t-text flex-1 text-slate-600 text-[15px] leading-relaxed select-text">${seg.correct_text}</div>
      `;

      div.querySelector('.play-btn').onclick = (e) => {
        e.stopPropagation();
        this.playSegment(idx);
      };
      div.querySelector('.t-text').onclick = () => {
        this.playSegment(idx);
      };

      this.elements.list.appendChild(div);
    });
  }

  playSegment(idx) {
    if (idx < 0 || idx >= this.segments.length) return;

    const seg = this.segments[idx];
    const targetTime = parseFloat(seg.start_time);
    const endTime = parseFloat(seg.end_time);

    console.log('[TranscriptMode] Playing segment:', idx, seg);

    if (this.checkInterval) clearInterval(this.checkInterval);

    this.highlightItem(idx);
    this.audio.pause();
    this.audio.playbackRate = 1.0;

    this.seeker.seekAndPlay(
      targetTime,
      endTime,
      () => this.updatePlayButton(true),
      () => {
        this.updatePlayButton(false);
        this.checkInterval = null;
      }
    );
  }

  highlightItem(idx) {
    if (this.activeIndex === idx) return;
    this.activeIndex = idx;

    Array.from(this.elements.list.children).forEach((el, i) => {
      if (i === idx) {
        el.classList.add('active');
        if (this.elements.autoScroll.checked) {
          el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      } else {
        el.classList.remove('active');
      }
    });

    if (idx >= 0 && this.segments[idx]) {
      this.elements.activeText.textContent = this.segments[idx].correct_text;
    }
  }

  updatePlayButton(playing) {
    if (playing) {
      this.elements.btnPlay.innerHTML = '<svg class="w-8 h-8" fill="currentColor" viewBox="0 0 24 24"><path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/></svg>';
    } else {
      this.elements.btnPlay.innerHTML = '<svg class="w-8 h-8 ml-1" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>';
    }
  }
}

// ==========================================
// Main Dictation App Class
// ==========================================

class DictationApp {
  constructor(config) {
    this.segments = config.segments;
    this.audio = config.audio;

    // Initialize modes
    this.dictationMode = new DictationMode(this.audio, this.segments, config.dictationElements);
    this.transcriptMode = new TranscriptMode(this.audio, this.segments, config.transcriptElements);

    // Set initial mode
    this.dictationMode.render();
  }

  switchTab(tabName) {
    document.querySelectorAll('.tab-pane').forEach(el => {
      el.classList.add('hidden');
      el.classList.remove('animate-fade-in-up');
    });
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

    const pane = document.getElementById('view-' + tabName);
    pane.classList.remove('hidden');
    void pane.offsetWidth;
    pane.classList.add('animate-fade-in-up');

    document.getElementById('tab-btn-' + tabName).classList.add('active');

    if (!this.audio.paused) this.audio.pause();
  }
}

// Export for global use
window.DictationApp = DictationApp;
window.switchTab = null; // Will be set by init function

