#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

def _configure_gtk3_windows():
    """
    Fix crítico para WeasyPrint en Windows.
    Busca e inyecta las DLLs de GTK3 en el PATH antes de arrancar Django.
    """
    if os.name != 'nt':
        return

    posibles_rutas = [
        r"C:\Program Files\GTK3-Runtime Win64\bin",
        r"C:\Program Files (x86)\GTK3-Runtime Win64\bin",
        r"C:\GTK3-Runtime Win64\bin",
    ]
    
    gtk_encontrado = False
    for path in posibles_rutas:
        if os.path.exists(path):
            try:
                # Python 3.8+ requiere add_dll_directory para cargar DLLs externas
                os.add_dll_directory(path)
                # Backup para sistemas legacy o entornos extraños
                os.environ['PATH'] = path + os.pathsep + os.environ['PATH']
                gtk_encontrado = True
                break
            except Exception:
                pass 
    
    if not gtk_encontrado and 'runserver' in sys.argv:
        print("⚠️  ADVERTENCIA WINDOWS: No se encontró GTK3 Runtime.")
        print("    WeasyPrint (para PDFs) podría fallar. Asegúrate de instalarlo.")

def main():
    """Run administrative tasks."""
    # 1. Inyectar dependencias del sistema (Windows) antes de cargar Django
    _configure_gtk3_windows()

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
