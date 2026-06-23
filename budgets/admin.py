from django.contrib import admin
from .models import Budget, BudgetCategory


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'period', 'total_amount', 'start_date', 'end_date', 'is_active')


@admin.register(BudgetCategory)
class BudgetCategoryAdmin(admin.ModelAdmin):
    list_display = ('budget', 'category', 'allocated_amount')
