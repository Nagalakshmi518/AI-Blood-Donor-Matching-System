/**
 * BloodNeed App Shell & Preloader Controller
 * Lightweight, zero-dependency UX enhancer (<3KB)
 */

(function () {
  // 1. Preloader dismissal
  function dismissPreloader() {
    const preloader = document.getElementById("bnPreloader");
    if (preloader && !preloader.classList.contains("loaded")) {
      preloader.classList.add("loaded");
      setTimeout(() => {
        if (preloader.parentNode) {
          preloader.style.display = "none";
        }
      }, 400);
    }
  }

  if (document.readyState === "complete") {
    setTimeout(dismissPreloader, 200);
  } else {
    window.addEventListener("load", () => {
      setTimeout(dismissPreloader, 250);
    });
    // Fallback safety timeout (max 1.5s)
    setTimeout(dismissPreloader, 1500);
  }

  // 2. Lightweight Modern Toast System
  window.showToast = function (message, type = "info", duration = 3500) {
    let container = document.getElementById("bnToastContainer");
    if (!container) {
      container = document.createElement("div");
      container.id = "bnToastContainer";
      container.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 100000;
        display: flex;
        flex-direction: column;
        gap: 10px;
        pointer-events: none;
        max-width: 90vw;
        width: 380px;
      `;
      document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `bn-toast bn-toast-${type}`;

    let icon = "🩸";
    let borderColor = "rgba(225, 29, 72, 0.4)";
    let bgGradient = "linear-gradient(135deg, rgba(22, 27, 46, 0.95), rgba(15, 23, 42, 0.98))";

    if (type === "success") {
      icon = "✅";
      borderColor = "rgba(16, 185, 129, 0.5)";
    } else if (type === "error") {
      icon = "⚠️";
      borderColor = "rgba(239, 68, 68, 0.5)";
    } else if (type === "ai" || type === "info") {
      icon = "🤖";
      borderColor = "rgba(6, 182, 212, 0.5)";
    }

    toast.style.cssText = `
      background: ${bgGradient};
      border: 1px solid ${borderColor};
      border-radius: 12px;
      padding: 14px 18px;
      color: #F8FAFC;
      font-size: 13.5px;
      font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
      backdrop-filter: blur(12px);
      display: flex;
      align-items: center;
      gap: 12px;
      pointer-events: auto;
      transform: translateY(20px);
      opacity: 0;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    `;

    toast.innerHTML = `
      <span style="font-size: 18px; flex-shrink: 0;">${icon}</span>
      <div style="flex: 1; line-height: 1.4;">${message}</div>
      <button style="background: none; border: none; color: #94A3B8; font-size: 16px; cursor: pointer; padding: 4px;" onclick="this.parentElement.remove()">✕</button>
    `;

    container.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
      toast.style.transform = "translateY(0)";
      toast.style.opacity = "1";
    });

    // Auto dismiss
    setTimeout(() => {
      toast.style.transform = "translateY(-10px)";
      toast.style.opacity = "0";
      setTimeout(() => toast.remove(), 300);
    }, duration);
  };
})();
