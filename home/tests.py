from datetime import timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Activity, Participation


def in_hours(hours):
    return timezone.now() + timedelta(hours=hours)


def form_time(hours):
    """What a datetime-local input would submit, `hours` from now."""
    return timezone.localtime(in_hours(hours)).strftime('%Y-%m-%dT%H:%M')


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
            'starts_at': form_time(24),
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
            starts_at=in_hours(48), description='Doubles', creator=self.host,
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
        card = next(a for a in response.context['my_plans'] if a.pk == self.activity.pk)
        self.assertEqual(card.going_count, 2)


class HostManageTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(username='host', password='password123')
        self.other = User.objects.create_user(username='other', password='password123')
        self.activity = Activity.objects.create(
            title='Old title', category='food', location='Canteen',
            starts_at=in_hours(24), description='Lunch', creator=self.host,
        )
        self.edit_url = reverse('edit_activity', args=[self.activity.pk])
        self.delete_url = reverse('delete_activity', args=[self.activity.pk])
        self.detail_url = reverse('activity_detail', args=[self.activity.pk])
        self.form = {
            'title': 'New title', 'category': 'study', 'location': 'Library',
            'starts_at': form_time(30), 'description': 'Changed',
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

    def test_feed_lists_soonest_first(self):
        sooner = Activity.objects.create(
            title='Sooner', category='study', location='Lib', starts_at=in_hours(2),
            description='', creator=self.other,
        )
        viewer = User.objects.create_user(username='viewer', password='password123')
        self.client.force_login(viewer)
        titles = [a.title for a in self.client.get(reverse('home')).context['activities']]
        self.assertEqual(titles, [sooner.title, self.activity.title])


class ScheduleTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(username='host', password='password123')
        self.guest = User.objects.create_user(username='guest', password='password123')
        self.client.login(username='guest', password='password123')

    def make(self, title, starts_at, creator=None):
        return Activity.objects.create(
            title=title, category='study', location='Lib', starts_at=starts_at,
            description='', creator=creator or self.host,
        )

    def form(self, **overrides):
        return {'title': 'Run', 'category': 'sports', 'location': 'Oval',
                'starts_at': form_time(24), 'description': '', **overrides}

    def test_feed_hides_ended_but_keeps_happening_now(self):
        self.make('Ended', in_hours(-3))
        self.make('Now', in_hours(-0.5))
        self.make('Later', in_hours(5))
        titles = [a.title for a in self.client.get(reverse('home')).context['activities']]
        self.assertEqual(titles, ['Now', 'Later'])

    def test_create_stores_local_time(self):
        self.client.post(reverse('create_activity'), self.form(starts_at='2099-03-14T15:30'))
        local = timezone.localtime(Activity.objects.get(title='Run').starts_at)
        self.assertEqual((local.year, local.month, local.day, local.hour, local.minute), (2099, 3, 14, 15, 30))

    def test_create_rejects_past_time(self):
        response = self.client.post(reverse('create_activity'), self.form(starts_at=form_time(-2)))
        self.assertContains(response, 'already passed')
        self.assertFalse(Activity.objects.exists())

    def test_create_rejects_garbage_time(self):
        response = self.client.post(reverse('create_activity'), self.form(starts_at='next friday'))
        self.assertContains(response, 'valid date and time')
        self.assertFalse(Activity.objects.exists())

    def test_error_keeps_typed_values(self):
        response = self.client.post(reverse('create_activity'), self.form(title='', starts_at='2099-01-02T08:00'))
        self.assertContains(response, 'value="2099-01-02T08:00"')

    def test_edit_form_prefills_local_time(self):
        activity = self.make('Mine', timezone.make_aware(timezone.datetime(2099, 5, 6, 7, 8)), creator=self.guest)
        response = self.client.get(reverse('edit_activity', args=[activity.pk]))
        self.assertContains(response, 'value="2099-05-06T07:08"')

    def test_cannot_join_ended_activity(self):
        ended = self.make('Ended', in_hours(-3))
        response = self.client.post(reverse('join_activity', args=[ended.pk]), follow=True)
        self.assertFalse(Participation.objects.exists())
        self.assertContains(response, 'This activity has ended.')
        self.assertNotContains(response, 'Join This Activity')

    def test_labels(self):
        tomorrow_9 = timezone.make_aware(timezone.datetime.combine(
            timezone.localdate() + timedelta(days=1), timezone.datetime.min.time().replace(hour=9)))
        self.assertEqual(self.make('A', tomorrow_9).when_label, 'Tomorrow, 9:00 AM')
        self.assertEqual(self.make('B', in_hours(-0.2)).when_label, 'Happening now')
        far = timezone.make_aware(timezone.datetime(2099, 12, 25, 18, 0))
        self.assertEqual(self.make('C', far).when_label, 'Dec 25, 2099, 6:00 PM')
        self.assertEqual(self.make('D', far).full_when_label, 'Friday, December 25, 2099 · 6:00 PM')


class ReseedDemoTests(TestCase):
    def setUp(self):
        from io import StringIO
        from django.core.management import call_command
        self.run = lambda *args: call_command('reseed_demo', *args, stdout=StringIO())
        self.user = User.objects.create_user(username='poster', password='password123')

    def test_moves_ended_starters_to_upcoming(self):
        from .demo_data import seed_starter_activities
        seed_starter_activities()
        Activity.objects.update(starts_at=in_hours(-48))
        self.assertFalse(Activity.upcoming().exists())

        self.run()
        self.assertEqual(Activity.upcoming().count(), 6)
        self.assertEqual(Activity.objects.count(), 6)

    def test_never_touches_user_posts_even_with_same_title(self):
        mine = Activity.objects.create(
            title='Study at Library', category='study', location='Home',
            starts_at=in_hours(-48), description='', creator=self.user,
        )
        self.run()
        mine.refresh_from_db()
        self.assertEqual(mine.location, 'Home')
        self.assertTrue(mine.is_past)
        self.assertEqual(Activity.objects.filter(creator__isnull=True).count(), 6)

    def test_recreates_missing_starters(self):
        self.run()
        self.assertEqual(Activity.objects.filter(creator__isnull=True).count(), 6)

    def test_keeps_joins_unless_asked(self):
        from .demo_data import seed_starter_activities
        seed_starter_activities()
        Participation.objects.create(activity=Activity.objects.first(), user=self.user)
        self.run()
        self.assertEqual(Participation.objects.count(), 1)
        self.run('--clear-joins')
        self.assertEqual(Participation.objects.count(), 0)


class YourPlansTests(TestCase):
    def setUp(self):
        self.me = User.objects.create_user(username='me', password='password123')
        self.other = User.objects.create_user(username='other', password='password123')
        self.client.force_login(self.me)

    def make(self, title, hours, creator):
        return Activity.objects.create(
            title=title, category='study', location='Lib', starts_at=in_hours(hours),
            description='', creator=creator,
        )

    def test_joined_and_hosted_go_to_plans_soonest_first_and_not_the_feed(self):
        later_joined = self.make('Joined later', 30, self.other)
        Participation.objects.create(activity=later_joined, user=self.me)
        self.make('Hosting soon', 5, self.me)
        self.make('Not mine', 10, self.other)

        ctx = self.client.get(reverse('home')).context
        self.assertEqual([a.title for a in ctx['my_plans']], ['Hosting soon', 'Joined later'])
        self.assertEqual([a.title for a in ctx['activities']], ['Not mine'])

    def test_plans_section_glows_and_hides_when_empty(self):
        self.make('Not mine', 10, self.other)
        page = self.client.get(reverse('home'))
        self.assertNotContains(page, 'Your plans')

        Participation.objects.create(activity=Activity.objects.get(), user=self.me)
        page = self.client.get(reverse('home'))
        self.assertContains(page, 'Your plans')
        self.assertContains(page, 'class="activity plan"')

    def test_ended_plans_drop_off(self):
        ended = self.make('Ended', -3, self.other)
        Participation.objects.create(activity=ended, user=self.me)
        self.assertEqual(self.client.get(reverse('home')).context['my_plans'], [])
