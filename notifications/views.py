from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import BillReminder, Notification
import datetime


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user)
    notifications.filter(is_read=False).update(is_read=True)
    bill_reminders = BillReminder.objects.filter(user=request.user, is_active=True)
    return render(request, 'notifications/list.html', {
        'notifications': notifications[:50],
        'bill_reminders': bill_reminders,
    })


@login_required
def add_bill_reminder(request):
    if request.method == 'POST':
        BillReminder.objects.create(
            user=request.user,
            title=request.POST['title'],
            amount=request.POST.get('amount') or None,
            due_date=request.POST['due_date'],
            frequency=request.POST.get('frequency', 'monthly'),
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, 'Bill reminder added!')
    return redirect('notification_list')


@login_required
def delete_bill_reminder(request, pk):
    reminder = get_object_or_404(BillReminder, pk=pk, user=request.user)
    reminder.delete()
    messages.success(request, 'Reminder deleted.')
    return redirect('notification_list')


@login_required
@require_POST
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('notification_list')


@login_required
def unread_count(request):
    """AJAX: return unread notification count for navbar badge."""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})
