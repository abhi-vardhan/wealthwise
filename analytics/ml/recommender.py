"""
Personalized financial recommendations engine.
Analyzes spending patterns and generates actionable advice.
"""
from decimal import Decimal
import datetime


def generate_recommendations(user) -> list:
    """
    Returns a list of recommendation dicts with title, description, type, and priority.
    """
    from transactions.models import Transaction
    from django.db.models import Sum, Avg, Count
    from budgets.models import Budget

    recommendations = []
    today = datetime.date.today()
    month_start = today.replace(day=1)

    # ---------- Current month stats ----------
    monthly_expenses = Transaction.objects.filter(
        user=user, transaction_type='expense',
        date__gte=month_start, date__lte=today
    )
    monthly_income = Transaction.objects.filter(
        user=user, transaction_type='income',
        date__gte=month_start, date__lte=today
    ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')

    total_expense = monthly_expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    profile = user.profile

    # --- 50/30/20 Rule Check ---
    if profile.monthly_income > 0:
        expense_ratio = float(total_expense) / float(profile.monthly_income)
        if expense_ratio > 0.8:
            recommendations.append({
                'title': '⚠️ High Expense Ratio',
                'description': f'You have spent {expense_ratio*100:.0f}% of your monthly income. '
                               f'Consider following the 50/30/20 rule: 50% needs, 30% wants, 20% savings.',
                'type': 'warning',
                'priority': 1,
            })
        elif expense_ratio < 0.5:
            recommendations.append({
                'title': '✅ Great Spending Control!',
                'description': f'You\'re spending only {expense_ratio*100:.0f}% of your income. '
                               f'Consider investing the surplus in mutual funds or SIPs.',
                'type': 'success',
                'priority': 3,
            })

    # --- Top spending category ---
    top_cat = (
        monthly_expenses.values('category__name', 'category__icon')
        .annotate(total=Sum('amount'))
        .order_by('-total')
        .first()
    )
    if top_cat and top_cat['total']:
        recommendations.append({
            'title': f'💡 Top Spend: {top_cat["category__icon"] or ""} {top_cat["category__name"] or "Uncategorized"}',
            'description': f'You spent ₹{top_cat["total"]:.0f} on {top_cat["category__name"] or "uncategorized"} '
                           f'this month. Review if this aligns with your priorities.',
            'type': 'info',
            'priority': 2,
        })

    # --- Budget alerts ---
    active_budgets = Budget.objects.filter(user=user, is_active=True, end_date__gte=today)
    for budget in active_budgets:
        pct = budget.get_percentage_used()
        if pct >= 90:
            recommendations.append({
                'title': f'🔴 Budget Alert: {budget.name}',
                'description': f'You\'ve used {pct}% of your "{budget.name}" budget. '
                               f'Only ₹{budget.get_remaining():.0f} remaining.',
                'type': 'danger',
                'priority': 1,
            })
        elif pct >= 70:
            recommendations.append({
                'title': f'🟡 Budget Warning: {budget.name}',
                'description': f'You\'ve used {pct}% of your "{budget.name}" budget.',
                'type': 'warning',
                'priority': 2,
            })

    # --- Savings recommendation ---
    if profile.savings_goal > 0 and monthly_income > 0:
        current_savings = monthly_income - total_expense
        if current_savings < profile.savings_goal:
            gap = profile.savings_goal - current_savings
            recommendations.append({
                'title': '🎯 Savings Goal Gap',
                'description': f'You\'re ₹{gap:.0f} short of your monthly savings goal of ₹{profile.savings_goal:.0f}. '
                               f'Try reducing discretionary spending.',
                'type': 'warning',
                'priority': 2,
            })

    # --- Emergency fund check ---
    recommendations.append({
        'title': '🏦 Emergency Fund Reminder',
        'description': 'Aim to maintain 3–6 months of expenses as an emergency fund in a liquid savings account.',
        'type': 'info',
        'priority': 4,
    })

    return sorted(recommendations, key=lambda x: x['priority'])
