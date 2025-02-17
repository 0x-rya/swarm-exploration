import socket
from threading import Thread

SERVER_IP = "10.1.32.230"
PORT = 8000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def new_conn(socket: socket.socket, address):
    print("connected\n", socket, tuple(address), flush=True)
    
    while True:
        continue
    socket.close()

try:    
    server.bind((SERVER_IP, PORT))
    server.listen(0)
    print("listening on", SERVER_IP + ":" + str(PORT))
    while True:
        client_socket, client_address = server.accept()
        # print("connected\n", client_socket, tuple(client_address))
        Thread(target=new_conn, args=(client_socket, client_address))
        
finally:
    # if not myServer._closed:
    server.close()