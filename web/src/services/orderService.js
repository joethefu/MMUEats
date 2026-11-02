import apiClient from "./apiClient";

export const cartService = {
  async get() {
    const { data } = await apiClient.get("/orders/cart/");
    return data;
  },
  async addItem({ meal_id, quantity = 1, special_instructions = "" }) {
    const { data } = await apiClient.post("/orders/cart/", { meal_id, quantity, special_instructions });
    return data;
  },
  async removeItem(itemId) {
    const { data } = await apiClient.delete("/orders/cart/", { params: { item_id: itemId } });
    return data;
  },
  async clear() {
    const { data } = await apiClient.delete("/orders/cart/");
    return data;
  },
};

export const orderService = {
  async checkout(payload) {
    const { data } = await apiClient.post("/orders/checkout/", payload);
    return data;
  },
  async list(params = {}) {
    const { data } = await apiClient.get("/orders/", { params });
    return data;
  },
  async get(id) {
    const { data } = await apiClient.get(`/orders/${id}/`);
    return data;
  },
  async updateStatus(id, payload) {
    const { data } = await apiClient.post(`/orders/${id}/update_status/`, payload);
    return data;
  },
  async cancel(id, reason = "") {
    const { data } = await apiClient.post(`/orders/${id}/cancel/`, { reason });
    return data;
  },
  async reorder(id) {
    const { data } = await apiClient.post(`/orders/${id}/reorder/`);
    return data;
  },
};
