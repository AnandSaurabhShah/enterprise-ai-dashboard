const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";
const SESSION_KEY = "enterprise-ai-session";

export type Session = {
  token: string;
  user: {
    email: string;
    name: string;
    provider: string;
    workspace: string;
    issuedAt: string;
  };
};

type RequestOptions = {
  method?: string;
  body?: BodyInit | null;
  headers?: Record<string, string>;
  auth?: boolean;
};

function parseResponseBody(bodyText: string) {
  if (!bodyText) {
    return null;
  }

  try {
    return JSON.parse(bodyText);
  } catch {
    return bodyText;
  }
}

async function request(path: string, options: RequestOptions = {}) {
  const session = getSession();
  const headers = new Headers(options.headers || {});

  if (options.auth !== false && session?.token) {
    headers.set("Authorization", `Bearer ${session.token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    method: options.method || "GET",
    headers,
    body: options.body,
  });

  const raw = await response.text();
  const payload = parseResponseBody(raw);

  if (!response.ok) {
    throw new Error(payload?.error || "Request failed.");
  }

  return payload;
}

export function getSession(): Session | null {
  const raw = window.localStorage.getItem(SESSION_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw);
  } catch {
    window.localStorage.removeItem(SESSION_KEY);
    return null;
  }
}

export function saveSession(session: Session) {
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function clearSession() {
  window.localStorage.removeItem(SESSION_KEY);
}

export async function loginWithPassword(email: string, password: string) {
  const session = await request("/auth/login", {
    method: "POST",
    auth: false,
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password, provider: "password" }),
  });

  saveSession(session);
  return session as Session;
}

export async function loginWithProvider(provider: "google" | "microsoft") {
  const email = `${provider}.demo@enterprise-ai.local`;
  const session = await request("/auth/login", {
    method: "POST",
    auth: false,
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, provider }),
  });

  saveSession(session);
  return session as Session;
}

export async function getDashboardSummary() {
  return request("/dashboard/summary");
}

export async function runFeatureAction(featureId: string, actionId: string, values: Record<string, unknown>) {
  const formData = new FormData();

  Object.entries(values).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }

    if (value instanceof File) {
      formData.append(key, value);
      return;
    }

    formData.append(key, String(value));
  });

  return request(`/features/${featureId}/${actionId}`, {
    method: "POST",
    body: formData,
  });
}
