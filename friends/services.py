"""Friendship rules, kept out of the views so home and profile can reuse them."""
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone

from .models import FriendRequest

# Relationship states, from the point of view of `user` looking at `other`.
SELF, FRIENDS, SENT, RECEIVED, NONE = 'self', 'friends', 'sent', 'received', 'none'


def _between(a, b):
    return FriendRequest.objects.filter(
        Q(from_user=a, to_user=b) | Q(from_user=b, to_user=a)
    )


def friend_ids(user):
    """IDs of everyone `user` is friends with."""
    rows = FriendRequest.objects.filter(
        Q(from_user=user) | Q(to_user=user), accepted=True
    ).values_list('from_user_id', 'to_user_id')
    return {b if a == user.id else a for a, b in rows}


def friends_of(user):
    return User.objects.filter(id__in=friend_ids(user)).select_related('profile').order_by('username')


def relationship(user, other):
    return relationships(user, [other])[other.id]


def relationships(user, others):
    """{other.id: state} for many users in one query."""
    ids = [o.id for o in others]
    states = {i: NONE for i in ids}
    if user.id in states:
        states[user.id] = SELF
    rows = FriendRequest.objects.filter(
        Q(from_user=user, to_user_id__in=ids) | Q(to_user=user, from_user_id__in=ids)
    )
    for r in rows:
        other_id = r.to_user_id if r.from_user_id == user.id else r.from_user_id
        if r.accepted:
            states[other_id] = FRIENDS
        else:
            states[other_id] = SENT if r.from_user_id == user.id else RECEIVED
    return states


def send_request(user, other):
    """Returns the resulting state. If `other` already asked `user`, this accepts it."""
    if user.id == other.id:
        return SELF
    existing = _between(user, other).first()
    if existing is None:
        FriendRequest.objects.get_or_create(from_user=user, to_user=other)
        return SENT
    if not existing.accepted and existing.to_user_id == user.id:
        return accept_request(user, other)
    return relationship(user, other)


def accept_request(user, sender):
    """`user` accepts a pending request from `sender`."""
    updated = FriendRequest.objects.filter(
        from_user=sender, to_user=user, accepted=False
    ).update(accepted=True, accepted_at=timezone.now())
    return FRIENDS if updated else relationship(user, sender)


def remove(user, other):
    """Decline, cancel or unfriend: whatever is between the two is deleted."""
    _between(user, other).delete()


def pending_received(user):
    return FriendRequest.objects.filter(to_user=user, accepted=False).select_related('from_user', 'from_user__profile')


def pending_sent(user):
    return FriendRequest.objects.filter(from_user=user, accepted=False).select_related('to_user', 'to_user__profile')


def search_users(user, query, limit=8):
    query = (query or '').strip().lstrip('@')
    if len(query) < 2:
        return []
    return list(
        User.objects.filter(username__icontains=query, is_active=True)
        .exclude(id=user.id)
        .select_related('profile')
        .order_by('username')[:limit]
    )


def _names_phrase(names):
    if len(names) == 1:
        return f'{names[0]} is going'
    if len(names) == 2:
        return f'{names[0]} and {names[1]} are going'
    return f'{names[0]}, {names[1]} +{len(names) - 2} more are going'


def friends_activity_labels(user, activities):
    """{activity.id: 'ben is going'} for activities your friends host or joined.

    Two queries total, whatever the number of activities.
    """
    from home.models import Participation  # avoid an import cycle at load time

    ids = friend_ids(user)
    if not ids:
        return {}
    activities = list(activities)
    by_activity = {}
    joins = (
        Participation.objects
        .filter(activity_id__in=[a.id for a in activities], user_id__in=ids)
        .select_related('user')
        .order_by('joined_at')
    )
    for p in joins:
        by_activity.setdefault(p.activity_id, []).append(p.user.username)

    labels = {}
    for a in activities:
        parts = []
        if a.creator_id in ids:
            parts.append(f'{a.creator.username} is hosting')
        if a.id in by_activity:
            parts.append(_names_phrase(by_activity[a.id]))
        if parts:
            labels[a.id] = ' \u00b7 '.join(parts)
    return labels
