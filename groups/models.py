from django.db import models
from django.contrib.auth.models import User


class ExpenseGroup(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(User, through='GroupMember', related_name='expense_groups')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def total_expenses(self):
        from django.db.models import Sum
        return self.group_expenses.aggregate(Sum('amount'))['amount__sum'] or 0


class GroupMember(models.Model):
    ROLES = [('admin', 'Admin'), ('member', 'Member')]
    group = models.ForeignKey(ExpenseGroup, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.group.name}"


class GroupExpense(models.Model):
    SPLIT_TYPES = [
        ('equal', 'Split Equally'),
        ('percentage', 'By Percentage'),
        ('custom', 'Custom Amount'),
    ]

    group = models.ForeignKey(ExpenseGroup, on_delete=models.CASCADE, related_name='group_expenses')
    paid_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paid_group_expenses')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)
    date = models.DateField()
    split_type = models.CharField(max_length=15, choices=SPLIT_TYPES, default='equal')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} — ₹{self.amount} in {self.group.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.split_type == 'equal':
            self._create_equal_splits()

    def _create_equal_splits(self):
        members = self.group.members.all()
        if not members.exists():
            return
        share = self.amount / members.count()
        ExpenseSplit.objects.filter(expense=self).delete()
        for member in members:
            ExpenseSplit.objects.create(
                expense=self,
                user=member,
                amount=share,
                is_settled=(member == self.paid_by),
            )


class ExpenseSplit(models.Model):
    expense = models.ForeignKey(GroupExpense, on_delete=models.CASCADE, related_name='splits')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expense_splits')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_settled = models.BooleanField(default=False)
    settled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('expense', 'user')

    def __str__(self):
        return f"{self.user.username} owes ₹{self.amount} for {self.expense.description}"
