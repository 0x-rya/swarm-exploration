import socket
from threading import Thread
import os
from dotenv import load_dotenv
import logging

# VARS
SERVER_IP = "10.1.32.230"
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
    
    while True:
        data = socket.recv(1024)
        print(data)
        logging.critical(data)
    socket.close()

# SERVER
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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