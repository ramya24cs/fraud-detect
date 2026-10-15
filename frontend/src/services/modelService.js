import api from "./api";

const modelService = {
  getCurrentModel: async () => {
    const response = await api.get("/models/current");
    return response.data;
  },

  retrainModel: async () => {
    const response = await api.post("/models/retrain");
    return response.data;
  },
};

export default modelService;