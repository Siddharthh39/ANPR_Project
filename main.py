from flask import Flask, request, render_template, redirect, url_for, flash, session
import os
import mysql.connector
from anpr import process_image
from ipfs_utils import upload_to_ipfs

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'your_secret_key_here' 

USERS = {
    "siddharth": "sid@12",
    "vaibhav": "vaibhav@12",
    "sarthak": "sarthak@12"
}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",
        database="anpr"
    )
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS vehicle_info (
                      id INT AUTO_INCREMENT PRIMARY KEY,
                      plate VARCHAR(20) UNIQUE,
                      name VARCHAR(100),
                      phone VARCHAR(15))''')
except mysql.connector.Error as err:
    print(f"Error: {err}")

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("Please log in to access this page.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip().lower()
        password = request.form['password']
        if username in USERS and USERS[username] == password:
            session['username'] = username
            flash("Logged in successfully!")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials. Please try again.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Logged out successfully.")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    cursor.execute("SELECT COUNT(*) FROM vehicle_info")
    total_vehicles = cursor.fetchone()[0]
    return render_template('dashboard.html', total_vehicles=total_vehicles)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        plate_number = process_image(file_path)
        
        if plate_number:
            ipfs_hash = upload_to_ipfs(file_path)
            
            cursor.execute("SELECT * FROM vehicle_info WHERE plate = %s", (plate_number,))
            record = cursor.fetchone()
            if record:
                flash(f"Vehicle found: Plate: {record[1]}, Owner: {record[2]}, Phone: {record[3]}")
                # Update IPFS hash if not already set
                if not record[4] and ipfs_hash:
                    cursor.execute("UPDATE vehicle_info SET ipfs_hash = %s WHERE id = %s", (ipfs_hash, record[0]))
                    conn.commit()
                return redirect(url_for('vehicles'))
            else:
                # Insert new record with the IPFS hash (owner details missing; redirect to registration)
                cursor.execute("INSERT INTO vehicle_info (plate, ipfs_hash) VALUES (%s, %s)", (plate_number, ipfs_hash))
                conn.commit()
                return redirect(url_for('register', plate=plate_number))
        else:
            flash("No plate detected in the image.")
            return redirect(request.url)
    return render_template('upload.html')


@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    plate = request.args.get('plate')
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        try:
            cursor.execute("UPDATE vehicle_info SET name=%s, phone=%s WHERE plate=%s", (name, phone, plate))
            conn.commit()
            flash("Vehicle registered successfully!")
        except mysql.connector.Error as err:
            flash(f"Error: {err}")
        return redirect(url_for('vehicles'))
    return render_template('register.html', plate=plate)

@app.route('/vehicles')
@login_required
def vehicles():
    cursor.execute("SELECT * FROM vehicle_info")
    records = cursor.fetchall()
    return render_template('vehicles.html', records=records)

if __name__ == '__main__':
    app.run(debug=True)
