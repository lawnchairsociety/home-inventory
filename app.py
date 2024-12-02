import os
import base64
from io import BytesIO
import qrcode
from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Base URL for the application (used for generating QR codes)
BASEURL = "http://127.0.0.1:5000" #change this to your own application URL 

# =====================
# Database Initialization
# =====================
def init_db():
    """
    Initialize the SQLite database.
    - Creates tables 'bins' and 'items' if they do not exist.
    - 'bins': Stores bin information (number, location, and QR code).
    - 'items': Stores items associated with specific bins.
    """
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        number TEXT NOT NULL,
        location TEXT NOT NULL,
        qr_code TEXT
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

# Initialize the database on application start
init_db()

# =====================
# Routes
# =====================

@app.route('/')
def index():
    """
    Home page: Displays a list of all bins.
    - Fetches bins from the database and displays them.
    - Provides links to view, edit, delete bins, and search for items.
    """
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bins ORDER BY number ASC')
    bins = cursor.fetchall()
    conn.close()
    return render_template('index.html', bins=bins)

@app.route('/bin/<int:bin_id>')
def bin_details(bin_id):
    """
    Displays details for a specific bin.
    - Includes the bin's location, QR code, and associated items.
    - Allows users to add, edit, or delete items in the bin.
    """
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
    """
    Add a new bin.
    - Generates a QR code for the bin based on its number and location.
    - Saves the bin details and QR code in the database.
    """
    if request.method == 'POST':
        number = request.form['number']
        location = request.form['location']
        
        # Generate QR code for the bin URL
        bin_url = f"{BASEURL}/bin/{number}"
        qr = qrcode.QRCode()
        qr.add_data(bin_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill="black", back_color="white")
        
        # Convert QR code to base64
        buffered = BytesIO()
        qr_img.save(buffered, format="PNG")
        qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()

        # Save bin to database
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO bins (number, location, qr_code) VALUES (?, ?, ?)', 
                       (number, location, qr_code_base64))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('add_bin.html')

@app.route('/edit_bin/<int:bin_id>', methods=['GET', 'POST'])
def edit_bin(bin_id):
    """
    Edit an existing bin.
    - Updates the bin's number, location, and QR code.
    """
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        number = request.form['number']
        location = request.form['location']
        
        # Generate updated QR code
        bin_url = f"{BASEURL}/bin/{number}"
        qr = qrcode.QRCode()
        qr.add_data(bin_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill="black", back_color="white")
        
        # Convert QR code to base64
        buffered = BytesIO()
        qr_img.save(buffered, format="PNG")
        qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()

        # Update bin in database
        cursor.execute('UPDATE bins SET number = ?, location = ?, qr_code = ? WHERE id = ?', 
                       (number, location, qr_code_base64, bin_id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    cursor.execute('SELECT * FROM bins WHERE id = ?', (bin_id,))
    bin = cursor.fetchone()
    conn.close()
    return render_template('edit_bin.html', bin=bin)

@app.route('/delete_bin/<int:bin_id>', methods=['POST'])
def delete_bin(bin_id):
    """
    Delete a bin and all its associated items.
    """
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM items WHERE bin_id = ?', (bin_id,))
    cursor.execute('DELETE FROM bins WHERE id = ?', (bin_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/add_item/<int:bin_id>', methods=['GET', 'POST'])
def add_item(bin_id):
    """
    Add a new item to a specific bin.
    """
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
    """
    Edit an existing item in a bin.
    """
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        cursor.execute('UPDATE items SET name = ?, description = ? WHERE id = ?', 
                       (name, description, item_id))
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
    """
    Delete an item from a bin.
    """
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute('SELECT bin_id FROM items WHERE id = ?', (item_id,))
    bin_id = cursor.fetchone()[0]
    cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('bin_details', bin_id=bin_id))

@app.route('/search_item', methods=['GET', 'POST'])
def search_item():
    """
    Search for items across all bins.
    - Returns items matching the search query, along with their associated bin details.
    """
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
    # Run the Flask application in debug mode
    app.run(debug=True)
