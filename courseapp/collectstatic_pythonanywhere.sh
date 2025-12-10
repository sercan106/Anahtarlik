#!/bin/bash
# Static Files Toplama Scripti - PythonAnywhere için
# Kullanım: bash collectstatic_pythonanywhere.sh

echo "📦 Static files toplanıyor..."

cd ~/courseapp || exit

# Virtual environment'i aktif et
source venv/bin/activate

# Static files klasörünü oluştur
mkdir -p staticfiles

# Collectstatic komutunu çalıştır
python manage.py collectstatic --noinput

echo "✅ Static files toplama tamamlandı!"
echo "📁 Dosyalar: ~/courseapp/staticfiles/"
echo ""
echo "🔍 Kontrol:"
echo "ls -la ~/courseapp/staticfiles/"

