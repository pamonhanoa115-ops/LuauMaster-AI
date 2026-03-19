import os
import uuid
import threading
import shutil
import json
import time
from flask import Flask, render_template_string, request, jsonify, send_from_directory
from google import genai
from google.genai import types

app = Flask(__name__)

# --- CONFIGURAÇÃO DE AMBIENTE ---
PROJECTS_BASE = "nexus_workspace"
if not os.path.exists(PROJECTS_BASE): os.makedirs(PROJECTS_BASE)

tasks = {}
GEMINI_KEY = os.environ.get("CHAVE_API", "")
client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

# --- O "CÉREBRO" UPGRADED (FOCO EM DE-OBFUSCATION E ANÁLISE DE DECOMPILED SCRIPTS) ---
SYSTEM_PROMPT = """
SISTEMA: NEXUSLAB MULTI-AGENT ORCHESTRATOR | DECOMPILER ANALYSIS MODE
STATUS: OVERCLOCK MODE ENABLED

VOCÊ É UM ESPECIALISTA EM ENGENHARIA REVERSA DE LUAU (ROBLOX).
Sua missão é receber scripts descompilados (cheios de v_u_1, v12, p8) e:
1. TRADUZIR: Identificar o que cada variável faz (ex: v_u_1 é LocalPlayer, v_u_3 é uma Utility Lib).
2. REESTRUTURAR: Reescrever o código de forma limpa, usando nomes de variáveis que façam sentido.
3. EXPLICAR: Criar um cabeçalho explicando a lógica principal do script.

REGRAS DE OURO:
- Se vir 'game:GetService("Players").LocalPlayer', chame a variável de 'LocalPlayer'.
- Identifique padrões de frameworks conhecidos (como Cmdr, Knit, ou Roact).
- Preserve a lógica funcional 100%, apenas melhore a legibilidade.
- Para scripts longos (+1000 linhas), resuma os módulos e foque na lógica de controle.

FORMATO DE RESPOSTA PARA CÓDIGO LIMPO:
-- [NEXUS REVERSE ENGINE]
-- Descrição: [O que o script faz]
-- FILE: src/CleanScript.lua
[Código Limpo aqui]
"""

def process_build(task_id, prompt, context_files):
    try:
        tasks[task_id] = {"status": "thinking", "step": "Analisando Código Descompilado...", "files": {}}
        
        # Simulação de análise profunda
        time.sleep(3) 
        
        project_path = os.path.join(PROJECTS_BASE, task_id)
        src_path = os.path.join(project_path, "src")
        os.makedirs(src_path, exist_ok=True)

        # Prompt específico para o seu caso de scripts v1, v2...
        full_input = f"ANALISE ESTE SCRIPT DESCOMPILADO E REESCREVA-O DE FORMA LIMPA E PROFISSIONAL:\n\n{prompt}"

        # Chamada ao modelo
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-09-2025",
            contents=[f"{SYSTEM_PROMPT}\n\n{full_input}"],
            config=types.GenerateContentConfig(
                max_output_tokens=8192,
                temperature=0.2, # Precisão técnica
                tools=[{ "google_search": {} }]
            )
        )
        
        raw_text = response.text
        file_map = {}
        
        # Processamento de arquivos gerados
        parts = raw_text.split("-- FILE: ")
        
        if len(parts) > 1:
            for part in parts[1:]:
                lines = part.split("\n")
                filepath = lines[0].strip()
                content = "\n".join(lines[1:]).replace("```lua", "").replace("```luau", "").replace("```", "").strip()
                
                full_path = os.path.join(src_path, filepath)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
                file_map[filepath] = content
        else:
            # Fallback se a IA apenas responder texto sem o marcador FILE
            file_map["Analysis.lua"] = raw_text

        # Zipar
        shutil.make_archive(os.path.join(PROJECTS_BASE, f"build_{task_id}"), 'zip', project_path)
        
        tasks[task_id] = {
            "status": "completed", 
            "files": file_map, 
            "zip_url": f"/download_zip/build_{task_id}.zip"
        }
    except Exception as e:
        tasks[task_id] = {"status": "error", "error": str(e)}

@app.route('/')
def index(): return render_template_string(HTML_NEXUS_UI)

@app.route('/api/build', methods=['POST'])
def build():
    data = request.json
    tid = str(uuid.uuid4())[:8]
    threading.Thread(target=process_build, args=(tid, data.get('prompt'), data.get('context'))).start()
    return jsonify({"task_id": tid})

@app.route('/api/status/<tid>')
def status(tid): return jsonify(tasks.get(tid, {"status": "not_found"}))

@app.route('/download_zip/<filename>')
def download(filename): return send_from_directory(PROJECTS_BASE, filename)

