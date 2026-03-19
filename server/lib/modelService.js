const MODEL_SERVICE_URL = process.env.MODEL_SERVICE_URL || "http://127.0.0.1:8790";

async function request(path, options = {}) {
  const response = await fetch(`${MODEL_SERVICE_URL}${path}`, {
    method: options.method || "GET",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    body: options.body,
  });

  const raw = await response.text();
  const payload = raw ? JSON.parse(raw) : null;

  if (!response.ok) {
    throw new Error(payload?.error || "Model service request failed.");
  }

  return payload;
}

export async function inferWithModelService(featureId, actionId, inputs, session) {
  return request("/infer", {
    method: "POST",
    body: JSON.stringify({
      featureId,
      actionId,
      inputs,
      session,
    }),
  });
}

export async function getModelSummary() {
  return request("/summary");
}

export async function getModelHealth() {
  return request("/health");
}
