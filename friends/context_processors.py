from .models import FriendRequest


def friend_requests_context(request):
    """Pending incoming request count, for the badge on the Friends nav link."""
    if request.user.is_authenticated:
        count = FriendRequest.objects.filter(to_user=request.user, accepted=False).count()
        return {'pending_friend_requests': count}
    return {'pending_friend_requests': 0}
