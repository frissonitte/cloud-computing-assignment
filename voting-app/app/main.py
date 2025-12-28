from flask import Flask, render_template, request, make_response, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import time

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

POLL_OPTIONS = ["Docker", "Kubernetes", "Ansible", "Terraform"]

db = SQLAlchemy(app)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    choice = db.Column(db.String(50), nullable=False)

def create_db():
    with app.app_context():
        retries = 5
        while retries > 0:
            try:
                db.create_all()
                print("Veritabanı bağlantısı başarılı!")
                break
            except Exception as e:
                print(f"Veritabanı bekleniyor... Hata: {e}")
                time.sleep(5)
                retries -= 1

create_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    voted_cookie = request.cookies.get('has_voted')

    if request.method == 'POST' and not voted_cookie:
        vote_value = request.form.get('vote')
        
        if vote_value in POLL_OPTIONS:
            new_vote = Vote(choice=vote_value)
            db.session.add(new_vote)
            db.session.commit()

            resp = make_response(redirect(url_for('index')))
            resp.set_cookie('has_voted', 'true', max_age=60*60*24*30)
            return resp

    results = []
    total_votes = Vote.query.count()
    
    for option in POLL_OPTIONS:
        count = Vote.query.filter_by(choice=option).count()
        percent = 0
        if total_votes > 0:
            percent = int((count / total_votes) * 100)
        
        results.append({
            "name": option,
            "count": count,
            "percent": percent
        })

    return render_template('index.html', 
                         results=results, 
                         total_votes=total_votes,
                         hostname=os.environ.get('HOSTNAME'),
                         show_results=voted_cookie is not None)

@app.route('/reset')
def reset():
    resp = make_response(redirect(url_for('index')))
    resp.set_cookie('has_voted', '', expires=0)
    return resp

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)