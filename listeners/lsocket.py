from classes import PIAListener, PIAMessage, PIAResponseMessage, PIAResponse
from classes import PIAProcess
from getopt import GetoptError,getopt
import socket
import time
import hashlib
import os


def md5s(s):
    m = hashlib.md5()
    m.update(s.encode("utf-8"))
    return m.hexdigest()

app = PIAListener(
    uuid = 'dbdca259-6dc9-40cb-b232-0861ec4888d5',
    m_name='PIA Socket Listener',
    author='Aliebc',
    version='0.0.1',
)

uid = md5s(os.getcwd())

nw: socket.socket

#conn_state : dict = {}
conn_state = PIAProcess.Manager().dict()

@app.mainloop(keep_alive = False, shared = conn_state)
def loop(fargs, args, kwargs):
    host = '127.0.0.1'
    port = 8167
    if len(fargs) > 1:
        try:
            opts, args = getopt(fargs[1:], 'h:p:', ['host=', 'port='])
        except GetoptError:
            print('PIA Socket Listener Usage: -h <host> -p <port>')
            return
        for opt, arg in opts:
            if opt in ('-h', '--host'):
                host = arg
            elif opt in ('-p', '--port'):
                port = int(arg)
    conn_state = kwargs['shared']
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sk.bind((host, port))
    sk.listen(5)
    print('[*] PIA Socket Listener is listening on %s:%d' % (host, port))
    while True:
        conn, addr = sk.accept()
        nw = conn
        conn.send(b'PIA Socket Listener\n')
        while True:
            conn.send(b'>>> ')
            data = conn.recv(1024)
            if len(data) <= 0:
                break
            conn_state[uid] = conn
            st = app.call(message=PIAMessage(
                uid = uid,
                uname = 'PIA-Tester',
                text = data.decode('utf-8'),
                type = 0,
                is_ai = False,
                timestamp = int(time.time() * 1000)
            ))
        conn_state.pop(uid)
        

@app.sender()
def sendto(messages: PIAResponse):
    global conn_state
    message:PIAResponseMessage = messages.messages[0]
    if message.type != 0:
        return False
    txt = message.text
    print('>>>AI: ' + txt)
    if messages.t_uid in conn_state.keys():
        cto : socket.socket = conn_state[messages.t_uid]
        cto.send(b'|AI| ')
        cto.send(txt.encode('utf-8'))
        cto.send(b'\n>>> ')
    return True