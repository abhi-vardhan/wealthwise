from django.contrib import admin
from .models import BillReminder, Notification

@admin.register(BillReminder)
class BillReminderAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'amount', 'due_date', 'frequency', 'is_active')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
