import requests

# Cores para o terminal (funciona na maioria dos terminais modernos)
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"

CORTEX_URL = "http://localhost:8001/cortex"


def print_box(title, content, color=CYAN):
    print(f"\n{color}┌── {title} {'─' * (60 - len(title))}┐{RESET}")
    for line in content.split("\n"):
        print(f"{color}│{RESET} {line}")
    print(f"{color}└{'─' * 64}┘{RESET}")


def chat_loop():
    print(f"{GREEN}🚀 NEXUS CORTEX CLIENT ONLINE{RESET}")
    print("Digite 'sair' para encerrar ou '/ingest' para atualizar memória.\n")

    while True:
        try:
            user_input = input(f"{YELLOW}Você > {RESET}")
            if user_input.lower() in ["sair", "exit", "quit"]:
                break

            if user_input.lower() == "/ingest":
                print("⏳ Ingerindo memória...")
                res = requests.post(f"{CORTEX_URL}/ingest", json={})
                print(f"✅ Memória atualizada: {res.json()}")
                continue

            # Envia para o Córtex
            print("🧠 Pensando...")
            response = requests.post(f"{CORTEX_URL}/chat", json={"message": user_input})

            if response.status_code == 200:
                data = response.json()

                # Exibe a resposta final
                print_box("CÓRTEX", data["reply"], GREEN)

                # Exibe o que aconteceu nos bastidores (Debug)
                if data.get("report"):
                    report_str = "\n".join(data["report"])
                    print(f"{CYAN}⚙️ EXECUÇÃO:{RESET}\n{report_str}")

                if (
                    data.get("citations")
                    and data["citations"] != "No relevant memory found."
                ):
                    print(f"{CYAN}📚 MEMÓRIA:{RESET}\n{data['citations'][:200]}...")

            else:
                print(f"❌ Erro {response.status_code}: {response.text}")

        except KeyboardInterrupt:
            print("\nEncerrando...")
            break
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
            print("Verifique se o servidor na porta 8001 está rodando.")


if __name__ == "__main__":
    chat_loop()
