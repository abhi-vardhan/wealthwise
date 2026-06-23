from django import forms
from django.db.models import Q
from .models import Transaction, Category
import datetime


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ('amount', 'transaction_type', 'category', 'description', 'date',
                  'payment_method', 'notes', 'is_recurring', 'recurrence_frequency')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(
            Q(user=user) | Q(is_default=True)
        )
        self.fields['date'].initial = datetime.date.today()
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault('class',
                    'w-full px-3 py-2 border border-gray-300 rounded-lg '
                    'focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm')


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'icon', 'color', 'category_type')
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class',
                'w-full px-3 py-2 border border-gray-300 rounded-lg '
                'focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm')
