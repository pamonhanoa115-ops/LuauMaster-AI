import os
import uuid
import threading
import shutil
import json
import re
from flask import Flask, render_template_string, request, jsonify, send_from_directory
from google import genai
from google.genai import types

app = Flask(__name__)

# --- CONFIGURAÇÃO ---
PROJECTS_BASE = "nexus_workspace"
if not os.path.exists(PROJECTS_BASE): os.makedirs(PROJECTS_BASE)

tasks = {}
GEMINI_KEY = os.environ.get("CHAVE_API", "")
client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

# --- PROMPT DE ARQUITETO DE MUNDO ---
SYSTEM_PROMPT = """
SISTEMA: NEXUSLAB WORLD ARCHITECT | BATTLEGROUNDS EDITION
STATUS: MAP_GENERATION_READY

VOCÊ É UM EXPERT EM MAPAS E SISTEMAS DE BATTLEGROUNDS NO ROBLOX.
Quando o usuário pedir um "Mapa", você deve:
1. Gerar scripts de 'Environment Generator' (que criam partes via script).
2. Gerar o sistema de Satchel (Tool, Server Script, Explosion Logic).
3. Incluir um arquivo 'README_MAPA.md' com instruções de montagem no Studio.

FORMATO OBRIGATÓRIO:
-- FILE: [Caminho]
[Código]
-- ENDFILE --
"""

def process_build(task_id, prompt, context_files=None):
    try:
        tasks[task_id] = {"status": "thinking", "step": "Nexus Orchestrator construindo o mundo...", "files": {}}
        project_path = os.path.join(PROJECTS_BASE, task_id)
        src_path = os.path.join(project_path, "src")
        os.makedirs(src_path, exist_ok=True)

        full_input = f"PEDIDO DE MAPA/SISTEMA: {prompt}\n\nARQUIVOS ENVIADOS: {json.dumps(context_files) if context_files else 'Nenhum'}"

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[f"{SYSTEM_PROMPT}\n\n{full_input}"],
            config=types.GenerateContentConfig(
                max_output_tokens=8192,
                temperature=0.4
            )
        )
        
        raw_text = response.text
        file_map = {}
        file_blocks = re.findall(r'-- FILE: (.*?)\n(.*?)\n-- ENDFILE --', raw_text, re.DOTALL)
        
        if file_blocks:
            for filepath, content in file_blocks:
                filepath = filepath.strip()
                content = content.strip()
                full_path = os.path.join(src_path, filepath)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f: f.write(content)
                file_map[filepath] = content
        else:
            file_map["Guia_Nexus.md"] = raw_text

        shutil.make_archive(os.path.join(PROJECTS_BASE, f"build_{task_id}"), 'zip', project_path)
        tasks[task_id] = {"status": "completed", "files": file_map, "zip_url": f"/download_zip/build_{task_id}.zip"}
    except Exception as e:
        tasks[task_id] = {"status": "error", "error": str(e)}

@app.route('/')
def index(): return render_template_string(HTML_NEXUS_UI)

@app.route('/api/build', methods=['POST'])
def build():
    data = request.json
    tid = str(uuid.uuid4())[:8]
    threading.Thread(target=process_build, args=(tid, data.get('prompt'), data.get('context_files'))).start()
    return jsonify({"task_id": tid})

@app.route('/api/status/<tid>')
def status(tid): return jsonify(tasks.get(tid, {"status": "not_found"}))

@app.route('/download_zip/<filename>')
def download(filename): return send_from_directory(PROJECTS_BASE, filename)

