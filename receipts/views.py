from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Receipt
from .ocr import extract_text, parse_receipt_data
import datetime


@login_required
def upload_receipt(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image = request.FILES['image']
        receipt = Receipt.objects.create(user=request.user, image=image)

        # Run OCR
        text = extract_text(receipt.image.path)
        data = parse_receipt_data(text)
        receipt.raw_text = text
        receipt.extracted_data = data
        receipt.processed = True
        receipt.save()

        messages.success(request, 'Receipt processed! Review and save the transaction below.')
        return redirect('review_receipt', pk=receipt.pk)

    receipts = Receipt.objects.filter(user=request.user).order_by('-created_at')[:20]
    return render(request, 'receipts/upload.html', {'receipts': receipts})


@login_required
def review_receipt(request, pk):
    receipt = get_object_or_404(Receipt, pk=pk, user=request.user)
    if request.method == 'POST':
        from transactions.models import Transaction, Category
        from django.db.models import Q
        category_id = request.POST.get('category')
        amount_raw = request.POST.get('amount', '').strip()
        description = request.POST.get('description', '').strip()
        date_str = request.POST.get('date', '') or str(datetime.date.today())

        # Validate amount
        try:
            amount = float(amount_raw.replace(',', '')) if amount_raw else None
            if not amount or amount <= 0:
                raise ValueError('invalid')
        except (ValueError, TypeError):
            messages.error(request, 'Please enter a valid amount before saving.')
            return redirect('review_receipt', pk=pk)

        category = None
        if category_id:
            category = Category.objects.filter(pk=category_id).first()

        try:
            t = Transaction.objects.create(
                user=request.user,
                amount=amount,
                description=description or receipt.extracted_data.get('merchant', 'Receipt scan'),
                date=date_str,
                transaction_type='expense',
                payment_method='cash',
                category=category,
                via_receipt=True,
            )
            receipt.transaction = t
            receipt.save()
            messages.success(request, f'Transaction ₹{amount:,.2f} saved from receipt!')
            return redirect('transaction_list')
        except Exception as e:
            messages.error(request, f'Error saving: {e}')

    from transactions.models import Category
    from django.db.models import Q
    categories = Category.objects.filter(
        Q(user=request.user) | Q(is_default=True), category_type='expense'
    )

    # Prefill from extracted OCR data
    extracted = receipt.extracted_data or {}
    prefill = {
        'amount': extracted.get('total') or '',
        'description': extracted.get('merchant') or 'Receipt scan',
        'date': extracted.get('date') or str(datetime.date.today()),
    }

    # AI-suggest category from merchant name
    suggested_cat = None
    if prefill['description']:
        from analytics.ml.categorizer import categorize_transaction
        suggested_cat = categorize_transaction(prefill['description'])

    return render(request, 'receipts/review.html', {
        'receipt': receipt,
        'categories': categories,
        'prefill': prefill,
        'suggested_cat': suggested_cat,
    })
