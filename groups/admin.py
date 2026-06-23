from django.contrib import admin
from .models import ExpenseGroup, GroupMember, GroupExpense, ExpenseSplit

admin.site.register(ExpenseGroup)
admin.site.register(GroupMember)
admin.site.register(GroupExpense)
admin.site.register(ExpenseSplit)
