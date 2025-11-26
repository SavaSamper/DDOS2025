"""
Streamlit-дашборд: симуляция сетевого трафика + realtime детектор аномалий (IsolationForest)

Безопасно: не отправляет пакеты в сеть. Генерирует синтетические логи и симулирует поток.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from sklearn.ensemble import IsolationForest
import matplotlib.pyplot as plt

st.set_page_config(page_title="NetSec Simulator & Anomaly Detector", layout="wide")

# --------------------
# Utility / generator
# --------------------
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

def random_ip():
    if random.random() < 0.6:
        return f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
    else:
        return f"192.168.{random.randint(0,255)}.{random.randint(1,254)}"

def base_pkt_size(proto):
    if proto == 'ICMP':
        return random.randint(60, 120)
    if proto == 'UDP':
        return random.randint(60, 600)
    if proto == 'TCP':
        return random.randint(60, 1500)
    return random.randint(60, 1500)

def generate_synthetic_logs(duration_seconds=300, normal_rate=50, anomaly_events=None):
    if anomaly_events is None:
        anomaly_events = [
            (30, 8, 'ICMP', 20, 'icmp-spike'),
            (90, 12, 'UDP', 15, 'udp-spike'),
            (150, 10, 'TCP', 25, 'tcp-spike'),
        ]
    start_time = datetime.utcnow()
    records = []
    for sec in range(duration_seconds):
        base_pkts_this_sec = max(1, int(np.random.normal(normal_rate, normal_rate * 0.15)))
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
        attackers = [random_ip() for _ in range(random.randint(1,3))] if label == 1 else None

        for _ in range(pkts_to_generate):
            t_stamp = start_time + timedelta(seconds=sec, milliseconds=random.randint(0,999))
            proto = active_anom[2] if label == 1 else random.choices(['TCP','UDP','ICMP'], weights=[0.6,0.3,0.1])[0]
            src = random.choice(attackers) if label == 1 else random_ip()
            dst = random.choice(['10.0.0.1','10.0.0.2','192.168.0.10','192.168.0.11']) if random.random() < 0.7 else random_ip()
            pkt_size = int(base_pkt_size(proto) * random.uniform(0.8,1.2))
            pkts_in_sec = random.randint(20,200) if label == 1 else random.randint(1,5)
            records.append({
                'timestamp': t_stamp.isoformat() + 'Z',
                'sec': sec,
                'src_ip': src,
                'dst_ip': dst,
                'protocol': proto,
                'pkt_size': pkt_size,
                'pkts_in_sec': pkts_in_sec,
                'label': label
            })
    return pd.DataFrame(records)

# --------------------
# Feature engineering
# --------------------
def aggregate_second_window(df_sec):
    total_packets = len(df_sec)
    unique_src = df_sec['src_ip'].nunique()
    avg_pkt_size = df_sec['pkt_size'].mean() if total_packets>0 else 0
    proto_counts = df_sec['protocol'].value_counts(normalize=True)
    pct_icmp = proto_counts.get('ICMP', 0.0)
    pct_udp = proto_counts.get('UDP', 0.0)
    pct_tcp = proto_counts.get('TCP', 0.0)
    max_pkts_from_src = df_sec.groupby('src_ip').size().max() if total_packets>0 else 0
    return {
        'pkt_rate': total_packets,
        'unique_src': unique_src,
        'avg_pkt_size': avg_pkt_size,
        'pct_icmp': pct_icmp,
        'pct_udp': pct_udp,
        'pct_tcp': pct_tcp,
        'max_pkts_from_src': max_pkts_from_src
    }

def build_feature_df(logs_df, duration_seconds):
    rows = []
    for sec in range(duration_seconds):
        sec_df = logs_df[logs_df['sec'] == sec]
        feats = aggregate_second_window(sec_df)
        feats['sec'] = sec
        feats['label'] = 1 if (not sec_df.empty and sec_df['label'].any()) else 0
        rows.append(feats)
    return pd.DataFrame(rows).set_index('sec')

# --------------------
# UI: Controls
# --------------------
st.title("📡 NetSec Simulator — Streamlit Real-time Anomaly Detector")

col1, col2 = st.columns([1,2])
with col1:
    st.header("Параметры симуляции")
    duration = st.number_input("Длительность симуляции (сек)", value=180, min_value=30, max_value=3600, step=30)
    normal_rate = st.number_input("Среднее пакетов/сек (нормально)", value=40, min_value=1, max_value=200)
    use_default_anoms = st.checkbox("Использовать дефолтные аномалии (icmp/udp/tcp)", value=True)
    if 'start_sim' not in st.session_state:
        st.session_state['start_sim'] = False
    if st.button("Сгенерировать данные и обучить модель"):
        st.session_state['start_sim'] = True

with col2:
    st.header("Модель и статус")
    st.markdown("IsolationForest будет обучен на первые 30% секунд как «нормальный» трафик.")
    n_estimators = st.slider("n_estimators (IsolationForest)", 10, 200, 100)
    contamination = st.slider("contamination (ожидаемая доля аномалий)", 0.0, 0.5, 0.02, step=0.01)
    if 'run_realtime' not in st.session_state:
        st.session_state['run_realtime'] = False
    if st.button("Запустить симуляцию в реальном времени"):
        st.session_state['run_realtime'] = True

# --------------------
# Placeholders для визуализации
# --------------------
placeholder_top = st.empty()
placeholder_charts = st.empty()
placeholder_table = st.empty()
placeholder_log = st.empty()
placeholder_download = st.empty()

# --------------------
# Main logic
# --------------------
if st.session_state['start_sim']:
    st.info("Генерируем синтетический трафик...")
    anomaly_events = None
    if use_default_anoms:
        anomaly_events = [
            (int(duration*0.15), max(5, int(duration*0.05)), 'ICMP', 18, 'icmp-spike'),
            (int(duration*0.5), max(6, int(duration*0.08)), 'UDP', 12, 'udp-spike'),
            (int(duration*0.75), max(5, int(duration*0.06)), 'TCP', 20, 'tcp-spike'),
        ]
    logs_df = generate_synthetic_logs(duration_seconds=duration, normal_rate=normal_rate, anomaly_events=anomaly_events)
    st.success(f"Создано записей: {len(logs_df)}")
    st.session_state['logs_df'] = logs_df

    st.info("Формируем признаки по секундам...")
    feat_df = build_feature_df(logs_df, duration)
    st.session_state['feat_df'] = feat_df
    st.success("Признаки сформированы.")

    train_cut = max(1, int(len(feat_df) * 0.3))
    X_train = feat_df.iloc[:train_cut][['pkt_rate','unique_src','avg_pkt_size','pct_icmp','pct_udp','pct_tcp','max_pkts_from_src']].fillna(0)
    clf = IsolationForest(n_estimators=n_estimators, contamination=contamination, random_state=RANDOM_SEED)
    clf.fit(X_train)
    st.session_state['clf'] = clf
    st.session_state['train_cut'] = train_cut

    with placeholder_top:
        st.subheader("Краткая статистика данных")
        c1, c2, c3 = st.columns(3)
        c1.metric("Записей логов", len(logs_df))
        c2.metric("Секунд (окна)", len(feat_df))
        c3.metric("Использовано для обучения (сек)", train_cut)

    csv_buffer = logs_df.to_csv(index=False)
    placeholder_download.download_button("⬇ Скачать raw CSV логов", data=csv_buffer, file_name="synthetic_network_logs.csv", mime="text/csv")

# --------------------
# Realtime simulation
# --------------------
if st.session_state['run_realtime']:
    if 'logs_df' not in st.session_state or 'feat_df' not in st.session_state or 'clf' not in st.session_state:
        st.error("Сначала нажмите «Сгенерировать данные и обучить модель»")
    else:
        logs_df = st.session_state['logs_df']
        feat_df = st.session_state['feat_df']
        clf = st.session_state['clf']
        train_cut = st.session_state['train_cut']

        st.info("Запускаем симуляцию по секундам (имитация реального времени).")
        chart_pkt = placeholder_charts.container()
        table_pl = placeholder_table.container()
        log_pl = placeholder_log.container()

        window = 60
        pkt_rates, anomaly_scores, secs, alerts = [], [], [], []

        for sec in range(len(feat_df)):
            row = feat_df.loc[sec]
            X_row = np.array([[row['pkt_rate'], row['unique_src'], row['avg_pkt_size'],
                               row['pct_icmp'], row['pct_udp'], row['pct_tcp'],
                               row['max_pkts_from_src']]])
            pred = clf.predict(X_row)[0]
            score = clf.decision_function(X_row)[0]
            is_anom = 1 if pred == -1 else 0

            pkt_rates.append(row['pkt_rate'])
            anomaly_scores.append(score)
            secs.append(sec)
            if is_anom:
                alerts.append((sec, row['pkt_rate'], row['label']))

            pkt_rates_display = pkt_rates[-window:]
            anomaly_scores_display = anomaly_scores[-window:]
            secs_display = secs[-window:]

            with chart_pkt:
                fig, (ax1, ax2) = plt.subplots(2,1, figsize=(10,5), constrained_layout=True)
                ax1.plot(secs_display, pkt_rates_display)
                ax1.set_title("Пакетов/сек (временной ряд)")
                ax1.set_ylabel("pkt_rate")
                ax1.grid(True)
                ax2.plot(secs_display, anomaly_scores_display)
                ax2.axhline(0, linestyle='--')
                ax2.set_title("Decision function (IsolationForest)")
                ax2.set_ylabel("score")
                ax2.set_xlabel("sec")
                ax2.grid(True)
                st.pyplot(fig)

            with table_pl:
                sub = feat_df.iloc[max(0, sec-10):sec+1].copy()
                Xsub = sub[['pkt_rate','unique_src','avg_pkt_size','pct_icmp','pct_udp','pct_tcp','max_pkts_from_src']].fillna(0)
                sub['pred_anomaly'] = (clf.predict(Xsub) == -1).astype(int)
                st.dataframe(sub.tail(10))

            with log_pl:
                if is_anom:
                    st.warning(f"ANOMALY @ sec={sec} | pkt_rate={int(row['pkt_rate'])} | true_label={int(row['label'])}")
                else:
                    st.info(f"sec={sec} | pkt_rate={int(row['pkt_rate'])} | normal")

            # Кнопка прерывания
            if st.button("Прервать симуляцию", key=f"stop_{sec}"):
                st.session_state['run_realtime'] = False
                st.warning("Симуляция прервана пользователем.")
                break

        st.success("Симуляция завершена.")
        if len(alerts) > 0:
            st.subheader("Логи сработавших алертов")
            df_alerts = pd.DataFrame(alerts, columns=['sec','pkt_rate','label'])
            st.table(df_alerts)
        else:
            st.info("Аномалии не обнаружены моделью.")