# --- UI COM SCROLLING FRAME E EDITOR DE CÓDIGO ---
HTML_NEXUS_UI = """
<!DOCTYPE html>
<html lang="pt-pt">
<head>
    <meta charset="UTF-8">
    <title>NexusLab 8.5 | Arquiteto de Mundos</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css">
    <style>
        :root { --nexus: #ff0055; --bg: #050505; }
        body { background: var(--bg); color: #fff; font-family: 'Inter', sans-serif; overflow: hidden; }
        
        /* Glassmorphism */
        .glass { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); backdrop-filter: blur(15px); }
        
        /* Janela de Visualização com Scroll */
        .artifact-window { height: calc(100vh - 40px); margin-top: 20px; margin-right: 20px; border: 1px solid rgba(255, 0, 85, 0.2); }
        
        /* Scrolling Frame para o Código */
        .code-container { 
            height: 100%; 
            overflow-y: auto; 
            overflow-x: auto;
            scrollbar-width: thin;
            scrollbar-color: #ff0055 #111;
        }
        .code-container::-webkit-scrollbar { width: 6px; height: 6px; }
        .code-container::-webkit-scrollbar-thumb { background: #ff0055; border-radius: 10px; }
        .code-container::-webkit-scrollbar-track { background: #111; }

        .file-tab { cursor: pointer; padding: 10px 20px; font-size: 10px; font-weight: bold; border-bottom: 2px solid transparent; transition: 0.3s; color: #666; white-space: nowrap; }
        .file-tab.active { border-bottom-color: var(--nexus); background: rgba(255, 0, 85, 0.1); color: #fff; }
        
        .loading-bar { height: 2px; width: 0%; background: var(--nexus); transition: width 0.5s; box-shadow: 0 0 10px var(--nexus); }
        
        pre[class*="language-"] { margin: 0 !important; background: transparent !important; padding: 20px !important; font-size: 13px !important; }
        code { font-family: 'Fira Code', monospace !important; }
    </style>
</head>
<body class="flex h-screen">

    <!-- BARRA LATERAL (CONTROLOS) -->
    <section class="w-1/3 flex flex-col p-6 h-full border-r border-white/5">
        <div class="flex items-center gap-3 mb-8">
            <div class="w-10 h-10 bg-[#ff0055] rounded-xl flex items-center justify-center shadow-[0_0_20px_rgba(255,0,85,0.4)]">
                <i class="fa-solid fa-mountain-city text-white text-lg"></i>
            </div>
            <h1 class="text-xl font-black tracking-tighter italic">NEXUS<span class="text-[#ff0055]">WORLD</span></h1>
        </div>

        <div id="console" class="flex-1 overflow-y-auto space-y-4 mb-4 pr-2 text-[11px] text-zinc-500">
            <div class="glass p-4 rounded-2xl border-l-2 border-[#ff0055]">
                [SISTEMA] <b>Scrolling Frame Ativado</b>. <br>
                Podes ler scripts longos diretamente aqui sem baixar.
            </div>
        </div>

        <div class="space-y-3">
            <div id="file-previews" class="hidden flex flex-wrap gap-2"></div>
            <div class="glass rounded-3xl p-4 border border-white/10">
                <textarea id="prompt-input" class="w-full bg-transparent outline-none text-sm h-28 resize-none" placeholder="O que queres buildar agora?"></textarea>
                <div class="flex justify-between items-center mt-3">
                    <label class="p-2 hover:bg-white/5 rounded-full cursor-pointer transition-all">
                        <i class="fa-solid fa-paperclip text-zinc-500"></i>
                        <input type="file" id="file-upload" class="hidden" multiple onchange="previewFiles(this)">
                    </label>
                    <button onclick="startBuild()" id="build-btn" class="bg-[#ff0055] text-white font-black px-8 py-2.5 rounded-xl text-[10px] uppercase tracking-widest hover:scale-105 transition-all">
                        Gerar Mapa
                    </button>
                </div>
            </div>
        </div>
    </section>

    <!-- ÁREA DE VISUALIZAÇÃO DO CÓDIGO (SCROLLING FRAME) -->
    <section class="flex-1 artifact-window glass rounded-3xl overflow-hidden flex flex-col relative">
        <div id="progress-bar" class="loading-bar"></div>
        
        <header class="h-14 border-b border-white/5 bg-black/40 flex items-center px-8 justify-between shrink-0">
            <div class="flex items-center gap-3">
                <i class="fa-solid fa-code text-[#ff0055] text-sm"></i>
                <span class="text-[10px] font-bold text-zinc-400 uppercase tracking-[0.2em]">Visualizador de Script</span>
            </div>
            <div class="flex gap-4">
                 <button onclick="copyCode()" class="text-[9px] bg-white/5 border border-white/10 px-4 py-2 rounded-full hover:bg-white/10 transition-all font-bold">
                    <i class="fa-solid fa-copy mr-2"></i> COPIAR
                </button>
                <div id="zip-link-area" class="hidden">
                    <a id="download-btn" href="#" class="text-[9px] bg-[#ff0055] px-5 py-2 rounded-full hover:scale-105 transition-all font-black text-white">
                        <i class="fa-solid fa-file-zipper mr-2"></i> DOWNLOAD ZIP
                    </a>
                </div>
            </div>
        </header>

        <!-- Barra de Abas -->
        <div id="file-tabs" class="flex bg-black/40 border-b border-white/5 overflow-x-auto shrink-0"></div>

        <!-- O SCROLLING FRAME REAL -->
        <div class="flex-1 overflow-hidden bg-[#0d0d0d]">
            <div id="scroll-frame" class="code-container">
                <pre id="code-display" class="language-lua"><code id="code-content">-- Nexus Engine pronta. Insira o seu prompt...</code></pre>
            </div>
        </div>
    </section>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-lua.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-markdown.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>

    <script>
        let currentFiles = {};
        let attached = [];

        function previewFiles(i){
            const box = document.getElementById('file-previews');
            box.innerHTML = ""; box.classList.remove('hidden');
            Array.from(i.files).forEach(f => {
                let r = new FileReader();
                r.onload = e => {
                    attached.push({name: f.name, content: e.target.result});
                    box.innerHTML += `<div class="bg-white/5 px-3 py-1 rounded-full text-[9px] border border-white/10 text-emerald-500 font-bold">${f.name}</div>`;
                };
                r.readAsText(f);
            });
        }

        async function startBuild() {
            const p = document.getElementById('prompt-input').value;
            const b = document.getElementById('build-btn');
            const c = document.getElementById('console');
            if(!p && attached.length === 0) return;

            b.disabled = true; b.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
            c.innerHTML += `<div class="text-white mt-4 italic opacity-80">>> ${p}</div>`;

            const res = await fetch('/api/build', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ prompt: p, context_files: attached })
            });
            const d = await res.json();
            poll(d.task_id);
            attached = [];
            document.getElementById('file-previews').innerHTML = "";
        }

        async function poll(tid) {
            const res = await fetch('/api/status/' + tid);
            const d = await res.json();
            const bar = document.getElementById('progress-bar');

            if(d.status === "thinking") {
                bar.style.width = "75%";
                setTimeout(() => poll(tid), 2000);
            } else if(d.status === "completed") {
                bar.style.width = "100%";
                document.getElementById('build-btn').disabled = false;
                document.getElementById('build-btn').innerText = "Gerar Mapa";
                document.getElementById('zip-link-area').classList.remove('hidden');
                document.getElementById('download-btn').href = d.zip_url;
                currentFiles = d.files;
                renderTabs(d.files);
                setTimeout(() => bar.style.width = "0%", 1000);
            }
        }

        function renderTabs(files) {
            const container = document.getElementById('file-tabs');
            container.innerHTML = "";
            Object.keys(files).forEach((name, i) => {
                const t = document.createElement('div');
                t.className = `file-tab ${i === 0 ? 'active' : ''}`;
                t.innerText = name;
                t.onclick = () => {
                    document.querySelectorAll('.file-tab').forEach(x => x.classList.remove('active'));
                    t.classList.add('active');
                    updateCode(name, files[name]);
                };
                container.appendChild(t);
                if(i===0) updateCode(name, files[name]);
            });
        }

        function updateCode(filename, content) {
            const codeBox = document.getElementById('code-content');
            const pre = document.getElementById('code-display');
            
            // Determinar linguagem
            let lang = "lua";
            if(filename.endsWith('.py')) lang = "python";
            if(filename.endsWith('.md')) lang = "markdown";

            pre.className = `language-${lang}`;
            codeBox.textContent = content;
            Prism.highlightElement(codeBox);
            
            // Resetar Scroll para o topo ao trocar de arquivo
            document.getElementById('scroll-frame').scrollTop = 0;
        }

        function copyCode() {
            const code = document.getElementById('code-content').textContent;
            const temp = document.createElement('textarea');
            temp.value = code;
            document.body.appendChild(temp);
            temp.select();
            document.execCommand('copy');
            document.body.removeChild(temp);
            alert('Código copiado para o clipboard!');
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))