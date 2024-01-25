#!/usr/bin/env python3
#######################
# AI Assistant Python Framework
# Date: 2024-01-25
#######################

__version__ = '1.0.0'

from checklist import ck as module_check
#from config import c
from classes import Configure
from getopt import getopt, GetoptError
import sys
import os
import re
import platform
from rich import print

HELP_TEXT = """PIA - Intelligent Assistant ({})
Usage: {} [options] [args]

-h, --help      Show this help text.
-v, --version   Show version info.
-c, --config    Set configure file path and variable name [default: config:c, use None to set default value].
-m, --module    Load agents/modules from py file [default: None].
-l, --listen    Load frontend listener from py file [default: None].
--show-config   Show configure info.
--daemon        Start daemon mode. (Linux/MacOS only)
""".format(platform.platform(),sys.argv[0])

# Global variables
global_settings = {
    'c' : Configure(),
    'show_config' : False,
    'show_help'   : False,
    'set_config'  : False,
    'config_file' : 'config:c',
    'model_lists' : [],
    'listen_lists': [],
    'daemon'      : False,
}

def show_help():
    print(HELP_TEXT, end='')
    sys.exit()
    
def daemon():
    if not hasattr(os, 'fork'):
        print('DaemonError: Your system does not support daemon mode.')
        sys.exit(1)
        
def show_version():
    print('Version: PIA-Core/{}'.format(__version__))

if __name__ == '__main__':
    try:
        opts, args = getopt(sys.argv[1:], 'hvc:m:l:', 
            ['help', 
            'version', 
            'config=', 
            'show-config', 
            'module=', 
            'daemon',
            'listen=']
        )
    except GetoptError as e:
        print('OptionError: ' + e.msg)
        print('Use -h or --help for help.')
        sys.exit(1)
    for opt, arg in opts:
        if opt == '-h' or opt == '--help':
            global_settings['show_help'] = True
        elif opt == '-v' or opt == '--version':
            show_version()
            sys.exit()
        elif opt == '-c' or opt == '--config':
            global_settings['config_file'] = arg
        elif opt == '--show-config':
            global_settings['show_config'] = True
        elif opt == '-m' or opt == '--module':
            global_settings['model_lists'].append(arg)
        elif opt == '-l' or opt == '--listen':
            global_settings['listen_lists'].append(arg)
    if global_settings['config_file'] != 'None':
        try:
            c: Configure = Configure()
            cf = global_settings['config_file'].split(':')
            if len(cf) == 1:
                cf.append('c')
            if len(cf) > 2:
                raise Exception('Invalid configure file path.')
            exec('from {} import {} as c'.format(cf[0], cf[1]))
            global_settings['c'] = c
        except Exception as e:
            print('ConfigError: ' + str(e))
            print('Use -h or --help for help.')
            sys.exit(1)
    if global_settings['show_help']:
        show_help()
    if global_settings['show_config']:
        print('You can use -c or --config to set configure file path.')
        print('Configure path: {}'.format(global_settings['config_file']))
        print(global_settings['c'])
        sys.exit()
    if len(global_settings['model_lists']) == 0 and len(global_settings['listen_lists']) == 0:
        show_version()
        print('You should add at least one module and listener.')
        print('Use -h or --help for help.')
        sys.exit()
    if global_settings['daemon']:
        daemon()
        

GENERATED_CONFIG = """
from classes import Configure

c = Configure()
c.loop.db_path = "wx_secret2.db"
c.loop.max_wait_time = 15
c.loop.memory = 10
"""