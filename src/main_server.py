import json
import socket
from threading import Thread
import os
from dotenv import load_dotenv
import logging
import valkey

# VARS
SERVER_IP = "10.1.107.112"
PORT = 8000

# LOGGING
format = "%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO, filemode='w', filename="server.log", datefmt="%H:%M:%S", force=True)

# ENV VARS
if load_dotenv():
    url: str | None = os.environ.get("SUPABASE_URL")
    key: str | None = os.environ.get("SUPABASE_KEY")

# CONNECTION HANDLER      
def new_conn(socket: socket.socket, address, idx: int):
    logging.info(f"connected on thread {idx}, {socket}, {tuple(address)}")
    ts = 0
    while True:
        data = socket.recv(1024)
        if len(data) == 0:
            continue
        
        data = json.dumps([val.split(',') for val in data.decode('utf-8').split("/")]).encode()
        print(data)
        vk.set(ts, data)
        logging.critical(data)
        ts += 1
    socket.close()

# SERVER
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# VALKEY
vk = valkey.Valkey(host='127.0.0.1', port=6379)

try:    
    server.bind((SERVER_IP, PORT))
    server.listen(0)
    print("listening on", SERVER_IP + ":" + str(PORT))
    idx = 1
    
    while True:
        client_socket, client_address = server.accept()
        
        print("connected\n", client_socket, tuple(client_address))
        Thread(target=new_conn, args=(client_socket, client_address, idx), daemon=True).start()
        idx += 1
finally:
    server.close()