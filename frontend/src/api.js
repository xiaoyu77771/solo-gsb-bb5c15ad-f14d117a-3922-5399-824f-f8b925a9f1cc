// 统一的后端请求封装：相对路径，开发期由 Vite 代理，生产期同源访问
async function request(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const message = data && data.detail ? data.detail : `请求失败（${res.status}）`;
    const err = new Error(message);
    err.status = res.status;
    throw err;
  }
  return data;
}

export const api = {
  createEvent: (title) =>
    request("/api/events", { method: "POST", body: JSON.stringify({ title }) }),
  getEvent: (eventId, token) =>
    request(`/api/events/${eventId}`, { headers: { "X-Event-Token": token } }),
  addParticipant: (eventId, token, name) =>
    request(`/api/events/${eventId}/participants`, {
      method: "POST",
      headers: { "X-Event-Token": token },
      body: JSON.stringify({ name }),
    }),
  deleteParticipant: (eventId, token, participantId) =>
    request(`/api/events/${eventId}/participants/${participantId}`, {
      method: "DELETE",
      headers: { "X-Event-Token": token },
    }),
  addConstraint: (eventId, token, giver_id, receiver_id) =>
    request(`/api/events/${eventId}/constraints`, {
      method: "POST",
      headers: { "X-Event-Token": token },
      body: JSON.stringify({ giver_id, receiver_id }),
    }),
  deleteConstraint: (eventId, token, constraintId) =>
    request(`/api/events/${eventId}/constraints/${constraintId}`, {
      method: "DELETE",
      headers: { "X-Event-Token": token },
    }),
  draw: (eventId, token) =>
    request(`/api/events/${eventId}/draw`, {
      method: "POST",
      headers: { "X-Event-Token": token },
    }),
  revealStatus: (token) => request(`/api/reveal/${token}`),
  revealNow: (token) => request(`/api/reveal/${token}`, { method: "POST" }),
};

const TOKEN_PREFIX = "secret-santa-token:";

export function saveEventToken(eventId, token) {
  try {
    localStorage.setItem(TOKEN_PREFIX + eventId, token);
  } catch {
    // 隐私模式等场景忽略，用户可通过“已有活动”手动粘贴令牌
  }
}

export function loadEventToken(eventId) {
  try {
    return localStorage.getItem(TOKEN_PREFIX + eventId) || "";
  } catch {
    return "";
  }
}
