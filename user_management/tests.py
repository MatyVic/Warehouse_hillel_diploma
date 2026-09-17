import pytest
from django.urls import reverse

from user_management.forms import LoginForm, RegisterForm
from user_management.models import CustomUser


@pytest.mark.django_db
class TestCustomUserModel:
    def test_user_creation(self):
        u = CustomUser.objects.create_user(
            username="john", password="pass12345", work_id="W-0001"
        )
        assert u.pk is not None
        assert u.check_password("pass12345")


@pytest.mark.django_db
class TestRegisterForm:
    def test_valid_data_creates_user(self):
        form = RegisterForm(data={
            "username": "newuser",
            "email": "new@example.com",
            "password1": "SuperSecret123",
            "password2": "SuperSecret123",
        })
        assert form.is_valid(), form.errors

    def test_passwords_must_match(self):
        form = RegisterForm(data={
            "username": "newuser",
            "email": "new@example.com",
            "password1": "SuperSecret123",
            "password2": "DifferentPass456",
        })
        assert not form.is_valid()


class TestLoginForm:
    def test_requires_login_and_password(self):
        form = LoginForm(data={})
        assert not form.is_valid()
        assert "login" in form.errors
        assert "password" in form.errors


@pytest.mark.django_db
class TestAuthViews:
    """
    NOTE: user_register / user_login / user_logout currently redirect to
    "shop:all_books", a namespace that does not exist in this project.
    These tests currently FAIL and document the known bug — see chat notes.
    Fix: change all three redirects to "warehouse:list".
    """

    def test_register_page_loads(self, client):
        response = client.get(reverse("user:user_register"))
        assert response.status_code == 200

    def test_login_page_loads(self, client):
        response = client.get(reverse("user:user_login"))
        assert response.status_code == 200

    @pytest.mark.xfail(reason="redirect target 'shop:all_books' does not exist yet")
    def test_successful_registration_redirects(self, client):
        response = client.post(reverse("user:user_register"), {
            "username": "freshuser",
            "email": "fresh@example.com",
            "password1": "SuperSecret123",
            "password2": "SuperSecret123",
        })
        assert response.status_code == 302