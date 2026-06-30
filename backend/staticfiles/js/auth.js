// Shared per-page auth guard + top navbar. Include after api.js.

const ROLE_HOME = {
  customer: "customer-dashboard",
  driver: "driver-dashboard",
  admin: "admin-overview",
};

/** Call at the top of any page that requires login. Pass allowedRoles to also gate by role. */
function requireAuth(allowedRoles) {
  const user = getCurrentUser();
  if (!getAccessToken() || !user) {
    window.location.href = "login";
    return null;
  }
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    window.location.href = ROLE_HOME[user.role] || "/";
    return null;
  }
  return user;
}

function logout() {
  clearSession();
  window.location.href = "/";
}

/** Single source of truth for sidebar nav per role. Keep in sync across the app shell. */
const NAV_LINKS = {
  customer: [
    ["customer-dashboard", "dashboard", "Dashboard"],
    ["my-deliveries", "local_shipping", "My Deliveries"],
    ["create-delivery", "add_circle", "Create Delivery"],
    ["fleet", "person_pin_circle", "Find Drivers"],
    ["wallet", "account_balance_wallet", "Wallet"],
    ["disputes", "gavel", "Disputes"],
  ],
  driver: [
    ["driver-dashboard", "dashboard", "Dashboard"],
    ["feed", "campaign", "Client Requests"],
    ["my-deliveries", "local_shipping", "My Deliveries"],
    ["wallet", "payments", "Earnings"],
    ["disputes", "gavel", "Disputes"],
  ],
  admin: [
    ["admin-overview", "dashboard", "Overview"],
    ["fleet-verification", "verified_user", "Fleet Verification"],
    ["financial-analytics", "monitoring", "Financial Analytics"],
    ["operations-monitoring", "hub", "Operations"],
    ["disputes", "gavel", "Disputes"],
    ["admin-panel", "admin_panel_settings", "Admin Panel"],
  ],
};

const ROLE_LABEL = { customer: "Customer Account", driver: "Driver Account", admin: "Admin Console" };
const ROLE_AVATAR_ICON = { customer: "person", driver: "person", admin: "shield" };

