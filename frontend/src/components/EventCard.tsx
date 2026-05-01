import { useState } from "react";
import type { Event } from "../types";
import "./EventCard.css";

interface EventCardProps {
  event: Event;
}

export default function EventCard({ event }: EventCardProps) {
  const [expanded, setExpanded] = useState(false);
  const dateObj = new Date(event.date_start + "T00:00:00");
  const day = dateObj.getDate();
  const month = dateObj.toLocaleString("en", { month: "short" });
  const isPast = dateObj < new Date();
  const isOpen = event.registration_status === "open";

  const maxElevation =
    event.distances
      ?.map((d) => d.elevation_gain ?? 0)
      .reduce((a, b) => Math.max(a, b), 0) ?? 0;

  return (
    <div
      className={`event-card ${expanded ? "expanded" : ""} ${isPast ? "past" : ""}`}
      onClick={() => setExpanded(!expanded)}
    >
      {expanded ? (
        <div
          className="card-image card-image-full"
          style={
            event.image_url
              ? { backgroundImage: `url(${event.image_url})` }
              : undefined
          }
        >
          {!event.image_url && (
            <div className="card-image-placeholder">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="m8 3 4 8 5-5 2 15H2L8 3z" />
              </svg>
            </div>
          )}
          <div className="card-image-date">
            <div className="day">{day}</div>
            <div className="month">{month}</div>
          </div>
        </div>
      ) : (
        <div
          className="card-image card-image-thumb"
          style={
            event.image_url
              ? { backgroundImage: `url(${event.image_url})` }
              : undefined
          }
        >
          {!event.image_url && (
            <div className="card-image-placeholder">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="m8 3 4 8 5-5 2 15H2L8 3z" />
              </svg>
            </div>
          )}
          <div className="card-image-date">
            <div className="day">{day}</div>
            <div className="month">{month}</div>
          </div>
        </div>
      )}

      <div className="card-body">
        <div className="card-header">
          <div>
            <div className="card-name">{event.name}</div>
            <div className="card-meta">
              {event.location && (
                <span>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                    <circle cx="12" cy="10" r="3" />
                  </svg>
                  {event.location}{event.county ? `, ${event.county}` : ""}
                </span>
              )}
              {maxElevation > 0 && (
                <span>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="m8 3 4 8 5-5 2 15H2L8 3z" />
                  </svg>
                  {maxElevation.toLocaleString()}m elevation
                </span>
              )}
            </div>
          </div>
          <div className={`card-status ${isPast ? "status-past" : isOpen ? "status-open" : "status-unknown"}`}>
            {isPast ? (
              "Past"
            ) : isOpen ? (
              <>
                <div className="status-dot" />
                Open
              </>
            ) : (
              "Upcoming"
            )}
          </div>
        </div>

        {event.distances && event.distances.length > 0 && (
          <div className="card-distances">
            {event.distances.map((d, i) => (
              <span key={i} className="distance-tag">
                {d.km}K
              </span>
            ))}
          </div>
        )}

        {expanded && (
          <div className="card-expanded" onClick={(e) => e.stopPropagation()}>
            {event.description && (
              <p className="card-description">{event.description}</p>
            )}
            <div className="card-details">
              {maxElevation > 0 && (
                <div className="detail-item">
                  <span className="detail-label">Elevation</span>
                  <span className="detail-value">
                    {maxElevation.toLocaleString()}m
                  </span>
                </div>
              )}
              <div className="detail-item">
                <span className="detail-label">Registration</span>
                <span
                  className="detail-value"
                  style={isOpen ? { color: "#2e7d32" } : undefined}
                >
                  {event.registration_status === "open"
                    ? "Open"
                    : event.registration_status === "closed"
                      ? "Closed"
                      : "Unknown"}
                </span>
              </div>
              {event.registration_deadline && (
                <div className="detail-item">
                  <span className="detail-label">Deadline</span>
                  <span className="detail-value">
                    {new Date(event.registration_deadline + "T00:00:00").toLocaleDateString("en", {
                      month: "long",
                      day: "numeric",
                      year: "numeric",
                    })}
                  </span>
                </div>
              )}
              {event.price && (
                <div className="detail-item">
                  <span className="detail-label">Price</span>
                  <span className="detail-value">{event.price}</span>
                </div>
              )}
            </div>
            {event.event_url && (
              <a
                href={event.event_url}
                target="_blank"
                rel="noopener noreferrer"
                className="card-cta"
              >
                Visit event page
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M7 17L17 7M17 7H7M17 7v10" />
                </svg>
              </a>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
