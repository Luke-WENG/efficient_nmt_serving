from __future__ import print_function
import sqlite3
import time
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from contextlib import closing
from web_nmt_client import web_query

DATABASE = './database/flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
# USERNAME = 'admin'
# PASSWORD = 'default'

app = Flask(__name__)
app.config.from_object(__name__)
# app.config.from)envvar('FLASKR_SETTINGS',silent=True)

def connect_db():
	return sqlite3.connect(app.config['DATABASE'])

def init_db():
	with closing(connect_db()) as db:
		with app.open_resource('schema.sql', mode='r') as f:
			db.cursor().executescript(f.read())
		db.commit()

def get_result(query):
    if len(query) < 1: # empty query
        return "Invalid Query Input"
    else:
        return web_query(query)

@app.before_request
def before_request():
	g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
	db = getattr(g, 'db', None)
	if db is not None:
		db.close()

@app.route('/')
def show_entries():
	cur = g.db.execute('SELECT title, query, result FROM entries ORDER BY id DESC')
	entries = [dict(title=row[0], query=row[1], result=row[2]) for row in cur.fetchall()]
	return render_template('show_entries.html', entries=entries)

@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)

    query_time = time.time()
    result = get_result(request.form['query'])
    latency = time.time() - query_time

    g.db.execute('INSERT INTO entries (title, query, result) VALUES (?, ?, ?)',
                 [session['username'], request.form['query'], result])
    g.db.commit()
    flash('New query was successfully posted! Latency: %.2f sec' % latency)
    return redirect(url_for('show_entries'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] == None:
            error = 'Invalid username'
        # elif request.form['password'] != app.config['PASSWORD']:
        #     error = 'Invalid password'
        else:
            if request.form['username'] == '':
                session['username'] = "Anony."
            else:
                session['username'] = request.form['username']
            session['logged_in'] = True
            flash('Hi '+session['username'])
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))


if __name__=='__main__':
	app.run()
