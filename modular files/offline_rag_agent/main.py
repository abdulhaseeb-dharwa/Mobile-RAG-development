from offline_rag_agent.config import MODEL_PATH, DB_PATH
from offline_rag_agent.rag_agent import OfflineRAGAgent
from offline_rag_agent.utils.logger import logger
from offline_rag_agent.utils.metrics import metrics_collector
from offline_rag_agent.utils.exceptions import RAGAgentError
import pandas as pd
import sys

def main():
    try:
        logger.info("Starting RAG Agent application")
        agent = OfflineRAGAgent(DB_PATH, MODEL_PATH)

        # Example query
        query = "Remove Mobile to Salesforce from customers"
        logger.info(f"Processing query: {query}")
        
        result = agent.process_query(query)

        if result["status"] == "success":
            logger.info("Query processed successfully")
            print("\n✅ Generated SQL:")
            print(result["sql"])
            
            print("\n📊 SQL Results:")
            df = pd.DataFrame(result["results"])
            print(df)
            
            if "metrics" in result:
                print("\n📈 Performance Metrics:")
                for metric, stats in result["metrics"].items():
                    print(f"{metric}: {stats}")
                
        elif result["status"] == "pending":
            logger.warning(f"Query pending: {result['message']}")
            print(f"⏳ {result['message']}")
        else:
            logger.error(f"Query failed: {result['message']}")
            print(f"❌ Error: {result['message']}")

    except RAGAgentError as e:
        logger.error(f"RAG Agent error: {str(e)}")
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)
    finally:
        try:
            agent.close()
            logger.info("Application closed successfully")
        except Exception as e:
            logger.error(f"Error closing application: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    main()
