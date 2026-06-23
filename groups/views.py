from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum
import datetime

from .models import ExpenseGroup, GroupMember, GroupExpense, ExpenseSplit


@login_required
def group_list(request):
    groups = request.user.expense_groups.all()
    return render(request, 'groups/list.html', {'groups': groups})


@login_required
def create_group(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '')
        member_usernames = request.POST.getlist('members')

        if not name:
            messages.error(request, 'Group name is required.')
            return redirect('create_group')

        group = ExpenseGroup.objects.create(
            name=name, description=description, created_by=request.user
        )
        GroupMember.objects.create(group=group, user=request.user, role='admin')

        for username in member_usernames:
            user = User.objects.filter(username=username.strip()).first()
            if user and user != request.user:
                GroupMember.objects.get_or_create(group=group, user=user)

        messages.success(request, f'Group "{name}" created!')
        return redirect('group_detail', pk=group.pk)

    all_users = User.objects.exclude(pk=request.user.pk)
    return render(request, 'groups/create.html', {'all_users': all_users})


@login_required
def group_detail(request, pk):
    group = get_object_or_404(ExpenseGroup, pk=pk, members=request.user)
    expenses = group.group_expenses.select_related('paid_by').order_by('-date')

    # Calculate balances
    balances = {}
    for member in group.members.all():
        paid = group.group_expenses.filter(paid_by=member).aggregate(Sum('amount'))['amount__sum'] or 0
        owes = ExpenseSplit.objects.filter(
            expense__group=group, user=member, is_settled=False
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        balances[member.username] = {'paid': float(paid), 'owes': float(owes), 'net': float(paid) - float(owes)}

    return render(request, 'groups/detail.html', {
        'group': group,
        'expenses': expenses,
        'balances': balances,
    })


@login_required
def add_group_expense(request, pk):
    group = get_object_or_404(ExpenseGroup, pk=pk, members=request.user)
    if request.method == 'POST':
        try:
            expense = GroupExpense.objects.create(
                group=group,
                paid_by=request.user,
                amount=request.POST['amount'],
                description=request.POST['description'],
                date=request.POST.get('date', datetime.date.today()),
                split_type=request.POST.get('split_type', 'equal'),
            )
            messages.success(request, 'Expense added and split among members!')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return redirect('group_detail', pk=pk)


@login_required
def settle_split(request, split_pk):
    split = get_object_or_404(ExpenseSplit, pk=split_pk, user=request.user)
    split.is_settled = True
    split.settled_at = datetime.datetime.now()
    split.save()
    messages.success(request, 'Marked as settled!')
    return redirect('group_detail', pk=split.expense.group.pk)
