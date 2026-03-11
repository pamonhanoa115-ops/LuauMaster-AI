import os
import base64
from flask import Flask, render_template_string, request, jsonify
from google import genai
from google.genai import types
from groq import Groq

# Configuração do App
app = Flask(__name__)

# --- VARIÁVEIS DE AMBIENTE (RENDER) ---
GEMINI_KEY = os.environ.get("CHAVE_API", "")
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")

# Inicialização dos Clientes com o novo SDK do Google (Gemini 2.0+)
client_gemini = None
if GEMINI_KEY:
    try:
        client_gemini = genai.Client(api_key=GEMINI_KEY)
    except Exception as e:
        print(f"Erro ao carregar Gemini: {e}")

client_groq = None
if GROQ_KEY:
    try:
        client_groq = Groq(api_key=GROQ_KEY)
    except Exception as e:
        print(f"Erro ao carregar Groq: {e}")

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
            white-space: pre-wrap;
        }

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

    <aside class="w-72 bg-[#0a0a0a] border-r border-white/5 flex flex-col hidden md:flex">
        <div class="p-8 flex items-center gap-3">
            <div class="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center font-black shadow-lg shadow-blue-600/30">LM</div>
            <div class="font-black text-xl tracking-tighter italic">LUAU<span class="text-blue-500">MASTER</span></div>
        </div>

        <div class="flex-1 px-4 overflow-y-auto">
            <button onclick="window.location.reload()" class="w-full py-3 glass rounded-xl text-sm font-bold flex items-center justify-center gap-2 mb-6 hover:bg-white/5 transition-all">
                <i class="fa-solid fa-plus text-blue-500"></i> Novo Projeto
            </button>
            <div class="text-[10px] font-black text-gray-600 uppercase tracking-widest px-2 mb-2 text-center">Controle de Versão v2.5</div>
        </div>

        <div class="p-6 border-t border-white/5">
            <div class="glass p-3 rounded-2xl flex flex-col items-center gap-2">
                <span class="text-[9px] text-gray-500 uppercase font-bold">Status da Cloud</span>
                <div class="flex items-center gap-2">
                    <div class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                    <span class="text-[10px] font-bold">Servidores Ativos</span>
                </div>
            </div>
        </div>
    </aside>

    <main class="flex-1 flex flex-col relative">
        <header class="p-4 flex justify-between items-center glass border-b border-white/5 z-10">
            <div class="flex items-center gap-4">
                <div class="flex flex-col">
                    <span class="text-[10px] font-black text-emerald-500 uppercase tracking-widest">IA Conectada</span>
                    <span class="text-xs font-bold">Kernel v2.0 Flash</span>
                </div>
            </div>
            <select id="engine" class="bg-black/50 text-[10px] font-black p-2 rounded-lg border border-white/10 outline-none">
                <option value="gemini">Gemini (Vision Active)</option>
                <option value="groq">Groq (Turbo Speed)</option>
            </select>
        </header>

        <div id="chat-messages" class="flex-1 overflow-y-auto p-6 md:p-12 space-y-8 chat-scroll">
            <div class="max-w-2xl mx-auto text-center py-20">
                <h1 class="text-5xl font-black mb-4 tracking-tighter">O que vamos codar hoje?</h1>
                <p class="text-gray-500">Manda um script, uma dúvida ou um print do teu Output.</p>
            </div>
        </div>

        <div class="p-6 md:p-10 w-full max-w-5xl mx-auto">
            <div class="glass rounded-3xl p-2 relative shadow-2xl">
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
        </div>
    </main>

    <script>
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

            chat.innerHTML += `
                <div class="flex flex-col items-end gap-2">
                    <div class="msg-user p-5 rounded-3xl text-sm max-w-[80%] shadow-xl">${text || "[Imagem para Análise]"}</div>
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
                        <div class="text-[10px] font-black text-blue-500 uppercase tracking-widest">LuauMaster Kernel Response</div>
                        <div class="text-gray-300 text-sm leading-relaxed">${data.response}</div>
                    </div>
                `;
                chat.scrollTop = chat.scrollHeight;
            } catch (err) {
                document.getElementById(loaderId).innerText = "❌ ERRO AO LIGAR AO SERVIDOR.";
            }
        }
        document.getElementById('prompt-input').addEventListener('keypress', (e) => { if(e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMsg(); } });
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

    sys_prompt = "Você é o LuauMaster AI. Expert em Roblox Luau. Use task.wait(), explique scripts e erros."

    try:
        if engine == 'gemini' and client_gemini:
            contents = [f"{sys_prompt}\n\nUsuário: {user_prompt}"]
            if image_data:
                contents.append(types.Part.from_bytes(data=base64.b64decode(image_data), mime_type="image/png"))
            
            # Usando modelo flash 2.0 que é o padrão atual do SDK para o que chamas de 2.5
            response = client_gemini.models.generate_content(model="gemini-2.5-flash", contents=contents)
            final_text = response.text
        
        elif engine == 'groq' and client_groq:
            completion = client_groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}]
            )
            final_text = completion.choices[0].message.content
        else:
            return jsonify({"response": "⚠️ Motor de IA não configurado no Render."}), 500

        # Formatação de Código para HTML
        formatted = final_text.replace('```lua', '<code-block>').replace('```luau', '<code-block>').replace('```', '</code-block>')
        formatted = formatted.replace('\n', '<br>')
        
        return jsonify({"response": formatted})

    except Exception as e:
        return jsonify({"response": f"<b style='color:red'>ERRO NO KERNEL:</b> {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)