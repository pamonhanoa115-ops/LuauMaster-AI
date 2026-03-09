import os
import base64
from flask import Flask, render_template_string, request, jsonify
import google.generativeai as genai
from groq import Groq

# Configuração do App
app = Flask(__name__)

# --- VARIÁVEIS DE AMBIENTE (RENDER) ---
GEMINI_KEY = os.environ.get("CHAVE_API", "")
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")

# Inicialização do Gemini (Suporta Imagens/Visão)
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    # Modelo 1.5-flash é o melhor para visão e velocidade
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    gemini_model = None

# Inicialização do Groq (Apenas Texto - Velocidade Extrema)
groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None

# --- INTERFACE HTML/CSS/JS (ESTILO NEXOLABS) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LuauMaster Studio | Cloud AI</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- Firebase SDK para Login Google -->
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-auth-compat.js"></script>

    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
        
        body { 
            font-family: 'Plus Jakarta Sans', sans-serif; 
            background: #050505; 
            color: #eee; 
            overflow: hidden; 
        }

        .glass { 
            background: rgba(255, 255, 255, 0.02); 
            border: 1px solid rgba(255, 255, 255, 0.08); 
            backdrop-filter: blur(20px); 
        }

        /* Estilo para Blocos de Código Luau */
        code-block { 
            display: block; 
            background: #000; 
            padding: 20px; 
            border-radius: 12px; 
            color: #00ffa3; 
            font-family: 'Courier New', monospace; 
            margin: 15px 0; 
            border-left: 4px solid #00ffa3; 
            overflow-x: auto; 
            font-size: 0.9rem;
        }

        /* Scrollbar Personalizada */
        .chat-scroll {
            scrollbar-width: thin;
            scrollbar-color: #333 transparent;
        }
        .chat-scroll::-webkit-scrollbar { width: 5px; }
        .chat-scroll::-webkit-scrollbar-thumb { background: #222; border-radius: 10px; }

        .msg-user { background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); align-self: flex-end; }
        .msg-ai { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); align-self: flex-start; }

        .loading-dot { width: 6px; height: 6px; background: #00ffa3; border-radius: 50%; animation: blink 1.4s infinite; }
        @keyframes blink { 0%, 100% { opacity: 0.3; } 50% { opacity: 1; } }
    </style>
</head>
<body class="flex h-screen w-full">

    <!-- SIDEBAR (Histórico e Login) -->
    <aside class="w-72 bg-[#0a0a0a] border-right border-white/5 flex flex-col hidden md:flex">
        <div class="p-8 flex items-center gap-3">
            <div class="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center font-black shadow-lg shadow-blue-600/30">LM</div>
            <div class="font-black text-xl tracking-tighter italic">LUAU<span class="text-blue-500">MASTER</span></div>
        </div>

        <div class="flex-1 px-4 overflow-y-auto">
            <button onclick="window.location.reload()" class="w-full py-3 glass rounded-xl text-sm font-bold flex items-center justify-center gap-2 mb-6 hover:bg-white/5 transition-all">
                <i class="fa-solid fa-plus text-blue-500"></i> Novo Projeto
            </button>
            <div class="text-[10px] font-black text-gray-600 uppercase tracking-widest px-2 mb-2">Histórico Cloud</div>
            <div id="history-list" class="space-y-2 text-sm text-gray-500 italic px-2">
                Nenhum chat salvo...
            </div>
        </div>

        <div class="p-6 border-t border-white/5">
            <div id="user-profile" class="glass p-3 rounded-2xl flex items-center gap-3">
                <button onclick="loginGoogle()" id="btn-login" class="text-xs font-bold flex items-center gap-2">
                    <i class="fa-brands fa-google text-red-500"></i> Entrar com Google
                </button>
                <div id="user-data" class="hidden flex items-center gap-3">
                    <img id="user-pic" class="w-8 h-8 rounded-full border border-blue-500">
                    <span id="user-name" class="text-[10px] font-bold truncate max-w-[100px]">User</span>
                </div>
            </div>
        </div>
    </aside>

    <!-- ÁREA DE CHAT -->
    <main class="flex-1 flex flex-col relative">
        <header class="p-4 flex justify-between items-center glass border-b border-white/5 z-10">
            <div class="flex items-center gap-4">
                <div class="flex flex-col">
                    <span class="text-[10px] font-black text-emerald-500 uppercase tracking-widest">Servidor Online</span>
                    <span class="text-xs font-bold">Kernel v2.5 Flash</span>
                </div>
            </div>
            <select id="engine" class="bg-black/50 text-[10px] font-black p-2 rounded-lg border border-white/10 outline-none">
                <option value="gemini">Gemini (Vision Active)</option>
                <option value="groq">Groq (Turbo Speed)</option>
            </select>
        </header>

        <!-- CONTAINER DE MENSAGENS -->
        <div id="chat-messages" class="flex-1 overflow-y-auto p-6 md:p-12 space-y-8 chat-scroll">
            <div class="max-w-2xl mx-auto text-center py-20 animate-pulse">
                <h1 class="text-5xl font-black mb-4 tracking-tighter">O que vamos codar hoje?</h1>
                <p class="text-gray-500">Manda um script, uma dúvida ou um print do teu Output.</p>
            </div>
        </div>

        <!-- INPUT FIXO EM BAIXO -->
        <div class="p-6 md:p-10 w-full max-w-5xl mx-auto">
            <div class="glass rounded-3xl p-2 relative shadow-2xl">
                <!-- Preview de Imagem -->
                <div id="img-preview-box" class="hidden p-3 flex">
                    <div class="relative w-24 h-24 rounded-xl overflow-hidden border-2 border-emerald-500">
                        <img id="preview-src" class="w-full h-full object-cover">
                        <button onclick="cancelImage()" class="absolute top-1 right-1 bg-black/80 w-6 h-6 rounded-full text-xs">×</button>
                    </div>
                </div>

                <div class="flex items-end gap-2 p-2">
                    <label class="p-4 hover:bg-white/5 rounded-2xl cursor-pointer text-gray-500 transition-all">
                        <i class="fa-solid fa-image"></i>
                        <input type="file" id="file-input" class="hidden" accept="image/*" onchange="handleImage(this)">
                    </label>
                    <textarea id="prompt-input" class="flex-1 bg-transparent p-4 outline-none resize-none h-16 text-sm" placeholder="Escreve aqui o teu pedido..."></textarea>
                    <button onclick="sendMsg()" class="w-14 h-14 bg-blue-600 hover:bg-blue-500 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-600/30 transition-all">
                        <i class="fa-solid fa-arrow-up text-white"></i>
                    </button>
                </div>
            </div>
            <div class="text-center text-[9px] font-bold text-gray-700 mt-4 uppercase tracking-widest">Powered by Render Cloud & LuauMaster Kernel</div>
        </div>
    </main>

    <script>
        // --- Lógica de Interface ---
        let base64Image = null;

        function handleImage(input) {
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    base64Image = e.target.result.split(',')[1];
                    document.getElementById('preview-src').src = e.target.result;
                    document.getElementById('img-preview-box').classList.remove('hidden');
                };
                reader.readAsDataURL(input.files[0]);
            }
        }

        function cancelImage() {
            base64Image = null;
            document.getElementById('img-preview-box').classList.add('hidden');
            document.getElementById('file-input').value = "";
        }

        async function sendMsg() {
            const input = document.getElementById('prompt-input');
            const chat = document.getElementById('chat-messages');
            const text = input.value.trim();
            const engine = document.getElementById('engine').value;

            if(!text && !base64Image) return;

            // Adicionar msg do utilizador
            chat.innerHTML += `
                <div class="flex flex-col items-end gap-2">
                    <div class="msg-user p-5 rounded-3xl text-sm max-w-[80%] shadow-xl">${text}</div>
                    ${base64Image ? '<span class="text-[9px] text-blue-500 font-bold uppercase tracking-widest">[Imagem Enviada]</span>' : ''}
                </div>
            `;
            
            input.value = "";
            const loaderId = "loader-" + Date.now();
            chat.innerHTML += `<div id="${loaderId}" class="flex items-center gap-2 p-4 text-[10px] text-emerald-500 font-bold tracking-widest"><div class="loading-dot"></div> PROCESSANDO COM ${engine.toUpperCase()}...</div>`;
            chat.scrollTop = chat.scrollHeight;

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        prompt: text,
                        image: base64Image,
                        engine: engine
                    })
                });
                
                const data = await response.json();
                document.getElementById(loaderId).remove();
                cancelImage();

                chat.innerHTML += `
                    <div class="msg-ai p-8 rounded-3xl space-y-4 max-w-[95%] border-l-4 border-blue-600 shadow-2xl">
                        <div class="text-[10px] font-black text-blue-500 uppercase tracking-widest">LuauMaster AI Response</div>
                        <div class="text-gray-300 text-sm leading-relaxed">${data.response}</div>
                    </div>
                `;
                chat.scrollTop = chat.scrollHeight;
            } catch (err) {
                document.getElementById(loaderId).innerText = "❌ ERRO AO LIGAR AO SERVIDOR.";
            }
        }

        // --- Configuração Firebase (Opcional - Colar chaves se quiseres Login real) ---
        function loginGoogle() {
            alert("Configura as chaves do Firebase no código para ativar o Login Google!");
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_prompt = data.get('prompt', '')
    image_data = data.get('image')
    engine = data.get('engine', 'gemini')

    system_msg = "Você é o LuauMaster AI. Especialista em Roblox Luau. Regras: Use task.wait(), código limpo, e explique didaticamente. Se houver imagem, analise o código ou o erro nela."

    try:
        if engine == 'gemini' and gemini_model:
            # Lógica de Visão e Texto
            content = [f"{system_msg}\n\nPergunta: {user_prompt}"]
            if image_data:
                content.append({'mime_type': 'image/png', 'data': image_data})
            
            gen_res = gemini_model.generate_content(content)
            final_text = gen_res.text
        
        elif engine == 'groq' and groq_client:
            # Apenas Texto (Groq não suporta imagem diretamente neste setup)
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": user_prompt}]
            )
            final_text = completion.choices[0].message.content
        else:
            return jsonify({"response": "IA não configurada no Render."}), 500

        # Formatação de Código para HTML
        formatted = final_text.replace('```lua', '<code-block>').replace('```luau', '<code-block>').replace('```', '</code-block>')
        formatted = formatted.replace('\n', '<br>')
        
        return jsonify({"response": formatted})

    except Exception as e:
        return jsonify({"response": f"<b style='color:red'>ERRO:</b> {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)