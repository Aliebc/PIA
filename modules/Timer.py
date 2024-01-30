from classes import PIAModule, PIAMessage, PIARequest, PIAResponse, PIAResponseMessage
import requests
import json
import time
import queue
import sqlite3
from datetime import datetime

class PriorityQueue:
    def __init__(self, db_file):
        self._db_file = db_file
        self._create_table()
        self._load_from_db()

    def _create_table(self):
        conn = sqlite3.connect(self._db_file)
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS priority_queue (priority INTEGER, item TEXT)')
        conn.commit()
        conn.close()

    def push(self, priority, item):
        conn = sqlite3.connect(self._db_file)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO priority_queue VALUES (?, ?)', (priority, item))
        conn.commit()
        conn.close()

    def pop(self):
        conn = sqlite3.connect(self._db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM priority_queue ORDER BY priority DESC LIMIT 1')
        result = cursor.fetchone()
        cursor.execute('DELETE FROM priority_queue WHERE priority = ?', (result[0],))
        conn.commit()
        conn.close()
        return result

    def try_pop(self):
        conn = sqlite3.connect(self._db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM priority_queue ORDER BY priority DESC LIMIT 1')
        result = cursor.fetchone()
        conn.commit()
        conn.close()
        return result

    def _load_from_db(self):
        conn = sqlite3.connect(self._db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM priority_queue ORDER BY priority DESC')
        items = cursor.fetchall()
        self._queue = queue.PriorityQueue()
        for priority, item in items:
            self._queue.put((priority, item))
        conn.close()


app = PIAModule(
    m_name='Timer module',
    author='hzh',
    version='0.0.1',
)
priority_queue = PriorityQueue('priority_queue.db')

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formataddr

app.register(
    function_name="create_timer",
    function_description="Set the message to be sent periodically.",
    function_parameters={
        "type": "object",
        "properties": {
            "timestamp":{
                "type":"string",
                "description":"The timestamp scheduled to send message, measured in milliseconds.For example:1706582445737.",
            },
            "content":{
                "type":"string",
                "description":"The content of the message to be sent periodically"
            },
            # "t_uid":{
            #     "type":"string",
            #     "description":"t_uid in dialogue; Format : Field(None, alias='t_uid', pattern=r'^[a-zA-Z0-9_]+$')"
            # },
            # "t_uname":{
            #     "type":"string",
            #     "description":"t_uname in dialogue; Format : Field(None, alias='t_uname', min_length=1, max_length=100)')"
            # }
        },
        'required': ['timestamp','content']
    }
)

@app.handler(func_list=['create_timer'])
def creat_timer(req:PIARequest=None, func_name = '', func_args = ''):
    print(req)
    args = json.loads(func_args)
    timestamp=args['timestamp']
    content=args['content']
    # t_uid="6f92a4d84bfaee14e1b33f01f693a131"
    # t_uname="PIA-Tester"
    t_uid=args['t_uid']
    print("get message:",timestamp,content,t_uid)
    priority_queue.push(timestamp,json.dumps({"content":content,"t_uid":t_uid}))


@app.mainloop(keep_alive = False)
def my_mainloop(argv:list = []):
    print('Timer Bot is running...')
    while(True):
        time.sleep(1)
        nextmessage = priority_queue.try_pop()
        # print(nextmessage)
        if nextmessage==None:
            continue
        else:
            nowtime = int(time.time()*1000)
            if nowtime>=nextmessage[0]:
                date_time = datetime.utcfromtimestamp(nextmessage[0] / 1000)  # 将毫秒转换为秒并创建 datetime 对象
                formatted_date_time = date_time.strftime('%Y-%m-%d %H:%M:%S')
                print(nextmessage)
                content = json.loads(nextmessage[1])
                app.callback(PIAResponse(
                    t_uid=content["t_uid"],
                    t_uname = "PIA-Tester",#module_call里面似乎没有用上
                    messages=[
                        PIAResponseMessage(
                            uname='Timer Bot',
                            text='您好, 时间{}到了了，这是您定时的消息:{}。'.format(formatted_date_time,content["content"]),
                            type=0,
                            timestamp=nowtime
                        )
                    ]
                ), direct=True)
                priority_queue.pop()


if __name__ == '__main__':
    scheduled_time = int(time.time()*1000+2000)
    content = '这是第一个定时任务'
    priority_queue.push(scheduled_time,json.dumps({"content":content,"t_uid":"123456"}))
    app.mainloop_handler()
    # priority_queue.push('Task 2', 1)
    # print(priority_queue.try_pop())  # 输出：Task 2
    # print(priority_queue.pop())  # 输出：Task 1
    #单独测试的时候直接运行这个文件
    # app.function_lists['create_timer']['handler']()
