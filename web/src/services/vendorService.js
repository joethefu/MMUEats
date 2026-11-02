import apiClient from "./apiClient";

export const vendorService = {
  async getMyRestaurant() {
    const { data } = await apiClient.get("/restaurants/mine/");
    return data;
  },
  async createRestaurant(payload) {
    const { data } = await apiClient.post("/restaurants/", payload, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },
  async updateRestaurant(slug, payload) {
    const { data } = await apiClient.patch(`/restaurants/${slug}/`, payload, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },
  async getDashboard() {
    const { data } = await apiClient.get("/analytics/vendor/dashboard/");
    return data;
  },
  async getSalesReport(params = {}) {
    const { data } = await apiClient.get("/analytics/vendor/sales-report/", { params });
    return data;
  },
  async listMyMeals(restaurantId) {
    const { data } = await apiClient.get("/meals/", { params: { restaurant: restaurantId } });
    return data;
  },
  async createMeal(payload) {
    const { data } = await apiClient.post("/meals/", payload);
    return data;
  },
  async updateMeal(id, payload) {
    const { data } = await apiClient.patch(`/meals/${id}/`, payload);
    return data;
  },
  async deleteMeal(id) {
    await apiClient.delete(`/meals/${id}/`);
  },
  async listCategories() {
    const { data } = await apiClient.get("/meals/categories/");
    return data;
  },
  async listOrders(params = {}) {
    const { data } = await apiClient.get("/orders/", { params });
    return data;
  },
  async updateOrderStatus(id, payload) {
    const { data } = await apiClient.post(`/orders/${id}/update_status/`, payload);
    return data;
  },
};
