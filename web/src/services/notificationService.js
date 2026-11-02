import apiClient from "./apiClient";

export const notificationService = {
  async list() {
    const { data } = await apiClient.get("/notifications/");
    return data;
  },
  async unreadCount() {
    const { data } = await apiClient.get("/notifications/unread_count/");
    return data;
  },
  async markRead(id) {
    const { data } = await apiClient.post(`/notifications/${id}/mark_read/`);
    return data;
  },
  async markAllRead() {
    const { data } = await apiClient.post("/notifications/mark_all_read/");
    return data;
  },
};

export function getWebSocketUrl(path) {
  const base = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

  // In production the frontend is typically served behind the same reverse
  // proxy as the API, so VITE_API_BASE_URL is relative (e.g. "/api") rather
  // than absolute — derive the WS origin from the page itself in that case,
  // since there's no host/protocol to transform from "http"/"https".
  if (!/^https?:\/\//.test(base)) {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}${path}`;
  }

  const wsBase = base.replace(/^http/, "ws").replace(/\/api\/?$/, "");
  return `${wsBase}${path}`;
}
