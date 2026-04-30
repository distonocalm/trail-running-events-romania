def test_list_sources_empty(client):
    response = client.get("/api/sources")
    assert response.status_code == 200
    assert response.json() == []


def test_create_source(client):
    response = client.post(
        "/api/sources",
        json={
            "name": "EliteRunning.ro",
            "url": "https://eliterunning.ro/calendar-competitii-2026/",
            "scraper_module": "scrapers.sources.eliterunning",
            "enabled": True,
            "scrape_interval_hours": 24,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "EliteRunning.ro"
    assert data["enabled"] is True


def test_list_sources_after_create(client):
    client.post(
        "/api/sources",
        json={
            "name": "EliteRunning.ro",
            "url": "https://eliterunning.ro/",
            "scraper_module": "scrapers.sources.eliterunning",
        },
    )
    response = client.get("/api/sources")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_update_source(client):
    resp = client.post(
        "/api/sources",
        json={
            "name": "Test",
            "url": "https://test.com",
            "scraper_module": "scrapers.sources.test",
        },
    )
    source_id = resp.json()["id"]
    response = client.patch(
        f"/api/sources/{source_id}", json={"enabled": False}
    )
    assert response.status_code == 200
    assert response.json()["enabled"] is False


def test_delete_source(client):
    resp = client.post(
        "/api/sources",
        json={
            "name": "Test",
            "url": "https://test.com",
            "scraper_module": "scrapers.sources.test",
        },
    )
    source_id = resp.json()["id"]
    response = client.delete(f"/api/sources/{source_id}")
    assert response.status_code == 204
    assert client.get("/api/sources").json() == []
