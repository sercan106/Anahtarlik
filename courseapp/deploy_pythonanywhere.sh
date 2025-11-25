#!/bin/bash
# PythonAnywhere Deployment Script
# Bu script'i PythonAnywhere konsolunda çalıştırın

echo "🚀 PythonAnywhere Deployment Başlatılıyor..."

# Proje dizinine git
cd ~/courseapp || exit 1

# Virtual environment'ı aktif et
echo "📦 Virtual environment aktif ediliyor..."
source venv/bin/activate || source ~/.virtualenvs/venv/bin/activate

# Bağımlılıkları güncelle
echo "📥 Bağımlılıklar güncelleniyor..."
pip install --upgrade pip
pip install -r requirements.txt

# Migrations uygula
echo "🗄️  Veritabanı migration'ları uygulanıyor..."
python manage.py migrate

# Static files topla
echo "📁 Static files toplanıyor..."
python manage.py collectstatic --noinput

echo "✅ Deployment hazırlıkları tamamlandı!"
echo "📝 Şimdi PythonAnywhere Web sekmesinden 'Reload' butonuna tıklayın."

