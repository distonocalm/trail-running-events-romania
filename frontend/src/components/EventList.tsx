import type { Event } from "../types";
import EventCard from "./EventCard";
import "./EventList.css";

interface EventListProps {
  events: Event[];
  loading: boolean;
}

function groupByMonth(events: Event[]): Map<string, Event[]> {
  const groups = new Map<string, Event[]>();
  for (const event of events) {
    const dateObj = new Date(event.date_start + "T00:00:00");
    const key = `${dateObj.getFullYear()}-${String(dateObj.getMonth()).padStart(2, "0")}`;
    const label = dateObj.toLocaleString("en", {
      month: "long",
      year: "numeric",
    });
    if (!groups.has(label)) {
      groups.set(label, []);
    }
    groups.get(label)!.push(event);
  }
  return groups;
}

export default function EventList({ events, loading }: EventListProps) {
  if (loading) {
    return (
      <div className="event-list">
        <div className="loading">Loading events...</div>
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div className="event-list">
        <div className="empty">No events found matching your filters.</div>
      </div>
    );
  }

  const grouped = groupByMonth(events);

  return (
    <div className="event-list">
      {Array.from(grouped.entries()).map(([month, monthEvents]) => (
        <div key={month}>
          <div className="month-label">{month}</div>
          {monthEvents.map((event) => (
            <EventCard key={event.id} event={event} />
          ))}
        </div>
      ))}
    </div>
  );
}
