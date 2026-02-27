from flask import Flask, render_template
from routes.bank_routes import bank_bp
from routes.dispute_routes import dispute_bp
from models.dispute_model import create_dispute_table

app = Flask(__name__)

# Register blueprints
app.register_blueprint(bank_bp)
app.register_blueprint(dispute_bp)

# Create DB table on startup
create_dispute_table()

# -----------------------------
# UI Routes
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# -----------------------------
# App Runner
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)