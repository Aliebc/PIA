#######################
# AI Assistant Python Framework
# Date: 2024-01-25
#######################

from config import c
from openai import OpenAI, AzureOpenAI

ai: OpenAI = None

if c.openai.api_type == 'openai':
    ai = OpenAI(
        api_key = c.openai.api_key,
        base_url = c.openai.api_base
    )
elif c.openai.api_type == 'azure':
    ai = AzureOpenAI(
        api_key = c.openai.api_key,
        api_version = c.openai.api_version,
        azure_endpoint = c.openai.azure_endpoint
    )