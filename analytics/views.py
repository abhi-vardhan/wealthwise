from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth, TruncDate
import datetime
import json

from transactions.models import Transaction, Category
from budgets.models import Budget
from .ml.forecaster import forecast_expenses, get_monthly_trend
from .ml.recommender import generate_recommendations


@login_required
def dashboard(request):
    user = request.user
    today = datetime.date.today()
    month_start = today.replace(day=1)

    # --- Summary cards ---
    monthly_income = Transaction.objects.filter(
        user=user, transaction_type='income',
        date__gte=month_start
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    monthly_expense = Transaction.objects.filter(
        user=user, transaction_type='expense',
        date__gte=month_start
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    total_balance = (
        Transaction.objects.filter(user=user, transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    ) - (
        Transaction.objects.filter(user=user, transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    )

    # --- Recent transactions ---
    recent_transactions = Transaction.objects.filter(user=user).select_related('category')[:8]

    # --- Category spending (pie chart) ---
    cat_spending = (
        Transaction.objects.filter(user=user, transaction_type='expense', date__gte=month_start)
        .values('category__name', 'category__color', 'category__icon')
        .annotate(total=Sum('amount'))
        .order_by('-total')[:8]
    )

    # --- Monthly trend chart ---
    trend = get_monthly_trend(user, months=6)

    # --- Active budgets ---
    active_budgets = Budget.objects.filter(user=user, is_active=True, end_date__gte=today)[:4]

    # --- Recommendations ---
    recommendations = generate_recommendations(user)[:4]

    # --- Forecast preview ---
    forecast = forecast_expenses(user, days_ahead=7)

    # --- Bill reminders ---
    from notifications.models import BillReminder
    upcoming_bills = BillReminder.objects.filter(
        user=user, is_active=True,
        due_date__gte=today,
        due_date__lte=today + datetime.timedelta(days=7)
    ).order_by('due_date')[:5]

    context = {
        'monthly_income': monthly_income,
        'monthly_expense': monthly_expense,
        'total_balance': total_balance,
        'net_savings': monthly_income - monthly_expense,
        'recent_transactions': recent_transactions,
        'cat_spending_json': json.dumps([
            {
                'name': c['category__name'] or 'Other',
                'color': c['category__color'] or '#6366f1',
                'amount': float(c['total']),
            } for c in cat_spending
        ]),
        'trend_json': json.dumps(trend),
        'active_budgets': active_budgets,
        'recommendations': recommendations,
        'forecast_json': json.dumps(forecast),
        'upcoming_bills': upcoming_bills,
        'today': today,
    }
    return render(request, 'analytics/dashboard.html', context)


@login_required
def analytics_detail(request):
    user = request.user
    today = datetime.date.today()
    month_start = today.replace(day=1)

    # Full forecast (30 days)
    forecast = forecast_expenses(user, days_ahead=30)
    trend = get_monthly_trend(user, months=12)
    recommendations = generate_recommendations(user)

    # Daily spending last 30 days
    daily = (
        Transaction.objects.filter(
            user=user, transaction_type='expense',
            date__gte=today - datetime.timedelta(days=30)
        )
        .annotate(day=TruncDate('date'))
        .values('day')
        .annotate(total=Sum('amount'))
        .order_by('day')
    )

    context = {
        'forecast_json': json.dumps(forecast),
        'trend_json': json.dumps(trend),
        'daily_json': json.dumps({
            'dates': [str(r['day']) for r in daily],
            'amounts': [float(r['total']) for r in daily],
        }),
        'recommendations': recommendations,
    }
    return render(request, 'analytics/detail.html', context)


@login_required
def forecast_api(request):
    days = int(request.GET.get('days', 30))
    data = forecast_expenses(request.user, days_ahead=days)
    return JsonResponse(data)
