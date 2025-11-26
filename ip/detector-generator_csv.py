"""
safe_traffic_generator.py

Генерирует синтетические сетевые логи (CSV) для учебного тестирования детектора аномалий.
Не отправляет никакие пакеты в сеть — только создает записи (таймстамп, src, dst, proto, pkt_size, pkt_per_sec, label).

Как использовать:
python safe_traffic_generator.py
"""

import csv
import random
import time
from datetime import datetime, timedelta
from ipaddress import IPv4Address

# ========== Параметры генерации ==========
DURATION_SECONDS = 300           # общая длительность симуляции
NORMAL_RATE = 50                 # среднее пакетов в секунду (нормальный)
ANOMALY_EVENTS = [
    # каждый event: (start_sec, duration_sec, proto, intensity_multiplier, description)
    (60, 10, 'ICMP', 20, 'icmp-flood-like spike'),
    (150, 15, 'UDP', 15, 'udp-flood-like spike'),
    (240, 8, 'TCP', 25, 'tcp-syn-like spike'),
]
OUTPUT_CSV = 'synthetic_network_log.csv'
SEED = 42

random.seed(SEED)


# ======= Вспомогательные функции =======
def random_ip():
    # генерируем приватные адреса для реалистичности
    # выбираем подсети из 10.0.0.0/8 и 192.168.0.0/16
    if random.random() < 0.6:
        base = IPv4Address(int(IPv4Address('10.0.0.0')) + random.randint(1, 2**24 - 2))
    else:
        base = IPv4Address(int(IPv4Address('192.168.0.0')) + random.randint(1, 2**16 - 2))
    return str(base)


def choose_dst():
    # несколько серверов / шлюзов как цели
    servers = ['10.0.0.1', '10.0.0.2', '192.168.0.10', '192.168.0.11']
    return random.choice(servers)


def base_pkt_size(proto):
    if proto == 'ICMP':
        return random.randint(60, 120)
    if proto == 'UDP':
        return random.randint(60, 600)
    if proto == 'TCP':
        return random.randint(60, 1500)
    return random.randint(60, 1500)


def is_in_anomaly(t, anomaly):
    start, dur, proto, mult, _ = anomaly
    return (t >= start) and (t < start + dur) and proto


# ======= Основная генерация =======
def generate_logs(duration_s, normal_rate, anomaly_events):
    """
    Возвращает список записей:
    timestamp, src_ip, dst_ip, proto, pkt_size, pkts_in_sec, label
    label: 0 - normal, 1 - anomaly
    """
    start_time = datetime.utcnow()
    records = []

    for sec in range(duration_s):
        # Уровень интенсивности в этой секунде: нормальный базовый + внесённый шум
        base_pkts_this_sec = max(1, int(random.gauss(normal_rate, normal_rate * 0.2)))

        # Проверяем, есть ли аномалия на этот момент
        multiplier = 1.0
        label = 0
        active_anom = None
        for an in anomaly_events:
            s, d, proto, mult, desc = an
            if sec >= s and sec < s + d:
                multiplier = mult
                label = 1
                active_anom = an
                break

        pkts_to_generate = int(base_pkts_this_sec * multiplier)

        # если есть аномалия, распределяем пакеты чаще от малой группы IP, чтобы симулировать атаку
        if label == 1:
            # 1-3 атакующих IP
            attackers = [random_ip() for _ in range(random.randint(1, 3))]
        else:
            attackers = None

        for _ in range(pkts_to_generate):
            # timestamp внутри секунды: равномерно
            t_stamp = start_time + timedelta(seconds=sec, milliseconds=random.randint(0, 999))
            if label == 1:
                proto = active_anom[2]
            else:
                proto = random.choices(['TCP', 'UDP', 'ICMP'], weights=[0.6, 0.3, 0.1])[0]

            if label == 1:
                src = random.choice(attackers)
                dst = choose_dst()
            else:
                src = random_ip()
                dst = choose_dst() if random.random() < 0.7 else random_ip()

            pkt_size = base_pkt_size(proto)
            # добавим небольшую вариацию
            pkt_size = int(pkt_size * random.uniform(0.8, 1.2))

            # pkts_in_sec — сколько пакетов от этого src в текущую секунду (для простоты ставим 1..)
            pkts_in_sec = random.randint(1, 5) if label == 0 else random.randint(20, 200)

            rec = {
                'timestamp': t_stamp.isoformat() + 'Z',
                'src_ip': src,
                'dst_ip': dst,
                'protocol': proto,
                'pkt_size': pkt_size,
                'pkts_in_sec': pkts_in_sec,
                'label': label
            }
            records.append(rec)

    return records


# ======== Сохранение в CSV ========
def save_csv(records, path):
    fieldnames = ['timestamp', 'src_ip', 'dst_ip', 'protocol', 'pkt_size', 'pkts_in_sec', 'label']
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow(r)


# ======== Запуск генерации ========
if __name__ == '__main__':
    print("Генерируем синтетический трафик...")
    recs = generate_logs(DURATION_SECONDS, NORMAL_RATE, ANOMALY_EVENTS)
    save_csv(recs, OUTPUT_CSV)
    print(f"Создан файл: {OUTPUT_CSV} (записей: {len(recs)})")
    print("Примечание: файл содержит метку 'label' (0 — нормал, 1 — аномалия).")
