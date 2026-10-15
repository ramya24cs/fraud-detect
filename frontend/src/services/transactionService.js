import api from "./api";

const transactionService = {
  predictTransaction: async (data) => {
    const response = await api.post("/transactions/predict", data);
    return response.data;
  },

  analyzeTransaction: async (data) => {
    const response = await api.post("/transactions/analyze", data);
    return response.data;
  },

  getRiskAlerts: async () => {
    const response = await api.get("/transactions/risk-alerts");
    return response.data;
  },

  getPendingReviews: async () => {
    const response = await api.get("/transactions/reviews/pending");
    return response.data;
  },

  getAssessments: async (params = {}) => {
    const response = await api.get("/transactions/assessments", { params });
    return response.data;
  },

  submitReviewDecision: async (assessmentId, decision) => {
    const response = await api.post(
      `/transactions/assessments/${assessmentId}/review`,
      { decision }
    );
    return response.data;
  },

  getTransaction: async (transactionId) => {
    const response = await api.get(`/transactions/${transactionId}`);
    return response.data;
  },

  getReviewQueue: async () => {
    const response = await api.get("/review-queue");
    return response.data;
  },
};

export default transactionService;