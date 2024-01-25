#######################
# AI Assistant Python Framework
# Date: 2024-01-25
#######################

from classes import Configure

c = Configure()

c.openai.api_base = "http://api.axgln.net/llms/v1"
c.openai.api_key = "123456"
c.loop.db_path = "wx_secret2.db"
c.loop.max_wait_time = 15
c.loop.memory = 10

