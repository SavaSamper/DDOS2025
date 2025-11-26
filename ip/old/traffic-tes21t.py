import pandas as pd
from sklearn.ensemble import IsolationForest

# Загружаем собранный трафик
df = pd.read_csv("traffic.csv")

# Оставляем только числовые признаки (всё, что нужно модели)
x = df.select_dtypes(include='number')

# Обучаем аномальный детектор
model = IsolationForest(contamination=0.05)
model.fit(x)
