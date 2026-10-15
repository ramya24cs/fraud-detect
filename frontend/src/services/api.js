import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8001",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const requestUrl = error.config?.url ?? "";
    const isAuthenticationRequest = requestUrl.startsWith("/auth/");

    if (error.response?.status === 401 && !isAuthenticationRequest) {
      localStorage.removeItem("access_token");
      window.dispatchEvent(new Event("auth:session-expired"));
    }

    return Promise.reject(error);
  }
);

export default api;