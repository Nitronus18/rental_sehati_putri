from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3
from datetime import date, datetime
from io import BytesIO
import pandas as pd

app = Flask(__name__)
app.secret_key = 'rahasia'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# ===============================
# 🔁 PENGEMBALIAN
# ===============================
@app.route('/pengembalian')
def pengembalian():
    nama = request.args.get('nama', '').strip()
    tanggal = request.args.get('tanggal', '').strip()

    conn = get_db_connection()
    query = 'SELECT * FROM rental WHERE 1=1'
    params = []

    if nama:
        query += ' AND nama_penyewa LIKE ?'
        params.append(f"%{nama}%")
    if tanggal:
        query += ' AND tanggal_kembali = ?'
        params.append(tanggal)

    query += ' ORDER BY tanggal_kembali ASC'
    data = conn.execute(query, params).fetchall()
    conn.close()

    daftar = []
    for item in data:
        terlambat = False
        denda = 0
        try:
            tanggal_kembali = datetime.strptime(item['tanggal_kembali'], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            tanggal_kembali = date.today()

        if item['status'] != 'kembali' and date.today() > tanggal_kembali:
            terlambat = True
            denda = 50000

        daftar.append({**dict(item), 'terlambat': terlambat, 'denda': denda})

    return render_template('pengembalian.html',
                           daftar_pengembalian=daftar,
                           active_page='pengembalian')

@app.route('/konfirmasi-pengembalian', methods=['POST'])
def konfirmasi_pengembalian():
    id_rental = request.form.get('id_rental')

    if not id_rental:
        flash('ID rental tidak valid.', 'danger')
        return redirect(url_for('pengembalian'))

    conn = get_db_connection()
    conn.execute(
        'UPDATE rental SET status = "kembali", tanggal_dikembalikan = ? WHERE id = ?',
        (date.today(), id_rental)
    )
    conn.commit()
    conn.close()

    flash('Pengembalian telah berhasil dikonfirmasi.', 'success')
    return redirect(url_for('pengembalian'))

# ===============================
# 📥 Laporan Keuangan Masuk
# ===============================
@app.route('/keuangan/masuk')
def laporan_keuangan_masuk():
    q = request.args.get('q', '').strip()
    tanggal = request.args.get('tanggal', '').strip()
    export = request.args.get('export')

    query = "SELECT * FROM log_transaksi WHERE tipe = 'masuk'"
    params = []

    if q:
        query += " AND nama_penyewa LIKE ?"
        params.append(f"%{q}%")
    if tanggal:
        query += " AND tanggal = ?"
        params.append(tanggal)

    query += " ORDER BY tanggal DESC"

    conn = get_db_connection()
    data = conn.execute(query, params).fetchall()
    conn.close()

    total = sum(row['nominal'] for row in data)

    if export == 'excel':
        rows = [dict(row) for row in data]
        df = pd.DataFrame(rows)
        if 'tanggal' not in df.columns:
            flash("Gagal export Excel: kolom 'tanggal' tidak ditemukan.", 'danger')
            return redirect(url_for("laporan_keuangan_masuk"))

        grouped = df.groupby("tanggal")

        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for tgl, group in grouped:
                total_nominal = group["nominal"].sum()
                group_with_total = pd.concat([group, pd.DataFrame([{
                    "tanggal": "",
                    "nama_penyewa": "",
                    "nama_barang": "",
                    "ukuran": "",
                    "jumlah": "",
                    "tanggal_mulai": "",
                    "tanggal_dikembalikan": "",
                    "no_loker": "",
                    "nominal": total_nominal,
                    "tipe": "TOTAL"
                }])], ignore_index=True)
                group_with_total.to_excel(writer, sheet_name=str(tgl), index=False)

        output.seek(0)
        return send_file(output,
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         download_name='laporan_masuk_per_tanggal.xlsx',
                         as_attachment=True)

    return render_template("keuangan_masuk.html",
                           data=data,
                           total=total,
                           active_page='keuangan_masuk')

# ===============================
# 📤 Laporan Keuangan Keluar
# ===============================
@app.route("/keuangan/keluar")
def laporan_keluar():
    q = request.args.get("q", "").strip()
    tanggal = request.args.get("tanggal", "").strip()
    export = request.args.get("export")

    conn = get_db_connection()
    query = "SELECT * FROM log_transaksi WHERE tipe = 'keluar'"
    params = []

    if q:
        query += " AND nama_barang LIKE ?"
        params.append(f"%{q}%")
    if tanggal:
        query += " AND tanggal = ?"
        params.append(tanggal)

    query += " ORDER BY tanggal DESC"
    data = conn.execute(query, params).fetchall()
    conn.close()

    total = sum(row['nominal'] for row in data)

    if export == "excel":
        rows = [dict(row) for row in data]
        df = pd.DataFrame(rows)

        if 'tanggal' not in df.columns:
            flash("Gagal export Excel: kolom 'tanggal' tidak ditemukan.", 'danger')
            return redirect(url_for("laporan_keluar"))

        grouped = df.groupby("tanggal")

        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for tgl, group in grouped:
                df_sheet = pd.DataFrame({
                    "No": list(range(1, len(group) + 1)),
                    "Keterangan": group["nama_barang"],
                    "Tanggal": group["tanggal"],
                    "Nominal": group["nominal"]
                })

                # Tambah baris total
                total_row = pd.DataFrame([{
                    "No": "",
                    "Keterangan": "TOTAL",
                    "Tanggal": "",
                    "Nominal": group["nominal"].sum()
                }])

                final_df = pd.concat([df_sheet, total_row], ignore_index=True)
                final_df.to_excel(writer, sheet_name=str(tgl), index=False)

        output.seek(0)
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"laporan_pengeluaran_{datetime.now().date()}.xlsx"
        )

    return render_template(
        "keuangan_keluar.html",
        data=data,
        total=total,
        active_page="keuangan_keluar"
    )

