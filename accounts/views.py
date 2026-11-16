from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from user_profile.models import Profile
from settings_app.models import UserSettings


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('home')

        return render(request, 'accounts/login.html', {
            'error': 'Invalid username or password.',
            'username': username,
        })

    return render(request, 'accounts/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        context = {
            'username': username,
            'email': email,
            'password': password,
            'confirm_password': confirm_password,
        }

        if not username or not email or not password or not confirm_password:
            context['error'] = 'Please fill in all required fields.'
            return render(request, 'accounts/register.html', context)

        if password != confirm_password:
            context['error'] = 'Passwords do not match.'
            return render(request, 'accounts/register.html', context)

        if len(password) < 6:
            context['error'] = 'Password must be at least 6 characters long.'
            return render(request, 'accounts/register.html', context)

        if User.objects.filter(username__iexact=username).exists():
            context['error'] = 'Username already exists.'
            return render(request, 'accounts/register.html', context)

        if User.objects.filter(email__iexact=email).exists():
            context['error'] = 'An account with this email already exists.'
            return render(request, 'accounts/register.html', context)

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            Profile.objects.get_or_create(user=user)
            UserSettings.objects.get_or_create(user=user)
        except Exception as e:
            context['error'] = f'Failed to create account: {str(e)}'
            return render(request, 'accounts/register.html', context)

        messages.success(request, 'Account created successfully! Please log in.')
        return redirect('login')

    return render(request, 'accounts/register.html')


def logout_view(request):
    logout(request)
    return redirect('login')
