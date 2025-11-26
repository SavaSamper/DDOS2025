import streamlit as st
import numpy as np
import pandas as pd
import time
from sklearn.ensemble import IsolationForest
from collections import Counter
import random
import math

# -----------------------------
# Генерация трафика под атакой
# -----------------------------

def generate_traffic(attack=False):
    if attack:
        packet_rate = random.randint(20000, 60000)
        tcp = random.randint(15000, 40000)
        udp = random.randint(3000, 15000)
        icmp = random.randint(2000, 8000)
        avg_size = random.randint(200, 500)
        src_ips = [f"10.0.0.{random.randint(1,10)}" for _ in range(300)]
    else:
        packet_rate = random.randint(200, 3000)
        tcp = random.randint(50, 2000)
        udp = random.randint(20, 800)
        icmp = random.randint(5, 50)
        avg_size = random.randint(400, 1500)
        src_ips = [f"10.0.0.{random.randint(1,40)}" for _ in range(50)]

    # энтропия IP
    def entropy(values):
        counts = Counter(values)
        probs = [c / len(values) for c in counts.values()]
        return -sum(p * math.log(p, 2) for p in probs)

    return {
        "packet_rate": packet_rate,
        "tcp": tcp,
        "udp": udp,
        "icmp": icmp,
        "avg_size": avg_size,
        "src_entropy": entropy(src_ips),
        "ratio_tcp_udp": tcp / (udp + 1),
        "burst": packet_rate / (avg_size + 1)
    }


# -----------------------------
# Streamlit dashboard
# -----------------------------

st.title("🛡 AI-система анализа трафика в реальном времени")

placeholder = st.empty()

# модель
model = IsolationForest(contamination=0.15)

# буфер данных
data_window = []

st.write("Запуск… обучение модели")

# первичное обучение
for _ in range(200):
    row = generate_traffic(attack=False)
    data_window.append(row)

df = pd.DataFrame(data_window)
model.fit(df)

st.success("Модель обучена!")

attack_mode = st.checkbox("Включить учебную атаку")

log = st.empty()

while True:
    row = generate_traffic(attack=attack_mode)
    data_window.append(row)
    df = pd.DataFrame(data_window[-200:])

    pred = model.predict([list(row.values())])[0]   # -1 = anomaly
    is_anomaly = (pred == -1)

    with placeholder.container():
        st.metric("Packet rate", row["packet_rate"])
        st.metric("Entropy", round(row["src_entropy"], 2))
        st.metric("TCP/UDP", round(row["ratio_tcp_udp"], 2))
        st.metric("Anomaly", "🔥 YES" if is_anomaly else "OK")

    log.write(df.tail(15))

    time.sleep(0.5)
