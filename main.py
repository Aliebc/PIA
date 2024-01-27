#!/usr/bin/env python3
#######################
# AI Assistant Python Framework
# Date: 2024-01-25
#######################

__version__ = '1.0.0'

from checklist import ck as module_check
from classes import Configure, PIAError, PIAListener, PIAModule, PIAMessage, PIARequest, PIAResponseMessage, PIAResponse
from getopt import getopt, GetoptError
import sys
import os
import re
import platform
import random
from rich import print as rprint
from pydantic import BaseModel, Field
from typing import List, Optional, Callable
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from multiprocess import Process
import signal
import time
import pickle
import copy

from openai import OpenAI

HELP_TEXT = """PIA - Intelligent Assistant ({})
Usage: {} [options] [args]

-h, --help      Show this help text.
-v, --version   Show version info.
-c, --config    Set configure file path and variable name [default: config:c, use None to set default value].
-m, --module    Load agents/modules from py file [default: None].
-l, --listen    Load frontend listener from py file [default: None].
--show-config   Show configure info.
--daemon        Start daemon mode. (Linux/MacOS only)
--server        Setup a simple socket server to debug PIA.
""".format(platform.platform(),sys.argv[0])

class PIASettings(BaseModel):
    c: Configure = Configure()
    show_config: bool = False
    show_help: bool = False
    set_config: bool = False
    config_file: str = Field('config:c', pattern=r'^[a-zA-Z0-9_]+(:[a-zA-Z0-9_]+)?$')
    module_lists: list = []
    modules: List[PIAModule] = []
    modules_process: List = []
    listen_lists: list = []
    listeners: List[PIAListener] = []
    listeners_process: List = []
    daemon: bool = False
    server: list = None
    
g_settings = PIASettings()

def show_help():
    print(HELP_TEXT, end='')
    sys.exit()
    
def daemon():
    if not hasattr(os, 'fork'):
        print('DaemonError: Your system does not support daemon mode.')
        sys.exit(1)
    pd = os.fork()
    if pd > 0:
        sys.exit(0)
    os.close(0)
    os.close(1)
        
def show_version():
    print('Version: PIA-Core/{}'.format(__version__))
    
def main_send(tp):
    settings: PIASettings = tp[0]
    tname: str = tp[1][5:]
    db = sqlite3.connect(settings.c.loop.db_path)
    cur = db.cursor()
    cur.execute(
        '''
        SELECT UID,UNAME,LISTENER FROM pia_listener WHERE UID = '{}'
        '''.format(tname)
    )
    df1 = cur.fetchall()
    if len(df1) == 0:
        return "OK"
    listener: PIAListener = None
    for l in settings.listeners:
        if l.uuid == df1[0][2]:
            listener = l
            break
    if listener is None:
        return "OK"
    cur.execute(
        '''
        SELECT NAME,TYPE,TEXT,CONTENT,TIME,IS_ME,IS_AI,SENT,ID FROM 
        chat_{} WHERE SENT = 0 AND IS_DELETED = 0 AND IS_ME = 1
        '''.format(tname)
    )
    df = cur.fetchall()
    for d in df:
        if d[1] == 0:
            st = listener.i_sender(PIAResponse(
                t_uid = tname,
                t_uname = df1[0][1],
                messages = [
                    PIAResponseMessage(
                        type=0,
                        uname=d[0],
                        text=d[2],
                        timestamp=d[4]
                    )
                ]
            ))
            if st:
                cur.execute(
                    '''
                    UPDATE chat_{} SET SENT = 1 WHERE ID = {}
                    '''.format(tname, d[8])
                )
                db.commit()
    db.close()
    return "Sent"
    
