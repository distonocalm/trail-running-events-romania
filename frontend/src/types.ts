export interface DistanceItem {
  name?: string;
  km: number;
  elevation_gain?: number;
}

export interface Event {
  id: string;
  name: string;
  date_start: string;
  date_end: string | null;
  location: string | null;
  county: string | null;
  distances: DistanceItem[] | null;
  description: string | null;
  registration_status: string | null;
  registration_deadline: string | null;
  price: string | null;
  event_url: string | null;
  image_url: string | null;
  year: number;
  created_at: string;
  updated_at: string;
}

export interface EventListResponse {
  items: Event[];
  total: number;
  page: number;
  per_page: number;
}

export interface Stats {
  event_count: number;
  source_count: number;
  county_count: number;
  upcoming_count: number;
}

export interface EventFilters {
  search?: string;
  month?: number;
  county?: string;
  distance_min?: number;
  distance_max?: number;
  upcoming?: boolean;
  page?: number;
  per_page?: number;
}
