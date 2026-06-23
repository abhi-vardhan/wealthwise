"""
Personalized financial recommendations engine.
Analyzes spending patterns and generates actionable, varied advice.
"""
from decimal import Decimal
import datetime
import calendar as cal_mod


def generate_recommendations(user) -> list:
    from transactions.models import Transaction
    from django.db.models import Sum, Q
    from budgets.models import Budget

    recs = []
    today = datetime.date.today()
    month_start = today.replace(day=1)
    last_month_end = month_start - datetime.timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    days_in_month = cal_mod.monthrange(today.year, today.month)[1]
    days_elapsed = (today - month_start).days + 1

    def _sum(qs):
        return float(qs.aggregate(Sum('amount'))['amount__sum'] or 0)

    this_exp_qs = Transaction.objects.filter(user=user, transaction_type='expense', date__gte=month_start, date__lte=today)
    this_inc_qs = Transaction.objects.filter(user=user, transaction_type='income',  date__gte=month_start, date__lte=today)
    last_exp_qs = Transaction.objects.filter(user=user, transaction_type='expense', date__gte=last_month_start, date__lte=last_month_end)

    total_exp = _sum(this_exp_qs)
    total_inc = _sum(this_inc_qs)
    last_exp  = _sum(last_exp_qs)

    daily_avg = total_exp / days_elapsed if days_elapsed else 0
    projected = daily_avg * days_in_month
    days_left = days_in_month - days_elapsed

    # 1. Projected overspend / great savings
    if total_inc > 0:
        if projected > total_inc * 0.9:
            recs.append({'title': '⚠️ Projected to Overspend This Month',
                'message': f'At ₹{daily_avg:,.0f}/day you are on track to spend ₹{projected:,.0f} — '
                           f'{projected/total_inc*100:.0f}% of income. Cut ₹{max(0, projected - total_inc*0.8):,.0f} from wants.',
                'priority': 'high', 'type': 'warning'})
        elif total_exp < total_inc * 0.5:
            sr = (total_inc - total_exp) / total_inc * 100
            recs.append({'title': f'🎉 Great Savings Rate — {sr:.0f}% Saved So Far',
                'message': f'You have saved ₹{total_inc-total_exp:,.0f} this month ({sr:.0f}%). '
                           f'Consider investing ₹{(total_inc-total_exp)*0.6:,.0f} in a SIP or liquid fund.',
                'priority': 'low', 'type': 'success'})

    # 2. Month-over-month change
    if last_exp > 0:
        chg = (total_exp - last_exp) / last_exp * 100
        if chg > 20:
            recs.append({'title': f'📈 Spending Up {chg:.0f}% vs Last Month',
                'message': f'Expenses rose from ₹{last_exp:,.0f} → ₹{total_exp:,.0f}. '
                           f'Review transactions to spot the spike.',
                'priority': 'high', 'type': 'warning'})
        elif chg < -15:
            recs.append({'title': f'📉 Spending Down {abs(chg):.0f}% — Well Done!',
                'message': f'Expenses fell from ₹{last_exp:,.0f} last month to ₹{total_exp:,.0f} this month. Keep it up!',
                'priority': 'low', 'type': 'success'})

    # 3. Top category insight
    top_cats = list(this_exp_qs.exclude(category=None).values('category__name','category__icon').annotate(total=Sum('amount')).order_by('-total')[:3])
    if top_cats and total_exp > 0:
        t = top_cats[0]
        pct = float(t['total']) / total_exp * 100
        if pct > 35:
            recs.append({'title': f'💡 {t["category__icon"] or ""} {t["category__name"]} = {pct:.0f}% of All Spending',
                'message': f'₹{float(t["total"]):,.0f} on {t["category__name"]} this month. '
                           f'Even a 15% cut here saves ₹{float(t["total"])*0.15:,.0f}.',
                'priority': 'medium', 'type': 'info'})
        if len(top_cats) >= 3:
            names = ' · '.join(f'{c["category__icon"]} {c["category__name"]}' for c in top_cats)
            recs.append({'title': '📊 Top 3 Spending Categories This Month',
                'message': f'{names} — combined ₹{sum(float(c["total"]) for c in top_cats):,.0f}.',
                'priority': 'low', 'type': 'info'})

    # 4. Weekend spending spike
    we_exp = _sum(this_exp_qs.filter(date__week_day__in=[1,7]))
    wd_exp = total_exp - we_exp
    we_days = sum(1 for i in range(days_elapsed) if (month_start+datetime.timedelta(i)).weekday()>=5)
    wd_days = days_elapsed - we_days
    if we_days > 0 and wd_days > 0:
        wd_d = wd_exp / wd_days
        we_d = we_exp / we_days
        if we_d > wd_d * 1.8:
            recs.append({'title': f'🎭 Weekend Spending is {we_d/wd_d:.1f}× Higher Than Weekdays',
                'message': f'₹{we_d:,.0f}/day on weekends vs ₹{wd_d:,.0f}/day on weekdays. '
                           f'Plan a fixed weekend entertainment budget to stay on track.',
                'priority': 'medium', 'type': 'warning'})

    # 5. Budget alerts — top 3 most critical
    budgets = Budget.objects.filter(user=user, is_active=True, end_date__gte=today)
    balerts = []
    for b in budgets:
        pct = b.get_percentage_used()
        rem = float(b.get_remaining())
        if pct >= 100:
            balerts.append((pct, {'title': f'🔴 {b.name} — Limit Exceeded',
                'message': f'Over by ₹{abs(rem):,.0f}. Budget was ₹{float(b.total_amount):,.0f}. '
                           f'Pause spending in this category for the rest of the month.',
                'priority': 'high', 'type': 'danger'}))
        elif pct >= 80:
            per_day = rem / max(days_left, 1)
            balerts.append((pct, {'title': f'🟡 {b.name} at {pct}% — ₹{rem:,.0f} Left',
                'message': f'{days_left} days left, ₹{rem:,.0f} remaining = ₹{per_day:,.0f}/day budget.',
                'priority': 'medium', 'type': 'warning'}))
        elif pct >= 50:
            balerts.append((pct, {'title': f'🟢 {b.name} on Track ({pct}%)',
                'message': f'₹{rem:,.0f} remaining with {days_left} days left. Spending is well-paced.',
                'priority': 'low', 'type': 'success'}))
    balerts.sort(key=lambda x: -x[0])
    for _, a in balerts[:3]:
        recs.append(a)

    # 6. 50/30/20 rule
    if total_inc > 0:
        sav_target = total_inc * 0.20
        actual_sav = max(0, total_inc - total_exp)
        if actual_sav < sav_target * 0.5:
            recs.append({'title': '💰 50/30/20 Rule: Savings Behind Target',
                'message': f'Target savings: ₹{sav_target:,.0f}/month (20% of ₹{total_inc:,.0f}). '
                           f'Current: ₹{actual_sav:,.0f}. Set up an auto-transfer on salary day to close the gap.',
                'priority': 'medium', 'type': 'info'})

    # 7. Subscription audit
    sub_qs = this_exp_qs.filter(Q(description__icontains='netflix')|Q(description__icontains='spotify')|Q(description__icontains='prime')|Q(description__icontains='hotstar')|Q(description__icontains='subscription'))
    sub_total = _sum(sub_qs)
    if sub_total >= 400:
        recs.append({'title': f'📱 Subscriptions: ₹{sub_total:,.0f}/month',
            'message': f'You have ₹{sub_total:,.0f} in streaming/subscription charges. '
                       f'Audit and cancel any service unused for >30 days. That\'s ₹{sub_total*12:,.0f}/year.',
            'priority': 'low', 'type': 'info'})

    # 8. Emergency fund (pad if fewer insights)
    if len(recs) < 4:
        avg_exp = (total_exp + last_exp) / 2 if last_exp > 0 else total_exp
        recs.append({'title': '🏦 Build Your Emergency Fund',
            'message': f'Target 6 months of expenses = ₹{avg_exp*6:,.0f}. '
                       f'Keep it in a high-yield savings account or liquid mutual fund for instant access.',
            'priority': 'low', 'type': 'info'})

    order = {'high': 0, 'medium': 1, 'low': 2}
    return sorted(recs, key=lambda x: order.get(x.get('priority', 'low'), 2))
