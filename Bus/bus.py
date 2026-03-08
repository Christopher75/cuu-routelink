import io
import logging
import qrcode
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib import messages
from django.conf import settings

from .models import Booking, Bus, CustomUser, Passenger, Payment, Rating

logger = logging.getLogger(__name__)


def bus_list_api(request):
    if 'payment_success' in request.session:
        del request.session['payment_success']

    source_id = request.GET.get('from')
    destination_id = request.GET.get('to')
    journey_date = request.GET.get('journey_date')
    bus_type = request.GET.get('bus_type')
    min_fare = request.GET.get('min_fare')
    max_fare = request.GET.get('max_fare')
    departure_period = request.GET.get('departure_period')
    sort_by = request.GET.get('sort_by', 'starting_time')

    now = timezone.localtime()
    buses = Bus.objects.filter(starting_time__gte=now, is_available=True).select_related(
        'source', 'destination', 'bus_operator'
    )

    if source_id:
        buses = buses.filter(source_id=source_id)
    if destination_id:
        buses = buses.filter(destination_id=destination_id)
    if journey_date:
        journey_datetime = timezone.datetime.strptime(journey_date, '%Y-%m-%d').date()
        buses = buses.filter(starting_time__date=journey_datetime)
    if bus_type:
        buses = buses.filter(bus_type__iexact=bus_type)
    if min_fare:
        buses = buses.filter(fare__gte=int(min_fare))
    if max_fare:
        buses = buses.filter(fare__lte=int(max_fare))
    if departure_period:
        hour_ranges = {
            'morning': (5, 12),
            'afternoon': (12, 17),
            'evening': (17, 21),
            'night': (21, 5),
        }
        period = departure_period.lower()
        if period in hour_ranges:
            start_h, end_h = hour_ranges[period]
            if period == 'night':
                from django.db.models import Q
                buses = buses.filter(
                    Q(starting_time__hour__gte=start_h) | Q(starting_time__hour__lt=end_h)
                )
            else:
                buses = buses.filter(
                    starting_time__hour__gte=start_h,
                    starting_time__hour__lt=end_h,
                )

    sort_map = {
        'fare_asc': 'fare',
        'fare_desc': '-fare',
        'departure': 'starting_time',
        'seats': '-seats',
    }
    buses = buses.order_by(sort_map.get(sort_by, 'starting_time'))

    if not buses.exists():
        return JsonResponse({'message': 'No buses found'}, status=404)

    def _duration_display(minutes):
        h, m = divmod(minutes, 60)
        return f"{h}h {m}m" if h else f"{m}m"

    buses_data = [
        {
            'bus_id': str(bus.bus_id),
            'bus_name': bus.bus_name,
            'source': bus.source.place_name,
            'destination': bus.destination.place_name,
            'bus_type': bus.bus_type,
            'fare': bus.fare,
            'starting_time': bus.starting_time.strftime('%Y-%m-%d %H:%M'),
            'arrival_time': bus.arrival_time.strftime('%Y-%m-%d %H:%M'),
            'seats': bus.seats,
            'available_seats': bus.available_seats(),
            'is_available': bus.is_available,
            'bus_operator': bus.bus_operator.operator_name,
            'bus_operator_contact': bus.bus_operator.operator_contact,
            'cancel_policy': bus.cancel_policy,
            'status': bus.status,
            'amenities': [a.strip() for a in bus.amenities.split(',') if a.strip()],
            'duration_minutes': int((bus.arrival_time - bus.starting_time).total_seconds() / 60),
            'duration_display': _duration_display(int((bus.arrival_time - bus.starting_time).total_seconds() / 60)),
        }
        for bus in buses
    ]
    return JsonResponse(buses_data, safe=False)


def bus_detail(request, bus_id):
    bus = get_object_or_404(Bus, pk=bus_id)
    average_rating = Rating.objects.filter(bus=bus).aggregate(Avg('rating_value'))['rating_value__avg']
    average_rating = round(average_rating, 1) if average_rating else None
    available_seats = bus.available_seats()
    reviews = Rating.objects.filter(bus=bus).select_related('user').order_by('-created_at')[:10]
    duration_minutes = int((bus.arrival_time - bus.starting_time).total_seconds() / 60)
    duration_h, duration_m = divmod(duration_minutes, 60)
    duration_display = f"{duration_h}h {duration_m}m" if duration_h else f"{duration_m}m"
    amenities = [a.strip() for a in bus.amenities.split(',') if a.strip()]
    return render(request, 'bus_detail.html', {
        'bus': bus,
        'average_rating': average_rating,
        'available_seats': available_seats,
        'reviews': reviews,
        'duration_display': duration_display,
        'amenities': amenities,
    })


