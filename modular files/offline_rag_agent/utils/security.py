import re
from typing import List, Optional
from .exceptions import SecurityError

class SecurityValidator:
    @staticmethod
    def validate_sql_injection(query: str) -> bool:
        """Check for potential SQL injection in the query."""
        # List of potentially dangerous SQL patterns
        dangerous_patterns = [
            r'--.*$',  # SQL comments
            r';\s*(?!$)',   # Multiple statements (semicolon not at end)
            r'/\*.*\*/',  # Multi-line comments
            r'UNION\s+ALL\s+SELECT',
            r'UNION\s+SELECT',
            r'DROP\s+TABLE',
            r'DELETE\s+FROM',
            r'UPDATE\s+.*\s+SET',
            r'INSERT\s+INTO',
            r'ALTER\s+TABLE',
            r'EXEC\s+.*',
            r'EXECUTE\s+.*',
            r'xp_cmdshell',
            r'sp_',
            r'0x[0-9a-fA-F]+'  # Hex encoded strings
        ]

        # Remove trailing semicolon for validation
        query_to_check = query.rstrip(';')

        # First, remove any legitimate aggregate functions and their arguments
        # This prevents false positives with COUNT(*), SUM(*), etc.
        query_to_check = re.sub(
            r'\b(COUNT|SUM|AVG|MIN|MAX)\s*\(\s*\*\s*\)',
            '',
            query_to_check,
            flags=re.IGNORECASE
        )

        # Check for dangerous patterns
        for pattern in dangerous_patterns:
            if re.search(pattern, query_to_check, re.IGNORECASE):
                raise SecurityError(f"Potential SQL injection detected: {pattern}")

        return True

    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """Sanitize user input to prevent injection attacks."""
        # Remove any null bytes
        input_str = input_str.replace('\0', '')
        
        # Remove any control characters
        input_str = ''.join(char for char in input_str if ord(char) >= 32)
        
        return input_str

    @staticmethod
    def validate_query_length(query: str, max_length: int = 1000) -> bool:
        """Validate that the query doesn't exceed maximum length."""
        if len(query) > max_length:
            raise SecurityError(f"Query exceeds maximum length of {max_length} characters")
        return True

class QueryValidator:
    @staticmethod
    def validate_query(query: str) -> bool:
        """Validate the query for security and correctness."""
        # Sanitize input
        query = SecurityValidator.sanitize_input(query)
        
        # Check query length
        SecurityValidator.validate_query_length(query)
        
        # Check for SQL injection
        SecurityValidator.validate_sql_injection(query)
        
        return True 