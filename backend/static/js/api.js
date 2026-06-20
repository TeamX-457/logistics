/**
 * LogisticsPro API client.
 * Thin async wrapper around fetch() — every call returns a Promise that
 * resolves to the parsed JSON body, or throws an ApiError on failure.
 *
 * Mirrors backend/static/docs/API_REFERENCE.md endpoint-for-endpoint.
 */

class ApiError extends Error {
  constructor(status, data) {
    super(typeof data === "object" ? JSON.stringify(data) : String(data));
    this.status = status;
    this.data = data;
  }
}

function getAccessToken() {
  return localStorage.getItem("access_token");
}
function getRefreshToken() {
  return localStorage.getItem("refresh_token");
}
function getCurrentUser() {
  const raw = localStorage.getItem("user");
  return raw ? JSON.parse(raw) : null;
}
function setSession({ access, refresh, user }) {
  if (access) localStorage.setItem("access_token", access);
  if (refresh) localStorage.setItem("refresh_token", refresh);
  if (user) localStorage.setItem("user", JSON.stringify(user));
}
function clearSession() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
}

async function refreshAccessToken() {
  const refresh = getRefreshToken();
  if (!refresh) throw new ApiError(401, { detail: "No refresh token." });

  const res = await fetch(`${BASE_URL}/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!res.ok) throw new ApiError(res.status, await res.json().catch(() => ({})));
  const data = await res.json();
  setSession({ access: data.access, refresh: data.refresh });
  return data.access;
}

/**
 * Core request helper.
 * @param {string} path - e.g. "/deliveries/"
 * @param {object} opts - { method, body, auth, isForm, params }
 */
async function request(path, opts = {}) {
  const { method = "GET", body, auth = true, isForm = false, params } = opts;

  let url = `${BASE_URL}${path}`;
  if (params) {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "")
    ).toString();
    if (qs) url += `?${qs}`;
  }

  const doFetch = async () => {
    const headers = {};
    if (!isForm) headers["Content-Type"] = "application/json";
    if (auth) {
      const token = getAccessToken();
      if (token) headers["Authorization"] = `Bearer ${token}`;
    }
    return fetch(url, {
      method,
      headers,
      body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
    });
  };

  let res = await doFetch();

  // Access token expired mid-session: refresh once, then retry.
  if (res.status === 401 && auth && getRefreshToken()) {
    try {
      await refreshAccessToken();
      res = await doFetch();
    } catch {
      clearSession();
      window.location.href = "login.html";
      return;
    }
  }

  if (res.status === 204) return null;

  const contentType = res.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await res.json() : await res.text();

  if (!res.ok) throw new ApiError(res.status, data);
  return data;
}

const API = {
  auth: {
    registerCustomer: (payload) =>
      request("/auth/register/customer/", { method: "POST", body: payload, auth: false }),
    registerDriver: (payload) =>
      request("/auth/register/driver/", { method: "POST", body: payload, auth: false }),
    login: (email, password) =>
      request("/auth/login/", { method: "POST", body: { email, password }, auth: false }),
    me: () => request("/auth/me/"),
    updateMe: (payload) => request("/auth/me/", { method: "PATCH", body: payload }),
    requestPasswordReset: (email) =>
      request("/auth/password-reset/", { method: "POST", body: { email }, auth: false }),
    confirmPasswordReset: (payload) =>
      request("/auth/password-reset/confirm/", { method: "POST", body: payload, auth: false }),
  },

  drivers: {
    setStatus: (payload) => request("/drivers/me/status/", { method: "PATCH", body: payload }),
  },

  addresses: {
    list: () => request("/addresses/"),
    create: (payload) => request("/addresses/", { method: "POST", body: payload }),
    update: (id, payload) => request(`/addresses/${id}/`, { method: "PATCH", body: payload }),
    remove: (id) => request(`/addresses/${id}/`, { method: "DELETE" }),
  },

  fleet: {
    listVerifications: (params) => request("/verifications/", { params }),
    getVerification: (id) => request(`/verifications/${id}/`),
    approve: (id) => request(`/verifications/${id}/approve/`, { method: "POST" }),
    reject: (id, reason) => request(`/verifications/${id}/reject/`, { method: "POST", body: { reason } }),
  },

  deliveries: {
    list: (params) => request("/deliveries/", { params }),
    get: (id) => request(`/deliveries/${id}/`),
    create: (payload) => request("/deliveries/", { method: "POST", body: payload }),
    estimate: (payload) => request("/deliveries/estimate/", { method: "POST", body: payload }),
    marketplace: (params) => request("/deliveries/marketplace/", { params }),
    cancel: (id) => request(`/deliveries/${id}/cancel/`, { method: "POST" }),
    acceptLoad: (id) => request(`/deliveries/${id}/accept-load/`, { method: "POST" }),
    advanceStatus: (id, payload) => request(`/deliveries/${id}/advance-status/`, { method: "POST", body: payload }),

    bids: {
      list: (deliveryId) => request(`/deliveries/${deliveryId}/bids/`),
      create: (deliveryId, payload) => request(`/deliveries/${deliveryId}/bids/`, { method: "POST", body: payload }),
      accept: (deliveryId, bidId) => request(`/deliveries/${deliveryId}/bids/${bidId}/accept/`, { method: "POST" }),
      reject: (deliveryId, bidId) => request(`/deliveries/${deliveryId}/bids/${bidId}/reject/`, { method: "POST" }),
    },
    tracking: {
      get: (deliveryId) => request(`/deliveries/${deliveryId}/tracking/`),
      post: (deliveryId, payload) => request(`/deliveries/${deliveryId}/tracking/`, { method: "POST", body: payload }),
    },
    messages: {
      list: (deliveryId) => request(`/deliveries/${deliveryId}/messages/`),
      create: (deliveryId, payload) => request(`/deliveries/${deliveryId}/messages/`, { method: "POST", body: payload }),
    },
    proposals: {
      list: (deliveryId) => request(`/deliveries/${deliveryId}/proposals/`),
      create: (deliveryId, payload) => request(`/deliveries/${deliveryId}/proposals/`, { method: "POST", body: payload }),
      accept: (deliveryId, proposalId) =>
        request(`/deliveries/${deliveryId}/proposals/${proposalId}/accept/`, { method: "POST" }),
      decline: (deliveryId, proposalId) =>
        request(`/deliveries/${deliveryId}/proposals/${proposalId}/decline/`, { method: "POST" }),
    },
  },

  disputes: {
    list: (params) => request("/disputes/", { params }),
    create: (payload) => request("/disputes/", { method: "POST", body: payload }),
    get: (id) => request(`/disputes/${id}/`),
    messages: {
      list: (id) => request(`/disputes/${id}/messages/`),
      create: (id, payload) => request(`/disputes/${id}/messages/`, { method: "POST", body: payload }),
    },
    evidence: {
      create: (id, formData) => request(`/disputes/${id}/evidence/`, { method: "POST", body: formData, isForm: true }),
    },
    resolve: (id, payload) => request(`/disputes/${id}/resolve/`, { method: "POST", body: payload }),
  },

  wallet: {
    get: () => request("/wallet/"),
    transactions: (params) => request("/wallet/transactions/", { params }),
    withdraw: (payload) => request("/wallet/withdraw/", { method: "POST", body: payload }),
    transfer: (payload) => request("/wallet/transfer/", { method: "POST", body: payload }),
    spendingSummary: (range) => request("/wallet/spending-summary/", { params: { range } }),
    settlements: (params) => request("/wallet/settlements/", { params }),
    paymentMethods: {
      list: () => request("/wallet/payment-methods/"),
      create: (payload) => request("/wallet/payment-methods/", { method: "POST", body: payload }),
      remove: (id) => request(`/wallet/payment-methods/${id}/`, { method: "DELETE" }),
      setDefault: (id) => request(`/wallet/payment-methods/${id}/set-default/`, { method: "POST" }),
    },
  },

  dashboard: {
    customer: () => request("/dashboard/customer/"),
    driver: () => request("/dashboard/driver/"),
    adminOverview: () => request("/dashboard/admin-overview/"),
    financialAnalytics: () => request("/dashboard/financial-analytics/"),
    operationsMonitoring: () => request("/dashboard/operations-monitoring/"),
    notifications: {
      list: () => request("/dashboard/notifications/"),
      clear: () => request("/dashboard/notifications/clear/", { method: "POST" }),
    },
  },
};
