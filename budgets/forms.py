from django import forms
from .models import Budget, BudgetCategory
from transactions.models import Category
from django.db.models import Q
import datetime


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ('name', 'period', 'total_amount', 'start_date', 'end_date', 'is_active')
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_date'].initial = datetime.date.today().replace(day=1)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault('class',
                    'w-full px-3 py-2 border border-gray-300 rounded-lg '
                    'focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm')


class BudgetCategoryForm(forms.ModelForm):
    class Meta:
        model = BudgetCategory
        fields = ('category', 'allocated_amount')

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(
            Q(user=user) | Q(is_default=True), category_type='expense'
        )
        for field in self.fields.values():
            field.widget.attrs.setdefault('class',
                'w-full px-3 py-2 border border-gray-300 rounded-lg '
                'focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm')