function ensureAppShellStyles() {
  if (document.getElementById("app-shell-styles")) return;
  const style = document.createElement("style");
  style.id = "app-shell-styles";
  style.textContent = `
    #app-sidebar{position:fixed;left:0;top:0;height:100vh;width:16rem;z-index:40;display:flex;flex-direction:column;padding:24px 16px;background:#eff4ff;border-right:1px solid #c6c6cd;transition:transform .25s ease;font-family:'Geist',sans-serif;}
    #app-sidebar .app-shell-brand{display:flex;align-items:center;gap:12px;padding:0 8px;margin-bottom:20px;}
    #app-sidebar .app-shell-brand img{width:32px;height:32px;border-radius:9999px;}
    #app-sidebar .app-shell-brand span{font-size:18px;font-weight:700;color:#131b2e;}
    #app-sidebar .app-shell-profile{display:flex;align-items:center;gap:12px;padding:8px;margin-bottom:16px;}
    #app-sidebar .app-shell-avatar{width:40px;height:40px;border-radius:9999px;background:#131b2e;color:#fff;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
    #app-sidebar .app-shell-profile p{margin:0;font-size:13px;color:#131b2e;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
    #app-sidebar .app-shell-profile span{font-size:11px;color:#45464d;}
    #app-sidebar nav{flex:1;display:flex;flex-direction:column;gap:4px;overflow-y:auto;}
    #app-sidebar .app-shell-link{display:flex;align-items:center;gap:12px;padding:11px 12px;border-radius:8px;color:#45464d;text-decoration:none;font-size:14px;font-weight:500;transition:background-color .15s ease;}
    #app-sidebar .app-shell-link:hover{background:#e5eeff;}
    #app-sidebar .app-shell-link.active{background:#fea619;color:#2a1700;font-weight:700;}
    #app-sidebar .app-shell-footer{margin-top:auto;padding-top:16px;border-top:1px solid #c6c6cd;display:flex;flex-direction:column;gap:4px;}
    #app-sidebar .app-shell-link.danger{color:#ba1a1a;}
    #app-sidebar .app-shell-link.danger:hover{background:#ffdad6;}
    #app-sidebar-backdrop{position:fixed;inset:0;background:rgba(11,28,48,.55);z-index:35;opacity:0;pointer-events:none;transition:opacity .2s ease;}
    #app-sidebar-backdrop.app-shell-open{opacity:1;pointer-events:auto;}
    #app-topbar{position:fixed;top:0;right:0;left:0;height:64px;z-index:20;display:flex;align-items:center;justify-content:space-between;padding:0 16px;background:#f8f9ff;border-bottom:1px solid #c6c6cd;font-family:'Geist',sans-serif;}
    #app-topbar .app-shell-burger{display:flex;align-items:center;justify-content:center;width:40px;height:40px;border-radius:8px;border:none;background:transparent;color:#45464d;cursor:pointer;}
    #app-topbar .app-shell-burger:hover{background:#e5eeff;}
    #app-topbar .app-shell-title{font-size:16px;font-weight:600;color:#131b2e;}
    #app-topbar .app-shell-actions{display:flex;align-items:center;gap:8px;}
    #app-topbar .app-shell-iconbtn{display:flex;align-items:center;justify-content:center;width:40px;height:40px;border-radius:8px;border:none;background:transparent;color:#45464d;cursor:pointer;}
    #app-topbar .app-shell-iconbtn:hover{background:#e5eeff;}
    main.app-shell-main{margin-left:0;}
    .app-shell-brand-mobile{display:flex;align-items:center;gap:8px;font-weight:700;color:#131b2e;}
    @media (min-width:768px){
      .app-shell-brand-mobile{display:none;}
      #app-topbar{left:16rem;}
      #app-sidebar-backdrop{display:none !important;}
    }
    @media (max-width:767.98px){
      #app-sidebar{transform:translateX(-100%);}
      #app-sidebar.app-shell-open{transform:translateX(0);}
      main.app-shell-main{margin-left:0 !important;}
    }
    @media (min-width:768px){
      main.app-shell-main{margin-left:16rem !important;}
    }
    html.dark body{background:#0b1424;}
    html.dark #app-sidebar{background:#0f1830;border-color:#28324d;}
    html.dark #app-sidebar .app-shell-brand span{color:#e7ecff;}
    html.dark #app-sidebar .app-shell-profile p{color:#e7ecff;}
    html.dark #app-sidebar .app-shell-profile span{color:#9aa6c8;}
    html.dark #app-sidebar .app-shell-link{color:#aab4d4;}
    html.dark #app-sidebar .app-shell-link:hover{background:#16223c;}
    html.dark #app-sidebar .app-shell-footer{border-color:#28324d;}
    html.dark #app-topbar{background:#0f1830;border-color:#28324d;}
    html.dark #app-topbar .app-shell-title,
    html.dark .app-shell-brand-mobile{color:#e7ecff;}
    html.dark #app-topbar .app-shell-burger,
    html.dark #app-topbar .app-shell-iconbtn{color:#aab4d4;}
    html.dark #app-topbar .app-shell-burger:hover,
    html.dark #app-topbar .app-shell-iconbtn:hover{background:#16223c;}
    html.dark .bg-surface,
    html.dark .bg-background,
    html.dark .bg-surface-bright,
    html.dark .bg-surface-dim,
    html.dark .bg-surface-variant,
    html.dark .bg-white{background-color:#101a30 !important;}
    html.dark .bg-surface-container-low,
    html.dark .bg-surface-container-lowest{background-color:#16223c !important;}
    html.dark .bg-surface-container{background-color:#1b2942 !important;}
    html.dark .bg-surface-container-high,
    html.dark .bg-surface-container-highest{background-color:#22304c !important;}
    html.dark .text-on-surface,
    html.dark .text-on-surface-variant,
    html.dark .text-on-background,
    html.dark .text-primary,
    html.dark .text-on-primary-container{color:#e7ecff !important;}
    html.dark .text-outline{color:#8b97b8 !important;}
    html.dark .text-secondary{color:#fea619 !important;}
    html.dark .border-outline-variant,
    html.dark .border-outline{border-color:#2a3a5c !important;}
    html.dark input,
    html.dark select,
    html.dark textarea{background-color:#16223c !important;color:#e7ecff !important;border-color:#2a3a5c !important;}
  `;
  document.head.appendChild(style);
}

