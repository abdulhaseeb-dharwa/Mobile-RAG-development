import threading
from offline_rag_agent.utils.logger import logger
from llama_cpp import Llama

class LocalLLMClient:
    def __init__(self, model_path: str):
        self.llm = None
        self.is_loaded = False
        self.load_thread = threading.Thread(target=self._load_model, args=(model_path,), daemon=True)
        self.load_thread.start()

    def _load_model(self, model_path):
        try:
            self.llm = Llama(model_path=model_path, n_ctx=16384, n_gpu_layers=0)
            self.is_loaded = True
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Model load error: {e}")

    def wait_for_model(self, timeout=30):
        self.load_thread.join(timeout)
        return self.is_loaded

    def generate_sql(self, prompt: str) -> str:
        if not self.is_loaded and not self.wait_for_model():
            return "Model not ready."
        
        wrapped_prompt = f"""You are a SQL query generator. Your task is to convert natural language questions into SQL queries.
You must ONLY output the SQL query without any explanations or additional text.
The SQL query should be wrapped in triple backticks with the sql language specifier.
        ### Instruction:
        {prompt}

        ### Response:"""

        encoded = self.llm.tokenize(prompt.encode("utf-8"))
        max_context_tokens = 16384
        max_response_tokens = 1024
        max_prompt_tokens = max_context_tokens - max_response_tokens

        if len(encoded) > max_prompt_tokens:
            logger.warning(f"Prompt too long ({len(encoded)} tokens), truncating.")
            encoded = encoded[:max_prompt_tokens]
            prompt = self.llm.detokenize(encoded).decode("utf-8", errors="ignore")

        try:
            output = self.llm(
                wrapped_prompt,
                max_tokens=max_response_tokens,
                stop=["### Question:", "### SQL Query:", "### USER QUESTION START"],
                echo=False,
                temperature=0.1  # Lower temperature for more focused output
            )
            response = output["choices"][0]["text"].strip()
            logger.debug(f"Raw LLM response: {response}")
            return response
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return "Error generating SQL."
