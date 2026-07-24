from flask import Flask, request, Response
import requests

app = Flask(__name__)

@app.route('/solo-tigo')
def solo_tigo():
    url_videx = request.args.get('url')
    if not url_videx:
        return "Falta la URL", 400

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        # Descargamos la página original de Videx
        resp = requests.get(url_videx, headers=headers)
        html = resp.text

        # Agregamos la base para que carguen los estilos y scripts de la web
        html = html.replace('<head>', '<head><base href="https://videx.lol/">')

        # Script y estilos limpios para hacer clic en Tigo y ocultar Fanatiz
        script_inteligente = """
        <style>
            /* Ocultamos solo la cabecera y elementos innecesarios, sin romper el reproductor */
            header, nav, footer, .events, .navbar { 
                display: none !important; 
            }
            body {
                background-color: #000 !important;
                margin: 0 !important;
                padding: 0 !important;
            }
        </style>
        <script>
            window.addEventListener('load', function() {
                // Esperamos medio segundo a que cargue la página
                setTimeout(function() {
                    var elementos = document.querySelectorAll('button, a, div, span');
                    for (var i = 0; i < elementos.length; i++) {
                        // Buscamos el texto TIGO SPORTS y le hacemos clic automático
                        if (elementos[i].innerText && elementos[i].innerText.toUpperCase().includes('TIGO SPORTS')) {
                            elementos[i].click();
                            break;
                        }
                    }

                    // Ocultamos los botones de Fanatiz para que no saturen
                    setTimeout(function() {
                        var todos = document.querySelectorAll('*');
                        for (var j = 0; j < todos.length; j++) {
                            let texto = todos[j].innerText || '';
                            if (texto.toUpperCase().includes('FANATIZ') && todos[j].children.length === 0) {
                                let padre = todos[j].closest('button') || todos[j].closest('a') || todos[j].closest('div');
                                if (padre) padre.style.display = 'none';
                            }
                        }
                    }, 800);

                }, 500);
            });
        </script>
        """

        # Inyectamos el script antes de cerrar el body
        html = html.replace('</body>', script_inteligente + '</body>')
        return Response(html, content_type='text/html')

    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
