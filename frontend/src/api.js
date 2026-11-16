const base = import.meta.env.VITE_API_BASE || "";

export async function api(path, { token, method = "GET", body } = {}) {
  const response = await fetch(`${base}/api${path}`, {
    method,
    headers: {
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  const data = response.status === 204 ? null : await response.json();
  if (!response.ok) {
    const detail = data?.detail;
    const error = new Error(Array.isArray(detail)
      ? detail.map((item) => `${item.loc.at(-1)}: ${item.msg}`).join("; ")
      : detail || "Request failed");
    error.status = response.status;
    throw error;
  }
  return data;
}
