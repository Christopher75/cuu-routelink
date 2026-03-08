from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (
    CustomUser, Place, BusOperator, Bus,
    Rating, Banner, Booking, Payment, Passenger,
)

admin.site.site_header = 'CUU RouteLink Admin Panel'
admin.site.site_title = 'CUU RouteLink — Cavendish University Uganda'
admin.site.index_title = 'Bus Transit Booking System Administration'


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'phone', 'dob', 'age', 'is_staff', 'date_joined')
    search_fields = ('email', 'first_name', 'username')
    list_filter = ('is_staff', 'is_active')
    ordering = ('-date_joined',)
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('dob', 'age', 'phone', 'profile_picture')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Profile', {'fields': ('email', 'dob', 'age', 'phone')}),
    )


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ('place_name', 'latitude', 'longitude')
    search_fields = ('place_name',)


@admin.register(BusOperator)
class BusOperatorAdmin(admin.ModelAdmin):
    list_display = ('operator_name', 'operator_contact')
    search_fields = ('operator_name',)


@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = (
        'bus_name', 'source', 'destination', 'bus_type', 'fare',
        'starting_time', 'seats', 'available_seats_display', 'status', 'is_available',
    )
    list_filter = ('bus_type', 'is_available', 'status', 'source', 'destination')
    search_fields = ('bus_name', 'bus_operator__operator_name')
    list_editable = ('status', 'is_available')

    def available_seats_display(self, obj):
        avail = obj.available_seats()
        color = 'green' if avail > 5 else ('orange' if avail > 0 else 'red')
        return format_html('<span style="color:{}">{}</span>', color, avail)
    available_seats_display.short_description = 'Available Seats'


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('rating_value', 'bus', 'user', 'review', 'created_at')
    list_filter = ('rating_value',)
    search_fields = ('bus__bus_name', 'user__email', 'review')


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('banner_title',)
    search_fields = ('banner_title',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'bus', 'user', 'booking_date', 'seats', 'is_cancelled', 'created_at')
    list_filter = ('booking_date', 'is_cancelled')
    search_fields = ('bus__bus_name', 'user__email')
    readonly_fields = ('booking_id', 'created_at', 'updated_at')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'booking', 'payment_date', 'amount', 'payment_method', 'payment_status')
    list_filter = ('payment_date', 'payment_status', 'payment_method')
    search_fields = ('payment_method', 'booking__booking_id')


@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    list_display = ('name', 'age', 'gender', 'seat_number', 'booking')
    search_fields = ('name', 'booking__booking_id')
    list_filter = ('gender',)
