from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import database
import os

app = Flask(__name__)
# Secret key needs to be static so sessions survive restarts.
app.secret_key = 'ucsd_baseball_super_secret_key_dev' 

database.init_db()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('index.html', user_id=session['user_id'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        
        conn = database.get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
        conn.close()
        
        if user and user['password_hash'] and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['user_id']
            session['role'] = user['role']
            return redirect(url_for('index'))
        else:
            flash('Invalid User ID or Password')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    return redirect(url_for('login'))

@app.route('/set_password/<token>', methods=['GET', 'POST'])
def set_password(token):
    conn = database.get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE invite_token = ?', (token,)).fetchone()
    
    if not user:
        conn.close()
        flash('Invalid or expired invite token')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match')
        elif len(password) < 6:
            flash('Password must be at least 6 characters')
        else:
            hashed = generate_password_hash(password)
            conn.execute('UPDATE users SET password_hash = ?, invite_token = NULL WHERE id = ?', 
                         (hashed, user['id']))
            conn.commit()
            conn.close()
            flash('Password set successfully. Please log in.')
            return redirect(url_for('login'))
            
    conn.close()
    return render_template('set_password.html', user_id=user['user_id'], role=user['role'].title())

if __name__ == '__main__':
    app.run(debug=True, port=8000)
