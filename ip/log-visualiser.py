import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Настройки страницы
st.set_page_config(page_title="Network Log Visualizer", layout="wide")

# Заголовок
st.title("📊 Network Log Visualizer")

# Загрузка файла
uploaded_file = st.file_uploader("Загрузите файл synthetic_network_log.csv", type=["csv"])

if uploaded_file is not None:
    # Чтение CSV
    df = pd.read_csv(uploaded_file)

    # Преобразование timestamp в datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Основная информация
    st.header("Общая информация")
    col1, col2, col3 = st.columns(3)
    col1.metric("Всего записей", len(df))
    col2.metric("Уникальных IP-источников", df['src_ip'].nunique())
    col3.metric("Уникальных IP-назначений", df['dst_ip'].nunique())

    # Визуализация: распределение пакетов по протоколам
    st.header("Распределение пакетов по протоколам")
    fig, ax = plt.subplots()
    df['protocol'].value_counts().plot(kind='bar', ax=ax)
    st.pyplot(fig)

    # Визуализация: динамика пакетов по времени
    st.header("Динамика пакетов по времени")
    df_time = df.set_index('timestamp').resample('1S').size()
    fig, ax = plt.subplots(figsize=(12, 4))
    df_time.plot(ax=ax)
    ax.set_ylabel("Количество пакетов")
    st.pyplot(fig)

    # Визуализация: распределение размеров пакетов
    st.header("Распределение размеров пакетов")
    fig, ax = plt.subplots()
    df['pkt_size'].plot(kind='hist', bins=30, ax=ax)
    st.pyplot(fig)

    # Таблица с последними записями
    st.header("Последние записи лога")
    st.dataframe(df.tail(10))

    # Фильтрация по аномалиям
    st.header("Фильтрация по аномалиям")
    show_anomalies = st.checkbox("Показать только аномалии")
    if show_anomalies:
        st.dataframe(df[df['label'] == 1])
