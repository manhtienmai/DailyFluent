/**
 * ck-audio-player.js — Global sticky audio player for DailyFluent Choukai
 *
 * Registers an Alpine.store('player', {...}) that any component can call:
 *   Alpine.store('player').play(url, label)
 *
 * Include this BEFORE Alpine CDN (or use Alpine.data).
 */

document.addEventListener('alpine:init', () => {
  Alpine.store('player', {
    src: '',
    label: '',
    visible: false,
    playing: false,
    currentTime: 0,
    duration: 0,
    buffered: 0,
    speed: 1,
    showSpeedMenu: false,
    speeds: [0.5, 0.75, 1, 1.25, 1.5, 2],
    _audio: null,
    _raf: null,

    /* Initialise the <audio> element (called once from x-init on the player bar) */
    initAudio(audioEl) {
      this._audio = audioEl;
      audioEl.addEventListener('loadedmetadata', () => {
        this.duration = audioEl.duration || 0;
      });
      audioEl.addEventListener('ended', () => {
        this.playing = false;
        this.currentTime = this.duration;
        this._stopTick();
      });
      audioEl.addEventListener('progress', () => {
        if (audioEl.buffered.length > 0) {
          this.buffered = audioEl.buffered.end(audioEl.buffered.length - 1);
        }
      });
    },

    /* Public API — call from any question card */
    play(url, label) {
      if (!url) return;
      const changed = url !== this.src;
      this.src = url;
      this.label = label || '';
      this.visible = true;

      if (this._audio) {
        if (changed) {
          this._audio.src = url;
          this._audio.playbackRate = this.speed;
          this.currentTime = 0;
          this.duration = 0;
          this.buffered = 0;
        }
        this._audio.play().then(() => {
          this.playing = true;
          this._startTick();
        }).catch(() => {});
      }
    },

    togglePlay() {
      if (!this._audio || !this.src) return;
      if (this.playing) {
        this._audio.pause();
        this.playing = false;
        this._stopTick();
      } else {
        this._audio.play().then(() => {
          this.playing = true;
          this._startTick();
        }).catch(() => {});
      }
    },

    seek(e) {
      if (!this._audio || !this.duration) return;
      const rect = e.currentTarget.getBoundingClientRect();
      const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
      this._audio.currentTime = pct * this.duration;
      this.currentTime = this._audio.currentTime;
    },

    skip(seconds) {
      if (!this._audio) return;
      this._audio.currentTime = Math.max(0, Math.min(this.duration || 9999, this._audio.currentTime + seconds));
      this.currentTime = this._audio.currentTime;
    },

    setSpeed(s) {
      this.speed = s;
      if (this._audio) this._audio.playbackRate = s;
      this.showSpeedMenu = false;
    },

    close() {
      if (this._audio) {
        this._audio.pause();
        this._audio.src = '';
      }
      this.playing = false;
      this.visible = false;
      this.src = '';
      this._stopTick();
    },

    get progressPct() {
      if (!this.duration) return 0;
      return (this.currentTime / this.duration) * 100;
    },

    get bufferedPct() {
      if (!this.duration) return 0;
      return (this.buffered / this.duration) * 100;
    },

    fmtTime(sec) {
      if (!sec || !isFinite(sec)) return '0:00';
      const m = Math.floor(sec / 60);
      const s = Math.floor(sec % 60);
      return m + ':' + String(s).padStart(2, '0');
    },

    _startTick() {
      this._stopTick();
      const tick = () => {
        if (!this.playing) return;
        this.currentTime = this._audio ? this._audio.currentTime : 0;
        this._raf = requestAnimationFrame(tick);
      };
      tick();
    },

    _stopTick() {
      if (this._raf) {
        cancelAnimationFrame(this._raf);
        this._raf = null;
      }
    },
  });
});
