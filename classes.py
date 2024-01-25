#######################
# AI Assistant Python Framework
# Date: 2024-01-25
#######################

__all__ = ['Configure']

from pydantic import BaseModel

class BaseConfig(BaseModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class OpenAIConfig(BaseConfig):
    api_key: str = '<None>'
    api_base: str = 'https://api.openai.com/v1'
        
    
class ContextConfig(BaseConfig):
    model: str = 'gpt-4'
    max_tokens: int = 100
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: list = ['\n']
    stream: bool = False
    
class LoopConfig(BaseConfig):
    db_path: str = 'wx_secret.db'
    memory: int = 10
    max_wait_time: int = 10

class Configure(BaseConfig):
    openai: OpenAIConfig = OpenAIConfig()
    context: ContextConfig = ContextConfig()
    loop: LoopConfig = LoopConfig()