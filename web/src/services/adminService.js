import apiClient from "./apiClient";

export const adminService = {
  async getDashboard() {
    const { data } = await apiClient.get("/analytics/admin/dashboard/");
    return data;
  },
  async listUsers(params = {}) {
    const { data } = await apiClient.get("/analytics/admin/users/", { params });
    return data;
  },
  async suspendUser(id) {
    const { data } = await apiClient.post(`/analytics/admin/users/${id}/suspend/`);
    return data;
  },
  async reactivateUser(id) {
    const { data } = await apiClient.post(`/analytics/admin/users/${id}/reactivate/`);
    return data;
  },
  async getAuditLogs() {
    const { data } = await apiClient.get("/analytics/admin/audit-logs/");
    return data;
  },
  async listVendorApplications(params = {}) {
    const { data } = await apiClient.get("/users/vendor-applications/", { params });
    return data;
  },
  async reviewVendorApplication(id, payload) {
    const { data } = await apiClient.post(`/users/vendor-applications/${id}/review/`, payload);
    return data;
  },
  async listDeliveryApplications(params = {}) {
    const { data } = await apiClient.get("/users/delivery-partner-applications/", { params });
    return data;
  },
  async reviewDeliveryApplication(id, payload) {
    const { data } = await apiClient.post(`/users/delivery-partner-applications/${id}/review/`, payload);
    return data;
  },
};
