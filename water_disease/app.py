from flask import Flask, render_template, request, redirect, session
import pandas as pd
import requests
from flask import send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
import os
from model import predict_risk,get_accuracy

app = Flask(__name__)
app.secret_key = "water_project"
API_KEY="d1f3014a84b6b7dfcec30a9135e1ee95"

# ---------------- STATE -> CAPITAL CITY ----------------
state_to_city = {
    "Andhra Pradesh": "amaravati",
    "Arunachal Pradesh": "itanagar",
    "Assam": "dispur",
    "Bihar": "patna",
    "Chhattisgarh": "raipur",
    "Goa": "panaji",
    "Gujarat": "gandhinagar",
    "Haryana": "chandigarh",
    "Himachal Pradesh": "shimla",
    "Jharkhand": "ranchi",
    "Karnataka": "bangalore",
    "Kerala": "thiruvananthapuram",
    "Madhya Pradesh": "bhopal",
    "Maharashtra": "mumbai",
    "Manipur": "imphal",
    "Meghalaya": "shillong",
    "Mizoram": "aizawl",
    "Nagaland": "kohima",
    "Odisha": "bhubaneswar",
    "Punjab": "chandigarh",
    "Rajasthan": "jaipur",
    "Sikkim": "gangtok",
    "Tamil Nadu": "chennai",
    "Telangana": "hyderabad",
    "Tripura": "agartala",
    "Uttar Pradesh": "lucknow",
    "Uttarakhand": "dehradun",
    "West Bengal": "kolkata",
    "Delhi": "delhi",
    "Jammu and Kashmir": "srinagar"
}

# ---------- LOAD CSV FILES ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ph_df = pd.read_csv(os.path.join(BASE_DIR, "data/ph.csv"))
tds_df = pd.read_csv(os.path.join(BASE_DIR, "data/tds.csv"))
turbidity_df = pd.read_csv(os.path.join(BASE_DIR, "data/turbidity.csv"))
do_df = pd.read_csv(os.path.join(BASE_DIR, "data/do.csv"))

# ---------- CLEAN STATE NAMES ----------
ph_df["State"] = ph_df["State"].str.strip().str.lower()
tds_df["State"] = tds_df["State"].str.strip().str.lower()
turbidity_df["State"] = turbidity_df["State"].str.strip().str.lower()
do_df["State"] = do_df["State"].str.strip().str.lower()


# ---------------- DISEASE FUNCTION ----------------
def get_diseases(risk):
    if risk < 25:
        return ["Low risk - Safe water"]

    elif risk < 50:
        return [
            "Mild Diarrhea",
            "Skin irritation"
        ]

    elif risk < 75:
        return [
            "Cholera",
            "Typhoid",
            "Gastroenteritis"
        ]

    else:
        return [
            "Severe Cholera",
            "Dysentery",
            "Hepatitis A",
            "E.coli infection"
        ]

#------------------PRECAUTIONS-----------------
def get_precautions(risk):

    if risk < 30:
        return [
        "Water is safe for drinking",
        "No immediate action required"
        ]

    elif risk < 60:
        return [
        "Boil water before drinking",
        "Use water filter",
        "Avoid street water"
        ]

    else:
        return [
        "Avoid drinking tap water",
        "Use RO/UV purified water",
        "Drink bottled water",
        "Inform local authorities"
        ]

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        try:
            users = pd.read_csv(os.path.join(BASE_DIR,"users.csv"))
        except Exception:
            users = pd.DataFrame(columns=["username","password"])

        users["username"] = users["username"].astype(str).str.strip()
        users["password"] = users["password"].astype(str).str.strip()

        user = users[
            (users["username"] == username) &
            (users["password"] == password)
        ]

        if not user.empty:
            session["user"] = username
            return redirect("/dashboard")
        else:
            return "Invalid username or password"

    return render_template("login.html")


