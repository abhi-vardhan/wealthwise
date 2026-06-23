from celery import shared_task
from django.utils import timezone
import datetime


@shared_task
def send_bill_reminders():
    """Daily task: send bill reminder notifications for upcoming due bills."""
    from .models import BillReminder, Notification
    from django.contrib.auth.models import User

    today = datetime.date.today()
    reminders = BillReminder.objects.filter(
        is_active=True,
        due_date__gte=today,
        due_date__lte=today + datetime.timedelta(days=7),
    )
    for reminder in reminders:
        days_left = (reminder.due_date - today).days
        title = f"📅 Bill Due: {reminder.title}"
        if days_left == 0:
            message = f'Your bill "{reminder.title}" is due TODAY!'
        else:
            message = f'Your bill "{reminder.title}" is due in {days_left} day(s) on {reminder.due_date}.'
        if reminder.amount:
            message += f' Amount: ₹{reminder.amount}'

        # Avoid duplicate notifications on the same day
        exists = Notification.objects.filter(
            user=reminder.user,
            notification_type='bill_reminder',
            title=title,
            created_at__date=today,
        ).exists()
        if not exists:
            Notification.objects.create(
                user=reminder.user,
                title=title,
                message=message,
                notification_type='bill_reminder',
            )
            # Optionally send email
            if reminder.user.profile.email_notifications and reminder.user.email:
                from django.core.mail import send_mail
                try:
                    send_mail(
                        subject=f'WealthWise — {title}',
                        message=message,
                        from_email='noreply@wealthwise.app',
                        recipient_list=[reminder.user.email],
                        fail_silently=True,
                    )
                except Exception:
                    pass


@shared_task
def check_budget_alerts():
    """Check all active budgets and create alerts if over threshold."""
    from budgets.models import Budget
    from .models import Notification
    import datetime

    today = datetime.date.today()
    budgets = Budget.objects.filter(is_active=True, end_date__gte=today)
    for budget in budgets:
        pct = budget.get_percentage_used()
        if pct >= 90:
            title = f'🔴 Budget Alert: {budget.name}'
            message = f'You have used {pct}% of your "{budget.name}" budget. Only ₹{budget.get_remaining():.0f} remaining.'
            level = 90
        elif pct >= 75:
            title = f'🟡 Budget Warning: {budget.name}'
            message = f'You have used {pct}% of your "{budget.name}" budget.'
            level = 75
        else:
            continue

        exists = Notification.objects.filter(
            user=budget.user,
            notification_type='budget_alert',
            title=title,
            created_at__date=today,
        ).exists()
        if not exists:
            Notification.objects.create(
                user=budget.user,
                title=title,
                message=message,
                notification_type='budget_alert',
            )


@shared_task
def retrain_categorizer(user_id: int):
    """Retrain the ML categorizer for a specific user based on their transactions."""
    from django.contrib.auth.models import User
    from transactions.models import Transaction
    from analytics.ml.categorizer import train_categorizer

    try:
        user = User.objects.get(pk=user_id)
        transactions = Transaction.objects.filter(user=user, category__isnull=False)
        if transactions.count() >= 20:
            train_categorizer(list(transactions))
    except User.DoesNotExist:
        pass
