from flask import render_template, url_for, flash, redirect, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from a11yGPT_package import app, db, login_manager
from a11yGPT_package.models import User, MonthlySpend, Session, generate_api_token
from a11yGPT_package.utils import scrape_html, run_gpt, is_valid_password
from threading import Thread
from datetime import datetime
import requests
import json

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('/index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')
        api_token = generate_api_token()

        new_user = User(email=email, password=hashed_password, api_token=api_token)

        if not is_valid_password(password):
            flash('Invalid password. Must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, one digit, and one special character.', 'danger')
            return render_template('register.html')

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Account created! Now you can login.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: This email already exists.', 'danger')

    return render_template('register.html')  # Render the registration template

@app.route('/api/start_session', methods=['POST'])
def start_session():
    token = request.form['token']
    url = request.form['url']

    # Check if the token is valid and belongs to a user
    user = User.query.filter_by(api_token=token).first()
    if not user:
        return jsonify({"error": "Invalid token"}), 401

    # Check if the user has enough budget (5 credits, $0.009/credit)
    current_month_spend = user.get_current_month_spend()
    if user.monthly_budget < current_month_spend + (5 * 0.009):
        return jsonify({"error": "Insufficient budget"}), 402

    # Deduct the cost from the user's budget
    current_month = datetime.now().strftime('%Y-%m')
    monthly_spend = MonthlySpend.query.filter_by(user_id=user.id, month=current_month).first()
    if monthly_spend:
        monthly_spend.spend += 5 * 0.009
    else:
        monthly_spend = MonthlySpend(user_id=user.id, month=current_month, spend=5 * 0.009)
        db.session.add(monthly_spend)
    db.session.commit()

    # Create a new session
    session = Session(user_id=user.id, url=url) 
    db.session.add(session)
    db.session.commit()

    # Pass the HTML to ChatGPT before saving results.
    run_gpt(session.id, scrape_html(session.id, url))
    
    # Return the results.
    return jsonify({"session_id": session.id, "results": session.results, "status": session.status}), 200

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user, remember=True)
            flash('You are now logged in.', 'success')
            return redirect(url_for('account'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/update_account', methods=['POST'])
def update_account():
    user = current_user

    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    credit_card = request.form['credit_card']
    monthly_budget = float(request.form['monthly_budget'])

    # Update email, credit card, and monthly budget
    user.email = email
    user.credit_card = credit_card
    user.monthly_budget = monthly_budget

    # Update password if provided
    if password:
        if not is_valid_password(password):
            flash('Invalid new password. Must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, one digit, and one special character.', 'danger')
            return redirect(url_for('account'))
        if confirm_password:
            if password == confirm_password:
                hashed_password = generate_password_hash(password, method='sha256')
                user.password = hashed_password
            else:
                flash('New password and confirm password do not match.', 'danger')
                return redirect(url_for('account'))
        else:
            flash('Please confirm your new password.', 'danger')
            return redirect(url_for('account'))

    db.session.commit()
    flash('Account updated successfully.', 'success')
    return redirect(url_for('account'))

@app.route('/account')
@login_required
def account():
    monthly_spends = current_user.monthly_spend_records  # Fetch monthly spends for the current user
    token = current_user.api_token
    return render_template('account.html', email=current_user.email, credit_card=current_user.credit_card, monthly_budget=current_user.monthly_budget, monthly_spends=monthly_spends, token=token)

@app.route('/support')
def support():
    return render_template('support.html')