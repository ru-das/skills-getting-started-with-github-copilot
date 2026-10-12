from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client():
    original_activities = deepcopy(app_module.activities)
    with TestClient(app_module.app) as test_client:
        yield test_client
    app_module.activities.clear()
    app_module.activities.update(original_activities)


def test_root_redirects_to_static_app(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert "Chess Club" in activities
    assert activities["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_student_to_activity(client):
    response = client.post(
        "/activities/Soccer%20Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up student@mergington.edu for Soccer Club"
    }
    assert "student@mergington.edu" in app_module.activities["Soccer Club"]["participants"]


def test_duplicate_signup_is_rejected(client):
    email = "michael@mergington.edu"

    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }


def test_unregister_removes_student_from_activity(client):
    response = client.delete(
        "/activities/Chess%20Club/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered michael@mergington.edu from Chess Club"
    }
    assert "michael@mergington.edu" not in app_module.activities["Chess Club"]["participants"]


@pytest.mark.parametrize(
    ("method", "path", "email", "expected_detail"),
    [
        ("post", "/activities/Unknown%20Club/signup", "student@mergington.edu", "Activity not found"),
        (
            "delete",
            "/activities/Chess%20Club/signup",
            "missing@mergington.edu",
            "Student is not signed up for this activity",
        ),
    ],
)
def test_signup_and_unregister_validate_activity_and_participant(
    client, method, path, email, expected_detail
):
    response = getattr(client, method)(path, params={"email": email})

    assert response.status_code == 404
    assert response.json() == {"detail": expected_detail}
