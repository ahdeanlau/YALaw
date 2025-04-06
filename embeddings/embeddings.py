from openai import OpenAI
from config.config_env import OPENAI_API_KEY

client = OpenAI(OPENAI_API_KEY)

response = client.embeddings.create(
    input="Hello",
    model="text-embedding-3-small"
)

print(response.data[0].embedding)
