import api from "./api";

const dashboardService = {
  getSummary: async () => {
    const response = await api.get("/dashboard/summary");
    return response.data;
  },

  getCostAnalytics: async () => {
    const response = await api.get("/dashboard/cost");
    return response.data;
  },
};

export default dashboardService;