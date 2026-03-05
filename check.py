import os
from flask import Flask, render_template_string, request
import google.generativeai as genai

app = Flask(__name__)

# --- SEGURANÇA E CONFIGURAÇÃO ---
# Pega a chave do "Environment" do Render para não vazar no GitHub
api_key = os.environ.get("CHAVE_API")
genai.configure(api_key=api_key)

# Configuração do "DNA" da IA (Instrução de Sistema)
instrucao_sistema = (
    "Você é o LuauMaster AI, instrutor oficial de Roblox Luau. "
    "Sua missão é ensinar e gerar scripts de forma didática e eficiente."
)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=instrucao_sistema
)

# Visual do site
HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>LuauMaster AI - Web</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #1a1a1a; color: #ffffff; display: flex; justify-content: center; padding: 20px; }
        .container { background-color: #2d2d2d; padding: 30px; border-radius: 15px; width: 100%; max-width: 700px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        h1 { color: #00ffa3; text-align: center; }
        input[type="text"] { width: 100%; padding: 15px; border-radius: 8px; border: none; background: #404040; color: white; margin-bottom: 10px; box-sizing: border-box;}
        button { width: 100%; background-color: #00ffa3; color: #1a1a1a; border: none; padding: 15px; border-radius: 8px; font-weight: bold; cursor: pointer; }
        .chat-box { background: #111; padding: 20px; border-radius: 8px; margin-top: 20px; min-height: 100px; border-left: 5px solid #00ffa3; white-space: pre-wrap; }
        .error { color: #ff4444; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 LuauMaster AI</h1>
        <p style="text-align:center">O instrutor de Roblox na nuvem</p>
        
        <form method="POST">
            <input type="text" name="pergunta" placeholder="O que vamos programar hoje?" required autofocus>
            <button type="submit">GERAR RESPOSTA</button>
        </form>

        {% if resposta %}
            <div class="chat-box">{{ resposta }}</div>
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
            # No plano Web simples, usamos o generate_content com a instrução de sistema já embutida
            response = model.generate_content(pergunta)
            resposta = response.text
        except Exception as e:
            resposta = f"<span class='error'>❌ Erro: {e}</span>"
    
    return render_template_string(HTML, resposta=resposta)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)