import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client(monkeypatch):
    test_activities = {
        "Chess Club": {
            "description": "Learn chess",
            "schedule": "Fridays",
            "max_participants": 2,
            "participants": ["already-signed-up@mergington.edu"],
        },
        "Art Club": {
            "description": "Create art",
            "schedule": "Wednesdays",
            "max_participants": 3,
            "participants": [],
        },
    }
    monkeypatch.setattr(app_module, "activities", test_activities)
    return TestClient(app_module.app)


def test_get_activities_returns_activity_details_and_participants(client):
    # Arrange
    expected_participants = ["already-signed-up@mergington.edu"]

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()["Chess Club"]["participants"] == expected_participants
    assert response.json()["Art Club"]["participants"] == []


def test_signup_adds_participant_and_updates_activity_list(client):
    # Arrange
    activity = "Art Club"
    email = "student@mergington.edu"

    # Act
    signup_response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    # Assert
    assert signup_response.status_code == 200
    assert signup_response.json() == {"message": f"Signed up {email} for {activity}"}
    assert activities_response.json()[activity]["participants"] == [email]


@pytest.mark.parametrize(
    ("activity", "email", "expected_status", "expected_detail"),
    [
        ("Unknown Club", "student@mergington.edu", 404, "Activity not found"),
        ("Chess Club", "already-signed-up@mergington.edu", 400,
         "Student already signed up for this activity"),
    ],
)
def test_signup_rejects_unknown_activity_and_duplicate_participant(
    client, activity, email, expected_status, expected_detail
):
    # Arrange
    signup_url = f"/activities/{activity}/signup"

    # Act
    response = client.post(signup_url, params={"email": email})

    # Assert
    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail


def test_unregister_removes_participant_and_updates_activity_list(client):
    # Arrange
    activity = "Chess Club"
    email = "already-signed-up@mergington.edu"

    # Act
    unregister_response = client.delete(
        f"/activities/{activity}/signup",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    # Assert
    assert unregister_response.status_code == 200
    assert unregister_response.json() == {
        "message": f"Unregistered {email} from {activity}"
    }
    assert activities_response.json()[activity]["participants"] == []


@pytest.mark.parametrize(
    ("activity", "email", "expected_detail"),
    [
        ("Unknown Club", "student@mergington.edu", "Activity not found"),
        ("Art Club", "not-signed-up@mergington.edu",
         "Student is not signed up for this activity"),
    ],
)
def test_unregister_rejects_unknown_activity_and_unregistered_participant(
    client, activity, email, expected_detail
):
    # Arrange
    unregister_url = f"/activities/{activity}/signup"

    # Act
    response = client.delete(unregister_url, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == expected_detail
