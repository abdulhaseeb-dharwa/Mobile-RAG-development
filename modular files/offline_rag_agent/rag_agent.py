from offline_rag_agent.schema_manager import DatabaseSchemaManager
from offline_rag_agent.llm_client import LocalLLMClient
from offline_rag_agent.query_processor import QueryProcessor
from offline_rag_agent.query_executor import QueryExecutor
from offline_rag_agent.utils.logger import logger
from offline_rag_agent.utils.metrics import track_time, metrics_collector
from offline_rag_agent.utils.security import QueryValidator
from offline_rag_agent.utils.exceptions import (
    RAGAgentError, ModelError, DatabaseError,
    QueryProcessingError, SecurityError, TimeoutError
)
from offline_rag_agent.config import QUERY_TIMEOUT

class OfflineRAGAgent:
    def __init__(self, db_path: str, model_path: str):
        logger.info("Initializing RAG Agent")
        try:
            self.schema_manager = DatabaseSchemaManager(db_path)
            self.llm_client = LocalLLMClient(model_path)
            self.query_processor = QueryProcessor(self.llm_client, self.schema_manager)
            self.query_executor = QueryExecutor(self.schema_manager)
            self.schema_manager.connect()
            self.schema_manager.get_schema()
            logger.info("RAG Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG Agent: {str(e)}")
            raise RAGAgentError(f"Initialization failed: {str(e)}")

    @track_time("query_processing_time")
    def process_query(self, user_query: str) -> dict:
        """Process a user query with improved error handling and metrics."""
        logger.info(f"Processing query: {user_query}")
        
        try:
            # Validate query
            QueryValidator.validate_query(user_query)
            
            # Check model status
            if not self.llm_client.is_loaded:
                if not self.llm_client.wait_for_model(timeout=QUERY_TIMEOUT):
                    logger.warning("Model loading timeout")
                    return {
                        "status": "pending",
                        "message": "Model loading timeout. Please try again.",
                        "user_query": user_query
                    }

            # Process query
            query_result = self.query_processor.process_query(user_query)
            sql = query_result["sql"]
            
            # Validate SQL
            is_valid, error = self.query_processor.validate_sql(sql)
            if not is_valid:
                logger.error(f"Invalid SQL generated: {error}")
                return {
                    "status": "error",
                    "message": f"Invalid SQL: {error}",
                    "user_query": user_query,
                    "sql": sql,
                    "results": None
                }

            # Execute query
            execution_result = self.query_executor.execute_query(sql)
            formatted_results = self.query_executor.format_results(execution_result)
            
            # Record success metrics
            metrics_collector.record_metric("successful_queries", 1)
            
            logger.info("Query processed successfully")
            return {
                "status": formatted_results["status"],
                "message": formatted_results["message"],
                "user_query": user_query,
                "sql": sql,
                "results": formatted_results["data"],
                "columns": formatted_results.get("columns", []),
                "summary": formatted_results.get("summary", {}),
                "metrics": {
                    "processing_time": metrics_collector.get_metric_stats("query_processing_time")
                }
            }

        except SecurityError as e:
            logger.error(f"Security error: {str(e)}")
            return {
                "status": "error",
                "message": f"Security error: {str(e)}",
                "user_query": user_query
            }
        except TimeoutError as e:
            logger.error(f"Timeout error: {str(e)}")
            return {
                "status": "error",
                "message": f"Query timeout: {str(e)}",
                "user_query": user_query
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}",
                "user_query": user_query
            }

    def close(self):
        """Close all connections and cleanup resources."""
        logger.info("Closing RAG Agent")
        try:
            self.schema_manager.close()
            logger.info("RAG Agent closed successfully")
        except Exception as e:
            logger.error(f"Error closing RAG Agent: {str(e)}")
            raise RAGAgentError(f"Failed to close RAG Agent: {str(e)}")
