import axios from "axios";
import { devPrint } from "./RandomUtils";
// import { ACCESS_TOKEN } from "./constants";

const apiUrl = import.meta.env.DEV
  ? "http://localhost:8000"
  : "/choreo-apis/awbo/backend/rest-api-be2/v1.0";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ? import.meta.env.VITE_API_URL : apiUrl,
});

export const getCSRF = async () => {
  try {
    const response = await api.get("/auth/csrf/");
    const csrfToken = response.headers["x-csrftoken"];
    if (csrfToken) {
      api.defaults.headers.common["X-CSRFToken"] = csrfToken;
      devPrint("CSRF token updated:", csrfToken);
    }
  } catch (error) {
    devPrint("Failed to fetch CSRF token:", error);
  }
};

api.interceptors.request.use(async (config) => {
  if (config.url === "/auth/csrf/") {
    return config;
  }
  if (!api.defaults.headers.common["X-CSRFToken"]) {
    await getCSRF();
  }
  return config;
});

export default api;
