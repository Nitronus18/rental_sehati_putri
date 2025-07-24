import sqlite3

def setup_database():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # ========================
    # TABEL STOK RENTAL
    # ========================
    c.execute('DROP TABLE IF EXISTS stok_rental')
    c.execute('''
        CREATE TABLE stok_rental (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_barang TEXT NOT NULL,
            kategori TEXT NOT NULL,
            ukuran TEXT NOT NULL,
            jumlah INTEGER NOT NULL,
            terakhir_masuk TEXT,
            terakhir_keluar TEXT
        )
    ''')

    dummy_stok = [
        ('Kebaya Putih', 'Adat', 'S', 4, '2025-07-01', '2025-07-05'),
        ('Kebaya Merah', 'Adat', 'M', 2, '2025-07-03', '2025-07-07'),
        ('Jas Hitam', 'Formal', 'L', 5, '2025-07-10', '2025-07-12'),
        ('Gaun Pesta Biru', 'Pesta', 'M', 3, '2025-07-08', '2025-07-09'),
        ('Seragam Sekolah', 'Kostum', 'XL', 6, '2025-07-04', '2025-07-06'),
        ('Kostum Polisi', 'Kostum', 'L', 2, '2025-07-05', None),
        ('Kebaya Hijau', 'Adat', 'L', 1, '2025-07-02', None),
    ]

    c.executemany('''
        INSERT INTO stok_rental (nama_barang, kategori, ukuran, jumlah, terakhir_masuk, terakhir_keluar)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', dummy_stok)

    # ========================
    # TABEL RENTAL
    # ========================
    c.execute('DROP TABLE IF EXISTS rental')
    c.execute('''
        CREATE TABLE rental (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_penyewa TEXT NOT NULL,
            nama_barang TEXT NOT NULL,
            tanggal_kembali TEXT NOT NULL,
            tanggal_dikembalikan TEXT,
            status TEXT DEFAULT 'dipinjam'
        )
    ''')

    c.executemany('''
        INSERT INTO rental (nama_penyewa, nama_barang, tanggal_kembali, status)
        VALUES (?, ?, ?, ?)
    ''', [
        ('Alya', 'Kebaya Putih', '2025-07-25', 'dipinjam'),
        ('Dina', 'Gaun Merah', '2025-07-22', 'kembali'),
        ('Rani', 'Kebaya Biru', '2025-07-23', 'kembali')
    ])

    # ========================
    # TABEL LOG TRANSAKSI
    # ========================
    c.execute('DROP TABLE IF EXISTS log_transaksi')
    c.execute('''
        CREATE TABLE log_transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT NOT NULL,
            nama_penyewa TEXT,
            nama_barang TEXT,
            ukuran TEXT,
            jumlah INTEGER,
            tanggal_mulai TEXT,
            tanggal_dikembalikan TEXT,
            no_loker TEXT,
            nominal INTEGER NOT NULL,
            tipe TEXT CHECK(tipe IN ('masuk', 'keluar')) NOT NULL
        )
    ''')

    dummy_transaksi = [
        # MASUK
        ('2025-07-20', 'Alya', 'Kebaya Putih', 'S', 1, '2025-07-20', '2025-07-21', 'L01', 150000, 'masuk'),
        ('2025-07-21', 'Rani', 'Jas Hitam', 'L', 2, '2025-07-21', '2025-07-22', 'L02', 200000, 'masuk'),
        ('2025-07-22', 'Dina', 'Gaun Pesta Biru', 'M', 1, '2025-07-22', '2025-07-23', 'L03', 175000, 'masuk'),

        # KELUAR
        ('2025-07-20', 'Admin', 'Biaya Listrik', '', 0, '', '', '', 50000, 'keluar'),
        ('2025-07-21', 'Admin', 'Beli Plastik', '', 0, '', '', '', 15000, 'keluar'),
        ('2025-07-23', 'Admin', 'Transport Antar', '', 0, '', '', '', 30000, 'keluar'),
    ]

    c.executemany('''
        INSERT INTO log_transaksi (
            tanggal, nama_penyewa, nama_barang, ukuran, jumlah,
            tanggal_mulai, tanggal_dikembalikan, no_loker, nominal, tipe
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', dummy_transaksi)

    conn.commit()
    conn.close()
    print("✅ Semua tabel berhasil dibuat dan data dummy dimasukkan!")

if __name__ == '__main__':
    setup_database()
