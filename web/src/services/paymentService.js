import apiClient from "./apiClient";

export const paymentService = {
  async stkPush({ order_id, phone_number }) {
    const { data } = await apiClient.post("/payments/mpesa/stk-push/", { order_id, phone_number });
    return data;
  },
  async simulate({ order_id, success = true }) {
    const { data } = await apiClient.post("/payments/mpesa/simulate/", { order_id, success });
    return data;
  },
  async list() {
    const { data } = await apiClient.get("/payments/mine/");
    return data;
  },
};