# ---------------- SIGNUP ----------------
@app.route("/register", methods=["GET","POST"])
@app.route("/signup", methods=["GET","POST"])
def register():

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        try:
            users = pd.read_csv(os.path.join(BASE_DIR, "users.csv"))
        except Exception:
            users = pd.DataFrame(columns=["username","password"])

        users["username"] = users["username"].astype(str).str.strip()

        if username in users["username"].values:
            return "User already registered. Please login."

        new_user = pd.DataFrame([[username,password]],columns=["username","password"])
        users = pd.concat([users,new_user],ignore_index=True)

        users.to_csv(os.path.join(BASE_DIR,"users.csv"),index=False)

        return redirect("/")

    return render_template("register.html")



    # ---------------- DASHBOARD ----------------
@app.route("/dashboard")
@app.route("/dashboard/<state>")
def dashboard(state=None):

    if "user" not in session:
        return redirect("/")

    states = sorted(state_to_city.keys())

    if state is None:
        return render_template("dashboard.html", states=states, graph_file=None)

    selected_state = state.strip().lower()

    ph_data = ph_df[ph_df["State"].str.contains(selected_state, case=False, na=False)]
    tds_data = tds_df[tds_df["State"].str.contains(selected_state, case=False, na=False)]
    turbidity_data = turbidity_df[turbidity_df["State"].str.contains(selected_state, case=False, na=False)]
    do_data = do_df[do_df["State"].str.contains(selected_state, case=False, na=False)]

    ph = round(ph_data.iloc[:, 1:].mean().mean(), 2) if not ph_data.empty else 7
    tds = round(tds_data.iloc[:, 1:].mean().mean(), 2) if not tds_data.empty else 300
    turbidity = round(turbidity_data.iloc[:, 1:].mean().mean(), 2) if not turbidity_data.empty else 3
    do = round(do_data.iloc[:, 1:].mean().mean(), 2) if not do_data.empty else 7

    selected_state = state.strip()
    city = state_to_city.get(selected_state)

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city},IN&appid={API_KEY}&units=metric"
    r = requests.get(url).json()

    temperature = r.get("main", {}).get("temp", 0)
    humidity = r.get("main", {}).get("humidity", 0)

    risk = predict_risk(ph, tds, turbidity, do, temperature, humidity)

    diseases = get_diseases(risk)
    precautions = get_precautions(risk)
    accuracy = get_accuracy()



    return render_template(
        "dashboard.html",
        states=states,
        state=selected_state.title(),
        risk=risk,
        temperature=temperature,
        humidity=humidity,
        ph=ph,
        tds=tds,
        turbidity=turbidity,
        do=do,
        diseases=diseases,
        accuracy=accuracy,
        precautions=precautions,

    )


# ---------------- DOWNLOAD PDF ----------------
@app.route("/download/<state>")
def download(state):

    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph(f"Water Risk Report - {state}", styles['Heading1']))
    story.append(Spacer(1,12))

    # Values
    story.append(Paragraph(f"Risk Level: {request.args.get('risk','')}", styles['Normal']))
    story.append(Paragraph(f"pH: {request.args.get('ph','')}", styles['Normal']))
    story.append(Paragraph(f"TDS: {request.args.get('tds','')}", styles['Normal']))
    story.append(Paragraph(f"Turbidity: {request.args.get('turbidity','')}", styles['Normal']))
    story.append(Paragraph(f"DO: {request.args.get('do','')}", styles['Normal']))
    story.append(Spacer(1,12))

    # Diseases
    story.append(Paragraph("Possible Diseases:", styles['Heading2']))
    story.append(Paragraph(request.args.get('diseases',''), styles['Normal']))
    story.append(Spacer(1,12))

    # Precautions
    story.append(Paragraph("Precautions:", styles['Heading2']))
    story.append(Paragraph(request.args.get('precautions',''), styles['Normal']))
    story.append(Spacer(1,12))

    story.append(Paragraph(
        "Generated by Smart Community Health Monitoring System",
        styles['Normal']
    ))

    file_path = f"static/report_{state}.pdf"

    doc = SimpleDocTemplate(file_path, pagesize=A4)
    doc.build(story)

    return send_file(file_path, as_attachment=True)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)