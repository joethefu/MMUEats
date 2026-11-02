import apiClient from "./apiClient";

function getDeviceId() {
  const KEY = "mmueats_device_id";
  let id = localStorage.getItem(KEY);
  if (!id) {
    id = "dev-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
    localStorage.setItem(KEY, id);
  }
  return id;
}

export const advertisementService = {
  getDeviceId,

  async getActive(placement = "startup_popup") {
    const { data } = await apiClient.get("/advertisements/active/", { params: { placement } });
    return data;
  },
  async trackImpression(adId) {
    return apiClient.post(`/advertisements/${adId}/impression/`, { device_id: getDeviceId(), platform: "web" });
  },
  async trackClick(adId) {
    const { data } = await apiClient.post(`/advertisements/${adId}/click/`, { device_id: getDeviceId(), platform: "web" });
    return data;
  },

  // Admin management
  async adminList() {
    const { data } = await apiClient.get("/advertisements/");
    return data;
  },
  async create(formData) {
    const { data } = await apiClient.post("/advertisements/", formData, { headers: { "Content-Type": "multipart/form-data" } });
    return data;
  },
  async update(id, formData) {
    const { data } = await apiClient.patch(`/advertisements/${id}/`, formData, { headers: { "Content-Type": "multipart/form-data" } });
    return data;
  },
  async remove(id) {
    await apiClient.delete(`/advertisements/${id}/`);
  },
  async analytics(id) {
    const { data } = await apiClient.get(`/advertisements/${id}/analytics/`);
    return data;
  },
};
