from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
import datetime
from .models import Transaction, Category
from .forms import TransactionForm, CategoryForm
from analytics.ml.categorizer import categorize_transaction


@login_required
def transaction_list(request):
    transactions = Transaction.objects.filter(user=request.user)

    # Filters
    q = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    t_type = request.GET.get('type', '')
    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')

    if q:
        transactions = transactions.filter(
            Q(description__icontains=q) | Q(notes__icontains=q)
        )
    if category_id:
        transactions = transactions.filter(category_id=category_id)
    if t_type:
        transactions = transactions.filter(transaction_type=t_type)
    if date_from:
        transactions = transactions.filter(date__gte=date_from)
    if date_to:
        transactions = transactions.filter(date__lte=date_to)

    total_income = transactions.filter(transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = transactions.filter(transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0

    paginator = Paginator(transactions, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    categories = Category.objects.filter(Q(user=request.user) | Q(is_default=True))
    return render(request, 'transactions/list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'total_income': total_income,
        'total_expense': total_expense,
        'net': total_income - total_expense,
    })


@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.user, request.POST, request.FILES)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            # Auto-categorize if no category selected
            if not transaction.category:
                suggested = categorize_transaction(transaction.description)
                if suggested:
                    transaction.category = suggested
                    transaction.ai_categorized = True
            transaction.save()
            messages.success(request, 'Transaction added successfully!')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'ok', 'id': transaction.id})
            return redirect('transaction_list')
    else:
        form = TransactionForm(request.user)
    return render(request, 'transactions/add.html', {'form': form})


@login_required
def edit_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.user, request.POST, request.FILES, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction updated!')
            return redirect('transaction_list')
    else:
        form = TransactionForm(request.user, instance=transaction)
    return render(request, 'transactions/add.html', {'form': form, 'edit': True})


@login_required
def delete_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    transaction.delete()
    messages.success(request, 'Transaction deleted.')
    return redirect('transaction_list')


@login_required
def categories_view(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.user = request.user
            cat.save()
            messages.success(request, 'Category created!')
            return redirect('categories')
    else:
        form = CategoryForm()
    categories = Category.objects.filter(Q(user=request.user) | Q(is_default=True))
    return render(request, 'transactions/categories.html', {'form': form, 'categories': categories})


@login_required
@require_POST
def quick_add_ajax(request):
    """AJAX endpoint for quick transaction add from dashboard."""
    data = json.loads(request.body)
    try:
        category = None
        if data.get('category_id'):
            category = Category.objects.get(id=data['category_id'])
        t = Transaction.objects.create(
            user=request.user,
            amount=data['amount'],
            description=data['description'],
            date=data.get('date', datetime.date.today()),
            transaction_type=data.get('type', 'expense'),
            payment_method=data.get('payment_method', 'upi'),
            category=category,
        )
        return JsonResponse({'status': 'ok', 'id': t.id})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
