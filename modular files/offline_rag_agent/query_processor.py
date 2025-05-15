import re
from typing import Dict, Tuple, Any
from offline_rag_agent.utils.logger import logger
from offline_rag_agent.utils.metrics import track_time, metrics_collector
from offline_rag_agent.utils.security import SecurityValidator
from offline_rag_agent.utils.exceptions import (
    QueryProcessingError, SecurityError, ValidationError
)
from offline_rag_agent.config import ALLOWED_SQL_KEYWORDS

class QueryProcessor:
    def __init__(self, llm_client, schema_manager):
        self.llm_client = llm_client
        self.schema_manager = schema_manager
        logger.info("QueryProcessor initialized")

    @track_time("query_generation_time")
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """Process the user query and generate SQL."""
        logger.info(f"Processing user query: {user_query}")
        
        try:
            # Validate input
            if not user_query or not isinstance(user_query, str):
                raise ValidationError("Invalid query input")

            # Get relevant schema information
            schema_info = self.schema_manager.filter_relevant_tables(user_query)
            #logger.info(f"Schema information: {schema_info}")
            
            # Create prompt with schema information
            prompt = self._create_sql_generation_prompt(user_query, schema_info)
            #logger.info(f"Prompt: {prompt}")
            
            # Generate SQL using LLM
            raw_sql = self.llm_client.generate_sql(prompt)
            logger.info(f"Raw generated SQL: {raw_sql}")

            # Parse SQL from the response
            sql = self._parse_sql(raw_sql)
            logger.info(f"Parsed SQL: {sql}")

            # Remove any remaining markdown formatting
            # sql = sql.replace('```sql', '').replace('```', '').strip()
            # logger.info(f"Cleaned SQL: {sql}")

            # Validate SQL
            is_valid, error = self.validate_sql(sql)
            if not is_valid:
                logger.error(f"SQL validation failed: {error}")
                raise QueryProcessingError(f"Invalid SQL generated: {error}")

            return {"sql": sql}

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise QueryProcessingError(f"Failed to process query: {str(e)}")

    def validate_sql(self, sql: str) -> Tuple[bool, str]:
        """Validate the generated SQL for security and correctness."""
        logger.debug(f"Validating SQL: {sql}")
        
        try:
            # Check for SQL injection
            SecurityValidator.validate_sql_injection(sql)

            # Basic SQL structure validation
            if not sql.strip().upper().startswith("SELECT"):
                return False, "Query must start with SELECT"

            # Normalize SQL for validation
            normalized_sql = sql.upper()
            
            # Extract the main parts of the query
            select_part = normalized_sql.split("FROM")[0].strip()
            
            # Split the SELECT part into words, preserving parentheses
            words = []
            current_word = ""
            in_parentheses = False
            
            for char in select_part:
                if char == '(':
                    if current_word:
                        words.append(current_word)
                    words.append(char)
                    current_word = ""
                    in_parentheses = True
                elif char == ')':
                    if current_word:
                        words.append(current_word)
                    words.append(char)
                    current_word = ""
                    in_parentheses = False
                elif char.isspace() and not in_parentheses:
                    if current_word:
                        words.append(current_word)
                        current_word = ""
                else:
                    current_word += char
            
            if current_word:
                words.append(current_word)
            
            # Validate each word
            i = 0
            while i < len(words):
                word = words[i]
                
                # Skip quoted strings and identifiers
                if word.startswith(('"', "'", "`")):
                    i += 1
                    continue
                
                # Handle aggregate functions
                if word in {"COUNT", "SUM", "AVG", "MIN", "MAX"}:
                    # Skip the function name and its arguments
                    while i < len(words) and words[i] != ")":
                        i += 1
                    i += 1
                    continue
                
                # Skip table/column names (including those with dots)
                if all(part.replace('_', '').isalnum() for part in word.split('.')):
                    i += 1
                    continue
                
                # Skip numbers and basic operators
                if word.replace('.', '').replace('-', '').isdigit() or word in {'=', '!=', '<>', '<', '>', '<=', '>=', '+', '-', '*', '/', '%', '(', ')', ',', 'AS'}:
                    i += 1
                    continue
                
                # Check against allowed keywords
                if word in ALLOWED_SQL_KEYWORDS:
                    i += 1
                    continue
                
                # Log the problematic word for debugging
                logger.debug(f"Disallowed word found in SELECT part: {word}")
                return False, f"Disallowed SQL keyword or pattern: {word}"
                
                i += 1

            # Record validation metrics
            metrics_collector.record_metric("sql_validations", 1)
            
            return True, ""

        except SecurityError as e:
            logger.error(f"Security validation failed: {str(e)}")
            return False, str(e)
        except Exception as e:
            logger.error(f"SQL validation error: {str(e)}")
            return False, f"Validation error: {str(e)}"

    def _create_sql_generation_prompt(self, user_query: str, schema_info: str) -> str:
        prompt = f"""
    ### USER QUESTION START
    {user_query}
    ### USER QUESTION END

    {schema_info}

    ### INSTRUCTIONS
    Provide only the SQL query inside triple backticks (```). Don't include anything else in your response.
    Strictly use the table names provided in the schema.
    If the required tables are not in this schema, respond with "TABLES_NOT_IN_CHUNK".
    # Example format:
    # ```sql
    # SELECT column FROM table WHERE condition;
    # ```
    # """
        return prompt.strip()

    def _parse_sql(self, response: str) -> str:
        """Extract SQL query from LLM response."""
        # First try to find SQL in code blocks
        sql_blocks = re.findall(r"```(?:sql)?\s*(.*?)\s*```", response, re.DOTALL)
        if sql_blocks:
            sql = sql_blocks[0].strip()
            # Remove any remaining markdown formatting
            sql = sql.replace('```sql', '').replace('```', '').strip()
            logger.debug(f"Extracted SQL from code block: {sql}")
            return sql
        
        # If no code blocks, try to find SQL statements
        sql_statements = re.findall(r"(?:SELECT|WITH)\s+.*?(?:;|$)", response, re.DOTALL | re.IGNORECASE)
        if sql_statements:
            sql = sql_statements[0].strip()
            logger.debug(f"Extracted SQL from statement: {sql}")
            return sql
        
        # If still no SQL found, try to extract any line containing SELECT
        select_lines = [line.strip() for line in response.split('\n') if 'SELECT' in line.upper()]
        if select_lines:
            sql = select_lines[0].strip()
            logger.debug(f"Extracted SQL from line: {sql}")
            return sql
        
        # If no SQL found at all, return the original response
        logger.warning("No SQL query found in LLM response, using raw response")
        return response.strip()
