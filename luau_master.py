import os
import base64
import threading
import time
from flask import Flask, render_template_string, request, jsonify
from google import genai
from google.genai import types
from groq import Groq

app = Flask(__name__)

# --- CONFIGURAÇÃO DE CHAVES ---
GEMINI_KEY = os.environ.get("CHAVE_API", "")
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")

# --- AGENTIC SYSTEM PROMPT (O "CÉREBRO" DA NEXO) ---
NEXUS_SYSTEM_PROMPT = """
SISTEMA: NEXUS-LABS-ORCHESTRATOR v5.6
ROLE: Expert em Engenharia de Software para Roblox (Luau).

PROTOCOLOS OBRIGATÓRIOS:
1. [ANALYSIS]: Antes de codar, valide se o sistema precisa de Client, Server ou ModuleScript.
2. [MATH_OPTIMIZATION]: Use CFrames, Vector3 e Dot Products para evitar cálculos caros. 
3. [ROBLOX_BEST_PRACTICES]: 
   - NUNCA use 'wait()', use 'task.wait()'.
   - Use 'task.defer' ou 'task.spawn' para threads.
   - Sempre use 'Connect' em eventos e limpe-os se necessário.
   - Instance.new("Part") -- Correto (sem pai no 2º argumento).

4. [STRUCTURE]: Responda com uma breve explicação do plano e depois o código em blocos Markdown.
"""

