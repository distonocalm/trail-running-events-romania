from unittest.mock import patch, MagicMock


def test_trigger_scrape_all(client):
    with patch("app.routers.scrape.get_celery_app") as mock_celery:
        mock_task = MagicMock()
        mock_task.id = "test-task-id-123"
        mock_celery.return_value.send_task.return_value = mock_task

        response = client.post("/api/scrape")
        assert response.status_code == 202
        data = response.json()
        assert data["task_id"] == "test-task-id-123"
        assert data["status"] == "dispatched"


def test_trigger_scrape_single_source(client):
    source_resp = client.post(
        "/api/sources",
        json={
            "name": "Test",
            "url": "https://test.com",
            "scraper_module": "scrapers.sources.test",
        },
    )
    source_id = source_resp.json()["id"]

    with patch("app.routers.scrape.get_celery_app") as mock_celery:
        mock_task = MagicMock()
        mock_task.id = "test-task-id-456"
        mock_celery.return_value.send_task.return_value = mock_task

        response = client.post(f"/api/scrape/{source_id}")
        assert response.status_code == 202
        data = response.json()
        assert data["task_id"] == "test-task-id-456"


def test_scrape_status(client):
    with patch("app.routers.scrape.get_celery_app") as mock_celery:
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.result = "Scraped 42 events"
        mock_celery.return_value.AsyncResult.return_value = mock_result

        response = client.get("/api/scrape/status?task_id=test-task-id-123")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
