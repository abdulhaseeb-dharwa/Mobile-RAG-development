import sqlite3
import pandas as pd
import threading
from offline_rag_agent.utils.loggin_utils import setup_logger
from contextlib import contextmanager
from typing import Optional, Dict

logger = setup_logger(__name__)

class DatabaseSchemaManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self.schema_cache: Optional[Dict] = None
        self._lock = threading.Lock()

    @contextmanager
    def get_connection(self):
        try:
            if not self.connection:
                self.connect()
            yield self.connection
        finally:
            if self.connection:
                self.connection.close()
                self.connection = None

    def connect(self):
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        logger.info(f"Connected to database at {self.db_path}")

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")

    def get_schema(self, refresh: bool = False) -> Dict:
        with self._lock:
            if self.schema_cache is not None and not refresh:
                return self.schema_cache

            if not self.connection:
                self.connect()

            schema = {"tables": [], "relationships": []}
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
                tables = cursor.fetchall()
                for table in tables:
                    table_name = table[0]
                    table_info = {"name": table_name, "columns": []}
                    cursor.execute(f"PRAGMA table_info('{table_name}');")
                    columns = cursor.fetchall()
                    for col in columns:
                        table_info["columns"].append({
                            "name": col[1],
                            "type": col[2],
                            "is_primary_key": bool(col[5]),
                            "not_null": bool(col[3]),
                            "default": col[4]
                        })
                    schema["tables"].append(table_info)
                    cursor.execute(f"PRAGMA foreign_key_list('{table_name}');")
                    foreign_keys = cursor.fetchall()
                    for fk in foreign_keys:
                        schema["relationships"].append({
                            "table": table_name,
                            "column": fk[3],
                            "references_table": fk[2],
                            "references_column": fk[4]
                        })

            self.schema_cache = schema
            return schema

    def format_schema_for_llm(self) -> str:
        schema = self.get_schema()
        formatted = "### DATABASE SCHEMA\n\n"
        for table in schema["tables"]:
            column_defs = []
            for col in table["columns"]:
                flags = []
                if col["is_primary_key"]:
                    flags.append("PK")
                if col["not_null"]:
                    flags.append("NN")
                flag_str = " ".join(flags)
                column_defs.append(f"{col['name']} {col['type']} {flag_str}".strip())
            formatted += f"{table['name']}({', '.join(column_defs)});\n"
        return formatted

    def filter_relevant_tables(self, user_query: str) -> str:
        schema = self.get_schema()
        query_lower = user_query.lower()
        relevant_tables = set()
        for table in schema["tables"]:
            if table["name"].lower() in query_lower:
                relevant_tables.add(table["name"])

        if not relevant_tables:
            fallback_tables = ["customer", "countries", "prospect", "visit"]
            relevant_tables.update([t for t in fallback_tables if t in [tbl["name"] for tbl in schema["tables"]]])

        formatted = "### DATABASE SCHEMA\n\n"
        for table in schema["tables"]:
            if table["name"] in relevant_tables:
                column_defs = []
                for col in table["columns"]:
                    flags = []
                    if col["is_primary_key"]:
                        flags.append("PK")
                    if col["not_null"]:
                        flags.append("NN")
                    flag_str = " ".join(flags)
                    column_defs.append(f"{col['name']} {col['type']} {flag_str}".strip())
                formatted += f"{table['name']}({', '.join(column_defs)});\n"
        return formatted

    def get_sample_data(self, limit: int = 3):
        if not self.connection:
            self.connect()
        schema = self.get_schema()
        samples = {}
        for table in schema["tables"]:
            try:
                query = f"SELECT * FROM {table['name']} LIMIT {limit};"
                samples[table['name']] = pd.read_sql_query(query, self.connection)
            except sqlite3.Error:
                samples[table['name']] = pd.DataFrame()
        return samples

    def format_sample_data_for_llm(self, limit: int = 3) -> str:
        samples = self.get_sample_data(limit)
        formatted = "SAMPLE DATA:\n\n"
        for table, df in samples.items():
            formatted += f"Table: {table}\n"
            if df.empty:
                formatted += "  (No data available)\n\n"
            else:
                table_str = df.to_string(index=False)
                formatted += "\n".join("  " + line for line in table_str.split("\n")) + "\n\n"
        return formatted
