#######################
# AI Assistant Python Framework
# Date: 2024-01-25
#######################

__all__ = ['BaseConfig']

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Callable, ClassVar
from multiprocess import Process
import multiprocess as PIAProcess

class BaseConfig(BaseModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class OpenAIConfig(BaseConfig):
    api_key: str = '<None>'
    api_base: str = 'https://api.openai.com/v1'
    
class ContextConfig(BaseConfig):
    model: str = 'gpt-4'
    max_tokens: int = 100
    max_user_length: int = 1000
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: list = ['\n']
    system_prompt: str = ''
    error_format: str = '{}'
    stream: bool = False
    
class LoopConfig(BaseConfig):
    db_path: str = 'wx_secret.db'
    memory: int = 10
    max_wait_time: int = 10
    interval: int = 3
    max_workers: int = 10

class Configure(BaseConfig):
    openai: OpenAIConfig = OpenAIConfig()
    context: ContextConfig = ContextConfig()
    loop: LoopConfig = LoopConfig()
    
class PIAMessage(BaseModel):
    """PIAMessage
    This class is used to store messages of human and AI.
    Parameters:
    - uid: The unique ID of the user.
    - uname: The name of the user.
    - text: The text of the message.
    - timestamp: The timestamp of the message.
    - type: The type of the message. 
    (0: text, 1: image, 2: video, 3: audio, 4: file, 5: location, 6: contact, 7: event, 8: system, 9: command, 10: other)
    - content: The content of the message. (bytes)
    - is_human: Is this message sent by human?
    - is_ai: Is this message sent by AI?
    - tokens_all: The number of tokens used in the message.
    - tokens_prompt: The number of tokens used in the prompt.
    - extension: The extension of the message.
    """
    uid: str = Field(None, alias='uid', pattern=r'^[a-zA-Z0-9_]+$')
    uname: str = Field(None, alias='uname', min_length=1, max_length=100)
    text: str = Field(None, alias='text', min_length=1, max_length=1000)
    timestamp: int = Field(None, alias='timestamp', ge=0)
    type: int = Field(None, alias='type', ge=0, le=10)
    content: bytes = Field(None, alias='content')
    is_human: bool = Field(False, alias='is_human')
    is_ai: bool = Field(True, alias='is_ai')
    tool_call: bool = Field(False, alias='tool_call')
    tokens_all: int = Field(None, alias='tokens_all', ge=0)
    tokens_prompt: int = Field(None, alias='tokens_prompt', ge=0)
    extension: str = ''
    
    def __str__(self) -> str:
        return 'PIAMessage({}/{}, {})'.format(self.uname, self.uid, str(len(self.text)) + ' bytes')
    
class PIARequest(BaseModel):
    uid: str = Field(None, alias='uid', pattern=r'^[a-zA-Z0-9_]+$')
    source: str = Field(None, alias='source', min_length=1, max_length=100)
    messages: List[PIAMessage] = Field([], alias='messages')
    
class PIAResponseMessage(BaseModel):
    uname: str = Field(None, alias='uname', min_length=1, max_length=100)
    text: str = Field(None, alias='text', min_length=1, max_length=1000)
    timestamp: int = Field(None, alias='timestamp', ge=0)
    type: int = Field(None, alias='type', ge=0, le=10)
    content: bytes = Field(None, alias='content')
    pass

class PIAResponse(BaseModel):
    t_uid: str = Field(None, alias='t_uid', pattern=r'^[a-zA-Z0-9_]+$')
    t_uname: str = Field(None, alias='t_uname', min_length=1, max_length=100)
    messages: List[PIAResponseMessage] = Field(None, alias='messages')

class PIAModule(BaseModel):
    """PIA Module
    You can use this class to create your own PIA modules.
    There are four main methods in this class:
    - register: Register a function
    You can use this method to register a function to PIA.
    PIA-Core will call this function when the function is called by AI.
    - handler: Handle the request (decorator)
    When PIA-Core receives a request which has function calls, it will call this method to handle the request.
    - mainloop: Main loop (decorator)
    You can use this method to create a main loop.
    PIA-Core will start up a single process to run this method. 
    - callback: Callback function
    You can use this method to send a response to PIA-Core actively.
    """
    m_name: str
    author: str
    version: str = '0.0.1'
    function_lists: dict = {}
    mainloop_handler:Callable = lambda *args, **kwargs: None
    mainloop_args: list = []
    i_callback:Callable = lambda *args, **kwargs: None
    ps: list = []
    def __init__(self, 
        m_name = '',
        author = '',
        version = '0.0.1', 
    *args, **kwargs):
        kwargs['m_name'] = m_name
        kwargs['author'] = author
        kwargs['version'] = version
        super().__init__(*args, **kwargs)
    
    def __str__(self):
        return 'PIAModule({}/{}, {})'.format(self.m_name, self.version, self.author)
    
    def __repr__(self) -> str:
        return self.__str__()

    def register(
        self, 
        function_name,
        function_description,
        function_parameters = {},
    ):
        """Register a function to PIA-Core

        Args:
            function_name (str): The name of the function.
            function_description (str): When and how to use this function.
            function_parameters (dict, optional): The parameters to use your function, read the docs of openai to get more details. Defaults to {}.

        Returns:
            bool: True if success, False if failed.
        """
        '''
        self.function_lists.append({
            'name': function_name,
            'description': function_description,
            'parameters': function_parameters
        })
        '''
        self.function_lists[function_name] = {
            'name': function_name,
            'description': function_description,
            'parameters': function_parameters
        }
        return True
    
    def handler(self, func_list:list, *args, **kwargs):
        for i in func_list:
            if i not in self.function_lists:
                raise PIAError('Function {} not found.'.format(i))
        def wrapper(func):
            for i in func_list:
                self.function_lists[i]['handler'] = func
            return func
        return wrapper
    
    def mainloop(self, keep_alive = True, *args, **kwargs):
        def wrapper(func):
            self.mainloop_handler = func
            if keep_alive:
                def wrapper2(*args, **kwargs):
                    while True:
                        try:
                            st = func(*args, **kwargs)
                            if st == False:
                                break
                        except Exception as e:
                            print(e)
                        except ...:
                            pass
                self.mainloop_handler = wrapper2
            return func
        return wrapper
    
    def run(self):
        ps = Process(target=self.mainloop_handler, args=(self.mainloop_args,))
        ps.start()
        self.ps.append(ps)
        return ps
    
    def stop(self):
        if len(self.ps) == 0:
            return False
        ps : Process = self.ps[-1]
        if ps:
            ps.terminate()
            ps = None
        return True
    
    def callback(self, response: PIAResponse, direct:bool = True):
        return self.i_callback(self, response, direct)
    
    def set_args(self, args:list):
        self.mainloop_args = args
        
    def set_call(self, callback:Callable):
        self.i_callback = callback
        
class PIAListener(BaseModel):
    m_name: str
    author: str
    version: str = '0.0.1'
    uuid: str = ''
    i_callback:Callable = lambda *args, **kwargs: None
    i_sender:Callable = lambda *args, **kwargs: None
    i_mainloop:Callable = lambda *args, **kwargs: None
    keep_alive: bool = True
    mainloop_args: list = []
    i_mainloop_args: list = []
    i_mainloop_kwargs: dict = {}
    ps: list = []
    def __init__(self, 
        uuid,
        m_name = '',
        author = '',
        version = '0.0.1',
    *args, **kwargs):
        kwargs['m_name'] = m_name
        kwargs['author'] = author
        kwargs['version'] = version
        kwargs['uuid'] = uuid
        super().__init__(*args, **kwargs)
        
    def __repr__(self) -> str:
        return 'PIAListener({}/{}, {})'.format(self.m_name, self.version, self.author)
    
    def __str__(self):
        return 'PIAListener({}/{}, {})'.format(self.m_name, self.version, self.author)
    
    def call(self, message: PIAMessage, *args, **kwargs):
        return self.i_callback(message, self, *args, **kwargs)
    
    def sender(self, *args, **kwargs):
        def wrapper(func):
            self.i_sender = func
            return func
        return wrapper
    
    def mainloop_keepalive(self, *args, **kwargs):
        while True:
            self.i_mainloop(*args, **kwargs)
    
    def mainloop(self, keep_alive = True, *args, **kwargs):
        def wrapper(func):
            self.i_mainloop = func
            self.i_mainloop_args = args
            self.i_mainloop_kwargs = kwargs
            if keep_alive:
                def wrapper2(*args, **kwargs):
                    while True:
                        try:
                            st = func(*args, **kwargs)
                            if st == False:
                                break
                        except Exception as e:
                            print(e)
                self.i_mainloop = wrapper2
                return func
            return func
        return wrapper
    
    def set_call(self, callback:Callable):
        self.i_callback = callback
        
    def set_args(self, args:list):
        self.mainloop_args = args
        
    def run(self):
        p_args = ()
        if self.i_mainloop.__code__.co_argcount == 1:
            p_args = (self.mainloop_args,)
        elif self.i_mainloop.__code__.co_argcount == 2:
            p_args = (self.mainloop_args, self.i_mainloop_args)
        elif self.i_mainloop.__code__.co_argcount == 3:
            p_args = (self.mainloop_args, self.i_mainloop_args, self.i_mainloop_kwargs)
        else:
            raise PIAError('Too many arguments in mainloop function.{}'.format(self))
        ps = Process(target=self.i_mainloop, args=p_args)
        self.ps.append(ps)
        ps.start()
        return ps
    
    def stop(self):
        if len(self.ps) == 0:
            return False
        ps : Process = self.ps[-1]
        if ps:
            ps.terminate()
            ps = None
        return True
    
class PIAError(Exception):
    """PIA Error
    This class is used to raise errors in PIA-Core.
    """
    messages: List[PIAMessage] = Field(None, alias='messages')
    stage: int = Field(None, alias='stage', ge=0, le=10)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)