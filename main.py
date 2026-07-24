from flask import Flask, request
from bs4 import BeautifulSoup
import requests

app = Flask(__name__)

@app.route('/solo-tigo')
def obtener_solo_tigo():
    url_videx = request.args.get('url')
    if not url_videx:
        return "Error: Falta la URL de Videx", 400

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }

    try:
        # 1. Descargamos la página original
        res = requests.get(url_videx, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')

        # 2. Corregimos las rutas relativas para que cargue los scripts de video
        if soup.head:
            base_tag = soup.new_tag('base', href='https://videx.lol/')
            soup.head.insert(0, base_tag)

        # 3. CSS MÁGICO: Oculta la interfaz y deja SOLO el reproductor al 100%
        css_limpiador = """
        <style>
            /* Ocultamos títulos, botones de Fanatiz, textos y encabezados */
            header, nav, footer, h1, h2, h3, p, span, .events, button {
                display: none !important;
            }
            body, html {
                margin: 0 !important;
                padding: 0 !important;
                width: 100% !important;
                height: 100% !important;
                background-color: #000 !important;
                overflow: hidden !important;
            }
            /* Hacemos que el contenedor del reproductor/video ocupe toda la pantalla */
            video, iframe, div[class*="player"], div[class*="video"] {
                display: block !important;
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100vw !important;
                height: 100vh !important;
                z-index: 999999 !important;
            }
        </style>
        """

        # 4. JS: Asegura la selección automática de Tigo Sports
        js_activar_tigo = """
        <script>
            window.addEventListener('DOMContentLoaded', function() {
                var elementos = document.querySelectorAll('button, a, div');
                for (var i = 0; i < elementos.length; i++) {
                    if (elementos[i].textContent.includes('TIGO SPORTS')) {
                        elementos[i].click();
                        break;
                    }
                }
            });
        </script>
        """

        # Inyectamos las reglas en el HTML
        if soup.head:
            soup.head.append(BeautifulSoup(css_limpiador, 'html.parser'))
            soup.head.append(BeautifulSoup(js_activar_tigo, 'html.parser'))

        return str(soup)

    except Exception as e:
        return f"Error al procesar el canal: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
          
