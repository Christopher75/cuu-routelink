import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.core.mail import send_mail
from django.conf import settings

from .forms import UserRegistrationForm, LoginForm, ContactForm, ProfileUpdateForm
from .models import CustomUser, Booking, Payment

logger = logging.getLogger(__name__)


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful. Please login.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'b_register.html', {'form': form})


def login(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:
                auth_login(request, user)
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    return render(request, 'b_login.html', {'form': form})


def logout(request):
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


def home(request):
    return render(request, 'home.html')


def about_us(request):
    return render(request, 'about_us.html')


def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            phone = form.cleaned_data['phone']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message_body = form.cleaned_data['message']
            try:
                send_mail(
                    subject,
                    f"Message from {name}\nPhone: {phone}\nEmail: {email}\n\n{message_body}",
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.ADMIN_EMAIL],
                    fail_silently=False,
                )
                messages.success(request, 'Your message has been sent successfully!')
            except Exception as e:
                logger.error(f"Contact form email failed: {e}")
                messages.error(request, 'Message could not be sent. Please try again.')
            return redirect('contact_us')
    else:
        form = ContactForm()
    return render(request, 'contact_us.html', {'form': form})


@login_required
def profile(request):
    user = request.user
    password_form = PasswordChangeForm(user)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_profile':
            form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('profile')
        elif action == 'change_password':
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                updated_user = password_form.save()
                update_session_auth_hash(request, updated_user)
                messages.success(request, 'Password changed successfully.')
                return redirect('profile')
        form = ProfileUpdateForm(instance=user)
    else:
        form = ProfileUpdateForm(instance=user)

    # Booking stats
    total_bookings = Booking.objects.filter(user=user, is_cancelled=False).count()
    cancelled_bookings = Booking.objects.filter(user=user, is_cancelled=True).count()
    total_spent = Payment.objects.filter(
        booking__user=user, booking__is_cancelled=False
    ).aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'profile.html', {
        'form': form,
        'password_form': password_form,
        'total_bookings': total_bookings,
        'cancelled_bookings': cancelled_bookings,
        'total_spent': total_spent,
    })
