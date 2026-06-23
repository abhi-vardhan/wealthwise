"""
Voice transaction processor using NLP (Stanza + regex patterns).
Parses utterances like:
  "I spent 500 rupees on food today"
  "Received salary of 50000"
  "Paid 1200 for electricity bill yesterday"
"""
import re
import datetime


AMOUNT_PATTERNS = [
    r'(?:rs\.?|₹|inr|rupees?)\s*([0-9,]+(?:\.\d+)?)',
    r'([0-9,]+(?:\.\d+)?)\s*(?:rs\.?|₹|rupees?|inr|bucks?)',
    r'([0-9,]+(?:\.\d+)?)',
]

EXPENSE_KEYWORDS = ['spent', 'paid', 'bought', 'purchased', 'charged', 'expense', 'cost', 'bill']
INCOME_KEYWORDS = ['received', 'got', 'earned', 'salary', 'income', 'credited', 'cashback', 'refund']

DATE_MAP = {
    'today': 0, 'yesterday': -1, 'day before yesterday': -2,
    'this morning': 0, 'this evening': 0, 'tonight': 0,
}

CATEGORY_KEYWORDS = {
    'food': ['food', 'restaurant', 'lunch', 'dinner', 'breakfast', 'snack', 'grocery',
             'zomato', 'swiggy', 'cafe', 'coffee', 'pizza', 'burger'],
    'transport': ['uber', 'ola', 'auto', 'taxi', 'bus', 'metro', 'fuel', 'petrol', 'train', 'cab'],
    'shopping': ['shopping', 'clothes', 'amazon', 'flipkart', 'myntra', 'shoes', 'bag'],
    'health': ['medicine', 'pharmacy', 'doctor', 'hospital', 'clinic', 'lab', 'gym'],
    'utilities': ['electricity', 'water', 'gas', 'internet', 'wifi', 'recharge', 'bill', 'rent'],
    'entertainment': ['movie', 'netflix', 'prime', 'hotstar', 'spotify', 'game'],
    'education': ['school', 'college', 'fees', 'course', 'books', 'tuition'],
    'salary': ['salary', 'stipend', 'freelance', 'payment received'],
}


def parse_voice_input(text: str) -> dict:
    """
    Parse natural language voice input into structured transaction data.
    Returns dict with: amount, transaction_type, description, date, category_hint
    """
    text_lower = text.lower().strip()
    result = {
        'original_text': text,
        'amount': None,
        'transaction_type': 'expense',
        'description': text,
        'date': datetime.date.today().isoformat(),
        'category_hint': None,
        'confidence': 0.0,
        'error': None,
    }

    # --- Determine transaction type ---
    for kw in INCOME_KEYWORDS:
        if kw in text_lower:
            result['transaction_type'] = 'income'
            break

    # --- Extract amount ---
    for pattern in AMOUNT_PATTERNS:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                result['amount'] = float(amount_str)
                result['confidence'] += 0.5
                break
            except ValueError:
                pass

    # --- Extract date ---
    for phrase, delta in DATE_MAP.items():
        if phrase in text_lower:
            d = datetime.date.today() + datetime.timedelta(days=delta)
            result['date'] = d.isoformat()
            result['confidence'] += 0.2
            break

    # --- Guess category ---
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            result['category_hint'] = category
            result['confidence'] += 0.3
            break

    # --- Build description ---
    # Remove amount references for cleaner description
    desc = re.sub(r'(?:rs\.?|₹|rupees?|inr)\s*[0-9,]+(?:\.\d+)?', '', text, flags=re.IGNORECASE)
    desc = re.sub(r'[0-9,]+(?:\.\d+)?\s*(?:rs\.?|₹|rupees?|inr|bucks?)', '', desc, flags=re.IGNORECASE)
    desc = re.sub(r'\b(?:today|yesterday|morning|evening|tonight)\b', '', desc, flags=re.IGNORECASE)
    desc = ' '.join(desc.split()).strip(' .,')
    if desc:
        result['description'] = desc

    if result['amount'] is None:
        result['error'] = 'Could not detect amount. Please say the amount clearly.'
        result['confidence'] = 0.0

    return result
