from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from . import services
from .models import FriendRequest


class FriendFlowTests(TestCase):
    def setUp(self):
        self.a = User.objects.create_user(username='alice', password='pw-123456')
        self.b = User.objects.create_user(username='bob', password='pw-123456')
        self.c = User.objects.create_user(username='carol', password='pw-123456')

    def login(self, user):
        self.client.force_login(user)

    def post(self, name, user, **data):
        return self.client.post(reverse(name, args=[user.pk]), data, follow=True)

    def test_send_then_accept_makes_friends_both_ways(self):
        self.login(self.a)
        self.post('friend_add', self.b)
        self.assertEqual(services.relationship(self.a, self.b), services.SENT)
        self.assertEqual(services.relationship(self.b, self.a), services.RECEIVED)

        self.login(self.b)
        response = self.post('friend_accept', self.a)
        self.assertContains(response, 'now friends')
        self.assertEqual(services.friend_ids(self.a), {self.b.id})
        self.assertEqual(services.friend_ids(self.b), {self.a.id})

    def test_adding_someone_who_already_asked_you_accepts(self):
        self.login(self.a)
        self.post('friend_add', self.b)
        self.login(self.b)
        self.post('friend_add', self.a)
        self.assertEqual(FriendRequest.objects.count(), 1)
        self.assertEqual(services.relationship(self.a, self.b), services.FRIENDS)

    def test_adding_twice_does_not_duplicate(self):
        self.login(self.a)
        self.post('friend_add', self.b)
        self.post('friend_add', self.b)
        self.assertEqual(FriendRequest.objects.count(), 1)

    def test_cannot_friend_yourself(self):
        self.login(self.a)
        self.post('friend_add', self.a)
        self.assertFalse(FriendRequest.objects.exists())

    def test_only_receiver_can_accept(self):
        self.login(self.a)
        self.post('friend_add', self.b)
        self.post('friend_accept', self.b)       # alice tries to accept her own request
        self.assertEqual(services.relationship(self.a, self.b), services.SENT)

    def test_decline_cancel_and_unfriend_remove_the_link(self):
        self.login(self.a)
        self.post('friend_add', self.b)
        self.login(self.b)
        self.assertContains(self.post('friend_remove', self.a), 'Declined')
        self.assertFalse(FriendRequest.objects.exists())

        self.login(self.a)
        self.post('friend_add', self.b)
        self.assertContains(self.post('friend_remove', self.b), 'Cancelled')
        self.assertFalse(FriendRequest.objects.exists())

        self.post('friend_add', self.b)
        services.accept_request(self.b, self.a)
        self.assertContains(self.post('friend_remove', self.b), 'Removed')
        self.assertEqual(services.friend_ids(self.a), set())

    def test_actions_require_post_and_login(self):
        self.login(self.a)
        self.assertEqual(self.client.get(reverse('friend_add', args=[self.b.pk])).status_code, 405)
        self.client.logout()
        self.client.post(reverse('friend_add', args=[self.b.pk]))
        self.assertFalse(FriendRequest.objects.exists())

    def test_next_redirect_only_to_same_site(self):
        self.login(self.a)
        ok = self.client.post(reverse('friend_add', args=[self.b.pk]), {'next': '/home/?q=bo'})
        self.assertEqual(ok.url, '/home/?q=bo')
        evil = self.client.post(reverse('friend_remove', args=[self.b.pk]), {'next': 'https://evil.example/'})
        self.assertEqual(evil.url, reverse('friends'))

    def test_search_page_and_json(self):
        self.login(self.a)
        page = self.client.get(reverse('friends'), {'q': 'bo'})
        self.assertContains(page, 'bob')
        self.assertNotContains(page, 'carol')
        self.assertContains(page, 'Add friend')

        data = self.client.get(reverse('friends_search_json'), {'q': '@CAR'}).json()
        self.assertEqual([(r['username'], r['state']) for r in data['results']], [('carol', 'none')])

        mine = self.client.get(reverse('friends_search_json'), {'q': 'alice'}).json()
        self.assertEqual(mine['results'], [])           # never yourself

        short = self.client.get(reverse('friends_search_json'), {'q': 'b'}).json()
        self.assertEqual(short['results'], [])          # needs 2+ letters

    def test_friends_page_sections_and_nav_badge(self):
        self.login(self.b)
        services.send_request(self.a, self.b)
        services.send_request(self.b, self.c)
        page = self.client.get(reverse('friends'))
        self.assertContains(page, 'Friend requests (1)')
        self.assertContains(page, 'Waiting for them to accept (1)')
        self.assertContains(page, 'class="nav-badge"')
        self.assertEqual(page.context['pending_friend_requests'], 1)

        home = self.client.get(reverse('home'))
        self.assertContains(home, reverse('friends'))
        self.assertContains(home, 'class="nav-badge"')

    def test_home_has_people_panel_wired_to_search(self):
        self.login(self.a)
        home = self.client.get(reverse('home'))
        self.assertContains(home, 'id="people-panel"')
        self.assertContains(home, reverse('friends_search_json'))
        self.assertContains(home, 'csrfmiddlewaretoken')


