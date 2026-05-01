import type { EventListResponse, Stats, EventFilters } from "./types";

const API_BASE = "/api";

export async function fetchEvents(
  filters: EventFilters = {}
): Promise<EventListResponse> {
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.month) params.set("month", String(filters.month));
  if (filters.county) params.set("county", filters.county);
  if (filters.distance_min)
    params.set("distance_min", String(filters.distance_min));
  if (filters.distance_max)
    params.set("distance_max", String(filters.distance_max));
  if (filters.upcoming) params.set("upcoming", "true");
  if (filters.page) params.set("page", String(filters.page));
  if (filters.per_page) params.set("per_page", String(filters.per_page));

  const url = `${API_BASE}/events?${params.toString()}`;
  const response = await fetch(url);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

export async function fetchStats(): Promise<Stats> {
  const response = await fetch(`${API_BASE}/stats`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}
