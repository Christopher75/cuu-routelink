from django.urls import path
from django.contrib.auth import views as auth_views

from .banner import banner_carousel_api
from .place import place_list_api
from .bus import (
    bus_list_api,
    bus_detail,
    bus_seats_api,
    book_bus,
    show_my_ticket,
    cancel_booking,
    payment_page,
    process_payment,
    add_rating,
    ticket_qr,
    admin_dashboard,
    stats_api,
)
from .views import home, login, logout, register, about_us, contact_us, profile

urlpatterns = [
    path('', home, name='home'),
    path('login/', login, name='login'),
    path('register/', register, name='register'),
    path('logout/', logout, name='logout'),
    path('about/', about_us, name='about_us'),
    path('contact/', contact_us, name='contact_us'),
    path('profile/', profile, name='profile'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),

    # Password reset (Django built-in)
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='password_reset.html',
        email_template_name='password_reset_email.html',
        subject_template_name='password_reset_subject.txt',
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='password_reset_done.html',
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='password_reset_confirm.html',
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html',
    ), name='password_reset_complete'),

    # API endpoints
    path('banners/', banner_carousel_api, name='banner_carousel_api'),
    path('places/', place_list_api, name='place_list_api'),
    path('buses/', bus_list_api, name='bus_list_api'),
    path('buses/<uuid:bus_id>/', bus_detail, name='bus_detail'),
    path('buses/<uuid:bus_id>/seats/', bus_seats_api, name='bus_seats_api'),

    # Booking flow
    path('book-bus/<uuid:bus_id>/', book_bus, name='book_bus'),
    path('payment/', payment_page, name='payment_page'),
    path('process-payment/', process_payment, name='process_payment'),
    path('my-tickets/', show_my_ticket, name='show_my_ticket'),
    path('cancel-booking/<uuid:booking_id>/', cancel_booking, name='cancel_booking'),
    path('add-rating/<uuid:booking_id>/', add_rating, name='add_rating'),
    path('ticket/<uuid:booking_id>/qr.png', ticket_qr, name='ticket_qr'),
    path('stats/', stats_api, name='stats_api'),
]
