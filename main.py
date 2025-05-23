import json
from sqlalchemy import MetaData, create_engine, text
from smolagents import CodeAgent, LiteLLMModel, tool
from smolagents.tools import get_json_schema
import gradio as gr

# Function to convert schema to a simplified list
def process_schema(metadata_obj: MetaData) -> list:
    simplified_schema = []
    for table_name, table in metadata_obj.tables.items():
        column_names = [col.name for col in table.columns]
        column_line = f"{table_name}: {', '.join(column_names)}"
        simplified_schema.append(column_line)
        for fk in table.foreign_keys:
            fk_line = f"{table_name}.{fk.parent.name} → {fk.column.table.name}.{fk.column.name}"
            simplified_schema.append(fk_line)
    return simplified_schema

# Tool to process SQL
@tool
def sql_engine(query: str) -> str:
    """
    Allows you to perform SQL queries on the current database. Returns a string representation of the result.
    This is the current schema:

    Args:
        query: The query to perform. This should be correct SQL.
    """
    output = ""
    with engine.connect() as con:
        rows = con.execute(text(query)).fetchall()
        output += "\n".join(str(row[0]) if len(row) == 1 else str(row) for row in rows)
    return output

# Database connection
engine = create_engine("mysql+mysqlconnector://root:fatec@localhost:3306/bookstore")
metadata_obj = MetaData()
metadata_obj.reflect(bind=engine)

# Process and add schema to tool description
simplified_schema = process_schema(metadata_obj)
sql_engine.description = f"""
Allows you to perform SQL queries on the current database. Returns a string representation of the result.
This is the current schema:\n{ '\n'.join(simplified_schema) }

Args:
    query: The query to perform. This should be correct SQL.
"""

# api_key="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"

# Iniciando modelo da LLM local
# lite_model = LiteLLMModel(  
#     "groq/llama3-8b-8192",
#     api_base="https://api.groq.com/openai/v1",
#     api_key=api_key
# )


# Local LLM
lite_model = LiteLLMModel(
    model_id="ollama/gemma3:4b",
    api_base="http://localhost:11434",
    api_key=None
)

# Create agent
agent = CodeAgent(
    tools=[sql_engine],
    model=lite_model
)

# Function to use in Gradio interface
def handle_user_input(user_input):
    context = """You should utilize the sql_engine tool to make queries into the database.
Use the engine as many times as necessary to get the best result based on the user's query.
When satisfied use final_answer(...) to display your response to the user.
REMEMBER THE ENGINE WILL ALWAYS RETURN A STRING.\n"""

    try:
        full_prompt = context + user_input
        response = agent.run(full_prompt)
        return response
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Create Gradio Interface
demo = gr.Interface(fn=handle_user_input, inputs="text", outputs="text", title="🧠 SmolAgent SQL Assistant", description="Ask me anything about your MySQL bookstore database!")

# Run it
if __name__ == "__main__":
    demo.launch(share=True)
