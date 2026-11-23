from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Activity, Participation


class HomeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='hometestuser',
            password='password123'
        )
        self.client.login(username='hometestuser', password='password123')

    def test_home_page_renders_with_activities_and_context(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome back, hometestuser.')
        self.assertContains(response, 'Explore by category')
        self.assertContains(response, 'Upcoming activities')
        self.assertContains(response, 'Post Sabay')
        self.assertContains(response, reverse('create_activity'))
        self.assertIn('user_settings', response.context)

    def test_create_activity_page_renders(self):
        response = self.client.get(reverse('create_activity'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Post a New Sabay Activity')

    def test_create_activity_post_success(self):
        response = self.client.post(reverse('create_activity'), {
            'title': 'Midterm Study Group',
            'category': 'study',
            'location': 'Library 2F',
            'time': 'Friday at 2 PM',
            'description': 'Let us study Calculus and Physics together.',
        }, follow=True)

        self.assertRedirects(response, reverse('home'))
        self.assertContains(response, 'New Sabay activity posted successfully!')
        self.assertTrue(Activity.objects.filter(title='Midterm Study Group').exists())


class JoinLeaveTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(username='host', password='password123')
        self.guest = User.objects.create_user(username='guest', password='password123')
        self.activity = Activity.objects.create(
            title='Badminton', category='sports', location='Gym',
            time='Saturday 9 AM', description='Doubles', creator=self.host,
        )
        self.detail_url = reverse('activity_detail', args=[self.activity.pk])
        self.join_url = reverse('join_activity', args=[self.activity.pk])
        self.leave_url = reverse('leave_activity', args=[self.activity.pk])
        self.client.login(username='guest', password='password123')

    def test_host_counts_as_going(self):
        self.assertEqual(self.activity.going_count, 1)

    def test_join_creates_participation(self):
        response = self.client.post(self.join_url, follow=True)
        self.assertRedirects(response, self.detail_url)
        self.assertTrue(Participation.objects.filter(activity=self.activity, user=self.guest).exists())
        self.assertEqual(self.activity.going_count, 2)
        self.assertContains(response, 'Leave Activity')
        self.assertContains(response, 'guest')

    def test_joining_twice_does_not_duplicate(self):
        self.client.post(self.join_url)
        response = self.client.post(self.join_url, follow=True)
        self.assertEqual(Participation.objects.filter(activity=self.activity).count(), 1)
        self.assertContains(response, "already joined")

    def test_leave_removes_participation(self):
        self.client.post(self.join_url)
        response = self.client.post(self.leave_url, follow=True)
        self.assertFalse(Participation.objects.filter(activity=self.activity, user=self.guest).exists())
        self.assertContains(response, 'Join This Activity')

    def test_host_cannot_join_own_activity(self):
        self.client.login(username='host', password='password123')
        response = self.client.post(self.join_url, follow=True)
        self.assertFalse(Participation.objects.exists())
        self.assertContains(response, reverse('edit_activity', args=[self.activity.pk]))
        self.assertNotContains(response, 'Join This Activity')

    def test_join_requires_post(self):
        self.assertEqual(self.client.get(self.join_url).status_code, 405)
        self.assertFalse(Participation.objects.exists())

    def test_join_requires_login(self):
        self.client.logout()
        response = self.client.post(self.join_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Participation.objects.exists())

    def test_home_feed_shows_real_going_count(self):
        self.client.post(self.join_url)
        response = self.client.get(reverse('home'))
        card = next(a for a in response.context['activities'] if a.pk == self.activity.pk)
        self.assertEqual(card.going_count, 2)


class HostManageTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(username='host', password='password123')
        self.other = User.objects.create_user(username='other', password='password123')
        self.activity = Activity.objects.create(
            title='Old title', category='food', location='Canteen',
            time='Noon', description='Lunch', creator=self.host,
        )
        self.edit_url = reverse('edit_activity', args=[self.activity.pk])
        self.delete_url = reverse('delete_activity', args=[self.activity.pk])
        self.detail_url = reverse('activity_detail', args=[self.activity.pk])
        self.form = {
            'title': 'New title', 'category': 'study', 'location': 'Library',
            'time': '3 PM', 'description': 'Changed',
        }

    def test_feed_and_detail_show_host(self):
        self.client.login(username='other', password='password123')
        self.assertContains(self.client.get(reverse('home')), 'Hosted by <strong>host</strong>', html=False)
        self.assertContains(self.client.get(self.detail_url), 'Hosted by <strong>host</strong>', html=False)

    def test_host_sees_edit_and_delete(self):
        self.client.login(username='host', password='password123')
        response = self.client.get(self.detail_url)
        self.assertContains(response, self.edit_url)
        self.assertContains(response, self.delete_url)

    def test_non_host_does_not_see_edit_or_delete(self):
        self.client.login(username='other', password='password123')
        response = self.client.get(self.detail_url)
        self.assertNotContains(response, self.edit_url)
        self.assertNotContains(response, self.delete_url)

    def test_edit_form_is_prefilled(self):
        self.client.login(username='host', password='password123')
        response = self.client.get(self.edit_url)
        self.assertContains(response, 'Edit Your Activity')
        self.assertContains(response, 'value="Old title"')

    def test_host_can_edit(self):
        self.client.login(username='host', password='password123')
        response = self.client.post(self.edit_url, self.form)
        self.assertRedirects(response, self.detail_url)
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.title, 'New title')
        self.assertEqual(self.activity.category, 'study')

    def test_non_host_cannot_edit(self):
        self.client.login(username='other', password='password123')
        response = self.client.post(self.edit_url, self.form)
        self.assertRedirects(response, self.detail_url)
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.title, 'Old title')

    def test_edit_rejects_blank_fields(self):
        self.client.login(username='host', password='password123')
        response = self.client.post(self.edit_url, {**self.form, 'title': ''})
        self.assertContains(response, 'Please fill in all required fields.')
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.title, 'Old title')

    def test_unknown_category_rejected(self):
        self.client.login(username='host', password='password123')
        response = self.client.post(reverse('create_activity'), {**self.form, 'category': 'hacking'})
        self.assertContains(response, 'Please pick one of the listed categories.')
        self.assertFalse(Activity.objects.filter(category='hacking').exists())

    def test_host_can_delete(self):
        Participation.objects.create(activity=self.activity, user=self.other)
        self.client.login(username='host', password='password123')
        response = self.client.post(self.delete_url)
        self.assertRedirects(response, reverse('home'))
        self.assertFalse(Activity.objects.filter(pk=self.activity.pk).exists())
        self.assertFalse(Participation.objects.exists())

    def test_non_host_cannot_delete(self):
        self.client.login(username='other', password='password123')
        self.client.post(self.delete_url)
        self.assertTrue(Activity.objects.filter(pk=self.activity.pk).exists())

    def test_delete_requires_post(self):
        self.client.login(username='host', password='password123')
        self.assertEqual(self.client.get(self.delete_url).status_code, 405)
        self.assertTrue(Activity.objects.filter(pk=self.activity.pk).exists())

    def test_card_button_reflects_role(self):
        self.client.login(username='host', password='password123')
        self.assertContains(self.client.get(reverse('home')), 'Manage your post')
        self.client.login(username='other', password='password123')
        Participation.objects.create(activity=self.activity, user=self.other)
        self.assertContains(self.client.get(reverse('home')), "You're going")

    def test_feed_lists_newest_first(self):
        newer = Activity.objects.create(
            title='Newer', category='study', location='Lib', time='Now',
            description='', creator=self.other,
        )
        self.client.login(username='other', password='password123')
        titles = [a.title for a in self.client.get(reverse('home')).context['activities']]
        self.assertEqual(titles[0], newer.title)
