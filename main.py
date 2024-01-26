#!/usr/bin/env python3
#######################
# AI Assistant Python Framework
# Date: 2024-01-25
#######################

__version__ = '1.0.0'

from checklist import ck as module_check
from classes import Configure, PIAError, PIAListener, PIAModule, PIAMessage
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
    listen_lists: list = []
    listeners: List[PIAListener] = []
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
        
def show_version():
    print('Version: PIA-Core/{}'.format(__version__))
    
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
        tables = [i[0] for i in tables]
        pass

def listener_call(message: PIAMessage, listener: PIAListener):
    print(message, listener)
    db = sqlite3.connect(g_settings.c.loop.db_path)
    cur = db.cursor()
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS chat_{} (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            NAME TEXT NOT NULL,
            CONTENT TEXT NOT NULL,
            TIME INTEGER NOT NULL,
            IS_MENTIONED INTEGER NOT NULL,
            IS_ME INTEGER NOT NULL,
            IS_AI INTEGER NOT NULL,
            IS_DELETED INTEGER NOT NULL DEFAULT 0,
            LISTENER TEXT NOT NULL,
            TOKENS_ALL INTEGER NOT NULL DEFAULT 0,
            TOKENS_PROMPT INTEGER NOT NULL DEFAULT 0
        )
        '''.format(message.uid)
    )
    db.commit()
    db.execute(
        '''
        INSERT INTO chat_{} (NAME, CONTENT, TIME, IS_MENTIONED, IS_ME, IS_AI, LISTENER) VALUES (?, ?, ?, ?, ?, ?, ?)
        '''.format(message.uid),
        (
            message.uname,
            message.text,
            message.timestamp,
            0,
            0,
            1,
            listener.m_name
        )
    )
    db.commit()
    db.close()
    return 'OK'

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
                ms: PIAModule = None
                exec('from {} import {} as ms'.format(mf[0], mf[1]))
                ms.set_args(ml)
                g_settings.modules.append(m)
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
    listener_ps_list = [l.run() for l in g_settings.listeners]
    mainl = Process(target=main_loop, args=(g_settings,))
    mainl.start()
    mainl.join()
    listener_ps_join = [l.join() for l in listener_ps_list]
    
