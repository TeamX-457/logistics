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

/** Renders a consistent top navbar into #navbar. */
function renderNavbar(activeHref) {
  const mount = document.getElementById("navbar");
  if (!mount) return;
  const user = getCurrentUser();

  const linksByRole = {
    customer: [
      ["customer-dashboard", "Dashboard"],
      ["create-delivery", "Create Delivery"],
      ["wallet", "Wallet"],
      ["disputes", "Disputes"],
    ],
    driver: [
      ["driver-dashboard", "Dashboard"],
      ["feed", "Feed"],
      ["wallet", "Wallet"],
      ["disputes", "Disputes"],
    ],
    admin: [
      ["admin-overview", "Overview"],
      ["fleet-verification", "Fleet Verification"],
      ["disputes", "Disputes"],
    ],
  };
  const links = (user && linksByRole[user.role]) || [];

  mount.innerHTML = `
    <nav class="bg-slate-900 text-white">
      <div class="max-w-6xl mx-auto px-6 h-14 flex items-center gap-6">
        <a href="/" class="font-bold tracking-tight flex items-center gap-2">
          <img src="/static/img/logo-mark.svg" alt="Logistica" class="w-6 h-6 rounded-full" />
          Logistica
        </a>
        <div class="flex items-center gap-1 flex-1">
          ${links
            .map(
              ([href, label]) => `
            <a href="${href}" class="px-3 py-2 rounded text-sm font-medium ${
                href === activeHref ? "bg-slate-800 text-white" : "text-slate-300 hover:text-white"
              }">${label}</a>`
            )
            .join("")}
        </div>
        ${
          user
            ? `<span class="text-sm text-slate-400">${user.email} · ${user.role}</span>
               <button onclick="logout()" class="text-sm font-medium px-3 py-1.5 rounded border border-slate-700 hover:bg-slate-800">Log out</button>`
            : ""
        }
      </div>
    </nav>
  `;
}

function showError(el, err) {
  const message =
    err && err.data
      ? typeof err.data === "string"
        ? err.data
        : err.data.detail || JSON.stringify(err.data)
      : String(err);
  el.textContent = message;
  el.classList.remove("hidden");
}
