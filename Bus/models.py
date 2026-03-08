from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.core.exceptions import ValidationError
from django.utils import timezone


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    dob = models.DateField(null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def get_full_name(self):
        full = super().get_full_name()
        return full if full else self.username


class Place(models.Model):
    place_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    place_name = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return self.place_name


class BusOperator(models.Model):
    operator_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operator_name = models.CharField(max_length=100)
    operator_contact = models.CharField(max_length=20)

    def __str__(self):
        return self.operator_name


class Bus(models.Model):
    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Departed', 'Departed'),
        ('Arrived', 'Arrived'),
        ('Cancelled', 'Cancelled'),
    ]

    bus_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bus_name = models.CharField(max_length=100)
    source = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='source')
    destination = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='destination')
    bus_type = models.CharField(max_length=100)
    fare = models.PositiveIntegerField()
    starting_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    seats = models.PositiveIntegerField()
    is_available = models.BooleanField(default=True)
    bus_operator = models.ForeignKey(BusOperator, on_delete=models.CASCADE)
    cancel_policy = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')
    amenities = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def available_seats(self):
        total_booked = self.booking_set.filter(is_cancelled=False).aggregate(
            total_seats=models.Sum('seats')
        )['total_seats'] or 0
        return self.seats - total_booked

    def can_accommodate(self, required_seats):
        return self.available_seats() >= required_seats

    def booked_seat_numbers(self):
        """Returns list of all booked seat numbers for this bus."""
        return list(
            Passenger.objects.filter(
                booking__bus=self,
                booking__is_cancelled=False,
                seat_number__isnull=False
            ).values_list('seat_number', flat=True)
        )

    def __str__(self):
        return f"{self.bus_name} ({self.source} → {self.destination})"


class Banner(models.Model):
    banner_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    banner_title = models.CharField(max_length=100)
    banner_image = models.ImageField(upload_to='banner_images/')

    def __str__(self):
        return self.banner_title


class Booking(models.Model):
    booking_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    booking_date = models.DateField()
    seats = models.PositiveIntegerField()
    starting_time = models.DateTimeField(null=True)
    arrival_time = models.DateTimeField(null=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    is_cancelled = models.BooleanField(default=False)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking {self.booking_id} — {self.bus.bus_name}"

    def clean(self):
        super().clean()
        if not self.pk and not self.is_cancelled:
            if not self.bus.can_accommodate(self.seats):
                raise ValidationError(
                    f"Only {self.bus.available_seats()} seats remaining on this bus"
                )

    def save(self, *args, **kwargs):
        if not self.pk:
            self.full_clean()
        super().save(*args, **kwargs)

    def cancel(self):
        self.is_cancelled = True
        self.cancelled_at = timezone.now()
        super().save(update_fields=['is_cancelled', 'cancelled_at', 'updated_at'])


class Rating(models.Model):
    RATING_CHOICES = [
        (1, '1 - Very Poor'),
        (2, '2 - Poor'),
        (3, '3 - Average'),
        (4, '4 - Good'),
        (5, '5 - Excellent'),
    ]
    rating_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    rating_value = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True)
    review = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('user', 'booking')]

    def __str__(self):
        return f"Rating {self.rating_value}/5 — {self.bus.bus_name}"


class Payment(models.Model):
    payment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    payment_date = models.DateField()
    amount = models.PositiveIntegerField()
    payment_method = models.CharField(max_length=100)
    payment_status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.payment_id} — UGX{self.amount}"


class Passenger(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    seat_number = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} (Seat {self.seat_number or 'N/A'})"

    class Meta:
        verbose_name = 'Passenger'
        verbose_name_plural = 'Passengers'
        ordering = ['seat_number', 'name']
