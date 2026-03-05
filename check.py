from google import genai
import os

CHAVE_API = "AIzaSyC_CFOZDIFufygft6PyLJfAeh043VK47u8"
client = genai.Client(api_key=CHAVE_API)

def chat_ia():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Criando uma sessão de chat com "Instrução de Sistema" (O DNA da IA)
    # Aqui você "ensina" ela antes de começar!
    chat = client.chats.create(
        model="models/gemini-2.5-flash",
        config={
            "system_instruction": "Você é o instrutor oficial do site LuauMaster. Sua missão é ensinar Roblox Luau. Sempre lembre das preferências do usuário durante a conversa."
        }
    )

    print("==========================================")
    print("   🧠 ASSISTENTE COM MEMÓRIA ATIVADA     ")
    print("      (Ela vai lembrar do que você disser) ")
    print("==========================================")

    while True:
        pergunta = input("\n👉 Você: ")

        if pergunta.lower() in ["sair", "exit", "quit"]:
            break

        print("\n⏳ Processando...")

        try:
            # Agora usamos 'send_message' em vez de 'generate_content'
            response = chat.send_message(pergunta)
            
            print("\n--- 🤖 IA ---")
            print(response.text)
            print("-" * 40)

        except Exception as e:
            print(f"\n❌ Erro: {e}")

if __name__ == "__main__":
    chat_ia()