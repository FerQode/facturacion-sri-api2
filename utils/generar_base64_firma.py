# utils/generar_base64_firma.py
import base64
import os
import sys

def generar_base64_firma(ruta_archivo):
    """
    Lee un archivo .p12 y devuelve su representación en Base64.
    """
    if not os.path.exists(ruta_archivo):
        print(f"❌ Error: No se encontró el archivo en {ruta_archivo}")
        return

    try:
        with open(ruta_archivo, "rb") as firma_file:
            encoded_string = base64.b64encode(firma_file.read()).decode('utf-8')
            
        print("\n✅ Firma convertida a Base64 exitosamente!")
        print("="*60)
        print("Copia el siguiente valor en tu variable de entorno SRI_FIRMA_BASE64:")
        print("="*60)
        print(encoded_string)
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error al convertir: {e}")

if __name__ == "__main__":
    # Ruta por defecto según tu estructura
    # utils/generar_base64_firma.py -> ../secrets/el_arbolito.p12
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta_p12 = os.path.join(base_dir, 'secrets', 'el_arbolito.p12')
    
    # Permitir pasar ruta como argumento
    if len(sys.argv) > 1:
        ruta_p12 = sys.argv[1]
        
    print(f"Buscando firma en: {ruta_p12}")
    generar_base64_firma(ruta_p12)
