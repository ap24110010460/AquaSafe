import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

# Load dataset
data = pd.read_csv("training_data.csv")

# Features and label
X = data[["pH","TDS","Turbidity","DO","Temperature","Humidity"]]
y = data["Risk"]

# Create model
model = RandomForestClassifier(n_estimators=200, random_state=42)

# Cross validation accuracy (best for small dataset)
scores = cross_val_score(model, X, y, cv=5)

MODEL_ACCURACY = round(scores.mean()*100,2)

# Train final model on full data
model.fit(X, y)


# -------- Predict Risk (REAL PERCENTAGE) --------
def predict_risk(ph,tds,turbidity,do,temp,humidity):

    input_data = [[ph,tds,turbidity,do,temp,humidity]]

    proba = model.predict_proba(input_data)[0]

    risk = max(proba) * 100

    return round(risk,2)


# -------- Get Model Accuracy --------
def get_accuracy():
    return MODEL_ACCURACY