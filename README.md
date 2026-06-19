# 👟 SoleStep — Aplikasi Web Toko Sepatu

Aplikasi web e-commerce sepatu lengkap dengan sistem autentikasi 3 level dan fitur CRUD.

---

## 🏗️ Teknologi

| Layer | Teknologi |
|-------|-----------|
| Frontend | HTML5, Tailwind CSS (CDN), Vanilla JS |
| Backend | Python 3, Flask, SQLAlchemy |
| Database | SQLite (auto-created) |
| Auth | JWT (JSON Web Token) |

---

## 👥 Level Pengguna

| Role | Akun Demo | Password | Akses |
|------|-----------|----------|-------|
| 👑 Super Admin (CEO) | ceo@solestep.com | superadmin123 | Full CRUD semua data, hapus produk/user, kelola semua |
| 🛡️ Admin (Pekerja) | admin@solestep.com | admin123 | Tambah/edit produk, kelola pesanan, kelola kategori |
| 🛒 User Biasa | user@solestep.com | user123 | Lihat produk, tambah keranjang, checkout, lihat pesanan |

---

## 🚀 Cara Menjalankan

### 1. Install Dependencies

```bash
cd sepatu-store
pip install -r requirements.txt
```

### 2. Jalankan Backend

```bash
cd backend
python app.py
```

Backend berjalan di: **http://localhost:5000**

### 3. Buka Frontend

Buka browser, akses: **http://localhost:5000**

(Frontend di-serve langsung oleh Flask)

---

## 📁 Struktur Proyek

```
sepatu-store/
├── backend/
│   └── app.py          # Flask backend + API routes
├── frontend/
│   └── index.html      # Single Page App (HTML + Tailwind + JS)
├── requirements.txt
└── README.md
```

---

## 🔌 API Endpoints

### Auth
- `POST /api/auth/register` — Daftar akun baru
- `POST /api/auth/login` — Login
- `GET /api/auth/me` — Data user saat ini

### Produk
- `GET /api/products` — Daftar produk (filter: search, category, featured)
- `GET /api/products/:id` — Detail produk
- `POST /api/products` — Tambah produk *(Admin/SuperAdmin)*
- `PUT /api/products/:id` — Edit produk *(Admin/SuperAdmin)*
- `DELETE /api/products/:id` — Hapus produk *(SuperAdmin only)*

### Kategori
- `GET /api/categories` — Daftar kategori
- `POST /api/categories` — Tambah kategori *(Admin/SuperAdmin)*
- `DELETE /api/categories/:id` — Hapus kategori *(SuperAdmin only)*

### Pesanan
- `POST /api/orders` — Buat pesanan *(User login)*
- `GET /api/orders` — Lihat pesanan (user: pesanan sendiri, admin: semua)
- `PUT /api/orders/:id/status` — Update status *(Admin/SuperAdmin)*

### Users *(SuperAdmin only)*
- `GET /api/users` — Semua pengguna
- `PUT /api/users/:id` — Update role user
- `DELETE /api/users/:id` — Hapus user

### Dashboard
- `GET /api/stats` — Statistik toko *(Admin/SuperAdmin)*

---

## ✨ Fitur Lengkap

- ✅ **CRUD Produk** — Tambah, lihat, edit, hapus dengan gambar
- ✅ **CRUD Kategori** — Manajemen kategori sepatu
- ✅ **User Login Leveling** — Super Admin, Admin, User Biasa
- ✅ **Keranjang Belanja** — Persistent di localStorage
- ✅ **Checkout & Pesanan** — Order tracking dengan status
- ✅ **Dashboard Admin** — Statistik, manajemen produk/pesanan/user
- ✅ **Pencarian & Filter** — Real-time search + filter kategori
- ✅ **Responsif** — Mobile-first design
- ✅ **Animasi Smooth** — CSS animations, hover effects, transitions
- ✅ **JWT Auth** — Secure token-based authentication
