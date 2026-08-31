import base64
import json
import re
import requests

# --- CONFIGURACIÓN DE APPS Y REPOSITORIOS GITHUB ---
CONFIGS = {
    'playPremium': {
        'name': 'PLAY TV PREMIUM',
        'token': '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',
        'owner': 'dxrioacxta',
        'repo': 'playprem',
        'path': 'canales.json'
    },
    'zuperPlay': {
        'name': 'ZUPER PLAY',
        'token': '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',
        'owner': 'dxrioacxta',
        'repo': 'playprem',
        'path': 'tv1.json'
    },
    'fieraTv': {
        'name': 'FIERA TV',
        'token': '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',
        'owner': 'DxrioOFC',
        'repo': 'FieraTv',
        'path': 'fieratv.json'
    }
}

# --- CONFIGURACIÓN DE PLAY TV (API MYSQL / CPANEL) ---
# Coloca aquí la URL web exacta donde subiste tu archivo PHP del panel (ejemplo: https://tuservidor.com/panel.php)
PLAY_TV_URL = "https://fullplay.com.py/api/flowapi.php"
PLAY_TV_USER = "DX-ADMIN"

URL_GITHUB_FUENTE = "https://raw.githubusercontent.com/americoParkSun/bm-4V7B91WziXP69YcpULMA3GStvxqGATvQnTFUY/refs/heads/main/1.json"
CLAVE = "Gta123"

# Patrón para detectar la Base + Token Flow de la ruta /live/
FLOW_PATTERN = re.compile(r"(https?://[^/]+?/tok_[^/]+?)(/live/.*)")

def decrypt_xor_base64(encrypted_text, key):
    if not encrypted_text or not isinstance(encrypted_text, str):
        return encrypted_text
    try:
        encrypted_bytes = base64.b64decode(encrypted_text, validate=True)
        decrypted_chars = [chr(byte ^ ord(key[i % len(key)])) for i, byte in enumerate(encrypted_bytes)]
        resultado = "".join(decrypted_chars)
        if "http" in resultado or "/" in resultado:
            return resultado
        return encrypted_text
    except Exception:
        return encrypted_text

def desencriptar_todo_recursivo(objeto, key):
    if isinstance(objeto, dict):
        nuevo_diccionario = {}
        if "category" in objeto and any(x in str(objeto["category"]).upper() for x in ["PELICULA", "MOVIE", "SERIE"]):
            return None
        
        for k, v in objeto.items():
            if k in ["url", "drm_license_uri"] and isinstance(v, str):
                nuevo_diccionario[k] = decrypt_xor_base64(v, key)
            else:
                valor_procesado = desencriptar_todo_recursivo(v, key)
                if valor_procesado is not None:
                    nuevo_diccionario[k] = valor_procesado
        return nuevo_diccionario

    elif isinstance(objeto, list):
        return [elem for elem in (desencriptar_todo_recursivo(e, key) for e in objeto) if elem is not None]

    return objeto

def extraer_token_flow(objeto):
    """Busca y extrae el primer token/base URL de Flow del JSON desencriptado."""
    if isinstance(objeto, str):
        match = FLOW_PATTERN.search(objeto)
        if match:
            return match.group(1)
    elif isinstance(objeto, dict):
        for v in objeto.values():
            token = extraer_token_flow(v)
            if token:
                return token
    elif isinstance(objeto, list):
        for elem in objeto:
            token = extraer_token_flow(elem)
            if token:
                return token
    return None

def actualizar_urls_flow(objeto, nuevo_base_token):
    """Reemplaza la base del token Flow conservando la ruta /live/..."""
    modificados = []

    def _procesar(obj, nombre_canal="Desconocido"):
        if isinstance(obj, dict):
            nombre = obj.get("name") or obj.get("title") or obj.get("nombre") or nombre_canal
            nuevo_dict = {}
            for k, v in obj.items():
                if isinstance(v, str):
                    match = FLOW_PATTERN.search(v)
                    if match:
                        path_canal = match.group(2)
                        url_nueva = f"{nuevo_base_token}{path_canal}"
                        nuevo_dict[k] = url_nueva
                        modificados.append((nombre, k, url_nueva))
                    else:
                        nuevo_dict[k] = v
                else:
                    nuevo_dict[k] = _procesar(v, nombre)
            return nuevo_dict

        elif isinstance(obj, list):
            return [_procesar(elem, nombre_canal) for elem in obj]
        
        return obj

    json_actualizado = _procesar(objeto)
    return json_actualizado, modificados

