"""
Management command: create_demo_data
Creates a realistic demo account with 1 month of transaction history,
budgets, and notifications for viva demonstration.

Usage:
    python manage.py create_demo_data
    python manage.py create_demo_data --reset   (delete existing demo data first)
"""
import random
import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction as db_transaction

from transactions.models import Transaction, Category
from budgets.models import Budget
from notifications.models import Notification


DEMO_USERNAME = 'demo'
DEMO_PASSWORD = 'demo1234'
DEMO_EMAIL = 'demo@wealthwise.ai'


# ── Realistic expense transactions for a student / young professional ────────
EXPENSE_TEMPLATES = [
    # (description, category_name, min_amt, max_amt, payment_method, frequency_per_month)
    ('Zomato food delivery', 'Food & Dining',    150, 450,  'upi',         10),
    ('Swiggy dinner',        'Food & Dining',    200, 500,  'upi',          6),
    ('Cafe Coffee Day',      'Food & Dining',    120, 280,  'upi',          4),
    ('Grocery supermarket',  'Groceries',        600, 1800, 'debit_card',   4),
    ('BigBasket online',     'Groceries',        800, 1500, 'upi',          2),
    ('Ola cab ride',         'Transport',         80, 300,  'upi',          8),
    ('Metro card recharge',  'Transport',        200, 500,  'upi',          2),
    ('Petrol bunk fuel',     'Transport',        500, 1200, 'cash',          3),
    ('Amazon shopping',      'Shopping',         299, 2499, 'credit_card',  3),
    ('Myntra clothes',       'Shopping',         599, 2999, 'credit_card',  1),
    ('Electricity bill',     'Utilities',        800, 1600, 'net_banking',  1),
    ('Jio mobile recharge',  'Utilities',        299, 599,  'upi',          1),
    ('Netflix subscription', 'Entertainment',    199, 649,  'credit_card',  1),
    ('Movie tickets PVR',    'Entertainment',    250, 600,  'upi',          2),
    ('Spotify premium',      'Entertainment',    119, 119,  'credit_card',  1),
    ('Pharmeasy medicines',  'Healthcare',       150, 800,  'upi',          2),
    ('Gym membership',       'Healthcare',       700, 1500, 'upi',          1),
    ('College exam fees',    'Education',        500, 2000, 'net_banking',  1),
    ('Udemy online course',  'Education',        299, 999,  'credit_card',  1),
    ('House rent',           'Housing',         5000, 8000, 'net_banking',  1),
    ('Restaurant lunch',     'Food & Dining',    180, 450,  'upi',          5),
    ('Bread and milk',       'Groceries',         60, 150,  'cash',         6),
    ('Bus ticket',           'Transport',         20, 80,   'cash',         5),
    ('Auto rickshaw',        'Transport',         40, 120,  'cash',         6),
    ('Snacks and beverages', 'Food & Dining',     50, 200,  'cash',         8),
]

INCOME_TEMPLATES = [
    ('Monthly salary credit',   'Salary & Wages',   45000, 65000, 'net_banking', 1),
    ('Freelance project payment', 'Freelance',       3000, 12000, 'upi',         1),
    ('Google Pay cashback',     'Cashback & Rewards', 10, 200,   'upi',         3),
    ('Scholarship credit',      'Grants & Scholarships', 2000, 5000, 'net_banking', 0),
    ('Part-time income',        'Freelance',         1500, 4000, 'upi',          1),
]


