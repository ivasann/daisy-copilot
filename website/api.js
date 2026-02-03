/* Daisy API helper */
(() => {
  const API_BASE = window.DAISY_API_BASE || "http://localhost:8000";

  async function request(path, options = {}) {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
    const isJson = res.headers.get("content-type")?.includes("application/json");
    const data = isJson ? await res.json() : null;
    if (!res.ok) {
      const message = data?.detail || `Request failed: ${res.status}`;
      throw new Error(message);
    }
    return data;
  }

  const DaisyAPI = {
    getBalance: (userId) => request(`/balance/${userId}`),
    earnCoins: (payload) => request("/earn-coins", { method: "POST", body: JSON.stringify(payload) }),
    spendCoins: (payload) => request("/spend-coins", { method: "POST", body: JSON.stringify(payload) }),
    logTask: (payload) => request("/log-task", { method: "POST", body: JSON.stringify(payload) }),
    pomodoroComplete: (payload) => request("/pomodoro-complete", { method: "POST", body: JSON.stringify(payload) }),
    aiChat: (payload) => request("/ai-chat", { method: "POST", body: JSON.stringify(payload) }),
    waitlist: (payload) => request("/waitlist", { method: "POST", body: JSON.stringify(payload) }),
    history: (userId) => request(`/history/${userId}`),
  };

  window.DaisyAPI = DaisyAPI;
})();
