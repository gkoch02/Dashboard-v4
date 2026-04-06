/* Dashboard Web UI — vanilla JS, no dependencies */
"use strict";

const STATUS_INTERVAL_MS  = 30_000;  // poll /api/status every 30 s
const IMAGE_INTERVAL_MS   = 60_000;  // refresh dashboard image every 60 s
const LOG_INTERVAL_MS     = 60_000;  // refresh log tail every 60 s

// --------------------------------------------------------------------------
// Utilities
// --------------------------------------------------------------------------

function $(id) { return document.getElementById(id); }

function fmt_age(minutes) {
  if (minutes === null || minutes === undefined) return "—";
  if (minutes < 1) return "<1 min ago";
  if (minutes < 60) return `${Math.round(minutes)} min ago`;
  const h = Math.floor(minutes / 60), m = Math.round(minutes % 60);
  return m > 0 ? `${h}h ${m}m ago` : `${h}h ago`;
}

function fmt_seconds(s) {
  if (s === null || s === undefined) return "—";
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m ago`;
}

function fmt_uptime(s) {
  if (s === null || s === undefined) return "—";
  const d = Math.floor(s / 86400), h = Math.floor((s % 86400) / 3600);
  const m = Math.floor((s % 3600) / 60);
  if (d > 0) return `${d}d ${h}h`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function staleness_badge(level) {
  const map = {
    fresh:   ["badge-ok",   "fresh"],
    aging:   ["badge-warn", "aging"],
    stale:   ["badge-bad",  "stale"],
    expired: ["badge-bad",  "expired"],
    unknown: ["badge-unknown", "—"],
  };
  const [cls, label] = map[level] || ["badge-unknown", level || "—"];
  return `<span class="badge ${cls}">${label}</span>`;
}

function breaker_badge(state) {
  const map = {
    closed:    ["badge-ok",   "ok"],
    half_open: ["badge-warn", "half-open"],
    open:      ["badge-bad",  "open"],
  };
  const [cls, label] = map[state] || ["badge-unknown", state || "—"];
  return `<span class="badge ${cls}">${label}</span>`;
}

function bar_class(pct) {
  if (pct >= 90) return "bad";
  if (pct >= 70) return "warn";
  return "";
}

function set_text(id, value) {
  const el = $(id);
  if (el) el.textContent = value;
}

// --------------------------------------------------------------------------
// Status update
// --------------------------------------------------------------------------

function applyStatus(data) {
  // Last run
  set_text("last-run", fmt_seconds(data.seconds_since_run));
  set_text("current-theme", data.current_theme || "—");

  // Quiet hours banner
  const banner = $("quiet-banner");
  if (banner) banner.classList.toggle("visible", !!data.quiet_hours_active);

  // Host metrics
  const h = data.host || {};
  set_text("host-hostname", h.hostname || "—");
  set_text("host-uptime",   fmt_uptime(h.uptime_seconds));
  set_text("host-load",     h.load_1m != null ? h.load_1m.toFixed(2) : "—");
  set_text("host-ip",       h.ip_address || "—");

  if (h.cpu_temp_c != null) {
    set_text("host-temp", `${h.cpu_temp_c.toFixed(1)} °C`);
  }

  if (h.ram_used_mb != null && h.ram_total_mb != null) {
    const pct = Math.round((h.ram_used_mb / h.ram_total_mb) * 100);
    set_text("host-ram", `${Math.round(h.ram_used_mb)} / ${Math.round(h.ram_total_mb)} MB`);
    const bar = $("ram-bar");
    if (bar) { bar.style.width = pct + "%"; bar.className = "bar-fill " + bar_class(pct); }
  }

  if (h.disk_used_gb != null && h.disk_total_gb != null) {
    const pct = Math.round((h.disk_used_gb / h.disk_total_gb) * 100);
    set_text("host-disk", `${h.disk_used_gb.toFixed(1)} / ${h.disk_total_gb.toFixed(1)} GB`);
    const bar = $("disk-bar");
    if (bar) { bar.style.width = pct + "%"; bar.className = "bar-fill " + bar_class(pct); }
  }

  // Sources table
  const tbody = $("sources-tbody");
  if (tbody && data.sources) {
    tbody.innerHTML = Object.entries(data.sources).map(([name, s]) => `
      <tr>
        <td><strong>${name}</strong></td>
        <td>${breaker_badge(s.breaker_state)}${s.consecutive_failures > 0
          ? ` <span class="text-muted">(${s.consecutive_failures} fail)</span>` : ""}</td>
        <td>${fmt_age(s.cache_age_minutes)}</td>
        <td>${staleness_badge(s.staleness)}</td>
        <td>${s.quota_today ?? "—"}</td>
      </tr>
    `).join("");
  }
}

async function refreshStatus() {
  const dot = $("refresh-dot");
  if (dot) dot.classList.add("pulse");
  try {
    const resp = await fetch("/api/status");
    if (!resp.ok) return;
    const data = await resp.json();
    applyStatus(data);
  } catch (_) { /* network error — keep stale UI */ }
  finally {
    if (dot) dot.classList.remove("pulse");
  }
}

// --------------------------------------------------------------------------
// Image refresh
// --------------------------------------------------------------------------

function refreshImage() {
  const img = $("dash-img");
  if (!img) return;
  img.src = "/image/latest?t=" + Date.now();
}

// --------------------------------------------------------------------------
// Log refresh
// --------------------------------------------------------------------------

async function refreshLogs() {
  try {
    const resp = await fetch("/api/logs?lines=100");
    if (!resp.ok) return;
    const data = await resp.json();
    const pre = $("log-output");
    if (pre) pre.textContent = data.lines.join("\n");
  } catch (_) {}
}

// --------------------------------------------------------------------------
// Boot
// --------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  refreshStatus();
  refreshLogs();

  setInterval(refreshStatus, STATUS_INTERVAL_MS);
  setInterval(refreshImage,  IMAGE_INTERVAL_MS);
  setInterval(refreshLogs,   LOG_INTERVAL_MS);
});
