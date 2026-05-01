def test_list_events_returns_all(client, sample_events):
    response = client.get("/api/events")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


def test_list_events_filter_by_month(client, sample_events):
    response = client.get("/api/events?month=7")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


def test_list_events_filter_by_county(client, sample_events):
    response = client.get("/api/events?county=Brașov")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


def test_list_events_filter_by_search(client, sample_events):
    response = client.get("/api/events?search=predeal")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Predeal Forest Run"


def test_list_events_filter_upcoming(client, sample_events):
    response = client.get("/api/events?upcoming=true")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["date_start"] >= "2026-05-01"


def test_list_events_filter_by_distance(client, sample_events):
    response = client.get("/api/events?distance_min=40&distance_max=110")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_list_events_pagination(client, sample_events):
    response = client.get("/api/events?page=1&per_page=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["per_page"] == 2
    assert data["page"] == 1


def test_get_event_by_id(client, sample_events):
    event_id = str(sample_events[0].id)
    response = client.get(f"/api/events/{event_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Carpathia Trails 2026"


def test_get_event_not_found(client, sample_events):
    response = client.get("/api/events/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_get_stats(client, sample_events):
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["event_count"] == 3
    assert data["county_count"] == 2
