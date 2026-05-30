import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

# 讀取 CSV 檔案
file_name = "final.csv"
df = pd.read_csv(file_name)

# 清除欄位名稱前後空格
df.columns = df.columns.str.strip()

# 設定特徵欄位與目標欄位
feature_cols = ["RelativeHumidity", "WindSpeed", "ApparentTemperature"]
target_col = "target"

# 清除空值
df = df.dropna(subset=feature_cols + [target_col])

X = df[feature_cols]
y = df[target_col]

# 切割資料集
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=0
)

# 建立決策樹模型
model = DecisionTreeClassifier(random_state=0)
model.fit(X_train, y_train)

# 預測
y_pred = model.predict(X_test)

# 印出結果
print("\n決策樹模型輸出結果：")
print("-" * 50)
print(f"目標值: {y_test.values}")
print(f"預測值: {y_pred}")
print(f"準確率: {model.score(X_test, y_test)}")

# 儲存模型
joblib.dump(model, "model.pkl")
print("模型已儲存成 model.pkl")
