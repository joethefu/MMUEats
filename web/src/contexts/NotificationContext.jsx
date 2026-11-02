import { createContext, useContext, useEffect, useRef, useState, useCallback } from "react";
import { notificationService, getWebSocketUrl } from "../services/notificationService";
import { tokenStorage } from "../services/apiClient";
import { useAuth } from "./AuthContext";

const NotificationContext = createContext(null);

export function NotificationProvider({ children }) {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const socketRef = useRef(null);

  const refresh = useCallback(async () => {
    if (!user) return;
    try {
      const [list, unread] = await Promise.all([notificationService.list(), notificationService.unreadCount()]);
      setNotifications(list.results || list);
      setUnreadCount(unread.unread_count);
    } catch {
      // Silent — notifications are a convenience layer, never block the app.
    }
  }, [user]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Live WebSocket connection: pushes new notifications instantly instead of
  // waiting for the next poll/page load. Falls back gracefully — if the socket
  // can't connect (network, no WS support), the REST-based refresh() above
  // still keeps notifications reasonably fresh on each page load.
  useEffect(() => {
    if (!user) {
      socketRef.current?.close();
      return;
    }
    const token = tokenStorage.getAccess();
    if (!token) return;

    const ws = new WebSocket(getWebSocketUrl(`/ws/notifications/?token=${token}`));
    socketRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.event === "notification") {
          setNotifications((prev) => [
            { id: payload.id, notification_type: payload.notification_type, title: payload.title, message: payload.message, data: payload.data, is_read: false, created_at: payload.created_at },
            ...prev,
          ]);
          setUnreadCount((c) => c + 1);
        }
        // "order_update" events are consumed directly by OrderDetailPage via its own listener.
      } catch {
        // ignore malformed frames
      }
    };

    ws.onerror = () => {
      // Swallow — REST refresh() is the fallback source of truth.
    };

    return () => ws.close();
  }, [user]);

  const markRead = async (id) => {
    await notificationService.markRead(id);
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    setUnreadCount((c) => Math.max(0, c - 1));
  };

  const markAllRead = async () => {
    await notificationService.markAllRead();
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    setUnreadCount(0);
  };

  return (
    <NotificationContext.Provider value={{ notifications, unreadCount, markRead, markAllRead, refresh }}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const ctx = useContext(NotificationContext);
  if (!ctx) throw new Error("useNotifications must be used within a NotificationProvider");
  return ctx;
}