def actualizar_en_github(config, nuevo_json):
    """Obtiene y actualiza rápidamente un archivo en GitHub vía API REST."""
    url_api = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/contents/{config['path']}"
    headers = {
        "Authorization": f"token {config['token']}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 1. Obtener SHA del archivo actual
    res = requests.get(url_api, headers=headers)
    if res.status_code != 200:
        print(f"❌ Error al consultar GitHub ({config['name']}): Código {res.status_code}")
        return

    sha = res.json()["sha"]
    contenido_actual = res.json().get("content", "")

    # 2. Reemplazar token en el JSON obtenido del repositorio
    try:
        json_actual = json.loads(base64.b64decode(contenido_actual).decode('utf-8'))
    except Exception as e:
        print(f"❌ Error al decodificar JSON de {config['name']}: {e}")
        return

    json_actualizado, reemplazos = actualizar_urls_flow(json_actual, nuevo_json)

    if not reemplazos:
        print(f"⚠️ No se encontraron enlaces de Flow para actualizar en {config['name']}.")
        return

    # 3. Subir el archivo actualizado a GitHub
    json_bytes = json.dumps(json_actualizado, indent=4, ensure_ascii=False).encode('utf-8')
    content_b64 = base64.b64encode(json_bytes).decode('utf-8')

    payload = {
        "message": "Actualización automática de Token Flow",
        "content": content_b64,
        "sha": sha
    }

    put_res = requests.put(url_api, headers=headers, json=payload)
    if put_res.status_code in [200, 201]:
        print(f"\n✅ ¡{config['name']} actualizado con éxito en GitHub!")
        print(f"📊 Canales actualizados ({len(reemplazos)}):")
        for canal, campo, url in reemplazos:
            print(f"   • [{canal}] ({campo}) -> {url[:70]}...")
    else:
        print(f"❌ Error al actualizar {config['name']} en GitHub: {put_res.status_code}")

def actualizar_play_tv(url_php, user_login, nuevo_token):
    """Actualiza la BD MySQL de PLAY TV directamente mediante la API de su panel PHP."""
    print(f"\n🔄 Procesando PLAY TV (Vía API MySQL / PHP)...")
    
    session = requests.Session()
    try:
        # 1. Autenticación en la sesión PHP
        res_login = session.post(url_php, json={"user_login": user_login}, timeout=10)
        if res_login.status_code != 200:
            print(f"❌ Error de autenticación en PLAY TV: Código {res_login.status_code}")
            return

        login_data = res_login.json()
        if login_data.get("status") != "success":
            print(f"❌ Autenticación rechazada en PLAY TV: {login_data.get('message')}")
            return

        # 2. Envío del token extraído para actualizar la Base de Datos
        payload = {
            "action": "manual",
            "token": nuevo_token,
            "portal": ""
        }
        res_update = session.post(url_php, json=payload, timeout=15)
        
        if res_update.status_code == 200:
            data = res_update.json()
            if data.get("status") == "success":
                canales = data.get("canales", 0)
                portales = data.get("portales", 0)
                print(f"✅ ¡PLAY TV actualizado con éxito en la Base de Datos!")
                print(f"📊 Filas actualizadas en MySQL:")
                print(f"   • Canales actualizados: {canales} filas")
                if portales > 0:
                    print(f"   • Portales actualizados: {portales} filas")
                print(f"   • Token asignado: {data.get('token_usado')}")
            else:
                print(f"❌ Error reportado por el panel PLAY TV: {data.get('message')}")
        else:
            print(f"❌ Error en la solicitud de actualización: Código {res_update.status_code}")

    except Exception as e:
        print(f"❌ Error al conectar con la API de PLAY TV: {e}")

# --- EJECUCIÓN PRINCIPAL ---
def ejecutar_script():
    print("🚀 Descargando archivo fuente desde GitHub...")
    response = requests.get(URL_GITHUB_FUENTE)
    if response.status_code != 200:
        print(f"Error al descargar fuente: {response.status_code}")
        return

    print("🔓 Desencriptando contenido JSON...")
    data_desencriptada = desencriptar_todo_recursivo(response.json(), CLAVE)

    print("🔍 Extrayendo Token de Flow...")
    nuevo_token = extraer_token_flow(data_desencriptada)

    if not nuevo_token:
        print("❌ No se encontró ningún token de Flow válido en el archivo fuente.")
        return

    print("\n" + "="*80)
    print(f"🔑 TOKEN DE FLOW EXTRAÍDO:")
    print(f"{nuevo_token}")
    print("="*80 + "\n")

    # 1. Actualizar las 3 aplicaciones hospedadas en GitHub
    for key, config in CONFIGS.items():
        print(f"\n🔄 Procesando {config['name']}...")
        actualizar_en_github(config, nuevo_token)

    # 2. Actualizar PLAY TV mediante API PHP (MySQL)
    if "tu-dominio.com" in PLAY_TV_URL:
        print("\n⚠️ IMPORTANTE: Recuerda cambiar 'https://tu-dominio.com/panel.php' en la variable PLAY_TV_URL por la URL real de tu panel.")
    else:
        actualizar_play_tv(PLAY_TV_URL, PLAY_TV_USER, nuevo_token)

if __name__ == "__main__":
    ejecutar_script()
