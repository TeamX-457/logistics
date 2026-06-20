// Small formatting helpers shared across pages.

function money(value) {
  const n = typeof value === "string" ? parseFloat(value) : value;
  if (Number.isNaN(n) || n === null || n === undefined) return "$0.00";
  return n.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

function dateTime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString();
}

function statusBadge(status) {
  const palette = {
    pending: "bg-slate-100 text-slate-700",
    negotiating: "bg-amber-100 text-amber-800",
    accepted: "bg-blue-100 text-blue-800",
    driver_arrived: "bg-blue-100 text-blue-800",
    in_transit: "bg-blue-100 text-blue-800",
    delayed: "bg-amber-100 text-amber-800",
    delivered: "bg-green-100 text-green-800",
    disputed: "bg-red-100 text-red-800",
    cancelled: "bg-slate-200 text-slate-600",
    approved: "bg-green-100 text-green-800",
    rejected: "bg-red-100 text-red-800",
    completed: "bg-green-100 text-green-800",
    processing: "bg-amber-100 text-amber-800",
    under_investigation: "bg-amber-100 text-amber-800",
    active: "bg-red-100 text-red-800",
    resolved: "bg-green-100 text-green-800",
  };
  const classes = palette[status] || "bg-slate-100 text-slate-700";
  return `<span class="inline-block text-xs font-semibold px-2 py-0.5 rounded ${classes}">${status.replace(/_/g, " ")}</span>`;
}

function el(id) {
  return document.getElementById(id);
}

function qs(name) {
  return new URLSearchParams(window.location.search).get(name);
}