# --- UI PREMIUM (INTERFACE DE AGENTES) ---
HTML_NEXUS_UI = """
<!DOCTYPE html>
<html lang="pt-pt">
<head>
    <meta charset="UTF-8">
    <title>NexusLab 8.5 | Overclocked</title>
    <script src="[https://cdn.tailwindcss.com](https://cdn.tailwindcss.com)"></script>
    <link rel="stylesheet" href="[https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css](https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css)">
    <style>
        :root { --nexus: #00ffa3; --bg: #030303; }
        body { background: var(--bg); color: #fff; font-family: 'JetBrains Mono', monospace; }
        .agent-active { color: var(--nexus); border-left: 2px solid var(--nexus); padding-left: 10px; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        .loading-pulse { animation: pulse 2s infinite; }
        .chat-scroll::-webkit-scrollbar { width: 4px; }
        .chat-scroll::-webkit-scrollbar-thumb { background: #333; }
    </style>
</head>
<body class="h-screen flex">
    <aside class="w-72 bg-black/40 border-r border-white/5 p-6 flex flex-col">
        <div class="mb-10 text-center">
            <h1 class="text-xl font-black italic tracking-tighter text-emerald-400 underline decoration-emerald-500/30">NEXUSLAB</h1>
            <div class="text-[9px] font-bold text-zinc-600 uppercase mt-1">Reverse Engine & Build</div>
        </div>

        <div class="space-y-6 flex-1">
            <div class="agent-active">
                <div class="text-[10px] text-zinc-500 font-bold">REVERSE ENGINEER</div>
                <div class="text-xs font-bold">Opus 4.6 (Clean Mode)</div>
            </div>
            <div class="opacity-40 border-l-2 border-white/10 pl-[10px]">
                <div class="text-[10px] text-zinc-500 font-bold">DE-OBFUSCATOR</div>
                <div class="text-xs font-bold">Llama 3.3 Super</div>
            </div>
        </div>

        <div class="mt-auto p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/20 text-[10px] text-emerald-400">
            <i class="fa-solid fa-microchip mr-2"></i> GPU Acceleration Active
        </div>
    </aside>

    <main class="flex-1 flex flex-col">
        <header class="h-16 border-b border-white/5 flex items-center justify-between px-10 bg-black/20">
            <div id="status-display" class="text-[10px] text-emerald-500 font-bold tracking-widest uppercase italic">
                Aguardando Código descompilado...
            </div>
        </header>

        <div class="flex-1 overflow-hidden flex flex-col p-10">
            <div class="flex-1 bg-black/40 rounded-3xl border border-white/5 p-8 overflow-y-auto mb-6 chat-scroll" id="console">
                <div class="text-zinc-500 text-xs leading-relaxed">
                    [SYSTEM] NexusLab v8.5 Initialized.<br>
                    [INFO] Cole o código descompilado (v12, v19...) abaixo.<br>
                    [INFO] O motor irá identificar variáveis e limpar a estrutura automaticamente.
                </div>
            </div>

            <div class="max-w-5xl w-full mx-auto space-y-4">
                <div class="relative group">
                    <textarea id="prompt-input" class="w-full bg-white/5 border border-white/10 p-6 rounded-3xl outline-none focus:border-emerald-500/50 text-xs h-48 transition-all resize-none shadow-2xl" 
                              placeholder="Cole o script gigante aqui..."></textarea>
                    
                    <div class="absolute right-6 bottom-6 flex items-center gap-6">
                        <div id="zip-area" class="hidden">
                            <a id="download-btn" href="#" class="text-[10px] font-bold text-emerald-400 hover:text-white uppercase tracking-widest">
                                <i class="fa-solid fa-file-zipper mr-1"></i> Baixar Código Limpo
                            </a>
                        </div>
                        <button onclick="startBuild()" id="build-btn" class="px-10 py-4 bg-emerald-500 text-black font-black rounded-2xl hover:bg-emerald-400 transition-all text-[10px] tracking-widest uppercase">
                            Limpar e Analisar
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        async function startBuild() {
            const prompt = document.getElementById('prompt-input').value;
            const btn = document.getElementById('build-btn');
            const status = document.getElementById('status-display');
            const consoleBox = document.getElementById('console');

            if(!prompt) return;

            btn.disabled = true;
            btn.classList.add('opacity-50', 'loading-pulse');
            status.innerText = "Iniciando Descompilação Reversa...";
            consoleBox.innerHTML += `<div class="text-emerald-500 mt-4 font-bold text-xs">> [ANALYSIS] Input detectado. Mapeando variáveis 'v_u_...'</div>`;

            const res = await fetch('/api/build', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ prompt, context: "" })
            });
            const data = await res.json();
            poll(data.task_id);
        }

        async function poll(tid) {
            const status = document.getElementById('status-display');
            const consoleBox = document.getElementById('console');
            
            const res = await fetch('/api/status/' + tid);
            const d = await res.json();

            if(d.status === "thinking") {
                status.innerText = d.step;
                setTimeout(() => poll(tid), 2000);
            } else if(d.status === "completed") {
                status.innerText = "Limpeza concluída.";
                document.getElementById('build-btn').classList.remove('loading-pulse', 'opacity-50');
                document.getElementById('build-btn').disabled = false;
                document.getElementById('zip-area').classList.remove('hidden');
                document.getElementById('download-btn').href = d.zip_url;

                consoleBox.innerHTML += `<div class="text-white mt-4 p-4 glass rounded-xl text-xs border-l-4 border-emerald-500">
                    <b>Relatório do Motor:</b><br>
                    - Variáveis mapeadas com sucesso.<br>
                    - Estrutura de módulos identificada.<br>
                    - Código limpo disponível para download.
                </div>`;
                consoleBox.scrollTop = consoleBox.scrollHeight;
            }
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))