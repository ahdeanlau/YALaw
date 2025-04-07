from openai import OpenAI
from config.config_env import OPENAI_API_KEY

openai_client = OpenAI(OPENAI_API_KEY)

response = openai_client.embeddings.create(
    input="Hello",
    model="text-embedding-3-small"
)

print(response.data[0].embedding)
