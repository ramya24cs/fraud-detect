import { useState } from "react";
import { login as loginUser } from "../services/authService";

export const useAuth = () => {
  const [token, setToken] = useState(
    localStorage.getItem("access_token")
  );

  const login = async (credentials) => {
    const data = await loginUser(credentials);

    if (data.access_token) {
      localStorage.setItem("access_token", data.access_token);
      setToken(data.access_token);
    }

    return data;
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    setToken(null);
  };

  return {
    token,
    isAuthenticated: Boolean(token),
    login,
    logout,
  };
};