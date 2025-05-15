class RAGAgentError(Exception):
    """Base exception class for RAG Agent errors."""
    pass

class ModelError(RAGAgentError):
    """Raised when there are issues with the LLM model."""
    pass

class DatabaseError(RAGAgentError):
    """Raised when there are database-related issues."""
    pass

class QueryProcessingError(RAGAgentError):
    """Raised when there are issues processing the query."""
    pass

class SecurityError(RAGAgentError):
    """Raised when security checks fail."""
    pass

class ValidationError(RAGAgentError):
    """Raised when input validation fails."""
    pass

class TimeoutError(RAGAgentError):
    """Raised when operations exceed their timeout."""
    pass 