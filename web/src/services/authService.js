import apiClient, { tokenStorage } from "./apiClient";

export const authService = {
  async register(payload) {
    // payload: { full_name, email, phone_number, password, confirm_password }
    const { data } = await apiClient.post("/auth/register/", payload);
    return data;
  },

  async login({ email, password }) {
    const { data } = await apiClient.post("/auth/login/", { email, password });
    tokenStorage.set(data.access, data.refresh);
    return data.user;
  },

  async logout() {
    const refresh = tokenStorage.getRefresh();
    try {
      if (refresh) await apiClient.post("/auth/logout/", { refresh });
    } finally {
      tokenStorage.clear();
    }
  },

  async verifyEmail(token) {
    const { data } = await apiClient.post("/auth/verify-email/", { token });
    return data;
  },

  async resendVerification(email) {
    const { data } = await apiClient.post("/auth/resend-verification/", { email });
    return data;
  },

  async requestPasswordReset(email) {
    const { data } = await apiClient.post("/auth/password-reset/request/", { email });
    return data;
  },

  async confirmPasswordReset({ token, password, confirm_password }) {
    const { data } = await apiClient.post("/auth/password-reset/confirm/", {
      token,
      password,
      confirm_password,
    });
    return data;
  },

  async changePassword({ old_password, new_password, confirm_password }) {
    const { data } = await apiClient.post("/auth/change-password/", {
      old_password,
      new_password,
      confirm_password,
    });
    return data;
  },

  async fetchCurrentUser() {
    const { data } = await apiClient.get("/users/me/");
    return data;
  },
};