# Inicialização dos Clientes
client_gemini = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
client_groq = Groq(api_key=GROQ_KEY) if GROQ_KEY else None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LuauMaster | Nexus Agentic</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&family=JetBrains+Mono&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; background: #020205; color: #e2e8f0; overflow: hidden; }
        .glass { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); backdrop-filter: blur(25px); }
        .nexus-code { 
            display: block; background: #000; padding: 24px; border-radius: 16px; 
            color: #10b981; font-family: 'JetBrains Mono', monospace; margin: 20px 0; 
            border-left: 4px solid #6366f1; overflow-x: auto; font-size: 0.85rem; line-height: 1.6;
        }
        .chat-scroll::-webkit-scrollbar { width: 4px; }
        .chat-scroll::-webkit-scrollbar-thumb { background: #1e1e2e; border-radius: 10px; }
        .msg-ai { background: rgba(99, 102, 241, 0.05); border: 1px solid rgba(99, 102, 241, 0.1); }
        .loading-bar { height: 2px; width: 0%; background: linear-gradient(90deg, #6366f1, #a855f7); transition: width 0.3s; }
    </style>
</head>
<body class="flex h-screen w-full">

    <aside class="w-80 bg-[#050508] border-r border-white/5 flex flex-col hidden lg:flex">
        <div class="p-8">
            <div class="flex items-center gap-3 mb-10">
                <div class="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center font-black shadow-lg shadow-indigo-600/20">N</div>
                <div class="font-black text-xl tracking-tighter italic">NEXUS<span class="text-indigo-500">CORE</span></div>
            </div>
            <nav class="space-y-2">
                <div class="p-4 glass rounded-2xl text-[10px] font-bold text-slate-500 uppercase tracking-widest">Sistemas Ativos</div>
                <div class="flex items-center gap-3 p-3 text-sm text-slate-400"><i class="fa-solid fa-microchip text-indigo-500"></i> Agentic v5.6</div>
                <div class="flex items-center gap-3 p-3 text-sm text-slate-400"><i class="fa-solid fa-bolt text-amber-500"></i> Low Latency</div>
            </nav>
        </div>
        <div class="mt-auto p-6 border-t border-white/5 text-[9px] text-slate-600 text-center font-mono uppercase tracking-widest">
            Powered by Gemini 2.5 Flash
        </div>
    </aside>

    <main class="flex-1 flex flex-col relative">
        <div id="progress" class="loading-bar fixed top-0 left-0 z-50"></div>
        
        <header class="p-4 flex justify-between items-center glass border-b border-white/5 z-10">
            <div class="flex items-center gap-4 pl-4">
                <div class="w-2 h-2 bg-indigo-500 rounded-full animate-ping"></div>
                <span class="text-[10px] font-black uppercase tracking-[0.2em] text-indigo-400">Neural Link Stable</span>
            </div>
            <select id="engine" class="bg-black/50 text-[10px] font-black p-2 px-4 rounded-full border border-white/10 outline-none hover:border-indigo-500/50 transition-all cursor-pointer">
                <option value="gemini">GEMINI 2.5 FLASH (NEXO)</option>
                <option value="groq">GROQ LLAMA 3.3 (TURBO)</option>
            </select>
        </header>

        <div id="chat-messages" class="flex-1 overflow-y-auto p-6 lg:p-12 space-y-10 chat-scroll">
            <div class="max-w-3xl mx-auto py-20 opacity-20">
                <h1 class="text-6xl font-black tracking-tighter mb-4">Ready for<br>Synthesis.</h1>
                <p class="font-mono text-sm">Waiting for agentic instructions...</p>
            </div>
        </div>

        <div class="p-6 w-full max-w-5xl mx-auto">
            <div class="glass rounded-[32px] p-2 relative shadow-2xl transition-all focus-within:border-indigo-500/30">
                <div id="img-preview-box" class="hidden p-4 flex">
                    <div class="relative w-20 h-20 rounded-2xl overflow-hidden border border-indigo-500">
                        <img id="preview-src" class="w-full h-full object-cover">
                        <button onclick="cancelImage()" class="absolute top-1 right-1 bg-black/80 w-5 h-5 rounded-full text-[10px]">×</button>
                    </div>
                </div>

                <div class="flex items-center gap-2 p-2">
                    <label class="w-12 h-12 flex items-center justify-center hover:bg-white/5 rounded-2xl cursor-pointer text-slate-500 transition-all">
                        <i class="fa-solid fa-paperclip"></i>
                        <input type="file" id="file-input" class="hidden" accept="image/*" onchange="handleImage(this)">
                    </label>
                    <input id="prompt-input" autocomplete="off" class="flex-1 bg-transparent p-4 outline-none text-sm" placeholder="O que vamos construir hoje?">
                    <button onclick="sendMsg()" id="send-btn" class="w-12 h-12 bg-indigo-600 hover:bg-indigo-500 rounded-2xl flex items-center justify-center transition-all shadow-lg shadow-indigo-600/20">
                        <i class="fa-solid fa-chevron-right text-white text-xs"></i>
                    </button>
                </div>
            </div>
        </div>
    </main>

    <script>
        let base64Image = null;
        const chat = document.getElementById('chat-messages');
        const input = document.getElementById('prompt-input');
        const progress = document.getElementById('progress');

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
            const text = input.value.trim();
            const engine = document.getElementById('engine').value;
            if(!text && !base64Image) return;

            input.value = "";
            progress.style.width = "30%";
            
            chat.innerHTML += `
                <div class="flex flex-col items-end gap-2 animate-in fade-in slide-in-from-right-4 duration-300">
                    <div class="bg-indigo-600/10 border border-indigo-600/20 p-5 rounded-[24px] rounded-tr-none text-sm max-w-[85%]">${text || "Análise de Imagem"}</div>
                </div>
            `;
            
            const loaderId = "loader-" + Date.now();
            chat.innerHTML += `<div id="${loaderId}" class="text-[9px] font-black text-indigo-500 uppercase tracking-widest animate-pulse">Consultando Agentes Nexus...</div>`;
            chat.scrollTop = chat.scrollHeight;

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ prompt: text, image: base64Image, engine: engine })
                });
                
                const data = await response.json();
                progress.style.width = "100%";
                setTimeout(() => progress.style.width = "0%", 500);
                
                document.getElementById(loaderId).remove();
                cancelImage();

                chat.innerHTML += `
                    <div class="msg-ai p-8 rounded-[32px] rounded-tl-none space-y-6 max-w-[95%] shadow-2xl border border-white/5 animate-in fade-in slide-in-from-left-4 duration-500">
                        <div class="flex items-center gap-3">
                            <div class="w-6 h-6 bg-indigo-500/20 rounded-md flex items-center justify-center text-[10px] font-bold text-indigo-400">NX</div>
                            <span class="text-[9px] font-black text-indigo-500 uppercase tracking-[0.2em]">Protocolo Finalizado</span>
                        </div>
                        <div class="text-slate-300 text-sm leading-relaxed font-light">${data.response}</div>
                    </div>
                `;
                chat.scrollTop = chat.scrollHeight;
            } catch (err) {
                document.getElementById(loaderId).innerText = "❌ FALHA NA LIGAÇÃO AOS AGENTES.";
            }
        }
        input.addEventListener('keypress', (e) => { if(e.key === 'Enter') sendMsg(); });
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

    try:
        if engine == 'gemini' and client_gemini:
            # Integração do Kernel Nexo no Gemini 2.5
            contents = [f"{NEXUS_SYSTEM_PROMPT}\n\nUSER_REQUEST: {user_prompt}"]
            if image_data:
                contents.append(types.Part.from_bytes(data=base64.b64decode(image_data), mime_type="image/png"))
            
            response = client_gemini.models.generate_content(
                model="gemini-2.5-flash", 
                contents=contents,
                config=types.GenerateContentConfig(temperature=0.3)
            )
            final_text = response.text
        
        elif engine == 'groq' and client_groq:
            completion = client_groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": NEXUS_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            final_text = completion.choices[0].message.content
        else:
            return jsonify({"response": "⚠️ Motor de IA não detetado ou API Key em falta."}), 500

        # Formatação de Código estilo NexoLabs
        # Substitui os blocos de markdown por divs formatadas para a UI
        import re
        
        # Converte blocos de código markdown para a classe nexus-code
        def code_replacer(match):
            code = match.group(2).strip()
            return f'<div class="nexus-code">{code}</div>'
        
        formatted = re.sub(r'```(lua|luau|json|text)?\n([\s\S]*?)\n```', code_replacer, final_text)
        formatted = formatted.replace('\n', '<br>')
        
        return jsonify({"response": formatted})

    except Exception as e:
        return jsonify({"response": f"<div class='p-4 border border-red-500/20 bg-red-500/5 text-red-400 text-xs rounded-xl'><b>KERNEL ERROR:</b> {str(e)}</div>"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)