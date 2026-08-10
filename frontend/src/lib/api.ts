import type {
  AcademyDetail,
  AcademyListResponse,
  AiRecommendationResponse,
  ClickEventPayload,
  CreatedResponse,
} from "./types";
import { ApiError } from "./types";

const DEFAULT_API_URL = "http://localhost:8000";

export function getApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL?.trim() || DEFAULT_API_URL;
  return raw.replace(/\/$/, "");
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const url = `${getApiBaseUrl()}${path}`;
  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
    });
  } catch (err) {
    throw new ApiError(
      err instanceof Error ? err.message : "네트워크 오류",
      0,
    );
  }

  if (!response.ok) {
    let body: unknown;
    try {
      body = await response.json();
    } catch {
      body = undefined;
    }
    const detail =
      typeof body === "object" &&
      body !== null &&
      "detail" in body &&
      typeof (body as { detail: unknown }).detail === "string"
        ? (body as { detail: string }).detail
        : `요청 실패 (${response.status})`;
    throw new ApiError(detail, response.status, body);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function fetchAcademies(params?: {
  q?: string;
  limit?: number;
  offset?: number;
}): Promise<AcademyListResponse> {
  const search = new URLSearchParams();
  if (params?.q) search.set("q", params.q);
  if (params?.limit != null) search.set("limit", String(params.limit));
  if (params?.offset != null) search.set("offset", String(params.offset));
  const qs = search.toString();
  return request<AcademyListResponse>(`/academies${qs ? `?${qs}` : ""}`);
}

/** Backend `limit` max is 100 — page until all academies are collected. */
const ACADEMY_PAGE_SIZE = 100;
const ACADEMY_MAX_PAGES = 50;

export async function fetchAllAcademies(params?: {
  q?: string;
}): Promise<AcademyListResponse> {
  const all: AcademyListResponse["items"] = [];
  let total = 0;
  let offset = 0;

  for (let page = 0; page < ACADEMY_MAX_PAGES; page++) {
    const res = await fetchAcademies({
      q: params?.q,
      limit: ACADEMY_PAGE_SIZE,
      offset,
    });
    total = res.total;
    if (res.items.length === 0) {
      break;
    }
    all.push(...res.items);
    if (all.length >= total || res.items.length < ACADEMY_PAGE_SIZE) {
      break;
    }
    const nextOffset = offset + res.items.length;
    if (nextOffset <= offset) {
      break;
    }
    offset = nextOffset;
  }

  return {
    items: all,
    total,
    limit: all.length,
    offset: 0,
  };
}

export function fetchAcademyDetail(
  academyId: number,
  init?: RequestInit,
): Promise<AcademyDetail> {
  return request<AcademyDetail>(`/academies/${academyId}`, init);
}

export function requestAiRecommendations(
  query: string,
  limit = 3,
): Promise<AiRecommendationResponse> {
  return request<AiRecommendationResponse>("/recommendations/ai", {
    method: "POST",
    body: JSON.stringify({ query, limit }),
  });
}

export function trackEvent(payload: ClickEventPayload): Promise<CreatedResponse> {
  return request<CreatedResponse>("/events", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
