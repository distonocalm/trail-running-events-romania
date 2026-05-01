import { useCallback, useEffect, useState } from "react";
import { fetchEvents, fetchStats } from "./api";
import Hero from "./components/Hero";
import FilterBar from "./components/FilterBar";
import EventList from "./components/EventList";
import type { Event, EventFilters, Stats } from "./types";

export default function App() {
  const [events, setEvents] = useState<Event[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [filters, setFilters] = useState<EventFilters>({ per_page: 100 });
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);

  const loadEvents = useCallback(async (f: EventFilters) => {
    setLoading(true);
    try {
      const data = await fetchEvents(f);
      setEvents(data.items);
      setTotalCount(data.total);
    } catch (err) {
      console.error("Failed to load events:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadEvents(filters);
  }, [filters, loadEvents]);

  useEffect(() => {
    fetchStats()
      .then(setStats)
      .catch((err) => console.error("Failed to load stats:", err));
  }, []);

  function handleFilterChange(newFilters: EventFilters) {
    setFilters({ ...newFilters, per_page: 100 });
  }

  return (
    <div className="app">
      <Hero stats={stats} />
      <FilterBar
        filters={filters}
        onFilterChange={handleFilterChange}
        totalCount={totalCount}
      />
      <EventList events={events} loading={loading} />
    </div>
  );
}
