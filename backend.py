#######################
# AI Assistant Python Framework
# Date: 2024-01-25
#######################

from config import c
from openai import OpenAI

ai = OpenAI(
    api_key=c.openai.api_key,
    base_url=c.openai.api_base
)