function escapeHtml(str) {
  return String(str === null || str === undefined ? "" : str).replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

function ensureUiDialogRoot() {
  if (document.getElementById("ui-dialog-root")) return;
  const style = document.createElement("style");
  style.textContent = `
    #ui-dialog-root{position:fixed;inset:0;z-index:10000;display:none;align-items:center;justify-content:center;padding:24px;}
    #ui-dialog-root.open{display:flex;}
    #ui-dialog-root .ui-dialog-backdrop{position:absolute;inset:0;background:rgba(11,28,48,.55);backdrop-filter:blur(2px);animation:ui-fade-in .18s ease;}
    #ui-dialog-root .ui-dialog-panel{position:relative;background:#fff;border-radius:12px;max-width:380px;width:100%;padding:28px;box-shadow:0 20px 60px rgba(11,28,48,.35);animation:ui-scale-in .18s ease;font-family:'Geist',sans-serif;}
    #ui-dialog-root .ui-dialog-title{font-size:17px;font-weight:700;color:#131b2e;margin:0 0 8px;}
    #ui-dialog-root .ui-dialog-message{font-size:14px;color:#45464d;margin:0 0 18px;line-height:1.5;white-space:pre-line;}
    #ui-dialog-root .ui-dialog-input{width:100%;border:1px solid #c6c6cd;border-radius:8px;padding:10px 12px;font-size:14px;font-family:inherit;margin-bottom:20px;box-sizing:border-box;}
    #ui-dialog-root .ui-dialog-input:focus{outline:none;border-color:#131b2e;}
    #ui-dialog-root .ui-dialog-actions{display:flex;gap:10px;justify-content:flex-end;}
    #ui-dialog-root .ui-dialog-btn{border:none;border-radius:8px;padding:10px 20px;font-size:14px;font-weight:600;font-family:inherit;cursor:pointer;}
    #ui-dialog-root .ui-dialog-btn-primary{background:#131b2e;color:#fff;}
    #ui-dialog-root .ui-dialog-btn-primary:hover{opacity:.9;}
    #ui-dialog-root .ui-dialog-btn-ghost{background:#f1f2f6;color:#131b2e;}
    #ui-dialog-root .ui-dialog-btn-ghost:hover{background:#e5e7ee;}
    #ui-dialog-root .ui-dialog-btn-danger{background:#ba1a1a;color:#fff;}
    @keyframes ui-fade-in{from{opacity:0;}to{opacity:1;}}
    @keyframes ui-scale-in{from{opacity:0;transform:scale(.95) translateY(6px);}to{opacity:1;transform:scale(1) translateY(0);}}
  `;
  document.head.appendChild(style);
  const root = document.createElement("div");
  root.id = "ui-dialog-root";
  document.body.appendChild(root);
}

function uiDialog({ title, message, type = "alert", defaultValue = "", placeholder = "", confirmLabel = "OK", cancelLabel = "Cancel", danger = false }) {
  ensureUiDialogRoot();
  const root = document.getElementById("ui-dialog-root");
  return new Promise((resolve) => {
    const showCancel = type !== "alert";
    const showInput = type === "prompt";
    root.innerHTML = `
      <div class="ui-dialog-backdrop"></div>
      <div class="ui-dialog-panel" role="dialog" aria-modal="true">
        ${title ? `<p class="ui-dialog-title">${escapeHtml(title)}</p>` : ""}
        <p class="ui-dialog-message">${escapeHtml(message)}</p>
        ${showInput ? `<input class="ui-dialog-input" type="text" id="ui-dialog-input-field" placeholder="${escapeHtml(placeholder)}" value="${escapeHtml(defaultValue)}"/>` : ""}
        <div class="ui-dialog-actions">
          ${showCancel ? `<button class="ui-dialog-btn ui-dialog-btn-ghost" id="ui-dialog-cancel">${escapeHtml(cancelLabel)}</button>` : ""}
          <button class="ui-dialog-btn ${danger ? "ui-dialog-btn-danger" : "ui-dialog-btn-primary"}" id="ui-dialog-confirm">${escapeHtml(confirmLabel)}</button>
        </div>
      </div>`;
    root.classList.add("open");
    const input = document.getElementById("ui-dialog-input-field");
    if (input) {
      input.focus();
      input.select();
    }
    const cleanup = (value) => {
      root.classList.remove("open");
      root.innerHTML = "";
      document.removeEventListener("keydown", onKey);
      resolve(value);
    };
    const confirmBtn = document.getElementById("ui-dialog-confirm");
    const onKey = (e) => {
      if (e.key === "Escape") cleanup(type === "confirm" ? false : null);
      if (e.key === "Enter" && (type !== "prompt" || document.activeElement === input)) confirmBtn.click();
    };
    document.addEventListener("keydown", onKey);
    confirmBtn.addEventListener("click", () => cleanup(type === "prompt" ? input.value : true));
    const cancelBtn = document.getElementById("ui-dialog-cancel");
    if (cancelBtn) cancelBtn.addEventListener("click", () => cleanup(type === "prompt" ? null : false));
    root.querySelector(".ui-dialog-backdrop").addEventListener("click", () => cleanup(type === "prompt" ? null : type === "confirm" ? false : true));
  });
}

function uiAlert(message, opts = {}) {
  return uiDialog({
    type: "alert",
    message,
    title: opts.title || (opts.kind === "error" ? "Something went wrong" : "Notice"),
    confirmLabel: opts.confirmLabel || "OK",
    danger: opts.kind === "error",
  });
}

function uiConfirm(message, opts = {}) {
  return uiDialog({
    type: "confirm",
    message,
    title: opts.title || "Please confirm",
    confirmLabel: opts.confirmLabel || "Confirm",
    cancelLabel: opts.cancelLabel || "Cancel",
    danger: opts.danger,
  });
}

function uiPrompt(message, opts = {}) {
  return uiDialog({
    type: "prompt",
    message,
    title: opts.title || "Input required",
    placeholder: opts.placeholder,
    defaultValue: opts.defaultValue,
    confirmLabel: opts.confirmLabel || "OK",
  });
}

(function hideAppLoader() {
  const loader = document.getElementById("app-loader");
  if (!loader) return;
  const hide = () => loader.classList.add("app-loader-hidden");
  const pageLoaded = new Promise((resolve) => {
    if (document.readyState === "complete") resolve();
    else window.addEventListener("load", resolve);
  });
  const fontsReady = (document.fonts && document.fonts.ready) ? document.fonts.ready : Promise.resolve();
  Promise.all([pageLoaded, fontsReady]).then(() => setTimeout(hide, 250));
  setTimeout(hide, 4000);
})();
