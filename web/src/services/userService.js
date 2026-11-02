import apiClient from "./apiClient";

export const userService = {
  async uploadProfilePicture(blob, filename = "avatar.jpg") {
    const form = new FormData();
    form.append("profile_picture", blob, filename);
    const { data } = await apiClient.patch("/users/me/", form);
    return data;
  },
  async deleteProfilePicture() {
    const { data } = await apiClient.delete("/users/me/profile-picture/");
    return data;
  },
  async updateMe(payload) {
    const { data } = await apiClient.patch("/users/me/", payload);
    return data;
  },
  async listDeliveryLocations() {
    const { data } = await apiClient.get("/users/delivery-locations/");
    return data;
  },
  async createDeliveryLocation(payload) {
    const { data } = await apiClient.post("/users/delivery-locations/", payload);
    return data;
  },
};

export const CAMPUS_LOCATIONS = [
  "Hostel A", "Hostel B", "Hostel C", "Hostel D", "Hostel E", "Hostel F",
  "Library", "Administration Block", "School of Computing", "School of Engineering",
  "Main Gate", "Sports Complex",
];
