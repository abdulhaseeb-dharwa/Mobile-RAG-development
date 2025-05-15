from offline_rag_agent.query_processor import QueryProcessor
from offline_rag_agent.llm_client import LocalLLMClient
from offline_rag_agent.schema_manager import DatabaseSchemaManager
from offline_rag_agent.config import DB_PATH, MODEL_PATH

def test_prompt_generation():
    schema_mgr = DatabaseSchemaManager(DB_PATH)
    llm = LocalLLMClient(MODEL_PATH)
    processor = QueryProcessor(llm, schema_mgr)
    
    dummy_query = "List all customers in France"
    prompt = processor._create_sql_generation_prompt(dummy_query, "customers(id TEXT, country TEXT);")
    
    assert "### USER QUESTION START" in prompt
    assert "List all customers in France" in prompt
    assert "customers(id TEXT, country TEXT);" in prompt
