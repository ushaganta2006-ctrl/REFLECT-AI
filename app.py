from flask import Flask, render_template, redirect, flash, url_for, request
from forms import RegistrationForm , LoginForm
from flask_sqlalchemy import SQLAlchemy

import markdown
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

client = genai.Client(api_key=API_KEY)

app = Flask(__name__)
app.config['SECRET_KEY'] = '10a4d399f8b982b1d377b56e5e2b6ebc'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

from models import Reflection

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET','POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f'Account created for {form.username.data}!' , 'success')
        return redirect(url_for('home'))
    return render_template('register.html', title='register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.email.data == "admin@blog.com" and form.password.data == "password":
            flash('You have been logged in!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/reflect', methods=['GET', 'POST'])
def reflect():
    ai_response = None
    study_topic = None
    latest_reflection_id = None

    if request.method == 'POST':
        study_topic = request.form.get("study_topic")
        reflection_text = request.form.get("reflection_text")
        study_duration = request.form.get("study_duration")
        confidence_level = request.form.get("confidence_level")

        if not study_topic or not reflection_text or not confidence_level:
            ai_response = "Please fill all required fields."
        else:
            prompt = f"""
        You are REFLECT.AI — an advanced metacognitive learning analyst designed to evaluate the QUALITY of a student’s learning process, not to reteach content.

        Your role is to diagnose thinking patterns, depth of understanding, confidence calibration, and study effectiveness.

        –––––––––––––––––––––––––––––––––––
        EVALUATION OBJECTIVES:

        1. Determine actual depth of conceptual understanding.
        2. Detect misconceptions, vague reasoning, or surface-level learning.
        3. Evaluate whether confidence level aligns with demonstrated understanding.
        4. Assess effectiveness of study strategy (active vs passive learning).
        5. Provide precise, supportive, and actionable improvement guidance.

        –––––––––––––––––––––––––––––––––––
        INPUT DATA:

        Study Topic: {study_topic}
        Reflection Text: {reflection_text}
        Study Duration: {study_duration}
        Confidence Level (1–5): {confidence_level}

        –––––––––––––––––––––––––––––––––––
        STRICT OUTPUT FORMAT:

        🔎 Learning Quality Assessment:
        ~ Understanding Level: Low / Medium / High
        ~ Confidence Accuracy: Overconfident / Accurate / Underconfident
        ~ Depth Indicator: Surface / Developing / Deep

        ⚠ Detected Issues:
        ~ Misconceptions:
        ~ Gaps in Understanding:
        ~ Study Strategy Weaknesses:

        🎯 Personalized Feedback:
        ~ What you did well:
        ~ What needs improvement:
        ~ Suggested next study action (1–2 high-impact steps):

        💡 Reflection Upgrade Question:
        ~ One powerful metacognitive question to ask next time.

        📘 Concept Reinforcement Cheat Sheet:
        - 5–8 concise bullet points summarizing the core ideas.
        - Keep it under 120 words.
        - This is a quick recall aid, not a full lesson.
        –––––––––––––––––––––––––––––––––––
        CONSTRAINTS:

        ~ Do NOT reteach the full topic.
        ~ Concept Reinforcement Cheat Sheet.
        ~ Do NOT provide external resources.
        ~ Be analytical but supportive.
        ~ Be concise yet insightful.
        ~ Maximum 250 words.
        ~ Use clear formatting and readable spacing.
        """

            try:
                response = client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=prompt
                )

                raw_text = response.text
                html_response = markdown.markdown(
                    raw_text,
                    extensions=["fenced_code", "tables"]
                )

                ai_response = html_response

                new_reflection = Reflection(
                    study_topic=study_topic,
                    cheat_sheet=html_response,
                    is_saved=False
                )

                db.session.add(new_reflection)
                db.session.commit()

                latest_reflection_id = new_reflection.id

            except Exception as e:
                ai_response = "⚠️ Something went wrong."

    return render_template('reflect.html',title='Reflect',ai_response=ai_response,latest_reflection_id=latest_reflection_id)

@app.route("/save_reflection/<int:id>", methods=["POST"])
def save_reflection(id):
    reflection = Reflection.query.get_or_404(id)
    reflection.is_saved = True
    db.session.commit()

    return redirect(request.referrer)

@app.route("/bookmark")
def bookmark():
    saved_reflections = Reflection.query.filter_by(is_saved=True)\
        .order_by(Reflection.timestamp.desc()).all()

    return render_template("bookmark.html", reflections=saved_reflections)

with app.app_context():
    Reflection.query.filter(Reflection.id.in_([1,2]))\
        .delete(synchronize_session=False)
    db.session.commit()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=10000)