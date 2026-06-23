from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
import datetime

from .processor import parse_voice_input
from transactions.models import Transaction, Category
from django.db.models import Q


@login_required
def voice_log(request):
    """Main voice logging page — uses Web Speech API in browser."""
    example_phrases = [
        "I spent 500 rupees on food today",
        "Received salary of 50000",
        "Paid 1200 for electricity bill yesterday",
        "Bought groceries for 800 at supermarket",
        "Uber 150 rupees this morning",
    ]
    return render(request, 'voice/log.html', {'example_phrases': example_phrases})


@login_required
@require_POST
def process_voice(request):
    """API endpoint: receive transcribed text, parse it, return structured data."""
    try:
        data = json.loads(request.body)
        text = data.get('text', '').strip()
        if not text:
            return JsonResponse({'error': 'No text provided'}, status=400)

        parsed = parse_voice_input(text)

        # Get category suggestion
        category_name = parsed.get('category_hint')
        category_data = None
        if category_name:
            cat = Category.objects.filter(
                Q(user=request.user) | Q(is_default=True),
                name__iexact=category_name
            ).first()
            if cat:
                category_data = {'id': cat.id, 'name': cat.name, 'icon': cat.icon}

        return JsonResponse({
            'parsed': parsed,
            'category': category_data,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def save_voice_transaction(request):
    """Save the confirmed voice transaction."""
    try:
        data = json.loads(request.body)
        category = None
        if data.get('category_id'):
            category = Category.objects.filter(pk=data['category_id']).first()

        t = Transaction.objects.create(
            user=request.user,
            amount=data['amount'],
            description=data.get('description', 'Voice transaction'),
            date=data.get('date', datetime.date.today()),
            transaction_type=data.get('transaction_type', 'expense'),
            payment_method=data.get('payment_method', 'cash'),
            category=category,
            via_voice=True,
        )
        return JsonResponse({'status': 'ok', 'id': t.id, 'description': t.description})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
