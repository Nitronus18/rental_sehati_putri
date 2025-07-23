from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'admin-rental'

# 🔧 DB Setup
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def buat_tabel_baju():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS baju (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            ukuran TEXT,
            kategori TEXT,
            stok INTEGER,
            harga INTEGER
        )
    ''')
    conn.commit()
    conn.close()

buat_tabel_baju()

@app.template_filter('rupiah')
def format_rupiah(value):
    try:
        return "Rp{:,.0f}".format(value).replace(",", ".")
    except:
        return "Rp0"

# 📦 Lihat Stok
@app.route('/stok')
def stok_baju():
    query = request.args.get('q', '').strip().lower()
    stok_filter = request.args.get('stok', 'semua')

    conn = get_db_connection()
    base = 'SELECT * FROM baju WHERE 1=1'
    params = []

    if stok_filter == 'tersedia':
        base += ' AND stok > 0'
    elif stok_filter == 'habis':
        base += ' AND stok = 0'

    if query:
        base += ' AND LOWER(nama) LIKE ?'
        params.append(f'%{query}%')

    base += ' ORDER BY nama ASC'
    baju = conn.execute(base, params).fetchall()
    conn.close()

    return render_template('stok_baju.html', baju=baju, query=query, stok_filter=stok_filter, active_page='stok')

# ➕ Tambah Baju
@app.route('/stok-baju/tambah', methods=['POST'])
def tambah_baju():
    nama = request.form['nama']
    ukuran = request.form['ukuran']
    kategori = request.form['kategori']
    harga = int(request.form['harga'])
    stok = int(request.form['stok'])

    conn = get_db_connection()
    conn.execute('INSERT INTO baju (nama, ukuran, kategori, stok, harga) VALUES (?, ?, ?, ?, ?)',
                 (nama, ukuran, kategori, stok, harga))
    conn.commit()
    conn.close()

    flash("✅ Baju berhasil ditambahkan.")
    return redirect(url_for('stok_baju'))

# ✏️ Update Stok
@app.route('/stok-baju/update/<int:id>', methods=['POST'])
def update_stok_baju(id):
    stok_baru = int(request.form['stok'])

    conn = get_db_connection()
    conn.execute('UPDATE baju SET stok = ? WHERE id = ?', (stok_baru, id))
    conn.commit()
    conn.close()

    flash("✅ Stok berhasil diperbarui.")
    return redirect(url_for('stok_baju'))

# 🏠 Dashboard
@app.route('/admin')
def dashboard_admin():
    return render_template('admin_dashboard.html', active_page='admin')

if __name__ == '__main__':
    app.run(debug=True)
