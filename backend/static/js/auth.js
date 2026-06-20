// Shared per-page auth guard + top navbar. Include after api.js.

const ROLE_HOME = {
  customer: "customer-dashboard.html",
  driver: "driver-dashboard.html",
  admin: "admin-overview.html",
};

/** Call at the top of any page that requires login. Pass allowedRoles to also gate by role. */
function requireAuth(allowedRoles) {
  const user = getCurrentUser();
  if (!getAccessToken() || !user) {
    window.location.href = "login.html";
    return null;
  }
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    window.location.href = ROLE_HOME[user.role] || "index.html";
    return null;
  }
  return user;
}

function logout() {
  clearSession();
  window.location.href = "login.html";
}

/** Renders a consistent top navbar into #navbar. */
function renderNavbar(activeHref) {
  const mount = document.getElementById("navbar");
  if (!mount) return;
  const user = getCurrentUser();

  const linksByRole = {
    customer: [
      ["customer-dashboard.html", "Dashboard"],
      ["create-delivery.html", "Create Delivery"],
      ["wallet.html", "Wallet"],
      ["disputes.html", "Disputes"],
    ],
    driver: [
      ["driver-dashboard.html", "Dashboard"],
      ["marketplace.html", "Marketplace"],
      ["wallet.html", "Wallet"],
      ["disputes.html", "Disputes"],
    ],
    admin: [
      ["admin-overview.html", "Overview"],
      ["fleet-verification.html", "Fleet Verification"],
      ["disputes.html", "Disputes"],
    ],
  };
  const links = (user && linksByRole[user.role]) || [];

  mount.innerHTML = `
    <nav class="bg-slate-900 text-white">
      <div class="max-w-6xl mx-auto px-6 h-14 flex items-center gap-6">
        <a href="index.html" class="font-bold tracking-tight">LogisticsPro</a>
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
