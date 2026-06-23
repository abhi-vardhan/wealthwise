from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    CATEGORY_TYPES = [
        ('expense', 'Expense'),
        ('income', 'Income'),
    ]
    ICONS = [
        ('🍔', 'Food'), ('🚗', 'Transport'), ('🏠', 'Housing'), ('🛍️', 'Shopping'),
        ('💊', 'Health'), ('🎬', 'Entertainment'), ('📚', 'Education'), ('💡', 'Utilities'),
        ('✈️', 'Travel'), ('💰', 'Salary'), ('📈', 'Investment'), ('🎁', 'Gifts'),
        ('📱', 'Tech'), ('💪', 'Fitness'), ('🐾', 'Pets'), ('🔧', 'Maintenance'),
    ]

    name = models.CharField(max_length=50)
    icon = models.CharField(max_length=10, default='💰')
    color = models.CharField(max_length=7, default='#6366f1')
    category_type = models.CharField(max_length=10, choices=CATEGORY_TYPES, default='expense')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
                             help_text='Null = default/global category')
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return f"{self.icon} {self.name}"


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('expense', 'Expense'),
        ('income', 'Income'),
        ('transfer', 'Transfer'),
    ]
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('net_banking', 'Net Banking'),
        ('wallet', 'Wallet'),
        ('cheque', 'Cheque'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=255)
    date = models.DateField()
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='expense')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='upi')
    receipt_image = models.ImageField(upload_to='receipts/', blank=True, null=True)
    via_voice = models.BooleanField(default=False)
    via_receipt = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    is_recurring = models.BooleanField(default=False)
    recurrence_frequency = models.CharField(
        max_length=10,
        choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('yearly', 'Yearly')],
        blank=True
    )
    ai_categorized = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.description} — ₹{self.amount} ({self.date})"
