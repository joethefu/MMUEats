import apiClient from "./apiClient";

export const restaurantService = {
  async list(params = {}) {
    const { data } = await apiClient.get("/restaurants/", { params });
    return data;
  },
  async get(slug) {
    const { data } = await apiClient.get(`/restaurants/${slug}/`);
    return data;
  },
  async listMeals(restaurantId) {
    const { data } = await apiClient.get("/meals/", { params: { restaurant: restaurantId } });
    return data;
  },
  async favorite(restaurantId) {
    const { data } = await apiClient.post("/restaurants/favorites/", { restaurant: restaurantId });
    return data;
  },
  async unfavorite(favoriteId) {
    await apiClient.delete(`/restaurants/favorites/${favoriteId}/`);
  },
  async listFavorites() {
    const { data } = await apiClient.get("/restaurants/favorites/");
    return data;
  },
  async listReviews(restaurantId) {
    const { data } = await apiClient.get("/restaurants/reviews/", { params: { restaurant: restaurantId } });
    return data;
  },
  async submitReview({ restaurant, rating, comment }) {
    const { data } = await apiClient.post("/restaurants/reviews/", { restaurant, rating, comment });
    return data;
  },
};

export const mealService = {
  async list(params = {}) {
    const { data } = await apiClient.get("/meals/", { params });
    return data;
  },
  async get(id) {
    const { data } = await apiClient.get(`/meals/${id}/`);
    return data;
  },
  async listCategories() {
    const { data } = await apiClient.get("/meals/categories/");
    return data;
  },
  async favorite(mealId) {
    const { data } = await apiClient.post("/meals/favorites/", { meal: mealId });
    return data;
  },
  async unfavorite(favoriteId) {
    await apiClient.delete(`/meals/favorites/${favoriteId}/`);
  },
  async listFavorites() {
    const { data } = await apiClient.get("/meals/favorites/");
    return data;
  },
  async listReviews(mealId) {
    const { data } = await apiClient.get("/meals/reviews/", { params: { meal: mealId } });
    return data;
  },
  async submitReview({ meal, rating, comment }) {
    const { data } = await apiClient.post("/meals/reviews/", { meal, rating, comment });
    return data;
  },
  async deleteReview(id) {
    await apiClient.delete(`/meals/reviews/${id}/`);
  },
};
