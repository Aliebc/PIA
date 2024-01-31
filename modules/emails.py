#!/usr/bin/env python3
from classes import PIAModule, PIAMessage, PIARequest, PIAResponse, PIAResponseMessage
import requests
import json
import time

app = PIAModule(
    m_name='Email module',
    author='hzh',
    version='0.0.1',
)
test_receiver = {"name":"xxx","useraddress":"xxx"}
test_sender = {"name":"人工智障","useraddress":"xxx","password":"xxx"}
test_content = {
                "title":"这是一个标题",
                "text":"这是正文",
                "attachments":[{"name":"附件1.txt","content": b'\xe8\xbf\x99\xe6\x98\xaf\xe4\xb8\x80\xe4\xb8\xaa\xe6\xb5\x8b\xe8\xaf\x95\xe9\x99\x84\xe4\xbb\xb6'.decode('utf-8')},
                               {"name":"附件2.txt","content": b'\xe8\xbf\x99\xe6\x98\xaf\xe4\xb8\x80\xe4\xb8\xaa\xe6\xb5\x8b\xe8\xaf\x95\xe9\x99\x84\xe4\xbb\xb6'.decode('utf-8')}]
                }

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formataddr

app.register(
    function_name="send_emails",
    function_description="send emails to subscriber",
    function_parameters={
        "type": "object",
        "properties": {
            "sublist" : {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name":{
                            "type":"string",
                            "description": "subscriber name",
                        },
                        "useraddress":{
                            "type":"string",
                            "description": "subscriber's email address",
                        }
                    },
                    "required": ["name","useraddress"],
                    "description": "One subscriber's information"
                },
                "description": "A list of subscriber's information"
            },
            "content" : {
                "type": "object",
                "properties": {
                    "title":{
                        "type":"string",
                        "description":"email title",
                    },
                    "text":{
                        "type":"string",
                        "description":"body text",
                    },
                    "attachments":{
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name":{
                                    "type":"string",
                                    "description":"Attachment name",
                                },
                                "content": {
                                    "type":"string",
                                    "description":"Binary attachment content,decoded by utf-8"
                                }
                            },
                            "description": "one attachment"
                         },
                        "description": "A list of attachments"
                    }
                },
                "required": ["title","text"]
            },
            "sender" : {
                "type": "object",
                "properties": {
                    "name":{
                        "type":"string",
                        "description":"sender name",
                    },
                    "useraddress":{
                        "type":"string",
                        "description":"sender's email address",
                    },
                    "password":{
                        "type":"string",
                        "description":"sender's email password"
                    }
                },
                "required": ["name","useraddress","password"]
            }
        },
        # "required": ["sublist","sender","content"]
        "required": ["sublist","content"]
    }
)

def smtp_login_obj(username,password):#password有时候要求是授权码
    smtp_obj = smtplib.SMTP_SSL("smtp.qq.com".encode(),465)#连接到SMTP服务器的端口号
    smtp_obj.login(username, password)
    return smtp_obj#函数返回已经登录的 SMTP 对象 smtp_obj

def gen_content_obj(content):#password有时候要求是授权码
    msg = MIMEMultipart()
    try:
        msg['Subject'] = content['title']
        text = MIMEText(content["text"], 'plain', 'utf-8')
        msg.attach(text)
    except Exception as e:
        print(f"Error occurred : {e}")
    if "attachments" in content:
        try:
            for attachment in content["attachments"]:
                obj = MIMEApplication(attachment["content"].encode('utf-8'))
                obj.add_header('Content-Disposition', 'attachment', filename=attachment["name"])
                msg.attach(obj)
        except Exception as e:
            print(f"Error occurred : {e}")
    return msg

@app.handler(func_list=['send_emails'])
def my_send_emails(req:PIARequest = None, func_name = '', func_args = ''):
    args = json.loads(func_args)
    sublist=args['sublist']
    content=args['content']
    print(content)
    # sender=args['sender']
    # content = test_content
    sender = test_sender
    try:
        with smtp_login_obj(sender["useraddress"], sender["password"]) as smtp_obj:
            for receiver in sublist:
                try:
                    msg = gen_content_obj(content=content)
                    msg['From'] = formataddr((sender["name"], sender["useraddress"]))
                    msg['To'] = formataddr((receiver["name"], receiver["useraddress"]))
                    # print(receiver["name"], receiver["useraddress"], sender["useraddress"])
                    # print(msg.as_string())
                    smtp_obj.sendmail(sender["useraddress"], receiver["useraddress"], msg.as_string())
                    print('Sent to: ' + receiver["useraddress"])
                except Exception as e:
                    print(f"Error occurred when sending email to {receiver['useraddress']}: {e}")
        return 'Successful'
    except Exception as e:
        print(f"Error occurred while handling SMTP connection: {e}")
        return 'Failed, reason: ' + str(e)

@app.mainloop(keep_alive = False)
def my_mainloop(argv:list = []):
    print('Email Bot is running...')


if __name__ == '__main__':
    #单独测试的时候直接运行这个文件
    app.function_lists['send_emails']['handler'](PIARequest(),'email',json.dumps({
            "sublist" : [test_receiver,],
            "sender" : test_sender,
            "content" : test_content
        })
    )