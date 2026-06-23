from django.db import models
from django.contrib.auth.models import User
from transactions.models import Category
import datetime


class Budget(models.Model):
    PERIOD_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                                 help_text='If set, tracks spending only for this category')
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='monthly')
    start_date = models.DateField(default=datetime.date.today)
    end_date = models.DateField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.period})"

    def get_spent(self):
        from transactions.models import Transaction
        from django.db.models import Sum
        qs = Transaction.objects.filter(
            user=self.user,
            transaction_type='expense',
            date__gte=self.start_date,
            date__lte=self.end_date,
        )
        if self.category_id:
            qs = qs.filter(category=self.category)
        return qs.aggregate(Sum('amount'))['amount__sum'] or 0

    def get_remaining(self):
        return self.total_amount - self.get_spent()

    def get_percentage_used(self):
        if self.total_amount == 0:
            return 0
        return min(int((self.get_spent() / self.total_amount) * 100), 100)


class BudgetCategory(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='category_budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ('budget', 'category')

    def __str__(self):
        return f"{self.budget.name} — {self.category.name}: ₹{self.allocated_amount}"

    def get_spent(self):
        from transactions.models import Transaction
        from django.db.models import Sum
        spent = Transaction.objects.filter(
            user=self.budget.user,
            category=self.category,
            transaction_type='expense',
            date__gte=self.budget.start_date,
            date__lte=self.budget.end_date,
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        return spent

    def get_percentage_used(self):
        if self.allocated_amount == 0:
            return 0
        return min(int((self.get_spent() / self.allocated_amount) * 100), 100)
