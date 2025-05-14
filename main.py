import json
from sqlalchemy import MetaData, create_engine, text
from smolagents import CodeAgent, LiteLLMModel, tool
from smolagents.tools import get_json_schema

def process_schema(metadata_obj: MetaData) -> list: # Função para converter schema do banco para uma lista de fácil entendimento
    # Uma lista representando o schema do banco, onde serão armazenados em ordem:
    # Nome da Tabela: Colunas em sequência
    # Foreign Keys da tabela se presentes -> Relacionamento
    simplified_schema = []
    
    # Iterando sobre as tabelas
    for table_name, table in metadata_obj.tables.items():
        column_names = [col.name for col in table.columns] # Criando uma lista com os nomes das colunas presentes na tabela atual
        column_line = f"{table_name}: {', '.join(column_names)}" # Convertendo valores para uma string
        simplified_schema.append(column_line) # Adicionando à lista

        # Iterando sobre as foreign_keys
        for fk in table.foreign_keys:
            fk_line = f"{table_name}.{fk.parent.name} → {fk.column.table.name}.{fk.column.name}"
            simplified_schema.append(fk_line)
    
    # print(simplified_schema)
    return simplified_schema

# Tool que processa código SQL gerado pela LLM
@tool
def sql_engine(query: str) -> str:
    """
    Allows you to perform SQL queries on the current database. Returns a string representation of the result.
    This is the current schema:

    Args:
        query: The query to perform. This should be correct SQL.
    """
    output=""
    with engine.connect() as con:
        rows = con.execute(text(query)).fetchall() # Executando a query
        output += "\n".join(str(row[0]) if len(row) == 1 else str(row) for row in rows) # Mandando as linhas de resposta do banco em forma de texto para o output
    
    return output

engine = create_engine("mysql+mysqlconnector://root:fatec@localhost:3306/bookstore") # Conectando ao banco
metadata_obj = MetaData()
metadata_obj.reflect(bind=engine) # Pegando schema do banco presente na 'engine' e guardando no objeto MetaData

simplified_schema = process_schema(metadata_obj) # Processando schema para uma lista

# Atualizando descrição da tool com os dados simplificados do schema do banco
sql_engine.description = f"""
Allows you to perform SQL queries on the current database. Returns a string representation of the result and a english interpreted text.
This is the current schema:\n{ '\n'.join(simplified_schema) }

Args:
    query: The query to perform. This should be correct SQL.
"""

api_key="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"

# Iniciando modelo da LLM local
# lite_model = LiteLLMModel(   
#     "groq/llama3-8b-8192",
#     api_base="https://api.groq.com/openai/v1",
#     api_key=api_key
# )


lite_model = LiteLLMModel(
    model_id="ollama/gemma3:4b",  # or "ollama/llama3:8b"
    api_base="http://localhost:11434",  # Local Ollama server
    api_key=None  # No key needed for local Ollama
)


# Iniciando agente com o modelo declarado anteriormente e passando as tools para o agente utilizar
agent = CodeAgent(
    tools=[sql_engine],
    model=lite_model
)

# Processo principal
if __name__ == "__main__":
    print("🧠 SmolAgent SQL Assistant ready. Ask me anything about your database!")
    while True:
        # Tentei adicionar um contexto para melhorar as respostas do agente (por padrão ele devolve exatamente a resposta do banco),
        # porém sem muito sucesso, no momento talvez funcione melhor sem esse contexto.
        context = """When utilizing a tool you should process the database's response into natural language.
Return to the user a user friendly answer with natural language in your final_answer(...) after processing the data received,
you should utilize the sql_engine tool again if necessary. REMEMBER TO PROCESS THE DATABASE'S RESPONSE INTO NATURAL LANGUAGE\n"""
        user_input = input("\n🧑 You: ")
        if user_input.lower() in ["exit", "quit"]: # 'exit' ou 'quit' para finalizar o processo
            print("👋 Goodbye!")
            break
        try:
            user_input = context + user_input # Passando o contexto antes do input do usuário (não sei se tem outro jeito de fazer isso)
            response = agent.run(user_input)
            print("\n🤖 Agent:", response)
            # user_input = "Analise and resume the SQL data :" + response
            # print(agent.run(user_input))

        except Exception as e:
            print("❌ Error:", e)