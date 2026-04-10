from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class SignUpViewTests(TestCase):
    def test_signup_page_is_available(self):
        response = self.client.get(reverse("games:signup"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create Account")

    def test_signup_creates_user_with_email(self):
        response = self.client.post(
            reverse("games:signup"),
            {
                "email": "user@example.com",
                "username": "newuser",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
            },
        )

        self.assertRedirects(response, reverse("games:home"))
        user = User.objects.get(username="newuser")
        self.assertEqual(user.email, "user@example.com")

    def test_signup_rejects_short_password(self):
        response = self.client.post(
            reverse("games:signup"),
            {
                "email": "user@example.com",
                "username": "newuser",
                "password1": "short",
                "password2": "short",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "This password is too short. It must contain at least 8 characters.",
        )
