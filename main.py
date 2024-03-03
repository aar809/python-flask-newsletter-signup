from flask import Flask, render_template, request, redirect, url_for, flash, Response
import sqlite3
import csv
import io
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'

# This is just a simple example. In a real-world application,
# you would likely want to use a more secure method of storing and verifying passwords.


@auth.verify_password
def verify_password(username, password):
  if username == 'admin' and password == 'yourpassword':
    return username  # if the user/password is correct, the user's name is returned to indicate success
  return None  # if the user/password is incorrect, None is returned


@auth.error_handler
def unauthorized():
  return Response('Please authenticate to access the admin panel.', 401,
                  {'WWW-Authenticate': 'Basic realm="Login Required"'})


# Create a SQLite database
def init_db():
  with app.app_context():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        );
        ''')
    conn.commit()
    conn.close()


@app.route('/', methods=['GET', 'POST'])
def index():
  if request.method == 'POST':
    name = request.form['name']
    email = request.form['email']

    try:
      conn = sqlite3.connect('database.db')
      cursor = conn.cursor()
      cursor.execute('INSERT INTO users (name, email) VALUES (?, ?)',
                     (name, email))
      conn.commit()
      flash('Data successfully stored!')
    except sqlite3.IntegrityError:
      flash('Email already exists in the database.')
    finally:
      conn.close()

    return redirect(url_for('index'))

  return render_template('index.html')


@app.route('/admin')
@auth.login_required
def admin():
  conn = sqlite3.connect('database.db')
  cursor = conn.cursor()
  cursor.execute('SELECT * FROM users')
  data = cursor.fetchall()
  conn.close()
  return render_template('admin.html', data=data)


@app.route('/export-csv')
def export_csv():
  conn = sqlite3.connect('database.db')
  cursor = conn.cursor()
  cursor.execute('SELECT * FROM users')
  data = cursor.fetchall()
  conn.close()

  si = io.StringIO()
  output = csv.writer(si)
  output.writerow(['ID', 'Name', 'Email'])
  for row in data:
    output.writerow(row)

  response = Response(si.getvalue(), content_type='text/csv')
  response.headers['Content-Disposition'] = 'attachment; filename=data.csv'
  return response


if __name__ == '__main__':
  init_db()
  app.run(host='0.0.0.0', port=8080)  # Replit.com uses port 8080