class Command(BaseCommand):
    help = 'Create a demo account with realistic 1-month transaction history for viva.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                            help='Delete existing demo user and recreate from scratch.')
        parser.add_argument('--months', type=int, default=1,
                            help='Number of months of history to generate (default 1).')

    def handle(self, *args, **options):
        if options['reset']:
            User.objects.filter(username=DEMO_USERNAME).delete()
            self.stdout.write('  Deleted existing demo user.')

        # ── Create / get demo user ────────────────────────────────────────────
        user, created = User.objects.get_or_create(
            username=DEMO_USERNAME,
            defaults={
                'email': DEMO_EMAIL,
                'first_name': 'Maanya',
                'last_name': 'Rajan',
                'is_active': True,
            }
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'  Created demo user: {DEMO_USERNAME} / {DEMO_PASSWORD}'))
        else:
            self.stdout.write(f'  Using existing demo user: {DEMO_USERNAME}')

        # Ensure UserProfile exists (signal should create it, but just in case)
        try:
            profile = user.profile
        except Exception:
            from accounts.models import UserProfile
            profile = UserProfile.objects.get_or_create(user=user)[0]

        # ── Resolve categories ────────────────────────────────────────────────
        all_cats = {c.name: c for c in Category.objects.filter(
            is_default=True
        )}
        if not all_cats:
            self.stdout.write(self.style.WARNING(
                '  No default categories found — run seed_categories first.'
            ))
            return

        def get_cat(name):
            """Return best-matching default category or None."""
            if name in all_cats:
                return all_cats[name]
            name_lower = name.lower()
            for k, v in all_cats.items():
                if name_lower in k.lower() or k.lower() in name_lower:
                    return v
            return None

        # ── Generate transactions ─────────────────────────────────────────────
        today = datetime.date.today()
        months = options['months']
        start_date = today - datetime.timedelta(days=30 * months)

        tx_created = 0

        with db_transaction.atomic():
            # INCOME — salary on the 1st, other income scattered
            for tmpl in INCOME_TEMPLATES:
                desc, cat_name, min_a, max_a, method, freq = tmpl
                cat = get_cat(cat_name)
                for m in range(months):
                    month_start = today - datetime.timedelta(days=30 * (m + 1))
                    for _ in range(freq):
                        if freq == 0:
                            continue
                        amt = Decimal(str(round(random.uniform(min_a, max_a), 2)))
                        day_offset = random.randint(0, 28)
                        tx_date = month_start + datetime.timedelta(days=day_offset)
                        if tx_date > today:
                            tx_date = today
                        Transaction.objects.create(
                            user=user,
                            amount=amt,
                            description=desc,
                            date=tx_date,
                            transaction_type='income',
                            payment_method=method,
                            category=cat,
                        )
                        tx_created += 1

            # Ensure salary on a fixed date each month
            salary_cat = get_cat('Salary & Wages')
            for m in range(months):
                salary_date = (today.replace(day=1) - datetime.timedelta(days=30 * m))
                try:
                    salary_date = salary_date.replace(day=1)
                except ValueError:
                    pass
                if salary_date <= today:
                    Transaction.objects.get_or_create(
                        user=user,
                        date=salary_date,
                        description='Monthly salary credit',
                        transaction_type='income',
                        defaults={
                            'amount': Decimal('55000.00'),
                            'payment_method': 'net_banking',
                            'category': salary_cat,
                        }
                    )
                    tx_created += 1

            # EXPENSES — scattered across the month with realistic frequency
            for tmpl in EXPENSE_TEMPLATES:
                desc, cat_name, min_a, max_a, method, freq = tmpl
                cat = get_cat(cat_name)
                for _ in range(freq * months):
                    amt = Decimal(str(round(random.uniform(min_a, max_a), 2)))
                    day_offset = random.randint(0, 30 * months - 1)
                    tx_date = start_date + datetime.timedelta(days=day_offset)
                    if tx_date > today:
                        tx_date = today
                    Transaction.objects.create(
                        user=user,
                        amount=amt,
                        description=desc,
                        date=tx_date,
                        transaction_type='expense',
                        payment_method=method,
                        category=cat,
                        notes='' if random.random() > 0.2 else 'Logged via demo',
                        ai_categorized=random.random() > 0.5,
                    )
                    tx_created += 1

        self.stdout.write(self.style.SUCCESS(f'  Created {tx_created} transactions'))

        # ── Budgets (with category links for accurate tracking) ───────────────
        budget_configs = [
            # (name, category_name, monthly_limit) — tuned for realistic demo %
            # Food spent ~₹6,500 → limit ₹7,500 = 87% (warning zone)
            # Transport spent ~₹3,500 → limit ₹4,500 = 78% (on track)
            # Shopping spent ~₹6,000 → limit ₹5,000 = 100%+ (exceeded for drama)
            # Entertainment spent ~₹550 → limit ₹1,500 = 37% (healthy)
            # Health spent ~₹0-1000 → limit ₹2,000 = low (healthy)
            # Salary income ~₹55k  → Total Budget ₹25,000 good demo
            ('Food & Dining Budget',     'Food & Dining',    7500,  'monthly'),
            ('Transport Budget',         'Transport',        4500,  'monthly'),
            ('Shopping Budget',          'Shopping',         5000,  'monthly'),
            ('Entertainment Budget',     'Entertainment',    1500,  'monthly'),
            ('Health & Wellness Budget', 'Health & Medical', 2000,  'monthly'),
            ('Monthly Total Budget',     None,              25000,  'monthly'),
        ]
        budgets_created = 0
        month_start = today.replace(day=1)
        import calendar
        month_end = month_start.replace(
            day=calendar.monthrange(month_start.year, month_start.month)[1]
        )
        Budget.objects.filter(user=user).delete()
        for name, cat_name, limit, period in budget_configs:
            cat = get_cat(cat_name) if cat_name else None
            Budget.objects.create(
                user=user,
                name=name,
                category=cat,
                total_amount=Decimal(str(limit)),
                period=period,
                start_date=month_start,
                end_date=month_end,
                is_active=True,
            )
            budgets_created += 1
        self.stdout.write(self.style.SUCCESS(f'  Created {budgets_created} budgets'))

        # ── Notifications ─────────────────────────────────────────────────────
        notif_data = [
            ('budget_alert', 'Food Budget Alert 🍔',
             'You have used 87% of your Food Budget this month. ₹1,040 remaining.', True),
            ('ai_insight', 'AI Insight: Spending Pattern 🤖',
             'Your transport spending increased by 23% compared to last month.', False),
            ('bill_reminder', 'Electricity Bill Due 💡',
             'Your electricity bill of approx ₹1,200 is due in 3 days.', False),
            ('goal_update', 'Savings Goal Reached! 🎉',
             'Great job! You saved ₹8,000 this month, exceeding your goal.', False),
            ('ai_insight', 'AI Tip: 50/30/20 Rule 📊',
             'Consider reducing discretionary spending by ₹2,000 to meet your savings target.', True),
            ('bill_reminder', 'Netflix Subscription 🎬',
             'Netflix ₹199 will be auto-debited tomorrow.', False),
        ]
        Notification.objects.filter(user=user).delete()
        for ntype, title, msg, is_read in notif_data:
            Notification.objects.create(
                user=user,
                notification_type=ntype,
                title=title,
                message=msg,
                is_read=is_read,
            )
        self.stdout.write(self.style.SUCCESS(f'  Created {len(notif_data)} notifications'))

        # ── Summary ───────────────────────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 55))
        self.stdout.write(self.style.SUCCESS('  DEMO ACCOUNT READY FOR VIVA'))
        self.stdout.write(self.style.SUCCESS('=' * 55))
        self.stdout.write(f'  URL:      http://127.0.0.1:8000/accounts/login/')
        self.stdout.write(f'  Username: {DEMO_USERNAME}')
        self.stdout.write(f'  Password: {DEMO_PASSWORD}')
        self.stdout.write(self.style.SUCCESS('=' * 55))
