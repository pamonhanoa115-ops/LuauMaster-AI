import os
from flask import Flask, render_template_string, request
import google.generativeai as genai

app = Flask(__name__)

# --- CONFIGURAÇÃO SEGURA ---
# Busca a chave nas variáveis de ambiente do Render
CHAVE_API = os.environ.get("CHAVE_API")
genai.configure(api_key=CHAVE_API)

# Instrução de Sistema para manter a IA no personagem
instrucao_sistema = (
    "Você é o LuauMaster AI, instrutor oficial de Roblox Luau. "
    "Sua missão é ensinar e gerar scripts de forma didática e eficiente."
)

# Inicializa o modelo
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=instrucao_sistema
)

# --- INTERFACE PREMIUM (ESTILO NEXOLABS) ---
HTML_PREMIUM = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LuauMaster Studio Premium</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        body { font-family: 'Inter', sans-serif; transition: background 0.3s; margin: 0; }
        .dark-theme { --bg: #0f0f0f; --sidebar: #181818; --card: #1e1e1e; --text: #ffffff; --border: #2a2a2a; }
        .light-theme { --bg: #f7f7f7; --sidebar: #ffffff; --card: #ffffff; --text: #1a1a1a; --border: #e2e8f0; }
        .theme-container { background-color: var(--bg); color: var(--text); }
        .sidebar { background-color: var(--sidebar); border-right: 1px solid var(--border); }
        .card-input { background-color: var(--card); border: 1px solid var(--border); }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-thumb { background: #333; border-radius: 10px; }
        .fade-in { animation: fadeIn 0.5s ease-in; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        code-block { display: block; background: #000; padding: 15px; border-radius: 8px; color: #00ffa3; font-family: monospace; margin-top: 10px; border-left: 4px solid #00ffa3; overflow-x: auto; }
    </style>
</head>
<body class="dark-theme theme-container h-screen flex overflow-hidden">
    <!-- SIDEBAR -->
    <aside class="sidebar w-64 flex-shrink-0 flex flex-col p-4 space-y-6">
        <div class="flex items-center gap-3 px-2">
            <div class="w-8 h-8 bg-blue-600 rounded flex items-center justify-center text-white font-bold text-xs">LM</div>
            <span class="font-bold text-lg tracking-tight">LuauMaster</span>
        </div>
        <nav class="flex-1 space-y-1 overflow-y-auto">
            <button onclick="window.location.href='/'" class="w-full flex items-center gap-3 p-2.5 hover:bg-white/5 rounded-lg transition-all text-sm">
                <i class="fa-solid fa-plus opacity-70"></i> <span>New task</span>
            </button>
            <div class="pt-6">
                <p class="text-[10px] font-bold text-gray-500 uppercase px-2 mb-2">Projects</p>
                <div class="space-y-1">
                    <div class="flex items-center gap-3 p-2 hover:bg-white/5 rounded-lg cursor-pointer text-sm">
                        <i class="fa-solid fa-folder text-blue-400"></i> <span>Roblox Studio</span>
                    </div>
                    <div class="flex items-center gap-3 p-2 hover:bg-white/5 rounded-lg cursor-pointer text-sm">
                        <i class="fa-solid fa-folder text-green-400"></i> <span>Modded Games</span>
                    </div>
                </div>
            </div>
        </nav>
        <div class="border-t border-white/5 pt-4 flex items-center justify-between">
            <div class="flex gap-4 text-gray-400 text-sm px-2">
                <i class="fa-solid fa-sun hover:text-white cursor-pointer" onclick="toggleTheme()"></i>
                <i class="fa-solid fa-gear hover:text-white cursor-pointer"></i>
            </div>
            <i class="fa-solid fa-right-from-bracket text-gray-400 hover:text-white cursor-pointer"></i>
        </div>
    </aside>

    <!-- MAIN CONTENT -->
    <main class="flex-1 flex flex-col relative overflow-y-auto">
        <header class="flex items-center justify-between p-4 px-6 sticky top-0 bg-transparent backdrop-blur-md z-10">
            <div class="flex items-center gap-2 text-sm font-medium hover:bg-white/5 p-2 rounded-lg cursor-pointer">
                <i class="fa-solid fa-robot text-blue-500"></i> LuauMaster 2.0 Flash <i class="fa-solid fa-chevron-down text-[10px]"></i>
            </div>
            <div class="w-8 h-8 rounded-full bg-red-900 border border-red-500 flex items-center justify-center text-[10px]">N</div>
        </header>

        <div class="flex-1 flex flex-col items-center py-10 px-4 max-w-4xl mx-auto w-full">
            {% if not resposta %}
            <div class="text-center mb-10 fade-in pt-20">
                <h1 class="text-5xl font-serif mb-6 opacity-90">What can I do for you?</h1>
            </div>
            {% endif %}

            <form action="/" method="POST" class="w-full card-input rounded-2xl shadow-2xl overflow-hidden focus-within:ring-1 ring-blue-500 transition-all mb-8">
                <textarea name="pergunta" class="w-full bg-transparent p-5 outline-none resize-none h-32 text-lg" placeholder="Descreva o script que você precisa..." required autofocus></textarea>
                <div class="flex items-center justify-between p-3 border-t border-white/5 bg-black/10">
                    <div class="flex items-center gap-4 text-gray-500 text-sm px-2">
                        <i class="fa-solid fa-plus hover:text-white cursor-pointer"></i>
                        <i class="fa-solid fa-globe hover:text-white cursor-pointer"></i>
                    </div>
                    <button type="submit" class="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center hover:bg-blue-500 transition-colors">
                        <i class="fa-solid fa-arrow-up text-white"></i>
                    </button>
                </div>
            </form>

            {% if resposta %}
            <div class="w-full fade-in pb-20">
                <div class="p-6 rounded-xl bg-white/5 border border-white/10 text-sm leading-relaxed">
                    <div class="prose prose-invert max-w-none">
                        {{ resposta | safe }}
                    </div>
                </div>
                <button onclick="window.location.href='/'" class="mt-6 text-blue-500 hover:underline text-sm">
                    <i class="fa-solid fa-rotate-left mr-2"></i> Iniciar nova tarefa
                </button>
            </div>
            {% endif %}
        </div>
    </main>

    <script>
        function toggleTheme() {
            const body = document.body;
            body.classList.toggle('dark-theme');
            body.classList.toggle('light-theme');
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    resposta = None
    if request.method == 'POST':
        pergunta = request.form['pergunta']
        try:
            response = model.generate_content(pergunta)
            # Formata blocos de código markdown para blocos visuais HTML
            texto_formatado = response.text.replace('```lua', '<code-block>').replace('```', '</code-block>')
            resposta = texto_formatado.replace('\n', '<br>')
        except Exception as e:
            resposta = f"<div style='color:#ff4444'>❌ Erro: {e}</div>"
    
    return render_template_string(HTML_PREMIUM, resposta=resposta)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)