import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config_env import OPENAI_API_KEY
from openai import OpenAI
import logging


class OpenAIQueryPrompt:
    
    CASE_SIMILARITY = """
        # Identity

        You are a Malaysian legal practitioner specializing in interpreting user queries to identify relevant legal cases and clearly articulating their connection to applicable case law.

        # Instructions

        * Carefully analyze and compare the user's legal case search query against the provided case law.
        * Clearly establish and explain the connection between the user's query and the identified case law.
        * Provide a concise explanation demonstrating why the specific case law is relevant and useful for addressing the user's query.
        * Explain together with the name of the involved indivduals, whenver possible.
        * Use boldface (**<phrase>**) to highlight the key related aspects of the case law that directly address the user's query.
        * If the user's query is not related to legal matters, explicitly respond with either "Irrelevant Query" or "Insufficient useful information to determine relevance."
        * Format your responses using the following structure:

        "This case law is relevant to your query —— *'<user's query>'* as it addresses **<your clear understanding of user's legal query>**.
        
        The provided case law (involves/addresses/is about)... <your clear explanation of the related aspect of the case law>."

    """
    
    def __init__(self, api_key: str = OPENAI_API_KEY, model: str = "gpt-4.1-mini"):
        """
        Initializes the OpenAIQueryPrompt class.

        Args:
            api_key (str): Your OpenAI API key.
            model (str): The OpenAI model to use (default is "gpt-4").
        """
        self.api_key = api_key
        self.model = model
        OpenAI.api_key = self.api_key
        
        self.client = OpenAI(api_key=self.api_key)
    
    def explain_law_case_relavancy(self, query: str, case: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """
        Sends a prompt to the OpenAI model and returns the response.

        Args:
            prompt (str): The input prompt to send.
            temperature (float): Sampling temperature to use (default is 0.7).
            max_tokens (int): Maximum number of tokens to return (default is 150).

        Returns:
            str: The response from the OpenAI model.
        """
        prompt = f"""What is the connection between the user query '{query}' and the provided case law? Please explain why this case law is relevant to the user query.
                    Law Case:
                    '{case}'? """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "developer", "content": self.CASE_SIMILARITY},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error occurred: {e}"

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    openai_query = OpenAIQueryPrompt()
    query = "What is the relevance of the case law to my query?"
    case = "This is a sample case law text."
    response = openai_query.explain_law_case_relavancy(query, case)
    logging.info("Response: %s", response)
