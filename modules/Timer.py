from classes import PIAModule, PIAMessage, PIARequest, PIAResponse, PIAResponseMessage
import requests
import json
import time
import queue
import sqlite3
from datetime import datetime, timezone, timedelta

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
    function_description="It is used to send a specified message at a specified time.",
    function_parameters={
        "type": "object",
        "properties": {
            "timestamp":{
                "type":"string",
                "description":"A timestamp for sending messages at a pre-set time.",
            },
            "content":{
                "type":"string",
                "description":"The content of the message to be sent periodically."
            },
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
    t_uid=req.uid
    print("get message:",int(time.time()),timestamp,content,t_uid)
    priority_queue.push(timestamp,json.dumps({"content":content,"t_uid":t_uid}))

def timestamp_to_beijing_time(timestamp):
    utc_datetime = datetime.utcfromtimestamp(timestamp).replace(tzinfo=timezone.utc)
    beijing_timezone = timezone(timedelta(hours=8))
    beijing_datetime = utc_datetime.astimezone(beijing_timezone)
    beijing_time_str = beijing_datetime.strftime('%Y-%m-%d %H:%M:%S')
    return beijing_time_str

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
                # date_time = datetime.utcfromtimestamp()  # 将毫秒转换为秒并创建 datetime 对象
                # formatted_date_time = date_time.strftime('%Y-%m-%d %H:%M:%S')
                formatted_date_time = timestamp_to_beijing_time(nextmessage[0])
                print(formatted_date_time)
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
    scheduled_time = int(time.time()+2)
    content = '这是第一个定时任务'
    priority_queue.push(scheduled_time,json.dumps({"content":content,"t_uid":"123456"}))
    app.mainloop_handler()