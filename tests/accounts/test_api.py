import pytest


@pytest.mark.django_db
class TestRegisterView:
    def test_api_returns_201_when_registration_is_valid(self, client):
        # Arrange
        payload = {
            "email": "new@example.com",
            "password": "securepass123",
            "first_name": "Marie",
            "last_name": "Martin",
        }

        # Act
        response = client.post("/api/auth/register/", data=payload, content_type="application/json")

        # Assert
        assert response.status_code == 201
        assert response.json()["email"] == "new@example.com"

    def test_api_returns_400_when_email_already_exists(self, client, test_user):
        # Arrange
        payload = {
            "email": "test@example.com",
            "password": "securepass123",
            "first_name": "Other",
            "last_name": "User",
        }

        # Act
        response = client.post("/api/auth/register/", data=payload, content_type="application/json")

        # Assert
        assert response.status_code == 400
        assert "email" in response.json()

    def test_api_returns_400_when_password_too_short(self, client):
        # Arrange
        payload = {
            "email": "new@example.com",
            "password": "short",
            "first_name": "Marie",
            "last_name": "Martin",
        }

        # Act
        response = client.post("/api/auth/register/", data=payload, content_type="application/json")

        # Assert
        assert response.status_code == 400


@pytest.mark.django_db
class TestLoginView:
    def test_api_returns_200_when_credentials_are_valid(self, client, test_user):
        # Arrange
        payload = {"email": "test@example.com", "password": "testpassword123"}

        # Act
        response = client.post("/api/auth/login/", data=payload, content_type="application/json")

        # Assert
        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"

    def test_api_returns_401_when_credentials_are_invalid(self, client, test_user):
        # Arrange
        payload = {"email": "test@example.com", "password": "wrongpassword"}

        # Act
        response = client.post("/api/auth/login/", data=payload, content_type="application/json")

        # Assert
        assert response.status_code == 401


@pytest.mark.django_db
class TestMeView:
    def test_api_returns_customer_data_when_authenticated(self, authenticated_client, test_user):
        # Act
        response = authenticated_client.get("/api/auth/me/")

        # Assert
        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"

    def test_api_returns_403_when_unauthenticated(self, client):
        # Act
        response = client.get("/api/auth/me/")

        # Assert
        assert response.status_code == 403
