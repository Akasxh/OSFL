"""Validates the test harness itself: in-process API client + live-server Playwright."""


def test_api_client_boots_offline(client):
    r = client.get("/api/state")
    assert r.status_code == 200
    body = r.json()
    assert "goals" in body and len(body["goals"]) == 3
    assert client.get("/api/llm/status").json()["available"] is False  # forced offline


def test_e2e_server_and_browser(base_url, page):
    page.goto(base_url)
    assert "OSFL" in page.title()
    page.wait_for_selector("text=Land a job", timeout=15000)
    page.wait_for_selector("text=Monte-Carlo simulation", timeout=15000)