/**
 * Renders the shared role-aware sidebar + mobile topbar shell.
 * Call once per page, right after requireAuth(). activeHref must match one of NAV_LINKS' hrefs.
 */
function renderAppShell(activeHref, opts = {}) {
  const user = getCurrentUser();
  if (!user) return;
  ensureAppShellStyles();

  const links = NAV_LINKS[user.role] || [];
  const name = `${user.first_name || ""} ${user.last_name || ""}`.trim() || user.email;
  const isDark = localStorage.getItem("theme") === "dark";
  if (isDark) document.documentElement.classList.add("dark");

  const linkHtml = ([href, icon, label]) => `
    <a class="app-shell-link${href === activeHref ? " active" : ""}" href="${href}">
      <span class="material-symbols-outlined">${icon}</span>
      <span>${escapeHtml(label)}</span>
    </a>`;

  document.body.insertAdjacentHTML(
    "afterbegin",
    `
    <aside id="app-sidebar">
      <div class="app-shell-brand">
        <img src="/static/img/logo-mark.svg" alt="Logistica"/>
        <span>Logistica</span>
      </div>
      <div class="app-shell-profile">
        <div class="app-shell-avatar"><span class="material-symbols-outlined">${ROLE_AVATAR_ICON[user.role] || "person"}</span></div>
        <div>
          <p>${escapeHtml(name)}</p>
          <span>${ROLE_LABEL[user.role] || ""}</span>
        </div>
      </div>
      <nav>${links.map(linkHtml).join("")}</nav>
      <div class="app-shell-footer">
        ${linkHtml(["profile", "account_circle", "Profile"])}
        <a class="app-shell-link" href="/static/docs/index.html" target="_blank">
          <span class="material-symbols-outlined">description</span>
          <span>Documentation</span>
        </a>
        <a class="app-shell-link danger" href="#" onclick="logout(); return false;">
          <span class="material-symbols-outlined">logout</span>
          <span>Log Out</span>
        </a>
      </div>
    </aside>
    <div id="app-sidebar-backdrop"></div>
    <header id="app-topbar">
      <div style="display:flex;align-items:center;gap:8px;">
        <button class="app-shell-burger" id="app-shell-burger">
          <span class="material-symbols-outlined">menu</span>
        </button>
        <div class="app-shell-brand-mobile">
          <img src="/static/img/logo-mark.svg" alt="Logistica" style="width:24px;height:24px;border-radius:9999px;"/>
          <span>Logistica</span>
        </div>
        <span class="app-shell-title">${escapeHtml(opts.title || "")}</span>
      </div>
      <div class="app-shell-actions" id="app-shell-actions">
        ${opts.actions || ""}
        <button class="app-shell-iconbtn" id="app-shell-theme-toggle" title="Toggle dark mode">
          <span class="material-symbols-outlined">${isDark ? "light_mode" : "dark_mode"}</span>
        </button>
      </div>
    </header>
  `
  );

  const main = document.querySelector("main");
  if (main) main.classList.add("app-shell-main");

  const sidebar = document.getElementById("app-sidebar");
  const backdrop = document.getElementById("app-sidebar-backdrop");
  const toggleDrawer = () => {
    sidebar.classList.toggle("app-shell-open");
    backdrop.classList.toggle("app-shell-open");
  };
  document.getElementById("app-shell-burger").addEventListener("click", toggleDrawer);
  backdrop.addEventListener("click", toggleDrawer);

  const themeBtn = document.getElementById("app-shell-theme-toggle");
  themeBtn.addEventListener("click", () => {
    const dark = !document.documentElement.classList.contains("dark");
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("theme", dark ? "dark" : "light");
    themeBtn.querySelector(".material-symbols-outlined").textContent = dark ? "light_mode" : "dark_mode";
  });
}
