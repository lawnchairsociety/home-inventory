from flask import Flask, render_template, request, redirect, url_for
import sqlite3

# Initialize Flask app
app = Flask(__name__)

# Function to initialize the database and create tables if they don't exist
def init_db():
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    
    # Create 'bins' table for storing bin information
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        number TEXT NOT NULL,
        location TEXT NOT NULL
    )''')
    
    # Create 'items' table for storing items inside bins
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

# Call the database initialization function
init_db()

# Route for the homepage, displays a list of all bins
@app.route('/')
def index():
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bins ORDER BY number ASC')
    bins = cursor.fetchall()
    conn.close()
    return render_template('index.html', bins=bins)

# Route to display details of a specific bin and its items
@app.route('/bin/<int:bin_id>')
def bin_details(bin_id):
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bins WHERE id = ?', (bin_id,))  # Fetch bin details
    bin = cursor.fetchone()
    cursor.execute('SELECT * FROM items WHERE bin_id = ?', (bin_id,))  # Fetch items in the bin
    items = cursor.fetchall()
    conn.close()
    return render_template('bin_details.html', bin=bin, items=items)

# Route to add a new bin
@app.route('/add_bin', methods=['GET', 'POST'])
def add_bin():
    if request.method == 'POST':
        number = request.form['number']  # Bin number from form
        location = request.form['location']  # Location from form
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO bins (number, location) VALUES (?, ?)', (number, location))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))  # Redirect to homepage
    return render_template('add_bin.html')

# Route to edit a bin
@app.route('/edit_bin/<int:bin_id>', methods=['GET', 'POST'])
def edit_bin(bin_id):
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        number = request.form['number']  # Updated bin number
        location = request.form['location']  # Updated location
        cursor.execute('UPDATE bins SET number = ?, location = ? WHERE id = ?', (number, location, bin_id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))  # Redirect to homepage
    
    cursor.execute('SELECT * FROM bins WHERE id = ?', (bin_id,))
    bin = cursor.fetchone()
    conn.close()
    return render_template('edit_bin.html', bin=bin)

# Route to delete a bin and its associated items
@app.route('/delete_bin/<int:bin_id>', methods=['POST'])
def delete_bin(bin_id):
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM items WHERE bin_id = ?', (bin_id,))  # Delete items in the bin
    cursor.execute('DELETE FROM bins WHERE id = ?', (bin_id,))  # Delete the bin itself
    conn.commit()
    conn.close()
    return redirect(url_for('index'))  # Redirect to homepage

# Route to add an item to a specific bin
@app.route('/add_item/<int:bin_id>', methods=['GET', 'POST'])
def add_item(bin_id):
    if request.method == 'POST':
        name = request.form['name']  # Item name from form
        description = request.form['description']  # Item description from form
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO items (name, description, bin_id) VALUES (?, ?, ?)',
                       (name, description, bin_id))
        conn.commit()
        conn.close()
        return redirect(url_for('bin_details', bin_id=bin_id))  # Redirect to bin details page
    return render_template('add_item.html', bin_id=bin_id)

# Route to edit an item
@app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        name = request.form['name']  # Updated item name
        description = request.form['description']  # Updated description
        cursor.execute('UPDATE items SET name = ?, description = ? WHERE id = ?', (name, description, item_id))
        conn.commit()
        conn.close()
        bin_id = request.form['bin_id']  # Redirect back to the bin containing the item
        return redirect(url_for('bin_details', bin_id=bin_id))
    
    cursor.execute('SELECT * FROM items WHERE id = ?', (item_id,))
    item = cursor.fetchone()
    cursor.execute('SELECT bin_id FROM items WHERE id = ?', (item_id,))
    bin_id = cursor.fetchone()[0]
    conn.close()
    return render_template('edit_item.html', item=item, bin_id=bin_id)

# Route to delete an item
@app.route('/delete_item/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute('SELECT bin_id FROM items WHERE id = ?', (item_id,))  # Get bin ID for redirect
    bin_id = cursor.fetchone()[0]
    cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))  # Delete the item
    conn.commit()
    conn.close()
    return redirect(url_for('bin_details', bin_id=bin_id))

# Route to search for bins
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form['query']  # Search query
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bins WHERE number LIKE ?", ('%' + query + '%',))
        bins = cursor.fetchall()
        conn.close()
        return render_template('search_results.html', bins=bins, query=query)
    return redirect(url_for('index'))

# Route to search for items
@app.route('/search_item', methods=['GET', 'POST'])
def search_item():
    if request.method == 'POST':
        query = request.form['query']  # Search query
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

# Run the Flask app in debug mode
if __name__ == '__main__':
    app.run(debug=True)
