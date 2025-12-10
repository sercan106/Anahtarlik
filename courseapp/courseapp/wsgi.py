"""
WSGI config for courseapp project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import sys

# PythonAnywhere için path ekleme
# Proje dizinini path'e ekle
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path:
    sys.path.insert(0, path)

# PythonAnywhere'de virtual environment'i aktif et (opsiyonel)
# Eğer virtual environment kullanıyorsanız, aşağıdaki satırları aktif edin:
# activate_this = os.path.join(path, 'venv', 'bin', 'activate_this.py')
# if os.path.exists(activate_this):
#     with open(activate_this) as file_:
#         exec(file_.read(), {'__file__': activate_this})

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'courseapp.settings')

application = get_wsgi_application()