def bus_seats_api(request, bus_id):
    """Returns booked seat numbers for a specific bus."""
    bus = get_object_or_404(Bus, pk=bus_id)
    booked = bus.booked_seat_numbers()
    return JsonResponse({'booked_seats': booked, 'total_seats': bus.seats})


def stats_api(request):
    """Public API returning site-wide stats for the home page counters."""
    total_passengers = Booking.objects.filter(is_cancelled=False).aggregate(
        total=Sum('seats')
    )['total'] or 0
    data = {
        'total_routes': Bus.objects.values('source', 'destination').distinct().count(),
        'total_buses': Bus.objects.filter(is_available=True).count(),
        'total_bookings': Booking.objects.filter(is_cancelled=False).count(),
        'total_passengers': total_passengers,
    }
    return JsonResponse(data)


@login_required
def book_bus(request, bus_id):
    if request.method == 'POST':
        bus = get_object_or_404(Bus, pk=bus_id)

        try:
            seats = int(request.POST.get('seats', 1))
            if seats < 1:
                raise ValueError('At least 1 seat required')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid number of seats.')
            return redirect('bus_detail', bus_id=bus_id)

        if not bus.can_accommodate(seats):
            messages.error(request, f'Only {bus.available_seats()} seats available.')
            return redirect('bus_detail', bus_id=bus_id)

        passengers = []
        for i in range(1, seats + 1):
            name = request.POST.get(f'passenger_name_{i}', '').strip()
            age_str = request.POST.get(f'passenger_age_{i}', '')
            gender = request.POST.get(f'passenger_gender_{i}', '')
            seat_num_str = request.POST.get(f'passenger_seat_{i}', '')

            if not (name and age_str and gender):
                messages.error(request, f'Missing details for passenger {i}.')
                return redirect('bus_detail', bus_id=bus_id)

            try:
                age = int(age_str)
                if not (1 <= age <= 120):
                    raise ValueError
            except ValueError:
                messages.error(request, f'Invalid age for passenger {i}.')
                return redirect('bus_detail', bus_id=bus_id)

            seat_number = None
            if seat_num_str:
                try:
                    seat_number = int(seat_num_str)
                except ValueError:
                    pass

            passengers.append({
                'name': name,
                'age': age,
                'gender': gender,
                'seat_number': seat_number,
            })

        request.session['temp_booking'] = {
            'bus_id': str(bus_id),
            'seats': seats,
            'total_fare': bus.fare * seats,
            'passengers': passengers,
        }
        return redirect('payment_page')

    return redirect('bus_detail', bus_id=bus_id)


@login_required
def show_my_ticket(request):
    from django.db.models import Prefetch
    rating_prefetch = Prefetch(
        'rating_set',
        queryset=Rating.objects.all(),
        to_attr='ratings'
    )

    status_filter = request.GET.get('status', 'all')
    search_q = request.GET.get('q', '')

    bookings_qs = Booking.objects.select_related(
        'bus', 'bus__source', 'bus__destination', 'bus__bus_operator'
    ).prefetch_related(rating_prefetch, 'passenger_set').filter(user=request.user)

    if status_filter == 'upcoming':
        bookings_qs = bookings_qs.filter(is_cancelled=False, starting_time__gte=timezone.now())
    elif status_filter == 'completed':
        bookings_qs = bookings_qs.filter(is_cancelled=False, arrival_time__lt=timezone.now())
    elif status_filter == 'cancelled':
        bookings_qs = bookings_qs.filter(is_cancelled=True)
    else:
        bookings_qs = bookings_qs.filter(is_cancelled=False)

    if search_q:
        from django.db.models import Q
        bookings_qs = bookings_qs.filter(
            Q(bus__bus_name__icontains=search_q) |
            Q(bus__source__place_name__icontains=search_q) |
            Q(bus__destination__place_name__icontains=search_q)
        )

    bookings_qs = bookings_qs.order_by('-booking_date')

    now = timezone.now()
    for booking in bookings_qs:
        if booking.ratings:
            rating = booking.ratings[0]
            booking.rating_value = rating.rating_value
            booking.review_text = rating.review
        else:
            booking.rating_value = None
            booking.review_text = None

    paginator = Paginator(bookings_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'show_my_ticket.html', {
        'page_obj': page_obj,
        'now': now,
        'rating_choices': Rating.RATING_CHOICES,
        'current_time': now,
        'status_filter': status_filter,
        'search_q': search_q,
    })


