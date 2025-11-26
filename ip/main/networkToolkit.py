import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest

# Настройки страницы
st.set_page_config(page_title="Network Toolkit", layout="wide")

# Навигация
st.sidebar.title("Навигация")
app_mode = st.sidebar.selectbox(
    "Выберите режим:",
    [
        "📊 Описание",
        "🔧 Генерация логов",
        "📈 Визуализация логов",
        "🚀 Симуляция в реальном времени",
        "🌐 Реальные данные"
    ]
)

# Общие функции
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

# Режим: Описание
if app_mode == "📊 Описание":
    st.title("Network Toolkit — Описание")
    st.markdown("""
    Это приложение объединяет три инструмента для работы с сетевым трафиком:

    1. **Генерация логов**: Создаёт синтетические логи сетевого трафика с аномалиями.
    2. **Визуализация логов**: Анализирует и визуализирует загруженные логи.
    3. **Симуляция в реальном времени**: Имитирует поток трафика и детектирует аномалии с помощью IsolationForest.

    Переключайтесь между режимами в боковом меню.
    """)

# Режим: Генерация логов
elif app_mode == "🔧 Генерация логов":
    st.title("Генерация синтетических логов")
    st.markdown("""
    Здесь вы можете сгенерировать синтетические логи сетевого трафика с заданными параметрами.
    """)
    duration = st.number_input("Длительность симуляции (сек)", value=180, min_value=30, max_value=3600, step=30)
    normal_rate = st.number_input("Среднее пакетов/сек (нормально)", value=40, min_value=1, max_value=200)
    use_default_anoms = st.checkbox("Использовать дефолтные аномалии (icmp/udp/tcp)", value=True)

    if st.button("Сгенерировать данные"):
        with st.spinner("Генерация логов..."):
            anomaly_events = None
            if use_default_anoms:
                anomaly_events = [
                    (int(duration*0.15), max(5, int(duration*0.05)), 'ICMP', 18, 'icmp-spike'),
                    (int(duration*0.5), max(6, int(duration*0.08)), 'UDP', 12, 'udp-spike'),
                    (int(duration*0.75), max(5, int(duration*0.06)), 'TCP', 20, 'tcp-spike'),
                ]
            logs_df = generate_synthetic_logs(duration_seconds=duration, normal_rate=normal_rate, anomaly_events=anomaly_events)
            st.success(f"Сгенерировано записей: {len(logs_df)}")
            csv_buffer = logs_df.to_csv(index=False).encode()
            st.download_button(
                label="⬇ Скачать CSV",
                data=csv_buffer,
                file_name="synthetic_network_logs.csv",
                mime="text/csv"
            )

# Режим: Визуализация логов
elif app_mode == "📈 Визуализация логов":
    st.title("Визуализация логов")
    st.markdown("""
    Загрузите CSV-файл с логами, чтобы проанализировать и визуализировать данные.
    """)
    uploaded_file = st.file_uploader("Загрузите файл CSV", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        st.header("Общая информация")
        col1, col2, col3 = st.columns(3)
        col1.metric("Всего записей", len(df))
        col2.metric("Уникальных IP-источников", df['src_ip'].nunique())
        col3.metric("Уникальных IP-назначений", df['dst_ip'].nunique())

        st.header("Распределение пакетов по протоколам")
        fig, ax = plt.subplots()
        df['protocol'].value_counts().plot(kind='bar', ax=ax)
        st.pyplot(fig)

        st.header("Динамика пакетов по времени")
        df_time = df.set_index('timestamp').resample('1S').size()
        fig, ax = plt.subplots(figsize=(12, 4))
        df_time.plot(ax=ax)
        ax.set_ylabel("Количество пакетов")
        st.pyplot(fig)

        st.header("Последние записи лога")
        st.dataframe(df.tail(10))

# Режим: Симуляция в реальном времени
elif app_mode == "🚀 Симуляция в реальном времени":
    st.title("Симуляция в реальном времени")
    st.markdown("""
    Загрузите CSV-файл с логами, чтобы запустить симуляцию и детектировать аномалии.
    """)
    uploaded_file = st.file_uploader("Загрузите файл CSV", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        duration = df['sec'].max() + 1
        feat_df = build_feature_df(df, duration)
        train_cut = max(1, int(len(feat_df) * 0.3))
        X_train = feat_df.iloc[:train_cut][['pkt_rate','unique_src','avg_pkt_size','pct_icmp','pct_udp','pct_tcp','max_pkts_from_src']].fillna(0)
        clf = IsolationForest(n_estimators=100, contamination=0.02, random_state=42)
        clf.fit(X_train)

        st.header("Симуляция")
        if st.button("Запустить симуляцию"):
            st.info("Симуляция запущена...")
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

                if sec % 10 == 0:
                    fig, (ax1, ax2) = plt.subplots(2,1, figsize=(10,5))
                    ax1.plot(secs[-window:], pkt_rates[-window:])
                    ax1.set_title("Пакетов/сек (временной ряд)")
                    ax1.set_ylabel("pkt_rate")
                    ax1.grid(True)
                    ax2.plot(secs[-window:], anomaly_scores[-window:])
                    ax2.axhline(0, linestyle='--')
                    ax2.set_title("Decision function (IsolationForest)")
                    ax2.set_ylabel("score")
                    ax2.set_xlabel("sec")
                    ax2.grid(True)
                    st.pyplot(fig)

                    if is_anom:
                        st.warning(f"ANOMALY @ sec={sec} | pkt_rate={int(row['pkt_rate'])} | true_label={int(row['label'])}")
                    else:
                        st.info(f"sec={sec} | pkt_rate={int(row['pkt_rate'])} | normal")

            st.success("Симуляция завершена.")
            if len(alerts) > 0:
                st.subheader("Логи сработавших алертов")
                df_alerts = pd.DataFrame(alerts, columns=['sec','pkt_rate','label'])
                st.table(df_alerts)
            else:
                st.info("Аномалии не обнаружены моделью.")


# Режим: Реальные данные
elif app_mode == "🌐 Реальные данные":
    st.title("Реальные данные в реальном времени")
    st.markdown("""
    Здесь отображаются реальные данные, получаемые из вашей программы.
    """)

# Путь к файлу с реальными данными
log_file_path = r"D:\ip\main\real_network_log.csv"

# Проверка существования файла
if os.path.exists(log_file_path):
    df = pd.read_csv(log_file_path)
    st.success("Файл успешно загружен!")

    # Визуализация данных
    st.header("Последние записи лога")
    st.dataframe(df.tail(10))

    st.header("Распределение пакетов по протоколам")
    fig, ax = plt.subplots()
    df['protocol'].value_counts().plot(kind='bar', ax=ax)
    st.pyplot(fig)
else:
    st.error(f"Файл {log_file_path} не найден. Проверьте путь и существование файла.")

