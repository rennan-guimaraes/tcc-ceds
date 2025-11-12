import ollama
import json

# --- 1. Funções Python ---


def get_weather(city: str):
    """Função Python que busca o clima"""
    print(f"--- Executando a ferramenta get_weather(city={city}) ---")
    if "são paulo" in city.lower():
        return json.dumps({"temperature": "25°C", "condition": "ensolarado"})
    elif "londres" in city.lower():
        return json.dumps({"temperature": "15°C", "condition": "nublado"})
    else:
        return json.dumps({"temperature": "N/A", "condition": "cidade não encontrada"})


def get_stock_price(symbol: str):
    """Função Python que busca o preço de ações"""
    symbol = symbol.upper()
    print(f"--- Executando a ferramenta get_stock_price(symbol={symbol}) ---")
    if symbol == "PETR4":
        return json.dumps({"symbol": "PETR4", "price": 38.50, "currency": "BRL"})
    elif symbol == "AAPL":
        return json.dumps({"symbol": "AAPL", "price": 215.00, "currency": "USD"})
    else:
        return json.dumps(
            {"symbol": symbol, "price": "N/A", "error": "símbolo não encontrado"}
        )


# --- 2. Ferramentas para o Modelo ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Obtém o clima atual para uma cidade específica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "O nome da cidade, ex: São Paulo, Londres",
                    }
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Obtém o preço de uma ação (stock) pelo seu símbolo (ticker).",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "O símbolo (ticker) da ação, ex: PETR4, AAPL",
                    }
                },
                "required": ["symbol"],
            },
        },
    },
]

# --- 3. Loop de Chat Interativo ---
print("Iniciando chat com 'Tool Use'. Digite 'sair' para terminar.")
while True:
    # qwen3:4b, llama3:8b
    MODELO = "qwen3:4b"

    prompt = input("\nVocê: ")
    if prompt.lower() == "sair":
        break

    # Zera o histórico de mensagens a cada novo prompt
    messages = [{"role": "user", "content": prompt}]

    print(f"...")

    # --- 4. Primeira chamada ao modelo (com as ferramentas) ---
    try:
        response = ollama.chat(
            model=MODELO,
            messages=messages,
            tools=tools,
        )
    except Exception as e:
        print(f"Erro ao chamar o modelo: {e}")
        continue

    # Adiciona a resposta (que deve ser um pedido de ferramenta) ao histórico
    messages.append(response["message"])

    # --- 5. Verifique se o modelo pediu para usar uma ferramenta ---
    if not response["message"].get("tool_calls"):
        print("\n[RESPOSTA DIRETA DO MODELO] 🤖")
        print(response["message"]["content"])
        continue  # O modelo respondeu diretamente, sem usar ferramenta

    # --- 6. Modelo Pediu uma Ferramenta ---
    print("\n[MODELO PEDINDO FERRAMENTA] 🧠")
    tool_calls = response["message"]["tool_calls"]

    # Loop para o caso do modelo querer chamar várias ferramentas
    for call in tool_calls:
        function_name = call["function"]["name"]
        function_args = call["function"]["arguments"]

        print(f"O modelo quer chamar: {function_name}({json.dumps(function_args)})")

        # --- 7. Execute a ferramenta "real" ---
        if function_name == "get_weather":
            city = function_args.get("city")
            result = get_weather(city)

        elif function_name == "get_stock_price":
            symbol = function_args.get("symbol")
            result = get_stock_price(symbol)

        else:
            print(f"Erro: Modelo tentou chamar função desconhecida: {function_name}")
            result = json.dumps({"error": "função não implementada"})

        # --- 8. Prepare a resposta da ferramenta ---
        print("\n[RESPOSTA DA FERRAMENTA] 🛠️")
        print(f"A função retornou (raw JSON): {result}")

        # Adicione a resposta da ferramenta ao histórico para o modelo "ler"
        messages.append(
            {
                "role": "tool",
                "content": result,
                # "name": function_name # Opcional, mas recomendado
            }
        )

        # --- 9. Chame o modelo uma ÚLTIMA vez ---
        # Agora o modelo tem o contexto (prompt + pedido + resultado)
        # para gerar a resposta final em linguagem natural.

        print("...")

        final_response = ollama.chat(model=MODELO, messages=messages)

        print("\n[RESPOSTA FINAL DO MODELO] 🤖")
        print(final_response["message"]["content"])
