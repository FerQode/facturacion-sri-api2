# core>utils>sri_validators.py
import re

def validar_identificacion_ecuador(identificacion: str) -> bool:
    """
    Valida RUC y Cédula de Ecuador.
    Algoritmos: Módulo 10 (Cédula) y Módulo 11 (RUC Sociedades/Públicas).
    RFC: Ficha Técnica SRI Offline v2.32
    """
    if not identificacion: 
        return False

    identificacion = str(identificacion).strip()
    longitud = len(identificacion)
    
    # Validar longitud básica
    if longitud not in [10, 13]:
        return False
        
    # Validar que sean solo dígitos
    if not identificacion.isdigit():
        return False

    codigo_provincia = int(identificacion[0:2])
    
    # Validar código de provincia (01-24 y 30 para extrojeros)
    if not((1 <= codigo_provincia <= 24) or codigo_provincia == 30):
        return False
        
    tercer_digito = int(identificacion[2])
    
    # --- CASO 1: Cédula o RUC Natural (Módulo 10) ---
    if tercer_digito < 6:
        base = identificacion[0:10] if longitud == 13 else identificacion
        return _validar_modulo10(base) and (identificacion[10:13] == '001' if longitud == 13 else True)

    # --- CASO 2: RUC Público (Módulo 11, 3er digito = 6) ---
    elif tercer_digito == 6:
         if longitud != 13: return False
         return _validar_modulo11_publico(identificacion)

    # --- CASO 3: RUC Jurídico (Módulo 11, 3er digito = 9) ---
    elif tercer_digito == 9:
         if longitud != 13: return False
         return _validar_modulo11_juridico(identificacion)
         
    return False

def _validar_modulo10(cedula: str) -> bool:
    """Algoritmo Modulo 10 para Cédulas y RUC Naturales"""
    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    suma = 0
    
    for i in range(9):
        valor = int(cedula[i]) * coeficientes[i]
        if valor >= 10:
            valor -= 9
        suma += valor
        
    digito_verificador = int(cedula[9])
    
    residuo = suma % 10
    resultado = (10 - residuo) if residuo != 0 else 0
    
    return resultado == digito_verificador

def _validar_modulo11_publico(ruc: str) -> bool:
    """Algoritmo Modulo 11 para RUC Público (3er digito 6)"""
    # Dígito verificador está en la posición 9 (índice 8)
    coeficientes = [3, 2, 7, 6, 5, 4, 3, 2]
    suma = 0
    
    for i in range(8):
        suma += int(ruc[i]) * coeficientes[i]
        
    residuo = suma % 11
    resultado = (11 - residuo) if residuo != 0 else 0
    
    return resultado == int(ruc[8]) and ruc[9:13] == '0001'

def _validar_modulo11_juridico(ruc: str) -> bool:
    """Algoritmo Modulo 11 para RUC Jurídico (3er digito 9)"""
    # Dígito verificador está en la posición 10 (índice 9)
    coeficientes = [4, 3, 2, 7, 6, 5, 4, 3, 2]
    suma = 0
    
    for i in range(9):
        suma += int(ruc[i]) * coeficientes[i]
        
    residuo = suma % 11
    resultado = (11 - residuo) if residuo != 0 else 0
    
    return resultado == int(ruc[9]) and ruc[10:13] == '001'