class FriendsGoingTests(TestCase):
    def setUp(self):
        from datetime import timedelta
        from django.utils import timezone
        from home.models import Activity
        self.Activity = Activity
        self.soon = timezone.now() + timedelta(days=1)
        self.me = User.objects.create_user(username='me', password='pw-123456')
        self.ben = User.objects.create_user(username='ben', password='pw-123456')
        self.ana = User.objects.create_user(username='ana', password='pw-123456')
        self.cy = User.objects.create_user(username='cy', password='pw-123456')
        self.dee = User.objects.create_user(username='dee', password='pw-123456')
        self.stranger = User.objects.create_user(username='stranger', password='pw-123456')
        for friend in (self.ben, self.ana, self.cy, self.dee):
            services.send_request(self.me, friend)
            services.accept_request(friend, self.me)
        self.client.force_login(self.me)

    def make(self, title, creator=None):
        return self.Activity.objects.create(
            title=title, category='study', location='Lib', starts_at=self.soon,
            description='', creator=creator,
        )

    def join(self, activity, *users):
        from home.models import Participation
        for u in users:
            Participation.objects.create(activity=activity, user=u)

    def card_labels(self):
        response = self.client.get(reverse('home'))
        return {a.title: a.friends_label for a in response.context['activities']}

    def test_labels_for_one_two_many_and_hosting(self):
        one, two, many = self.make('One'), self.make('Two'), self.make('Many')
        hosted = self.make('Hosted', creator=self.ben)
        self.join(one, self.ben)
        self.join(two, self.ben, self.ana)
        self.join(many, self.ben, self.ana, self.cy, self.dee)
        self.join(hosted, self.ana)
        labels = self.card_labels()
        self.assertEqual(labels['One'], 'ben is going')
        self.assertEqual(labels['Two'], 'ben and ana are going')
        self.assertEqual(labels['Many'], 'ben, ana +2 more are going')
        self.assertEqual(labels['Hosted'], 'ben is hosting \u00b7 ana is going')

    def test_non_friends_and_pending_requests_are_not_shown(self):
        a = self.make('A')
        pending = User.objects.create_user(username='pending', password='pw-123456')
        services.send_request(self.me, pending)
        self.join(a, self.stranger, pending)
        self.assertEqual(self.card_labels()['A'], '')

    def test_works_both_ways(self):
        a = self.make('A')
        self.join(a, self.me)
        self.client.force_login(self.ben)
        self.assertEqual(self.card_labels()['A'], 'me is going')

    def test_detail_page_marks_friends(self):
        a = self.make('A', creator=self.ana)
        self.join(a, self.ben, self.stranger)
        page = self.client.get(reverse('activity_detail', args=[a.pk]))
        self.assertContains(page, 'Host \u00b7 Friend')
        self.assertContains(page, 'companion-badge friend', count=1)
