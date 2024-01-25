#!/usr/bin/env python3
#######################
# AI Assistant Python Framework
# Date: 2024-01-25
#######################

__version__ = '1.0.0'

from checklist import ck as module_check
#from config import c
from classes import Configure
from getopt import getopt
import sys
import os
import platform

HELP_TEXT = """PIA - Intelligent Assistant ({})
Usage: {} [options] [args]

-h, --help      Show this help text.
-v, --version   Show version info.
-c, --config    Set configure file path [default: config.py].
-m, --module    Load agents modules from py file [default: None].
-l, --listen    Load frontend listener from py file [default: None].
--show-config   Show configure info.
--daemon        Start daemon mode. (Linux/MacOS only)
""".format(platform.platform(),sys.argv[0])

# Global variables
global_settings = {
    'c' : Configure(),
    'show_config' : False,
    'show_help'   : False,
    'config_file' : 'config.py',
    'model_lists' : [],
    'listen_lists': [],
}

def show_help():
    print(HELP_TEXT, end='')
    sys.exit()

if __name__ == '__main__':
    opts, args = getopt(sys.argv[1:], 'hvc:', 
        ['help', 'version', 'config=']
    )
    for opt, arg in opts:
        if opt == '-h' or opt == '--help':
            global_settings['show_help'] = True
        elif opt == '-v' or opt == '--version':
            print('Version: PIA/{}'.format(__version__))
            sys.exit()
        elif opt == '-c' or opt == '--config':
            global_settings['config_file'] = arg
    if global_settings['show_help']:
        show_help()
    if len(global_settings['model_lists']) == 0 and len(global_settings['listen_lists']) == 0:
        print('Version: PIA/{}'.format(__version__))
        print('Use -h or --help for help.')
        sys.exit()