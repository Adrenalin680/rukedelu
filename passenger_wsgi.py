import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# Для Beget - указываем правильные пути
import site
site.addsitedir(os.path.join(os.path.dirname(__file__), 'venv/lib/python3.9/site-packages'))

# Активируем виртуальное окружение
activate_this = os.path.join(os.path.dirname(__file__), 'venv/bin/activate_this.py')
if os.path.exists(activate_this):
    with open(activate_this) as f:
        exec(f.read(), {'__file__': activate_this})

from app import app as application
