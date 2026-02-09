import os
import sys
import traceback

sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

try:
    import django
    django.setup()
    from adapters.infrastructure.models import EventoModel
    print("Success importing EventoModel")
except Exception:
    with open("traceback.log", "w") as f:
        traceback.print_exc(file=f)
    print("Failed. Traceback written to traceback.log")