def main_exec(tp):
    settings: PIASettings = tp[0]
    tname: str = tp[1][5:]
    db = sqlite3.connect(settings.c.loop.db_path)
    cur = db.cursor()
    cur.execute(
        '''
        SELECT NAME,TYPE,TEXT,CONTENT,TIME,IS_ME,IS_AI FROM 
        chat_{} WHERE IS_DELETED = 0 AND ID > (SELECT MAX(ID) - {} FROM chat_{} WHERE IS_DELETED = 0)
        '''.format(tname, settings.c.loop.memory, tname)
    )
    df = cur.fetchall()
    if len(df) == 0:
        return "No message"
    if df[-1][5] == 1:
        return "Answered"
    if int(time.time()*1000) - df[-1][4]  < settings.c.loop.max_wait_time * 1000:
        return "Waiting"
    respT = ""
    try:
        ai = OpenAI(
            api_key = settings.c.openai.api_key,
            base_url = settings.c.openai.api_base
        )
        my_tools = []
        my_tools_table = {}
        for m in settings.modules:
            for i,j in m.function_lists.items():
                jj = copy.deepcopy(j)
                jj['handler'] = []
                my_tools.append({
                    'type' : 'function',
                    'function' : jj
                })
                my_tools_table[i] = j
        u_prompt = ''
        uname = tname
        for d in df:
            if d[1] == 0:
                ti: str = time.strftime("%Y-%m-%d %H时%M分%S秒", time.localtime(d[4]/1000))
                u_prompt += d[0] + f"({ti})" + ": " + d[2] + "\n"
            if d[6]!= 0:
                uname = d[0]
        mess = [
        {
                    "role" : "system",
                    "content" : 
                    settings.c.context.system_prompt.format(uname, 
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        },
        {
                    "role" : "user",
                    "content" : u_prompt
        }
        ]
        #rprint(mess)
        comp = ai.chat.completions.create(
            model = settings.c.context.model,
            messages = mess,
            tool_choice="auto" if len(my_tools) > 0 else None,
            tools=my_tools if len(my_tools) > 0 else None,
        )
        mess.append(comp.choices[0].message)
        while comp.choices[0].message.tool_calls:
            tool_calls = comp.choices[0].message.tool_calls
            for tool_call in tool_calls:
                caller = my_tools_table[tool_call.function.name]['handler']
                args = tool_call.function.arguments
                resp = caller(
                    PIARequest(), 
                    tool_call.function.name, 
                    tool_call.function.arguments
                )
                mess.append({
                    'tool_call_id': tool_call.id,
                    'role': 'tool',
                    "name": tool_call.function.name,
                    "content": resp,
                })
            comp = ai.chat.completions.create(
                model = settings.c.context.model,
                messages = mess
            )
            mess.append(comp.choices[0].message)
        respT = comp.choices[0].message.content
    except Exception as e:
        print(e)
        respT = settings.c.context.error_format.format(str(e))
    db.execute(
        '''
        INSERT INTO chat_{} (NAME, TEXT, TIME, IS_MENTIONED, IS_ME, IS_AI, LISTENER, TOKENS_ALL, TOKENS_PROMPT) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''.format(tname),
        (
            "ME",
            respT,
            int(time.time()*1000),
            0,
            1,
            1,
            'openai',
            comp.usage.total_tokens,
            comp.usage.prompt_tokens
        )
    )
    db.commit()
    db.close()
    return "OK"
    
def main_loop(settings: PIASettings):
    while True:
        time.sleep(settings.c.loop.interval)
        db = sqlite3.connect(settings.c.loop.db_path)
        cur = db.cursor()
        cur.execute(
            '''
            SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'chat_%'
            '''
        )
        tables = cur.fetchall()
        tables = [(settings, i[0]) for i in tables]
        with ThreadPoolExecutor(max_workers=settings.c.loop.max_workers) as executor:
            for i in executor.map(main_exec, tables):
                #print(i)
                pass
            for j in executor.map(main_send, tables):
                #print(j)
                pass
            executor.shutdown(wait=True)

def listener_call(message: PIAMessage, listener: PIAListener):
    #print(message, listener)
    db = sqlite3.connect(g_settings.c.loop.db_path)
    cur = db.cursor()
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS chat_{} (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            NAME TEXT NOT NULL,
            TYPE INTEGER NOT NULL DEFAULT 0,
            TEXT TEXT,
            CONTENT BLOB,
            TIME INTEGER NOT NULL,
            IS_MENTIONED INTEGER NOT NULL,
            IS_ME INTEGER NOT NULL,
            IS_AI INTEGER NOT NULL,
            IS_DELETED INTEGER NOT NULL DEFAULT 0,
            SENT INTEGER NOT NULL DEFAULT 0,
            LISTENER TEXT NOT NULL,
            TOKENS_ALL INTEGER NOT NULL DEFAULT 0,
            TOKENS_PROMPT INTEGER NOT NULL DEFAULT 0
        )
        '''.format(message.uid)
    )
    db.commit()
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS pia_listener (
            UID TEXT UNIQUE PRIMARY KEY,
            UNAME TEXT NOT NULL,
            LISTENER TEXT NOT NULL
        )
        '''
    )
    db.commit()
    if message.type == 0:
        db.execute(
            '''
            INSERT INTO chat_{} (NAME, TEXT, TIME, IS_MENTIONED, IS_ME, IS_AI, LISTENER) VALUES (?, ?, ?, ?, ?, ?, ?)
            '''.format(message.uid),
            (
                message.uname,
                message.text,
                message.timestamp,
                0,
                0,
                message.is_ai,
                listener.m_name
            )
        )
    elif message.type == 8:
        if message.text == 'clear':
            db.execute(
                '''
                UPDATE chat_{} SET IS_DELETED = 1
                '''.format(message.uid)
            )
        
    db.commit()
    
    db.execute(
        '''
        INSERT OR IGNORE INTO pia_listener (UID, UNAME, LISTENER) VALUES (?, ?, ?)
        ''',
        (
            message.uid,
            message.uname,
            listener.uuid
        )
    )
    db.commit()
    db.close()
    return 'OK'

def module_call(module: PIAModule, response: PIAResponse, direct: bool = True):
    message: PIAResponseMessage
    db = sqlite3.connect(g_settings.c.loop.db_path)
    cur = db.cursor()
    cur.execute(
        '''
        SELECT UID,UNAME,LISTENER FROM pia_listener WHERE UID = '{}'
        '''.format(response.t_uid)
    )
    df = cur.fetchall()
    if len(df) == 0:
        return False
    tname = df[0][0]
    for message in response.messages:
        if message.type == 0:
            db.execute(
                '''
                INSERT INTO chat_{} (NAME, TEXT, TIME, IS_MENTIONED, IS_ME, IS_AI, LISTENER) VALUES (?, ?, ?, ?, ?, ?, ?)
                '''.format(tname),
                (
                    message.uname,
                    message.text,
                    message.timestamp,
                    0,
                    1 if direct else 0,
                    1,
                    module.m_name
                )
            )
            db.commit()
    db.close()
    return True

def sig_exit(signum, frame):
    for l in g_settings.listeners:
        l.stop()
    sys.exit(0)
    
signal.signal(signal.SIGINT, sig_exit)

if __name__ == '__main__':
    try:
        opts, args = getopt(sys.argv[1:], 'hvc:m:l:', 
            ['help', 
            'version', 
            'config=', 
            'show-config', 
            'module=', 
            'daemon',
            'server=',
            'listen=']
        )
    except GetoptError as e:
        print('OptionError: ' + e.msg)
        print('Use -h or --help for help.')
        sys.exit(1)
    for opt, arg in opts:
        if opt == '-h' or opt == '--help':
            g_settings.show_help = True
        elif opt == '-v' or opt == '--version':
            show_version()
            sys.exit()
        elif opt == '-c' or opt == '--config':
            g_settings.config_file = arg
        elif opt == '--show-config':
            g_settings.show_config = True
        elif opt == '-m' or opt == '--module':
            if arg not in g_settings.module_lists:
                g_settings.module_lists.append(arg)
        elif opt == '-l' or opt == '--listen':
            if arg not in g_settings.listen_lists:
                g_settings.listen_lists.append(arg)
        elif opt == '--server':
            g_settings.server = arg
    if g_settings.config_file != 'None':
        try:
            c: Configure = Configure()
            cf = g_settings.config_file.split(':')
            if len(cf) == 1:
                cf.append('c')
            if len(cf) > 2:
                raise PIAError('Invalid configure file path.')
            exec('from {} import {} as c'.format(cf[0], cf[1]))
            g_settings.c = c
        except PIAError as e:
            print('ConfigError: ' + str(e))
            print('Use -h or --help for help.')
            sys.exit(1)
    if g_settings.show_help:
        show_help()
    if g_settings.server:
        g_settings.listen_lists = ['listeners.lsocket:app']
    if True:
        for m in g_settings.module_lists:
            try:
                ml = m.split(',')
                mf = ml[0].split(':')
                if len(mf) == 1:
                    mf.append('app')
                if len(mf) > 2:
                    raise PIAError('Invalid module file path.')
                ms: PIAModule = None
                exec('from {} import {} as ms'.format(mf[0], mf[1]))
                ms.set_args(ml)
                g_settings.modules.append(ms)
            except PIAError as e:
                print('ModuleError: ' + str(e))
                print('Use -h or --help for help.')
                sys.exit(1)
        for l in g_settings.listen_lists:
            try:
                ll = l.split(',')
                lf = ll[0].split(':')
                if len(lf) == 1:
                    lf.append('app')
                if len(lf) > 2:
                    raise PIAError('Invalid listener file path.')
                ls: PIAListener = None
                exec('from {} import {} as ls'.format(lf[0], lf[1]))
                ls.set_args(ll)
                g_settings.listeners.append(ls)
            except PIAError as e:
                print('ListenerError: ' + str(e))
                print('Use -h or --help for help.')
                sys.exit(1)
    if g_settings.show_config:
        print('You can use -c or --config to set configure file path.')
        print('Configure path: {}'.format(g_settings.config_file))
        rprint(g_settings.c)
        rprint('Modules: {}'.format(g_settings.modules))
        rprint('Listeners: {}'.format(g_settings.listeners))
        sys.exit()
    if len(g_settings.module_lists) == 0 and len(g_settings.listen_lists) == 0:
        show_version()
        print('You should add at least one module and listener.')
        print('Use -h or --help for help.')
        sys.exit()
    if g_settings.daemon:
        daemon()
    
    for l in g_settings.listeners:
        l.set_call(listener_call)
    for m in g_settings.modules:
        m.set_call(module_call)
    g_settings.listeners_process = [l.run() for l in g_settings.listeners]
    g_settings.modules_process = [m.run() for m in g_settings.modules]
    mainl = Process(target=main_loop, args=(g_settings,))
    mainl.start()
    mainl.join()
    listener_ps_join = [l.join() for l in g_settings.listeners_process]
    
