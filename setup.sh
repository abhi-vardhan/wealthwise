#!/usr/bin/env bash
# WealthWise AI — Quick Setup Script
set -e

echo "========================================="
echo "  WealthWise AI — Project Setup"
echo "========================================="

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy env file
if [ ! -f .env ]; then
  cp .env.example .env
  echo "✅ Created .env — edit it with your settings"
fi

echo "🗄️  Running migrations..."
python manage.py makemigrations
python manage.py migrate

echo "🌱 Seeding default categories..."
python manage.py seed_categories

echo "👤 Creating superuser (optional)..."
echo "  Run: python manage.py createsuperuser"

echo ""
echo "========================================="
echo "  ✅ Setup complete!"
echo "  Run: source venv/bin/activate"
echo "  Then: python manage.py runserver"
echo "  Open: http://127.0.0.1:8000"
echo "========================================="
