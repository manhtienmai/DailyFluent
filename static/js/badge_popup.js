/**
 * Badge Popup Manager
 * Handles displaying badge popups with queueing support.
 */

window.BadgeManager = (function() {
    let queue = [];
    let isShowing = false;
    let confettiInstance = null;
    
    // DOM Elements
    const elements = {
        overlay: null,
        backdrop: null,
        panel: null,
        icon: null,
        title: null,
        desc: null,
        closeBtn: null,
        canvas: null
    };
    
    function init() {
        elements.overlay = document.getElementById('badge-popup-overlay');
        elements.backdrop = document.getElementById('badge-popup-backdrop');
        elements.panel = document.getElementById('badge-popup-panel');
        elements.icon = document.getElementById('badge-popup-icon');
        elements.title = document.getElementById('badge-popup-title');
        elements.desc = document.getElementById('badge-popup-desc');
        elements.closeBtn = document.getElementById('badge-popup-close');
        elements.canvas = document.getElementById('badge-confetti');
        
        if (elements.closeBtn) {
            elements.closeBtn.addEventListener('click', hide);
        }

        // Initialize confetti if library exists (optional)
        if (typeof confetti !== 'undefined' && elements.canvas) {
            confettiInstance = confetti.create(elements.canvas, {
                resize: true,
                useWorker: true
            });
        }
    }
    
    function show(badge) {
        if (!elements.overlay) init();
        if (!elements.overlay) return; // Guard if template not present

        // Set content
        elements.icon.textContent = badge.icon || '🏆';
        elements.title.textContent = badge.name || 'New Badge';
        elements.desc.textContent = badge.description || '';
        
        // Show
        elements.overlay.classList.remove('hidden');
        
        // Animate in
        requestAnimationFrame(() => {
            elements.backdrop.classList.remove('opacity-0');
            elements.panel.classList.remove('opacity-0', 'scale-95');
            elements.panel.classList.add('opacity-100', 'scale-100');
            
            // Trigger confetti
            if (confettiInstance) {
                confettiInstance({
                    particleCount: 100,
                    spread: 70,
                    origin: { y: 0.6 }
                });
            }
        });
        
        isShowing = true;
    }
    
    function hide() {
        if (!elements.overlay) return;
        
        // Animate out
        elements.backdrop.classList.add('opacity-0');
        elements.panel.classList.remove('opacity-100', 'scale-100');
        elements.panel.classList.add('opacity-0', 'scale-95');
        
        setTimeout(() => {
            elements.overlay.classList.add('hidden');
            isShowing = false;
            processQueue(); // Show next if any
        }, 300); // Match transition duration
    }
    
    function processQueue() {
        if (isShowing || queue.length === 0) return;
        
        const badge = queue.shift();
        show(badge);
    }
    
    function enqueue(badgeOrBadges) {
        // Handle single object, array, or string (JSON)
        let badges = badgeOrBadges;
        if (typeof badges === 'string') {
            try {
                badges = JSON.parse(badges);
            } catch (e) {
                console.error("Invalid badge data", e);
                return;
            }
        }
        
        if (Array.isArray(badges)) {
            queue.push(...badges);
        } else if (badges && typeof badges === 'object') {
            queue.push(badges);
        }
        
        processQueue();
    }
    
    // Auto-check for server-rendered badges
    document.addEventListener('DOMContentLoaded', () => {
        init();
        if (window.NEW_BADGES && window.NEW_BADGES.length > 0) {
            enqueue(window.NEW_BADGES);
        }
    });

    return {
        show: enqueue, // Public API maps to enqueue
        init: init
    };
})();