# ➕ Tambah pengeluaran
@app.route("/keuangan/keluar/tambah", methods=["POST"])
def tambah_pengeluaran():
    tanggal = request.form.get("tanggal")
    keterangan = request.form.get("keterangan")
    nominal = request.form.get("nominal")

    if not (tanggal and keterangan and nominal):
        flash("Semua kolom harus diisi.")
        return redirect(url_for("laporan_keluar"))

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO log_transaksi (tanggal, tipe, nama_barang, nominal)
        VALUES (?, 'keluar', ?, ?)
    """, (tanggal, keterangan, nominal))
    conn.commit()
    conn.close()

    flash("Pengeluaran berhasil ditambahkan.")
    return redirect(url_for("laporan_keluar"))

# ❌ Hapus pengeluaran
@app.route("/keuangan/keluar/hapus/<int:id>", methods=["POST"])
def hapus_pengeluaran(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM log_transaksi WHERE id = ? AND tipe = 'keluar'", (id,))
    conn.commit()
    conn.close()

    flash("Data pengeluaran berhasil dihapus.")
    return redirect(url_for("laporan_keluar"))

# ===============================
# 🔧 HALAMAN DUMMY
# ===============================
@app.route('/lihat-stok')
@app.route('/stok-masuk')
@app.route('/stok-keluar')
@app.route('/daftar-booking')
@app.route('/tambah-booking')
@app.route('/jadwal-booking')
@app.route('/daftar-rental')
@app.route('/laporan-booking')
@app.route('/pengaturan')
@app.route('/admin')
@app.route('/stok')
@app.route('/booking')
@app.route('/rental')
def placeholder():
    return render_template('placeholder.html', title="Halaman Sedang Dibuat", active_page='')

# ===============================
# ▶️ JALANKAN SERVER
# ===============================
if __name__ == '__main__':
    app.run(debug=True)
