from scapy.all import sniff
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

packet_count = 0   # количество пакетов за секунду

def on_packet(pkt):
    global packet_count
    packet_count += 1

# запускаем прослушивание пакетов в фоне
import threading
threading.Thread(target=lambda: sniff(prn=on_packet, store=False), daemon=True).start()

counts = []

def update(i):
    global packet_count
    counts.append(packet_count)
    packet_count = 0

    plt.cla()
    plt.plot(counts, label="Packets per second")
    plt.legend()
    plt.xlabel("Seconds")
    plt.ylabel("Packets")

ani = FuncAnimation(plt.gcf(), update, interval=1000)
plt.title("Входящие пакеты (PPS)")
plt.show()
