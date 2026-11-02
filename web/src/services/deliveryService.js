import apiClient from "./apiClient";

export const deliveryService = {
  async getProfile() {
    const { data } = await apiClient.get("/deliveries/profile/");
    return data;
  },
  async updateProfile(payload) {
    const { data } = await apiClient.patch("/deliveries/profile/", payload);
    return data;
  },
  async listAvailable() {
    const { data } = await apiClient.get("/deliveries/available/");
    return data;
  },
  async listMine(params = {}) {
    const { data } = await apiClient.get("/deliveries/mine/", { params });
    return data;
  },
  async accept(deliveryId) {
    const { data } = await apiClient.post(`/deliveries/mine/${deliveryId}/accept/`);
    return data;
  },
  async reject(deliveryId) {
    const { data } = await apiClient.post(`/deliveries/mine/${deliveryId}/reject/`);
    return data;
  },
  async getEarnings() {
    const { data } = await apiClient.get("/deliveries/earnings/");
    return data;
  },
  async updateOrderStatus(orderId, payload) {
    const { data } = await apiClient.post(`/orders/${orderId}/update_status/`, payload);
    return data;
  },
};
