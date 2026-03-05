from flask import Flask, render_template_string, request
from google import genai

app = Flask(__name__)

# Configuração da sua IA
CHAVE_API = "AIzaSyC_CFOZDIFufygft6PyLJfAeh043VK47u8"
client = genai.Client(api_key=CHAVE_API)

# O Visual do seu site (HTML + CSS)
HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>LuauMaster AI</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #1a1a1a; color: #ffffff; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .container { background-color: #2d2d2d; padding: 40px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); width: 80%; max-width: 600px; text-align: center; }
        h1 { color: #00ffa3; font-size: 2.5em; margin-bottom: 10px; }
        input[type="text"] { width: 100%; padding: 15px; margin: 20px 0; border: none; border-radius: 8px; background: #404040; color: white; box-sizing: border-box; }
        button { background-color: #00ffa3; color: #1a1a1a; border: none; padding: 15px 30px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 1em; }
        button:hover { background-color: #00cc82; }
        pre { background: #111; padding: 20px; border-radius: 8px; text-align: left; white-space: pre-wrap; word-wrap: break-word; color: #00ff00; margin-top: 20px; border-left: 5px solid #00ffa3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>LuauMaster AI</h1>
        <p>Gere scripts de Roblox instantaneamente</p>
        
        <form method="POST">
            <input type="text" name="pergunta" placeholder="Ex: Crie um script de corrida com checkpoint" required>
            <button type="submit">GERAR SCRIPT AGORA</button>
        </form>

        {% if resposta %}
            <pre>{{ resposta }}</pre>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    resposta = None
    if request.method == 'POST':
        pergunta = request.form['pergunta']
        try:
            # Chama a IA usando o modelo que funcionou antes
            response = client.models.generate_content(
                model="models/gemini-2.5-flash",
                contents=f"Você é o LuauMaster AI. Gere um script de Roblox: {pergunta}"
            )
            resposta = response.text
        except Exception as e:
            resposta = f"Erro ao gerar script: {e}"
    
    return render_template_string(HTML, resposta=resposta)

if __name__ == '__main__':
    app.run(debug=True)