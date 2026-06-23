from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Budget, BudgetCategory
from .forms import BudgetForm, BudgetCategoryForm
import datetime


@login_required
def budget_list(request):
    today = datetime.date.today()
    active_budgets = Budget.objects.filter(user=request.user, is_active=True,
                                           end_date__gte=today)
    past_budgets = Budget.objects.filter(user=request.user).exclude(
        is_active=True, end_date__gte=today
    )
    return render(request, 'budgets/list.html', {
        'active_budgets': active_budgets,
        'past_budgets': past_budgets,
    })


@login_required
def create_budget(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            budget.save()
            messages.success(request, f'Budget "{budget.name}" created!')
            return redirect('budget_detail', pk=budget.pk)
    else:
        form = BudgetForm()
    return render(request, 'budgets/create.html', {'form': form})


@login_required
def budget_detail(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    cat_form = BudgetCategoryForm(request.user)

    if request.method == 'POST':
        cat_form = BudgetCategoryForm(request.user, request.POST)
        if cat_form.is_valid():
            bc = cat_form.save(commit=False)
            bc.budget = budget
            bc.save()
            messages.success(request, 'Category allocation added!')
            return redirect('budget_detail', pk=pk)

    category_budgets = budget.category_budgets.select_related('category').all()
    return render(request, 'budgets/detail.html', {
        'budget': budget,
        'category_budgets': category_budgets,
        'cat_form': cat_form,
    })


@login_required
def delete_budget(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    budget.delete()
    messages.success(request, 'Budget deleted.')
    return redirect('budget_list')
