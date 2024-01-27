from classes import PIAListener, PIAMessage, PIAResponseMessage, PIAResponse
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

@app.mainloop(keep_alive = True)
def loop(fargs):
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sk.bind(('127.0.0.1', 8167))
    sk.listen(5)
    conn, addr = sk.accept()
    nw = conn
    conn.send(b'PIA Socket Listener\n')
    while True:
        conn.send(b'>>> ')
        data = conn.recv(1024)
        if len(data) == 0:
            break
        st = app.call(message=PIAMessage(
            uid = uid,
            uname = 'PIA-Tester',
            text = data.decode('utf-8'),
            type = 0,
            timestamp = int(time.time() * 1000)
        ))
    return True

@app.sender()
def sendto(message: PIAResponse):
    global nw
    print(message)
    message = message.messages[0]
    if message.type != 0:
        return False
    txt = message.text
    #a = nw.send(txt.encode('utf-8'))
    a = print(txt)
    return True