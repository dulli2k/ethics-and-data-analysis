from fastapi.testclient import TestClient
from main import app, create_access_token

client = TestClient(app)


def test_login_success():
    response = client.post(
        "/token", data={"username": "admin", "password": "securepassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_get_tracts_unauthorized():
    response = client.get("/tracts/")
    assert response.status_code == 401


def test_get_tracts_authorized():
    token = create_access_token({"sub": "admin"})
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/tracts/", headers=headers)
    assert response.status_code == 200
    tracts = response.json()
    assert isinstance(tracts, list)
    assert len(tracts) > 0
    required_keys = {
        "census_tract",
        "inclusion_score",
        "growth_score",
        "economy_score",
        "community_score",
    }
    assert required_keys.issubset(set(tracts[0].keys()))


def test_get_single_tract_authorized():
    token = create_access_token({"sub": "admin"})
    headers = {"Authorization": f"Bearer {token}"}

    # Use a known census tract from igs_data.csv
    tract_id = "06037102107"
    response = client.get(f"/tracts/{tract_id}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["census_tract"] == tract_id


def test_users_me():
    token = create_access_token({"sub": "admin"})
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "admin"
