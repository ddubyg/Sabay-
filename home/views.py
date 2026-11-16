from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Activity


def get_or_seed_activities():
    if Activity.objects.count() == 0:
        initial_activities = [
            {
                'title': 'Study at Library',
                'category': 'study',
                'location': 'CIT-U Library 3F',
                'time': 'Today, 3:00 PM',
                'description': 'Reviewing for Midterm Exam in Algorithms and Data Structures. Bring your notes and laptop!',
                'participants_count': 3,
            },
            {
                'title': 'Pick-up Basketball Game',
                'category': 'sports',
                'location': 'Campus Gymnasium Court',
                'time': 'Tomorrow, 5:00 PM',
                'description': 'Casual 5v5 half-court or full-court games after class. All skill levels welcome!',
                'participants_count': 5,
            },
            {
                'title': 'Valorant 5-Stack Ranked',
                'category': 'gaming',
                'location': 'Discord / Online',
                'time': 'Tonight, 8:00 PM',
                'description': 'Ranked competitive climb tonight. Need 2 friendly chill teammates. Comms required!',
                'participants_count': 3,
            },
            {
                'title': 'Samgyup Lunch Treat',
                'category': 'food',
                'location': 'Korean BBQ Spot Near Campus',
                'time': 'Friday, 12:30 PM',
                'description': 'Unlimited samgyupsal buffet after our Friday classes. Splitting the bill evenly!',
                'participants_count': 4,
            },
            {
                'title': 'Carpool to IT Park',
                'category': 'commute',
                'location': 'CIT-U Main Gate',
                'time': 'Daily, 5:30 PM',
                'description': 'Heading towards IT Park / Lahug after afternoon classes. Safe, comfortable ride.',
                'participants_count': 2,
            },
            {
                'title': 'Coffee & Chill / Coding',
                'category': 'hangout',
                'location': 'Cafe Talk Lounge',
                'time': 'Thursday, 4:00 PM',
                'description': 'Quiet productive cafe session with iced lattes and chill beats. Working on personal coding tasks.',
                'participants_count': 3,
            },
        ]
        for item in initial_activities:
            Activity.objects.create(**item)

    return Activity.objects.all()


@login_required
def home_view(request):
    activities = get_or_seed_activities()
    return render(request, 'home/home.html', {
        'activities': activities
    })


@login_required
def activity_detail_view(request, pk):
    activity = get_object_or_404(Activity, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'join':
            activity.participants_count += 1
            activity.save()
            messages.success(request, f'You joined "{activity.title}"! See you there 🎉')
        return redirect('activity_detail', pk=pk)

    # Build a companions list based on participants_count
    companion_names = [
        ('A', 'Alex R.', 'BS Computer Science, 3rd Year'),
        ('M', 'Maria S.', 'BS Nursing, 2nd Year'),
        ('J', 'Jake T.', 'BS Architecture, 4th Year'),
        ('C', 'Carla M.', 'BS Psychology, 1st Year'),
        ('R', 'Rico B.', 'BS Information Technology, 3rd Year'),
        ('S', 'Sofia L.', 'BS Business Admin, 2nd Year'),
    ]
    companions = companion_names[:min(activity.participants_count, len(companion_names))]

    category_emojis = {
        'study': '📚',
        'sports': '🏀',
        'gaming': '🎮',
        'food': '🍜',
        'commute': '🚗',
        'hangout': '☕',
    }
    emoji = category_emojis.get(activity.category.lower(), '🎯')

    return render(request, 'home/activity_detail.html', {
        'activity': activity,
        'companions': companions,
        'emoji': emoji,
    })


@login_required
def create_activity_view(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        category = request.POST.get('category', 'study').strip()
        location = request.POST.get('location', '').strip()
        time = request.POST.get('time', '').strip()
        description = request.POST.get('description', '').strip()

        if not title or not location or not time:
            return render(request, 'home/create_activity.html', {
                'error': 'Please fill in all required fields.',
                'title': title,
                'category': category,
                'location': location,
                'time': time,
                'description': description,
            })

        Activity.objects.create(
            title=title,
            category=category,
            location=location,
            time=time,
            description=description,
            creator=request.user,
            participants_count=1,
        )

        messages.success(request, 'New Sabay activity posted successfully!')
        return redirect('home')

    return render(request, 'home/create_activity.html')
