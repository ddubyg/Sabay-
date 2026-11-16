import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import UserSettings


class SettingsAppTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='settingstestuser',
            password='password123'
        )
        self.client.login(username='settingstestuser', password='password123')

    def test_settings_page_renders_with_user_settings(self):
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Settings')
        self.assertContains(response, 'Dark Mode')
        self.assertContains(response, 'Activity Notifications')

    def test_toggle_theme_ajax(self):
        # Toggle on
        response = self.client.post(
            reverse('toggle_theme'),
            data=json.dumps({'dark_mode': True}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['dark_mode'], True)

        settings = UserSettings.objects.get(user=self.user)
        self.assertTrue(settings.dark_mode)

        # Toggle off
        response = self.client.post(
            reverse('toggle_theme'),
            data=json.dumps({'dark_mode': False}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['dark_mode'], False)

        settings.refresh_from_db()
        self.assertFalse(settings.dark_mode)

    def test_toggle_notifications_ajax(self):
        response = self.client.post(
            reverse('toggle_notifications'),
            data=json.dumps({'notifications': False}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['notifications'], False)

        settings = UserSettings.objects.get(user=self.user)
        self.assertFalse(settings.notifications)

    def test_save_settings_form_post(self):
        response = self.client.post(reverse('settings'), {
            'dark_mode': 'on',
            'notifications': 'on',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Settings saved successfully!')

        settings = UserSettings.objects.get(user=self.user)
        self.assertTrue(settings.dark_mode)
        self.assertTrue(settings.notifications)
