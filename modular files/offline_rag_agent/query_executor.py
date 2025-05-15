from typing import Dict, Any, List
import pandas as pd
import numpy as np
from offline_rag_agent.utils.logger import logger
from offline_rag_agent.utils.metrics import track_time, metrics_collector
from offline_rag_agent.utils.exceptions import (
    DatabaseError, TimeoutError, QueryProcessingError
)
from offline_rag_agent.config import QUERY_TIMEOUT

class QueryExecutor:
    def __init__(self, schema_manager):
        self.schema_manager = schema_manager
        logger.info("QueryExecutor initialized")

    @track_time("query_execution_time")
    def execute_query(self, sql: str) -> Dict[str, Any]:
        """Execute the SQL query with timeout and error handling."""
        logger.info(f"Executing SQL query: {sql}")
        
        try:
            if not self.schema_manager.connection:
                self.schema_manager.connect()

            # Execute query with timeout
            self.schema_manager.connection.execute(f"PRAGMA busy_timeout = {QUERY_TIMEOUT * 1000}")
            cursor = self.schema_manager.connection.execute(sql)
            
            # Fetch results
            results = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            # Record metrics
            metrics_collector.record_metric("rows_returned", len(results))
            
            logger.info(f"Query executed successfully, returned {len(results)} rows")
            return {
                "status": "success",
                "data": results,
                "columns": columns
            }

        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            if "timeout" in str(e).lower():
                raise TimeoutError(f"Query execution timed out after {QUERY_TIMEOUT} seconds")
            raise DatabaseError(f"Failed to execute query: {str(e)}")

    def format_results(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format the query results with additional metadata."""
        logger.debug("Formatting query results")
        
        try:
            if execution_result["status"] != "success":
                return execution_result

            # Convert to DataFrame for easier manipulation
            df = pd.DataFrame(
                execution_result["data"],
                columns=execution_result["columns"]
            )

            # Generate summary statistics
            summary = {
                "row_count": len(df),
                "column_count": len(df.columns),
                "column_types": df.dtypes.to_dict()
            }

            # Add basic statistics for numeric columns
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
            if not numeric_cols.empty:
                summary["numeric_stats"] = df[numeric_cols].describe().to_dict()

            # Record formatting metrics
            metrics_collector.record_metric("result_formatting_time", 1)

            return {
                "status": "success",
                "message": "Query executed successfully",
                "data": df.to_dict(orient='records'),
                "columns": df.columns.tolist(),
                "summary": summary
            }

        except Exception as e:
            logger.error(f"Error formatting results: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to format results: {str(e)}",
                "data": execution_result.get("data", []),
                "columns": execution_result.get("columns", [])
            }
