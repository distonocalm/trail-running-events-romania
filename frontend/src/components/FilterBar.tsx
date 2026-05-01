import { useState } from "react";
import type { EventFilters } from "../types";
import "./FilterBar.css";

interface FilterBarProps {
  filters: EventFilters;
  onFilterChange: (filters: EventFilters) => void;
  totalCount: number;
}

type DistancePreset = "all" | "upcoming" | "ultra" | "marathon" | "short";

const DISTANCE_PRESETS: { key: DistancePreset; label: string }[] = [
  { key: "all", label: "All" },
  { key: "upcoming", label: "Upcoming" },
  { key: "ultra", label: "Ultra (50K+)" },
  { key: "marathon", label: "Marathon" },
  { key: "short", label: "Short (<21K)" },
];

export default function FilterBar({
  filters,
  onFilterChange,
  totalCount,
}: FilterBarProps) {
  const [activePreset, setActivePreset] = useState<DistancePreset>("all");
  const [searchValue, setSearchValue] = useState("");

  function handlePreset(preset: DistancePreset) {
    setActivePreset(preset);
    const newFilters: EventFilters = { ...filters };
    delete newFilters.distance_min;
    delete newFilters.distance_max;
    delete newFilters.upcoming;

    switch (preset) {
      case "upcoming":
        newFilters.upcoming = true;
        break;
      case "ultra":
        newFilters.distance_min = 50;
        break;
      case "marathon":
        newFilters.distance_min = 42;
        newFilters.distance_max = 50;
        break;
      case "short":
        newFilters.distance_max = 21;
        break;
    }
    onFilterChange(newFilters);
  }

  function handleSearch(value: string) {
    setSearchValue(value);
    onFilterChange({ ...filters, search: value || undefined });
  }

  return (
    <div className="filters">
      <input
        type="text"
        className="filter-search"
        placeholder="Search events..."
        value={searchValue}
        onChange={(e) => handleSearch(e.target.value)}
      />
      {DISTANCE_PRESETS.map((preset) => (
        <button
          key={preset.key}
          className={`filter-pill ${activePreset === preset.key ? "active" : ""}`}
          onClick={() => handlePreset(preset.key)}
        >
          {preset.label}
        </button>
      ))}
      <span className="filter-count">{totalCount} events</span>
    </div>
  );
}
