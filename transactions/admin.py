from django.contrib import admin
from .models import Transaction, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'category_type', 'is_default', 'user')
    list_filter = ('category_type', 'is_default')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'transaction_type', 'category', 'date', 'user')
    list_filter = ('transaction_type', 'category', 'payment_method')
    search_fields = ('description', 'notes')
    date_hierarchy = 'date'
