import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

const ACCESS_TOKEN_KEY = "mmueats_access_token";
const REFRESH_TOKEN_KEY = "mmueats_refresh_token";

export const tokenStorage = {
  getAccess: () => localStorage.getItem(ACCESS_TOKEN_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_TOKEN_KEY),
  set: (access, refresh) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  },
  clear: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },
};

const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use((config) => {
  const token = tokenStorage.getAccess();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  // Let the browser set "multipart/form-data; boundary=..." itself for file uploads.
  // Forcing the JSON default here makes axios serialise the FormData to JSON, which the
  // backend rejects with "The submitted data was not a file. Check the encoding type on the form."
  if (typeof FormData !== "undefined" && config.data instanceof FormData) {
    config.headers.delete ? config.headers.delete("Content-Type") : delete config.headers["Content-Type"];
  }
  return config;
});

// Refresh-on-401 queue so simultaneous requests don't each trigger their own refresh.
let isRefreshing = false;
let pendingQueue = [];

function resolveQueue(error, token = null) {
  pendingQueue.forEach(({ resolve, reject }) => (error ? reject(error) : resolve(token)));
  pendingQueue = [];
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status !== 401 || originalRequest._retry || originalRequest.url?.includes("/auth/token/refresh")) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        pendingQueue.push({ resolve, reject });
      }).then((token) => {
        originalRequest.headers.Authorization = `Bearer ${token}`;
        return apiClient(originalRequest);
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;
    const refresh = tokenStorage.getRefresh();

    if (!refresh) {
      tokenStorage.clear();
      window.dispatchEvent(new Event("mmueats:logout"));
      return Promise.reject(error);
    }

    try {
      const { data } = await axios.post(`${BASE_URL}/auth/token/refresh/`, { refresh });
      tokenStorage.set(data.access, data.refresh);
      resolveQueue(null, data.access);
      originalRequest.headers.Authorization = `Bearer ${data.access}`;
      return apiClient(originalRequest);
    } catch (refreshError) {
      resolveQueue(refreshError, null);
      tokenStorage.clear();
      window.dispatchEvent(new Event("mmueats:logout"));
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export default apiClient;
