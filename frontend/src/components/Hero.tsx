import type { Stats } from "../types";
import "./Hero.css";

interface HeroProps {
  stats: Stats | null;
}

export default function Hero({ stats }: HeroProps) {
  return (
    <section className="hero">
      <nav className="hero-nav">
        <div className="hero-logo">Trail Running Romania</div>
        <div className="hero-links">
          <span>Events</span>
          <span>About</span>
        </div>
      </nav>
      <div className="hero-content">
        <h1>
          Discover every <span className="accent">trail race</span> in Romania.
        </h1>
        <p>
          All trail running events for 2026 in one place. From forest runs to
          mountain ultras across the Carpathians.
        </p>
        {stats && (
          <div className="stats">
            <div className="stat">
              <div className="stat-number">{stats.event_count}</div>
              <div className="stat-label">Events</div>
            </div>
            <div className="stat">
              <div className="stat-number">{stats.county_count}</div>
              <div className="stat-label">Counties</div>
            </div>
            <div className="stat">
              <div className="stat-number">{stats.source_count}</div>
              <div className="stat-label">Sources</div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
