import os


DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://trailrunner:trailrunner_dev@localhost:5432/trail_events",
)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
