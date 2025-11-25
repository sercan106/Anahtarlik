# PythonAnywhere WSGI Configuration Template
# Bu dosyayı PythonAnywhere Web sekmesindeki WSGI configuration file'a kopyalayın
# 
# KULLANIM:
# 1. PythonAnywhere dashboard'undan "Web" sekmesine gidin
# 2. "WSGI configuration file" linkine tıklayın
# 3. Aşağıdaki kodu kopyalayıp yapıştırın
# 4. 'username' kısmını kendi PythonAnywhere kullanıcı adınızla değiştirin
# 5. Proje path'ini doğru ayarlayın (genellikle /home/username/courseapp)
# 6. Virtual environment path'ini doğru ayarlayın

import os
import sys

# Proje dizinini path'e ekle
# ÖNEMLİ: 'username' kısmını kendi PythonAnywhere kullanıcı adınızla değiştirin!
# Eğer projeniz farklı bir dizindeyse, path'i ona göre ayarlayın
path = '/home/username/courseapp'
if path not in sys.path:
    sys.path.insert(0, path)

# Virtual environment'ı aktif et
# İki seçenek var:
# 1. Proje içinde venv kullanıyorsanız:
activate_this = '/home/username/courseapp/venv/bin/activate_this.py'
# 2. Virtualenvwrapper kullanıyorsanız:
# activate_this = '/home/username/.virtualenvs/venv/bin/activate_this.py'

if os.path.exists(activate_this):
    exec(open(activate_this).read(), {'__file__': activate_this})

# Django settings modülünü ayarla
os.environ['DJANGO_SETTINGS_MODULE'] = 'courseapp.settings'

# WSGI application'ı import et
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()



