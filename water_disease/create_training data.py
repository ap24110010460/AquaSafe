import pandas as pd
import random

rows = []

for i in range(200):

    ph = round(random.uniform(5.5, 8.5),2)
    tds = random.randint(100, 1200)
    turbidity = round(random.uniform(1, 10),2)
    do = round(random.uniform(3, 10),2)
    temp = random.randint(20, 40)
    humidity = random.randint(30, 90)

    # Risk logic
    score = 0

    if ph < 6 or ph > 8:
        score += 1

    if tds > 500:
        score += 1

    if turbidity > 5:
        score += 1

    if do < 5:
        score += 1

    if temp > 32:
        score += 1

    if humidity > 75:
        score += 1

    if score <= 1:
        risk = "Low"
    elif score <= 3:
        risk = "Medium"
    else:
        risk = "High"

    rows.append([ph, tds, turbidity, do, temp, humidity, risk])

df = pd.DataFrame(rows, columns=[
    "pH",
    "TDS",
    "Turbidity",
    "DO",
    "Temperature",
    "Humidity",
    "Risk"
])

df.to_csv("training_data.csv", index=False)

print("Dataset generated successfully!")