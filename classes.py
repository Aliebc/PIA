#######################
# AI Assistant Python Framework
# Date: 2024-01-25
#######################

__all__ = ['Configure']

class OpenAIConfig:
    api_key: str = '<None>'
    api_base: str = 'https://api.openai.com/v1'
    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
    
class ContextConfig:
    model: str = 'gpt-4'
    max_tokens: int = 100
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: list = ['\n']
    stream: bool = False
    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
    
class LoopConfig:
    db_path: str = 'wx_secret.db'
    memory: int = 10
    max_wait_time: int = 10
    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)

class Configure:
    openai: OpenAIConfig = OpenAIConfig()
    context: ContextConfig = ContextConfig()
    loop: LoopConfig = LoopConfig()
    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
    
    def __repr__(self) -> str:
        return f'<Configure Info>'