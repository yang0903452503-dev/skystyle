import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

file_name = "final.csv"
df = pd.read_csv(file_name)

df.columns = df.columns.str.strip()

feature_cols = ["RelativeHumidity", "WindSpeed", "ApparentTemperature"]
target_col = "target"

df = df.dropna(subset=feature_cols + [target_col])

X = df[feature_cols]
y = df[target_col]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=0
)

model = DecisionTreeClassifier(random_state=0)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

print("\n決策樹模型輸出結果：")
print("-" * 50)
print(f"目標值: {y_test.values}")
print(f"預測值: {y_pred}")
print(f"準確率: {model.score(X_test, y_test)}")

joblib.dump(model, "model.pkl")
print("模型已儲存成 model.pkl")
