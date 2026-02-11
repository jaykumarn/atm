#!/usr/bin/env python3
"""ATM Simulator Web Application"""
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# In-memory data store (same as original script)
users_db = {
    'user1': {'pin': '1234', 'balance': 1000, 'locked': False, 'attempts': 0},
    'user2': {'pin': '2222', 'balance': 2000, 'locked': False, 'attempts': 0},
    'user3': {'pin': '3333', 'balance': 3000, 'locked': False, 'attempts': 0},
}

MAX_PIN_ATTEMPTS = 3


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').lower().strip()
        pin = request.form.get('pin', '').strip()
        
        if not username or not pin:
            flash('Please enter both username and PIN.', 'error')
            return render_template('login.html')
        
        if username not in users_db:
            flash('Invalid username.', 'error')
            return render_template('login.html')
        
        user = users_db[username]
        
        if user['locked']:
            flash('This account has been locked due to too many failed attempts.', 'error')
            return render_template('login.html')
        
        if not pin.isdigit() or len(pin) != 4:
            flash('PIN must consist of 4 digits.', 'error')
            return render_template('login.html')
        
        if pin != user['pin']:
            user['attempts'] += 1
            remaining = MAX_PIN_ATTEMPTS - user['attempts']
            if user['attempts'] >= MAX_PIN_ATTEMPTS:
                user['locked'] = True
                flash('3 unsuccessful PIN attempts. Your card has been locked!', 'error')
            else:
                flash(f'Invalid PIN. {remaining} attempt(s) remaining.', 'error')
            return render_template('login.html')
        
        # Successful login
        user['attempts'] = 0
        session['username'] = username
        flash(f'Welcome, {username.capitalize()}!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    username = session['username']
    balance = users_db[username]['balance']
    return render_template('dashboard.html', username=username, balance=balance)


@app.route('/statement')
@login_required
def statement():
    username = session['username']
    balance = users_db[username]['balance']
    return render_template('statement.html', username=username, balance=balance)


@app.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    username = session['username']
    user = users_db[username]
    
    if request.method == 'POST':
        try:
            amount = int(request.form.get('amount', 0))
        except ValueError:
            flash('Please enter a valid amount.', 'error')
            return render_template('withdraw.html', balance=user['balance'])
        
        if amount <= 0:
            flash('Please enter a positive amount.', 'error')
        elif amount % 10 != 0:
            flash('Amount must be in multiples of 10 Euro.', 'error')
        elif amount > user['balance']:
            flash('Insufficient balance.', 'error')
        else:
            user['balance'] -= amount
            flash(f'Successfully withdrew {amount} Euro. New balance: {user["balance"]} Euro.', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('withdraw.html', balance=user['balance'])


@app.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    username = session['username']
    user = users_db[username]
    
    if request.method == 'POST':
        try:
            amount = int(request.form.get('amount', 0))
        except ValueError:
            flash('Please enter a valid amount.', 'error')
            return render_template('deposit.html', balance=user['balance'])
        
        if amount <= 0:
            flash('Please enter a positive amount.', 'error')
        elif amount % 10 != 0:
            flash('Amount must be in multiples of 10 Euro.', 'error')
        else:
            user['balance'] += amount
            flash(f'Successfully deposited {amount} Euro. New balance: {user["balance"]} Euro.', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('deposit.html', balance=user['balance'])


@app.route('/change-pin', methods=['GET', 'POST'])
@login_required
def change_pin():
    username = session['username']
    user = users_db[username]
    
    if request.method == 'POST':
        current_pin = request.form.get('current_pin', '').strip()
        new_pin = request.form.get('new_pin', '').strip()
        confirm_pin = request.form.get('confirm_pin', '').strip()
        
        if current_pin != user['pin']:
            flash('Current PIN is incorrect.', 'error')
        elif not new_pin.isdigit() or len(new_pin) != 4:
            flash('New PIN must consist of 4 digits.', 'error')
        elif new_pin == user['pin']:
            flash('New PIN must be different from current PIN.', 'error')
        elif new_pin != confirm_pin:
            flash('New PIN and confirmation do not match.', 'error')
        else:
            user['pin'] = new_pin
            flash('PIN changed successfully.', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('change_pin.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
