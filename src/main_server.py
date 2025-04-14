import math
import time
import random
import valkey
import socket
import logging
import robo_em
from threading import Thread

# VARS
VALKEY_IP = '127.0.0.1' # "10.1.107.112"
PORT = 8000

# LOGGING
format = "%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO, filemode='w', filename="server.log", datefmt="%H:%M:%S", force=True)

# CONNECTION HANDLER      
def new_conn(socket: socket.socket, address, idx: int, commRange: int):
    logging.info(f"connected on thread {idx}, {socket}, {tuple(address)}")
    
    # Send the robot ID to the client so it knows its identifier
    socket.send(str(idx).encode('utf-8'))
    
    while True:
        data = socket.recv(1024)
        if len(data) == 0:
            continue
        
        # Store with timestamp and robot ID
        timestamp = time.time()
        data_str = data.decode('utf-8')
        
        # Maintain a set of active robots
        vk.sadd("active_robots", str(idx))
        # vk.expire(f"robot:{idx}:active", 5)  # Robot considered inactive after 5 seconds

        if data_str == "Connection Established":
            continue
        
        # Format: timestamp,robot_id,data
        storage_data = f"{timestamp},{idx},{commRange},{data_str}"
        
        # Store in a list for each robot to make retrieval easier
        vk.rpush(f"robot:{idx}:history", storage_data)

        (pos_x, pos_y), parsedData, err = robo_em.parse_data_str(data_str)
        if err:
            continue

        pos_x, pos_y = int(pos_x), int(pos_y)
        for (x, y), value in parsedData:
            if value == 1:                                      ## update only if value is 1, because 0 might conflict with other robots' data
                vk.set(f"robot:{idx}:km:{idx}:{x}:{y}", value)

        for other_idx in vk.smembers("active_robots"):
            other_idx = int(other_idx.decode("utf-8"))

            if other_idx == idx:
                continue
            histData = vk.lrange(f"robot:{other_idx}:history", -1, -1)
            if len(histData) == 0:
                continue
            else:
                histData = histData[0].decode("utf-8")
            (other_x, other_y), _, err = robo_em.parse_data_str(histData)
            if err:
                continue

            other_x, other_y = int(other_x), int(other_y)
            dist = math.sqrt(
                (pos_x - other_x) ** 2 + (pos_y - other_y) ** 2
            )
            print(f"{pos_x, pos_y} and {other_x, other_y} give {dist}")
            if dist < commRange:
                kms = vk.keys(f"robot:{other_idx}:km:{other_idx}:*")
                for km in kms:
                    km = km.decode("utf-8")
                    x, y = km.split(":")[-2:]
                    value = vk.get(km).decode("utf-8")
                    resp = vk.set(
                        f"robot:{idx}:km:{other_idx}:{x}:{y}",
                        value
                    )
        
        logging.info(f"Stored data: {storage_data}")
    
    # If we get here, the connection was closed
    vk.srem("active_robots", str(idx))
    socket.close()

# SERVER
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# VALKEY
vk = valkey.Valkey(host=VALKEY_IP, port=6379)

try:    
    server.bind(('127.0.0.1', PORT))
    server.listen(0)
    print("listening on", VALKEY_IP + ":" + str(PORT))
    idx = 1
    
    # Clear any previous robot data
    vk.delete("active_robots")
    
    while True:
        client_socket, client_address = server.accept()
        
        print("connected\n", client_socket, tuple(client_address))
        Thread(target=new_conn, args=(client_socket, client_address, idx, random.randint(2, 5)), daemon=True).start()
        idx += 1
finally:
    server.close()
