import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import google.generativeai as genai
from llama_index.core import (
    Settings,
    Document,
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
)
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.gemini import Gemini
from llama_index.core import SQLDatabase, SimpleDirectoryReader, Document
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.core.indices.struct_store import SQLTableRetrieverQueryEngine
from llama_index.vector_stores.singlestoredb import SingleStoreVectorStore
from database import DATABASE_URL
from llama_index.core import SQLDatabase
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    String,
    Integer,
    select,
    column,
)
from llama_index.core.indices.struct_store import SQLTableRetrieverQueryEngine
from llama_index.core.objects import (
    SQLTableNodeMapping,
    ObjectIndex,
    SQLTableSchema,
)
from llama_index.core import VectorStoreIndex
# Load environment variables
load_dotenv()

# Initialize OpenAI client
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
client = genai.GenerativeModel("gemini-1.5-flash")
# client = OpenAI(api_key=os.getenv("GOOGLE_API_KEY"))
llm = Gemini(
    model="models/gemini-1.5-flash",
    # api_key="some key",  # uses GOOGLE_API_KEY env var by default
)

# llm = MistralAI(api_key=MISTRAL_API_KEY, model="open-mistral-7b")
embed_model = GoogleGenAIEmbedding(model_name="text-embedding-004", embed_batch_size=300)
# vector_store = SingleStoreVectorStore(
#     table_name='vector_store',
#     content_field="content",
#     metadata_field="metadata",
#     vector_field="vector",
#     host=os.getenv("SINGLESTORE_HOST"),
#     user=os.getenv("SINGLESTORE_USERNAME"),
#     password=os.getenv("SINGLESTORE_PASSWORD"),
#     database=os.getenv("SINGLESTORE_DATABASE"),
#     port=os.getenv("SINGLESTORE_PORT"),

# )

# Apply settings globally
Settings.llm = llm
Settings.embed_model = embed_model
# Settings.vector_store = vector_store
# storage_context = StorageContext.from_defaults(vector_store=vector_store)






# TABLE_NAME = os.getenv("TABLE_NAME")





def create_query_engine(engine):
    """Create a query engine for the given database engine"""
    try:
        sql_database = SQLDatabase(engine)
        all_table_names = sql_database.get_usable_table_names()
        table_node_mapping = SQLTableNodeMapping(sql_database)

        table_schema_objs = []
        for table_name in all_table_names:
            table_schema_objs.append(SQLTableSchema(table_name=table_name))

        obj_index = ObjectIndex.from_objects(
            table_schema_objs,
            table_node_mapping,
            VectorStoreIndex,
        )

        query_engine = SQLTableRetrieverQueryEngine(
            sql_database,
            obj_index.as_retriever(similarity_top_k=1),
        )

        if query_engine:
            return query_engine
        else:
            raise Exception("Failed to create query engine")
    except Exception as e:
        raise Exception(f"Error creating query engine: {e}")

if(DATABASE_URL):
    engine = create_engine(DATABASE_URL)
    metadata_obj = MetaData()
    query_engine = create_query_engine(engine)
else:
    engine = None
    metadata_obj = None
    query_engine = None

def reset_engine(db_url):
    try:
        """Reset the engine"""
        global engine, metadata_obj, query_engine
        engine = create_engine(db_url)
        metadata_obj = MetaData()
        query_engine = create_query_engine(engine)
        return engine
    except Exception as e:
        print(f"Error resetting engine: {e}")
        raise Exception(f"Error resetting engine: {e}")

def get_schema(ENGINE=engine):
    """Get the schema of the database"""
    try:
        sql_database = SQLDatabase(ENGINE)
        all_table_names = sql_database.get_usable_table_names()
        # table_node_mapping = SQLTableNodeMapping(sql_database)

        table_schema_objs = []
        for table_name in all_table_names:
            table_schema_objs.append(SQLTableSchema(table_name=table_name))
    except Exception as e:
        print(f"Error getting schema: {e}")
        raise Exception(f"Error getting schema: {e}")


def generate_sql_from_question(question, chat_history=None):
    """Generate SQL query from natural language question"""
    try:
        # query_engine  = create_query_engine(ENGINE)
        prompt = f"""Here is the question from User : {question}."""
        response = query_engine.query(prompt)
        # print(response)
        result = response.response
        # print(result)
        sql_result  = response.metadata['result']
        query =  response.metadata['sql_query']

        return (result, sql_result, query)
    
    except Exception as e:
        print(f"Error generating SQL: {e}")
        raise Exception(f"Error generating SQL: {e}")

def explain_sql_query(sql_query):
    """Generate an explanation for the SQL query"""
    try:
        prompt = f"""
        You are an AI assistant that explains SQL queries in simple terms.
        This is the query - {sql_query}
        Please explain the query in simple terms. Do not include any SQL code or technical jargon.
        Use plain language that a non-technical person can understand.
        For example, if the query is "SELECT * FROM users WHERE age > 30", you might say:
        "This query retrieves all users who are older than 30 years."
        """
        response = client.generate_content(prompt)
        result = response.text
        return result
    
    except Exception as e:
        print(f"Error explaining SQL: {e}")
        raise Exception(f"Error explaining SQL: {e}")

def process_chat_message(message, chat_history=None):
    """Process a chat message and generate a response"""
    try:
        # Generate SQL from the user's question
        content, sql_result, sql_query = generate_sql_from_question(message , chat_history)
        # print(content)
        if not content:
            return {
                "type": "error",
                "content": "I couldn't generate a SQL query for your question. Could you please rephrase it?"
            }
        
        # Return the SQL query for execution
        return {
            "sql_result": json.loads(json.dumps(sql_result, default=str)),            
            "content": content,
            "sql_query" : sql_query,
            "type": "results",
        }
    
    except Exception as e:
        print(f"Error processing chat message: {e}")
        return {
            "type": "error",
            "content": f"An error occurred: {str(e)}"
        }