@login_required
def cancel_booking(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
        if booking.is_cancelled:
            messages.warning(request, 'This booking is already cancelled.')
        else:
            booking.cancel()
            try:
                _send_cancellation_email(request.user, booking)
            except Exception as e:
                logger.warning(f"Cancellation email failed: {e}")
            messages.success(request, 'Booking cancelled successfully.')
    return redirect('show_my_ticket')


@login_required
def payment_page(request):
    booking_details = request.session.get('temp_booking')
    if not booking_details:
        return redirect('home')
    return render(request, 'payment_page.html', booking_details)


@login_required
def process_payment(request):
    if request.method == 'POST':
        booking_details = request.session.pop('temp_booking', None)
        if not booking_details:
            messages.error(request, 'Session expired. Please start over.')
            return redirect('home')

        try:
            with transaction.atomic():
                bus = Bus.objects.select_for_update().get(bus_id=booking_details['bus_id'])

                # Server-side amount calculation — ignore client-submitted amount
                expected_amount = bus.fare * booking_details['seats']

                booking = Booking(
                    bus=bus,
                    seats=booking_details['seats'],
                    user=request.user,
                    booking_date=timezone.now().date(),
                    starting_time=bus.starting_time,
                    arrival_time=bus.arrival_time,
                )
                booking.full_clean()
                booking.save()

                for passenger_info in booking_details['passengers']:
                    Passenger.objects.create(
                        booking=booking,
                        name=passenger_info['name'],
                        age=passenger_info['age'],
                        gender=passenger_info['gender'],
                        seat_number=passenger_info.get('seat_number'),
                    )

                payment_method = request.POST.get('payment_method', 'Unknown')
                Payment.objects.create(
                    booking=booking,
                    payment_date=timezone.now().date(),
                    amount=expected_amount,
                    payment_method=payment_method,
                    payment_status='Completed',
                )

            try:
                _send_booking_confirmation(request.user, booking, bus, booking_details, expected_amount, payment_method)
            except Exception as e:
                logger.warning(f"Booking confirmation email failed: {e}")

            request.session['payment_success'] = True
            request.session['last_booking_id'] = str(booking.booking_id)
            return redirect('show_my_ticket')

        except ValidationError as e:
            messages.error(request, f"Booking failed: {e.messages[0]}")
            return redirect('bus_detail', bus_id=booking_details['bus_id'])

        except Exception as e:
            logger.error(f"Payment processing error: {e}")
            messages.error(request, 'An error occurred during payment processing.')
            return redirect('home')

    return redirect('payment_page')


def _send_booking_confirmation(user, booking, bus, booking_details, amount, payment_method):
    passenger_lines = '\n'.join(
        f"  - {p['name']} (Age: {p['age']}, Gender: {p['gender']})"
        for p in booking_details['passengers']
    )
    body = f"""Dear {user.get_full_name() or user.email},

Your booking is confirmed!

Booking ID: {booking.booking_id}
Bus: {bus.bus_name} ({bus.bus_type})
Route: {bus.source.place_name} \u2192 {bus.destination.place_name}
Departure: {bus.starting_time.strftime('%d %b %Y, %H:%M')}
Arrival: {bus.arrival_time.strftime('%d %b %Y, %H:%M')}
Seats: {booking_details['seats']}
Amount Paid: UGX {amount:,}
Payment Method: {payment_method}

Passengers:
{passenger_lines}

Thank you for choosing CUU RouteLink!
Cavendish University Uganda \u2014 Final Year Project, 2026
"""
    send_mail(
        subject=f'Booking Confirmed \u2014 {bus.source.place_name} to {bus.destination.place_name}',
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def _send_cancellation_email(user, booking):
    body = f"""Dear {user.get_full_name() or user.email},

Your booking has been cancelled.

Booking ID: {booking.booking_id}
Bus: {booking.bus.bus_name} ({booking.bus.bus_type})
Route: {booking.bus.source.place_name} \u2192 {booking.bus.destination.place_name}
Departure: {booking.starting_time.strftime('%d %b %Y, %H:%M') if booking.starting_time else 'N/A'}
Seats: {booking.seats}
Cancelled at: {booking.cancelled_at.strftime('%d %b %Y, %H:%M') if booking.cancelled_at else 'N/A'}

If you have any questions, please contact us.

CUU RouteLink \u2014 Cavendish University Uganda
"""
    send_mail(
        subject=f'Booking Cancelled \u2014 {booking.bus.source.place_name} to {booking.bus.destination.place_name}',
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


@login_required
def add_rating(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
        rating_value = request.POST.get('rating_value')
        review = request.POST.get('review', '')

        existing = Rating.objects.filter(booking=booking).first()
        if existing:
            existing.rating_value = rating_value
            existing.review = review
            existing.save()
        else:
            Rating.objects.create(
                bus=booking.bus,
                user=request.user,
                booking=booking,
                rating_value=rating_value,
                review=review,
            )

        messages.success(request, 'Thank you for your feedback!')
        return redirect('show_my_ticket')


@login_required
def ticket_qr(request, booking_id):
    """Generates and serves a QR code image for a booking."""
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)

    qr_data = (
        f"CUU RouteLink Ticket\n"
        f"Booking: {booking.booking_id}\n"
        f"Route: {booking.bus.source.place_name} \u2192 {booking.bus.destination.place_name}\n"
        f"Departure: {booking.starting_time.strftime('%d %b %Y %H:%M') if booking.starting_time else 'N/A'}\n"
        f"Seats: {booking.seats}"
    )

    qr = qrcode.QRCode(version=1, box_size=8, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return HttpResponse(buffer, content_type='image/png')


def _is_staff(user):
    return user.is_staff


@login_required
@user_passes_test(_is_staff)
def admin_dashboard(request):
    from datetime import timedelta
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_bookings_month = Booking.objects.filter(
        created_at__gte=month_start, is_cancelled=False
    ).count()

    revenue_month = Payment.objects.filter(
        created_at__gte=month_start,
        booking__is_cancelled=False
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_bookings_all = Booking.objects.filter(is_cancelled=False).count()
    cancelled_count = Booking.objects.filter(is_cancelled=True).count()
    cancellation_rate = round(
        (cancelled_count / (total_bookings_all + cancelled_count) * 100)
        if (total_bookings_all + cancelled_count) > 0 else 0, 1
    )

    total_users = CustomUser.objects.filter(is_staff=False).count()
    avg_rating_val = Rating.objects.aggregate(avg=Avg('rating_value'))['avg']
    avg_rating = round(avg_rating_val, 1) if avg_rating_val else None

    total_revenue_all = Payment.objects.filter(
        booking__is_cancelled=False
    ).aggregate(total=Sum('amount'))['total'] or 0

    popular_routes = (
        Booking.objects.filter(is_cancelled=False)
        .values('bus__source__place_name', 'bus__destination__place_name')
        .annotate(count=Count('booking_id'))
        .order_by('-count')[:5]
    )

    recent_bookings = (
        Booking.objects.select_related('bus', 'user', 'bus__source', 'bus__destination')
        .order_by('-created_at')[:10]
    )

    recent_ratings = (
        Rating.objects.select_related('user', 'bus')
        .order_by('-created_at')[:5]
    )

    # Monthly revenue for chart (last 6 months)
    monthly_data = []
    for i in range(5, -1, -1):
        month = (now.replace(day=1) - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = (month.replace(day=28) + timedelta(days=4)).replace(day=1)
        rev = Payment.objects.filter(
            created_at__gte=month,
            created_at__lt=next_month,
            booking__is_cancelled=False
        ).aggregate(total=Sum('amount'))['total'] or 0
        monthly_data.append({'month': month.strftime('%b %Y'), 'revenue': rev})

    # Bus occupancy
    buses = Bus.objects.all()[:10]
    occupancy_data = [
        {
            'name': bus.bus_name,
            'route': f"{bus.source.place_name}\u2192{bus.destination.place_name}",
            'total': bus.seats,
            'booked': bus.seats - bus.available_seats(),
            'rate': round(((bus.seats - bus.available_seats()) / bus.seats * 100) if bus.seats > 0 else 0, 1),
        }
        for bus in buses
    ]

    return render(request, 'dashboard.html', {
        'total_bookings_month': total_bookings_month,
        'revenue_month': revenue_month,
        'total_bookings_all': total_bookings_all,
        'cancellation_rate': cancellation_rate,
        'total_users': total_users,
        'avg_rating': avg_rating,
        'total_revenue_all': total_revenue_all,
        'popular_routes': popular_routes,
        'recent_bookings': recent_bookings,
        'recent_ratings': recent_ratings,
        'monthly_data': monthly_data,
        'occupancy_data': occupancy_data,
    })
