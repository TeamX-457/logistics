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
