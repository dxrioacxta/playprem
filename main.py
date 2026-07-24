from flask import Flask, request, redirect
import requests
import re

app = Flask(__name__)

@app.route('/solo-tigo')
def extraer_m3u8():
    url_videx = request.args.get('url')
    if not url_videx:
        return "Falta la URL de Videx", 400

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': 'https://videx.lol/'
    }

    try:
        # 1. Obtenemos el HTML de la página de Videx
        respuesta = requests.get(url_videx, headers=headers, timeout=10)
        html = respuesta.text

        # 2. Buscamos mediante Expresiones Regulares la URL directa del .m3u8 (incluyendo su token)
        patrones = [
            r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*',
            r'https?://[^\s"\'<>]+/live/[^\s"\'<>]*'
        ]

        link_m3u8 = None
        for patron in patrones:
            coincidencias = re.findall(patron, html)
            if coincidencias:
                # Priorizamos el enlace que contenga la señal viva
                link_m3u8 = coincidencias[0]
                break

        # 3. Si encontramos el enlace .m3u8 fresco con token, redirigimos directamente la señal
        if link_m3u8:
            return redirect(link_m3u8, code=302)
        else:
            return "No se pudo extraer el enlace m3u8", 404

    except Exception as e:
        return f"Error al procesar la señal: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
    
