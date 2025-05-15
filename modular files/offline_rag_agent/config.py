## File: offline_rag_agent/config.py
from pathlib import Path
import os

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = str(BASE_DIR / "models" / "evolvedseeker_1_3.Q4_K_M.gguf")
DB_PATH = str(BASE_DIR / "data" / "cargill.db")

# Logging configuration
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = str(LOG_DIR / "rag_agent.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Performance settings
MAX_QUERY_LENGTH = int(os.getenv("MAX_QUERY_LENGTH", "1000"))
QUERY_TIMEOUT = int(os.getenv("QUERY_TIMEOUT", "30"))  # seconds
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))  # seconds

# Security settings
ALLOWED_SQL_KEYWORDS = {
    # Basic SQL keywords
    "SELECT", "FROM", "WHERE", "GROUP BY", "ORDER BY", "HAVING",
    "JOIN", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN", "ON",
    "AND", "OR", "NOT", "IN", "LIKE", "IS", "NULL",
    
    # Additional common keywords
    "AS", "DISTINCT", "COUNT", "SUM", "AVG", "MIN", "MAX",
    "CASE", "WHEN", "THEN", "ELSE", "END",
    "ASC", "DESC", "LIMIT", "OFFSET",
    "WITH", "UNION", "ALL",
    
    # Common functions
    "COALESCE", "IFNULL", "NULLIF", "CAST",
    "UPPER", "LOWER", "TRIM", "LENGTH",
    "SUBSTR", "REPLACE", "CONCAT",
    "ROUND", "FLOOR", "CEIL",
    "DATE", "DATETIME", "STRFTIME",
    
    # Common operators
    "=", "!=", "<>", "<", ">", "<=", ">=",
    "+", "-", "*", "/", "%",
    "||", "&&"
}

# Metrics settings
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() == "true"
METRICS_RETENTION_DAYS = int(os.getenv("METRICS_RETENTION_DAYS", "7"))

# Create necessary directories
LOG_DIR.mkdir(parents=True, exist_ok=True)

print(f"MODEL_PATH: {MODEL_PATH}")
print(f"DB_PATH: {DB_PATH}")

