from classes import PIAModule, PIARequest

import requests
import json
import time

app = PIAModule(
    m_name='IP Geolocation Bot',
    author='Aliebc',
    version='0.0.1',
)

'''
每个模块有四个部分,
register, handler, mainloop, callback
register用于向PIA注册函数, 在这里用自然语言描述函数的功能, 参数, 返回值等
handler用于处理函数, 在这里用Python代码实现函数的功能
当Core需要主动调用模块时, 会调用handler
mainloop用于处理主循环, 在这里可以进行轮询等操作
callback可以用来主动给用户发送消息, 分为直接发送(直接调用发送接口)和间接发送(即先发给秘书, 再由秘书复述给用户)
'''

#向PIA注册函数, 可以多次注册
app.register(
    function_name='get_ip_geo',
    function_description='Get the geo location of an IPv4 address',
    function_parameters={
        'type': 'object',
        'properties': {
            'ip': {
                'type': 'string',
                'description': 'The valid IPv4/IPv6 address'
            }
        },
        'required': ['ip']
    }
)

def get_ip_geo(ip:str) -> str:
    ret = requests.get('http://ip-api.com/json/{}'.format(ip))
    ret = ret.json()
    return "{}/{}/{}".format(ret['country'],ret['regionName'],ret['city'])

# 为业务函数注册handler
@app.handler(func_list=['get_ip_geo'])
def my_func(req:PIARequest = None, func_name = '', func_args = '') -> str:
    args = json.loads(func_args)
    resp = get_ip_geo(args['ip'])
    return resp

# PIA-Core会启动一个进程来调用管理这个函数
@app.mainloop(keep_alive = False)
def my_mainloop(argv:list = []):
    print('Geolocation Bot is running...')
