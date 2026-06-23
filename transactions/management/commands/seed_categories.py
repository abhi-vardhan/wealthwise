from django.core.management.base import BaseCommand
from transactions.models import Category


DEFAULT_CATEGORIES = [
    # Expense categories
    {'name': 'Food & Dining', 'icon': '🍔', 'color': '#f59e0b', 'category_type': 'expense'},
    {'name': 'Transport', 'icon': '🚗', 'color': '#3b82f6', 'category_type': 'expense'},
    {'name': 'Housing & Rent', 'icon': '🏠', 'color': '#8b5cf6', 'category_type': 'expense'},
    {'name': 'Shopping', 'icon': '🛍️', 'color': '#ec4899', 'category_type': 'expense'},
    {'name': 'Health & Medical', 'icon': '💊', 'color': '#10b981', 'category_type': 'expense'},
    {'name': 'Entertainment', 'icon': '🎬', 'color': '#6366f1', 'category_type': 'expense'},
    {'name': 'Education', 'icon': '📚', 'color': '#06b6d4', 'category_type': 'expense'},
    {'name': 'Utilities', 'icon': '💡', 'color': '#f97316', 'category_type': 'expense'},
    {'name': 'Travel', 'icon': '✈️', 'color': '#14b8a6', 'category_type': 'expense'},
    {'name': 'Fitness', 'icon': '💪', 'color': '#84cc16', 'category_type': 'expense'},
    {'name': 'Personal Care', 'icon': '🧴', 'color': '#d946ef', 'category_type': 'expense'},
    {'name': 'Gifts', 'icon': '🎁', 'color': '#ef4444', 'category_type': 'expense'},
    {'name': 'Technology', 'icon': '📱', 'color': '#64748b', 'category_type': 'expense'},
    {'name': 'Maintenance', 'icon': '🔧', 'color': '#78716c', 'category_type': 'expense'},
    {'name': 'Pets', 'icon': '🐾', 'color': '#a3e635', 'category_type': 'expense'},
    {'name': 'Insurance', 'icon': '🛡️', 'color': '#0ea5e9', 'category_type': 'expense'},
    # Income categories
    {'name': 'Salary', 'icon': '💰', 'color': '#22c55e', 'category_type': 'income'},
    {'name': 'Freelance', 'icon': '💻', 'color': '#2563eb', 'category_type': 'income'},
    {'name': 'Investment', 'icon': '📈', 'color': '#16a34a', 'category_type': 'income'},
    {'name': 'Business', 'icon': '🏢', 'color': '#7c3aed', 'category_type': 'income'},
    {'name': 'Rental Income', 'icon': '🏘️', 'color': '#0d9488', 'category_type': 'income'},
    {'name': 'Cashback/Refund', 'icon': '🔄', 'color': '#0891b2', 'category_type': 'income'},
    {'name': 'Gift Received', 'icon': '🎀', 'color': '#be185d', 'category_type': 'income'},
]


class Command(BaseCommand):
    help = 'Seed the database with default transaction categories'

    def handle(self, *args, **options):
        created_count = 0
        for cat_data in DEFAULT_CATEGORIES:
            _, created = Category.objects.get_or_create(
                name=cat_data['name'],
                is_default=True,
                defaults=cat_data,
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'✅ Seeded {created_count} default categories ({len(DEFAULT_CATEGORIES) - created_count} already existed)')
        )
