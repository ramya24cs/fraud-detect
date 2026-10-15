import api from "./api";

const feedbackService = {
  submitFeedback: async (data) => {
    const response = await api.post("/feedback", data);
    return response.data;
  },
};

export default feedbackService;