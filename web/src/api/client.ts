const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const API_PREFIX = "/api/v1";

export type User = {
  id: string;
  email: string;
  full_name: string;
  role: "patient" | "doctor" | "admin";
  auth_provider: "local" | "google";
  avatar_url: string | null;
  is_active: boolean;
};

export type CurrentUserClaims = {
  user_id: string;
  email: string;
  role: "patient" | "doctor" | "admin";
};

export type ConsentStatus = {
  has_valid_consent: boolean;
  current_policy_version: string;
  latest_accepted_policy_version: string | null;
};

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${API_PREFIX}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
  });

  const text = await response.text();
  const payload = text ? JSON.parse(text) : {};

  if (!response.ok) {
    const message = payload.detail ?? payload.message ?? response.statusText;
    throw new ApiError(response.status, String(message));
  }

  return payload as T;
}

export async function getMe(): Promise<CurrentUserClaims> {
  return request<CurrentUserClaims>("/auth/me");
}

export async function login(email: string, password: string): Promise<{ user: User }> {
  return request<{ user: User }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function register(
  email: string,
  password: string,
  fullName: string,
): Promise<User> {
  return request<User>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
}

export async function logout(): Promise<void> {
  await request<{ status: string }>("/auth/logout", { method: "POST" });
}

export async function getGoogleOAuthUrl(): Promise<string> {
  const body = await request<{ url: string }>("/auth/google");
  return body.url;
}

export async function exchangeGoogleAuthCode(authCode: string): Promise<{ user: User }> {
  return request<{ user: User }>("/auth/google/exchange", {
    method: "POST",
    body: JSON.stringify({ auth_code: authCode }),
  });
}

export async function getConsentStatus(): Promise<ConsentStatus> {
  return request<ConsentStatus>("/consent/status");
}

export async function acceptConsent(policyVersion: string): Promise<void> {
  await request("/consent/accept", {
    method: "POST",
    body: JSON.stringify({ policy_version: policyVersion }),
  });
}
