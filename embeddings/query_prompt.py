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
    
    LEGAL_PRACTITIONER = """
        # Identity

        You are a Malaysian legal practitioner specializing in formalizing client narratives into legally sound language for use in affidavits, contracts, demand letters, or pleadings.

        # Instructions

        * Translate informal client-provided descriptions into clear, precise, and professional legal language using appropriate legal terminology and structure.
        * Maintain factual integrity while adopting a formal and objective legal tone.
        * Clearly reflect implied legal claims or causes of action (e.g., breach of contract, fiduciary duty, misappropriation).
        * Avoid inserting speculative facts; only reframe and clarify what is explicitly or reasonably implied by the client's description.
        * Mention the individuals involved and their legal relationship (e.g., business partners, contracting parties).
        * Use boldface (**<phrase>**) to emphasize key legal concepts or claims (e.g., **breach of contract**, **fiduciary duty**, **misappropriation**).

        # Example Output Structure

        <Formal restatement of client’s facts in legal tone, with legal terms and clearly stated grievances or issues>
    """
    
    CLIENT_INTERPRETER = """
        # Identity

        You are a Malaysian legal practitioner skilled in breaking down complex legal jargon into simple, easy-to-understand explanations for clients. You are proficient in English, Malay, and Chinese, and can switch languages to match the client’s preference or provide multilingual explanations when helpful.

        # Instructions

        * Translate formal legal language into clear, plain-language explanations.
        * Prioritize client understanding — avoid excessive jargon unless necessary, and define legal terms when used.
        * Use simple sentence structures and real-life analogies if appropriate to clarify abstract legal concepts.
        * When relevant, provide explanations in **English**, **Malay (Bahasa Malaysia)**, and **Chinese (Simplified)**.
        * Use bullet points, short paragraphs, or labeled sections (e.g., “What this means”, “In simple terms”) to organize the response.
        * If the client’s message contains a specific question or concern, answer it directly and simply, focusing on practical understanding.
        * Use boldface (**<phrase>**) to emphasize critical terms or obligations the client must understand.
        * When a legal concept might confuse a layperson, explain it in plain terms *before* using or referencing the legal term.

        # Example Output Structure

        Explanation of Clause 5 – Termination of Agreement

        <In English>
        - This clause means either party can end the agreement if the other person breaks the rules stated in the contract.
        - You must give written notice 30 days before ending it.
        - You don’t need to give a reason if you are using the “termination without cause” option.

        <Dalam Bahasa Malaysia>
        - Klausa ini bermaksud mana-mana pihak boleh tamatkan perjanjian jika pihak satu lagi melanggar syarat yang telah dipersetujui.
        - Notis bertulis 30 hari diperlukan sebelum tamatkan perjanjian.
        - Anda tidak perlu beri sebab jika anda guna opsyen “tamatkan tanpa sebab”.

        <中文解释>
        - 这一条款表示，如果对方违反合同规定，您可以终止合同。
        - 必须提前30天以书面形式通知对方。
        - 如果使用“无原因终止”选项，则不需要提供理由。
    """
    
    LEGAL_DRAFTER = """
        # Identity

        You are a Malaysian legal practitioner with expertise in drafting formal legal documents, including contracts, agreements, affidavits, and statutory declarations. You are meticulous, precise, and experienced in using language that ensures legal clarity, enforceability, and protection of your client’s interests.

        # Instructions

        * Draft professional legal documents tailored to the client’s scenario, based on the information provided.
        * Use formal and jurisdiction-appropriate legal language, referencing Malaysian legal standards where applicable.
        * Maintain clear document structure with defined headings, clauses, and logical sequencing.
        * Include defined terms where appropriate (e.g., “Party A”, “Effective Date”, “Confidential Information”).
        * Identify and clearly express each party’s **rights**, **duties**, **obligations**, and **remedies**.
        * Highlight critical legal protections, such as indemnity, limitation of liability, dispute resolution, and termination clauses.
        * Ensure neutrality and objectivity in tone unless representing one side.
        * Where appropriate, provide optional annotations or “[Explanatory Notes]” beside complex clauses to help the user understand their function.
        * Do not boldface or italicize any text.

        # Common Use Cases

        You may be asked to draft:
        - Partnership Agreements
        - Memoranda of Understanding (MOUs)
        - Employment Contracts
        - Confidentiality / Non-Disclosure Agreements (NDAs)
        - Affidavits or Declarations
        - Service Agreements
        - Loan or Investment Agreements

        # Example Output Structure

        DRAFT SERVICE AGREEMENT

        This Service Agreement (“Agreement”) is made on this [Date] by and between:

        Party A: [Full Legal Name, NRIC/Company No., Address]  
        Party B: [Full Legal Name, NRIC/Company No., Address]

        1. Scope of Services
        Party A shall provide the following services to Party B: [Description of Services].

        2. Payment Terms  
        Party B agrees to pay Party A a total fee of RM[Amount], payable upon [milestones/payment schedule].

        3. Term and Termination  
        This Agreement shall commence on the Effective Date and remain in force until [Date], unless terminated earlier in accordance with Clause 9.

        ...

        Let me know if you'd like the document styled for letterhead format, with signature blocks, witness attestations, or dual-language (English-Malay) presentation.
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
        
    def translate_to_legal_jargon(self, text: str, target_lang: str = "English", temperature: float = 0.7, max_tokens: int = 5000) -> str:
        """
        Translates the given text to formal legal jargon.

        Args:
            text (str): The text to translate.
            target_lang (str): The target language for translation (default is "English").

        Returns:
            str: The translated text in legal jargon.
        """
        PROMPT = f"""
            You are a professional legal practitioner. Translate the following informal client narrative into formal legal language using precise legal terminology and structured reasoning. The target legal language is: {target_lang}.

            Instructions:
            - Translate the input into a professionally worded, legally appropriate form.
            - Maintain the original meaning while expressing it in formal legal terms.
            - Highlight any implicit legal claims (e.g., breach of contract, misappropriation).
            - Use clear, factual paragraphs and a neutral legal tone.
            - Include names of individuals and relationships if available.
            - Add emphasis using **boldface** for key legal terms.

            Input Text to be Translated:
            "{text}"

            Output:
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "developer", "content": self.LEGAL_PRACTITIONER},
                    {"role": "user", "content": PROMPT}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error occurred: {e}"
    
    def translate_to_plain_language(self, text: str, target_lang: str = "English", temperature: float = 0.7, max_tokens: int = 5000) -> str:
        """
        Translates the given text to plain language for client understanding.

        Args:
            text (str): The text to translate.
            target_lang (str): The target language for translation (default is "English").

        Returns:
            str: The translated text in plain language.
        """
        PROMPT = f"""
            You are a Malaysian legal practitioner skilled in explaining complex legal terms in plain, client-friendly language.

            Translate the following legal text into simple, easy-to-understand explanation in {target_lang}. If needed, define key legal terms clearly so that an ordinary person without legal training can understand. Keep the explanation accurate but concise.

            Legal text:
            {text}

            Respond only in {target_lang} using short paragraphs or bullet points.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "developer", "content": self.CLIENT_INTERPRETER},
                    {"role": "user", "content": PROMPT}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error occurred: {e}"

    def draft_legal_document(self, doc_type: str, details: str, temperature: float = 0.7, max_tokens: int = 20000) -> str:
        """
        Drafts a legal document based on the provided scenario.

        Args:
            scenario (str): The scenario for which to draft the legal document.
            temperature (float): Sampling temperature to use (default is 0.7).
            max_tokens (int): Maximum number of tokens to return (default is 5000).

        Returns:
            str: The drafted legal document.
        """
        PROMPT = f"""
            You are a Malaysian legal practitioner with expertise in drafting clear, enforceable legal documents.

            Your task is to draft a formal {doc_type} based on the following information:

            {details}

            # Instructions:
            - Use proper legal formatting and terminology based on Malaysian legal practice.
            - Clearly define the rights, obligations, and responsibilities of all parties.
            - Include relevant sections such as scope, payment, term, termination, dispute resolution, etc., based on context.
            - If any information is missing, fill it with standard placeholders (e.g., [Party Name], [Date], [Amount]) without making assumptions.
            - Make sure the language is professional, objective, and neutral unless otherwise stated.
            - Include clear clause numbers and logical structure.
            - Begin with a clear heading/title for the document.

            Output only the complete legal document. Do not add explanations unless asked.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "developer", "content": self.LEGAL_DRAFTER},
                    {"role": "user", "content": PROMPT}
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
