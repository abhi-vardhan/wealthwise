"""
Transaction Categorizer using TF-IDF + Logistic Regression.
Falls back to keyword matching when no trained model is available.
Can be upgraded to FinBERT for production.
"""
import os
import pickle
import numpy as np
from pathlib import Path

# Keyword-based fallback categories
KEYWORD_MAP = {
    'food': ['zomato', 'swiggy', 'restaurant', 'cafe', 'pizza', 'burger', 'biryani',
             'lunch', 'dinner', 'breakfast', 'snack', 'coffee', 'tea', 'grocery', 'supermarket'],
    'transport': ['uber', 'ola', 'rapido', 'metro', 'bus', 'auto', 'taxi', 'fuel',
                  'petrol', 'diesel', 'toll', 'parking', 'train', 'flight', 'irctc'],
    'shopping': ['amazon', 'flipkart', 'myntra', 'meesho', 'nykaa', 'clothes',
                 'shoes', 'bag', 'watch', 'jewellery', 'furniture'],
    'health': ['hospital', 'clinic', 'medicine', 'pharmacy', 'doctor', 'dentist',
               'medplus', 'apollo', 'diagnostic', 'lab test', 'gym', 'yoga'],
    'utilities': ['electricity', 'water', 'gas', 'internet', 'broadband', 'mobile',
                  'recharge', 'wifi', 'airtel', 'jio', 'bsnl', 'rent'],
    'entertainment': ['netflix', 'prime', 'hotstar', 'spotify', 'movie', 'cinema',
                      'concert', 'game', 'play', 'amusement', 'disney'],
    'education': ['school', 'college', 'university', 'course', 'udemy', 'coursera',
                  'books', 'stationery', 'tuition', 'fees'],
    'travel': ['hotel', 'resort', 'airbnb', 'flight', 'holiday', 'vacation', 'trip',
               'makemytrip', 'goibibo', 'booking'],
}


def categorize_transaction(description: str):
    """
    Returns a Category object (or None) for a given transaction description.
    First tries a trained ML model, falls back to keyword matching.
    """
    from transactions.models import Category

    if not description:
        return None

    text = description.lower()

    # Try loading trained model
    model_path = Path(__file__).parent.parent.parent / 'ml_models' / 'categorizer.pkl'
    if model_path.exists():
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            vectorizer = model_data['vectorizer']
            clf = model_data['classifier']
            label_encoder = model_data['label_encoder']
            X = vectorizer.transform([text])
            pred = clf.predict(X)[0]
            category_name = label_encoder.inverse_transform([pred])[0]
            category = Category.objects.filter(name__iexact=category_name, is_default=True).first()
            if category:
                return category
        except Exception:
            pass

    # Keyword fallback
    for category_name, keywords in KEYWORD_MAP.items():
        if any(kw in text for kw in keywords):
            category = Category.objects.filter(name__iexact=category_name).first()
            if category:
                return category

    return None


def train_categorizer(transactions):
    """
    Train a TF-IDF + Logistic Regression categorizer on historical transactions.
    Call this from a management command or Celery task.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import LabelEncoder

    descriptions = [t.description for t in transactions if t.category]
    labels = [t.category.name for t in transactions if t.category]

    if len(set(labels)) < 2:
        return False

    vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
    X = vectorizer.fit_transform(descriptions)

    le = LabelEncoder()
    y = le.fit_transform(labels)

    clf = LogisticRegression(max_iter=500)
    clf.fit(X, y)

    model_path = Path(__file__).parent.parent.parent / 'ml_models' / 'categorizer.pkl'
    model_path.parent.mkdir(exist_ok=True)
    with open(model_path, 'wb') as f:
        pickle.dump({'vectorizer': vectorizer, 'classifier': clf, 'label_encoder': le}, f)

    return True
