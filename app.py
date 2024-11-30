from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        number TEXT NOT NULL,
        location TEXT NOT NULL
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        bin_id INTEGER,
        FOREIGN KEY (bin_id) REFERENCES bins (id)
    )''')
    conn.commit()
    conn.close()

init_db()

# Routes
@app.route('/')
def index():
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bins')
    bins = cursor.fetchall()
    conn.close()
    return render_template('index.html', bins=bins)

@app.route('/bin/<int:bin_id>')
def bin_details(bin_id):
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bins WHERE id = ?', (bin_id,))
    bin = cursor.fetchone()
    cursor.execute('SELECT * FROM items WHERE bin_id = ?', (bin_id,))
    items = cursor.fetchall()
    conn.close()
    return render_template('bin_details.html', bin=bin, items=items)

@app.route('/add_bin', methods=['GET', 'POST'])
def add_bin():
    if request.method == 'POST':
        number = request.form['number']
        location = request.form['location']
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO bins (number, location) VALUES (?, ?)', (number, location))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('add_bin.html')

@app.route('/edit_bin/<int:bin_id>', methods=['GET', 'POST'])
def edit_bin(bin_id):
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        number = request.form['number']
        location = request.form['location']
        cursor.execute('UPDATE bins SET number = ?, location = ? WHERE id = ?', (number, location, bin_id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    cursor.execute('SELECT * FROM bins WHERE id = ?', (bin_id,))
    bin = cursor.fetchone()
    conn.close()
    return render_template('edit_bin.html', bin=bin)

@app.route('/delete_bin/<int:bin_id>', methods=['POST'])
def delete_bin(bin_id):
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM items WHERE bin_id = ?', (bin_id,))
    cursor.execute('DELETE FROM bins WHERE id = ?', (bin_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/add_item/<int:bin_id>', methods=['GET', 'POST'])
def add_item(bin_id):
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO items (name, description, bin_id) VALUES (?, ?, ?)',
                       (name, description, bin_id))
        conn.commit()
        conn.close()
        return redirect(url_for('bin_details', bin_id=bin_id))
    return render_template('add_item.html', bin_id=bin_id)

@app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        cursor.execute('UPDATE items SET name = ?, description = ? WHERE id = ?', (name, description, item_id))
        conn.commit()
        conn.close()
        bin_id = request.form['bin_id']
        return redirect(url_for('bin_details', bin_id=bin_id))
    cursor.execute('SELECT * FROM items WHERE id = ?', (item_id,))
    item = cursor.fetchone()
    cursor.execute('SELECT bin_id FROM items WHERE id = ?', (item_id,))
    bin_id = cursor.fetchone()[0]
    conn.close()
    return render_template('edit_item.html', item=item, bin_id=bin_id)

@app.route('/delete_item/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute('SELECT bin_id FROM items WHERE id = ?', (item_id,))
    bin_id = cursor.fetchone()[0]
    cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('bin_details', bin_id=bin_id))

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form['query']
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bins WHERE number LIKE ?", ('%' + query + '%',))
        bins = cursor.fetchall()
        conn.close()
        return render_template('search_results.html', bins=bins, query=query)
    return redirect(url_for('index'))

@app.route('/search_item', methods=['GET', 'POST'])
def search_item():
    if request.method == 'POST':
        query = request.form['query']
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT items.name, bins.number, bins.location 
            FROM items 
            JOIN bins ON items.bin_id = bins.id 
            WHERE items.name LIKE ?
        ''', ('%' + query + '%',))
        results = cursor.fetchall()
        conn.close()
        return render_template('item_search_results.html', results=results, query=query)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)