import pytest
from offline_rag_agent.schema_manager import DatabaseSchemaManager
from offline_rag_agent.config import DB_PATH


def test_schema_contains_tables():
    mgr = DatabaseSchemaManager(DB_PATH)
    schema = mgr.get_schema()
    assert "tables" in schema
    assert isinstance(schema["tables"], list)
    assert len(schema["tables"]) > 0
