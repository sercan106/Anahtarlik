#!/bin/bash
# PythonAnywhere Deployment Script
# Bu script projeyi PythonAnywhere'e deploy etmek için gerekli komutları çalıştırır

echo "🚀 PythonAnywhere Deployment Script Başlatılıyor..."

# Proje dizinine git
cd ~/courseapp || exit

# Virtual environment'i aktif et
echo "📦 Virtual environment aktif ediliyor..."
source venv/bin/activate

# Bağımlılıkları yükle
echo "📥 Bağımlılıklar yükleniyor..."
pip install --upgrade pip
pip install -r requirements.txt

# Migration'ları çalıştır
echo "🗄️  Veritabanı migration'ları çalıştırılıyor..."
python manage.py migrate

# Static files'ı topla
echo "📦 Static files toplanıyor..."
python manage.py collectstatic --noinput

# Media klasörünü oluştur (yoksa)
echo "📁 Media klasörü kontrol ediliyor..."
mkdir -p media
mkdir -p staticfiles
mkdir -p logs

# İzinleri ayarla
echo "🔐 Dosya izinleri ayarlanıyor..."
chmod 755 media
chmod 755 staticfiles
chmod 755 logs

echo "✅ Deployment tamamlandı!"
echo ""
echo "📝 Sonraki adımlar:"
echo "1. Web app ayarlarını kontrol edin (Static/Media mapping)"
echo "2. Web app'i reload edin"
echo "3. Siteyi test edin: https://yourusername.pythonanywhere.com"
echo ""
echo "🔍 Hata kontrolü için:"
echo "- Error log: Web sekmesi > Error log"
echo "- Django log: ~/courseapp/logs/django.log"

