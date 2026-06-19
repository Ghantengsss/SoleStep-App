from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import os
import functools

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app, origins="*", supports_credentials=True)

app.config['SECRET_KEY'] = 'solestep-secret-2024-ultrasecure'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///solestep.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== MODELS ====================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')  # superadmin, admin, user
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    orders = db.relationship('Order', backref='user', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    size_options = db.Column(db.String(200), default='39,40,41,42,43,44')
    image_url = db.Column(db.String(300), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, processing, shipped, delivered, cancelled
    address = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    size = db.Column(db.String(10), nullable=True)
    price = db.Column(db.Float, nullable=False)
    product = db.relationship('Product')

# ==================== AUTH HELPERS ====================

def generate_token(user):
    payload = {
        'user_id': user.id,
        'role': user.role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def token_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Token diperlukan'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'User tidak ditemukan'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token kadaluarsa'}), 401
        except Exception:
            return jsonify({'error': 'Token tidak valid'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @functools.wraps(f)
        def decorated(current_user, *args, **kwargs):
            if current_user.role not in roles:
                return jsonify({'error': 'Akses ditolak'}), 403
            return f(current_user, *args, **kwargs)
        return token_required(decorated)
    return decorator

# ==================== AUTH ROUTES ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    if not data or not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'error': 'Data tidak lengkap'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email sudah terdaftar'}), 409
    user = User(
        name=data['name'],
        email=data['email'],
        password=generate_password_hash(data['password']),
        role='user'
    )
    db.session.add(user)
    db.session.commit()
    token = generate_token(user)
    return jsonify({'token': token, 'user': {'id': user.id, 'name': user.name, 'email': user.email, 'role': user.role}}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email dan password diperlukan'}), 400
    user = User.query.filter_by(email=data['email']).first()
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'error': 'Email atau password salah'}), 401
    token = generate_token(user)
    return jsonify({'token': token, 'user': {'id': user.id, 'name': user.name, 'email': user.email, 'role': user.role}})

@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_me(current_user):
    return jsonify({'id': current_user.id, 'name': current_user.name, 'email': current_user.email, 'role': current_user.role})

# ==================== PRODUCT ROUTES ====================

@app.route('/api/products', methods=['GET'])
def get_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    featured = request.args.get('featured', '')

    query = Product.query
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%') | Product.brand.ilike(f'%{search}%'))
    if category:
        cat = Category.query.filter_by(slug=category).first()
        if cat:
            query = query.filter_by(category_id=cat.id)
    if featured == 'true':
        query = query.filter_by(is_featured=True)

    pagination = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items

    return jsonify({
        'products': [serialize_product(p) for p in products],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@app.route('/api/products/<int:pid>', methods=['GET'])
def get_product(pid):
    p = Product.query.get_or_404(pid)
    return jsonify(serialize_product(p))

@app.route('/api/products', methods=['POST'])
@role_required('superadmin', 'admin')
def create_product(current_user):
    data = request.json
    if not data or not data.get('name') or not data.get('price'):
        return jsonify({'error': 'Data tidak lengkap'}), 400
    p = Product(
        name=data['name'],
        brand=data.get('brand', ''),
        description=data.get('description', ''),
        price=float(data['price']),
        stock=int(data.get('stock', 0)),
        size_options=data.get('size_options', '39,40,41,42,43,44'),
        image_url=data.get('image_url', ''),
        category_id=data.get('category_id'),
        is_featured=data.get('is_featured', False)
    )
    db.session.add(p)
    db.session.commit()
    return jsonify(serialize_product(p)), 201

@app.route('/api/products/<int:pid>', methods=['PUT'])
@role_required('superadmin', 'admin')
def update_product(current_user, pid):
    p = Product.query.get_or_404(pid)
    data = request.json
    for field in ['name', 'brand', 'description', 'price', 'stock', 'size_options', 'image_url', 'category_id', 'is_featured']:
        if field in data:
            val = data[field]
            if field == 'price': val = float(val)
            if field == 'stock': val = int(val)
            setattr(p, field, val)
    db.session.commit()
    return jsonify(serialize_product(p))

@app.route('/api/products/<int:pid>', methods=['DELETE'])
@role_required('superadmin')
def delete_product(current_user, pid):
    p = Product.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    return jsonify({'message': 'Produk dihapus'})

def serialize_product(p):
    return {
        'id': p.id,
        'name': p.name,
        'brand': p.brand,
        'description': p.description,
        'price': p.price,
        'stock': p.stock,
        'size_options': p.size_options.split(',') if p.size_options else [],
        'image_url': p.image_url,
        'category_id': p.category_id,
        'category': p.category.name if p.category else None,
        'is_featured': p.is_featured,
        'created_at': p.created_at.isoformat()
    }

# ==================== CATEGORY ROUTES ====================

@app.route('/api/categories', methods=['GET'])
def get_categories():
    cats = Category.query.all()
    return jsonify([{'id': c.id, 'name': c.name, 'slug': c.slug} for c in cats])

@app.route('/api/categories', methods=['POST'])
@role_required('superadmin', 'admin')
def create_category(current_user):
    data = request.json
    c = Category(name=data['name'], slug=data['slug'])
    db.session.add(c)
    db.session.commit()
    return jsonify({'id': c.id, 'name': c.name, 'slug': c.slug}), 201

@app.route('/api/categories/<int:cid>', methods=['DELETE'])
@role_required('superadmin')
def delete_category(current_user, cid):
    c = Category.query.get_or_404(cid)
    db.session.delete(c)
    db.session.commit()
    return jsonify({'message': 'Kategori dihapus'})

# ==================== ORDER ROUTES ====================

@app.route('/api/orders', methods=['POST'])
@token_required
def create_order(current_user):
    data = request.json
    items_data = data.get('items', [])
    if not items_data:
        return jsonify({'error': 'Keranjang kosong'}), 400

    total = 0
    order_items = []
    for item in items_data:
        product = Product.query.get(item['product_id'])
        if not product:
            return jsonify({'error': f'Produk {item["product_id"]} tidak ditemukan'}), 404
        if product.stock < item['quantity']:
            return jsonify({'error': f'Stok {product.name} tidak mencukupi'}), 400
        product.stock -= item['quantity']
        subtotal = product.price * item['quantity']
        total += subtotal
        order_items.append(OrderItem(product_id=product.id, quantity=item['quantity'], size=item.get('size'), price=product.price))

    order = Order(user_id=current_user.id, total=total, address=data.get('address', ''), notes=data.get('notes', ''))
    db.session.add(order)
    db.session.flush()
    for oi in order_items:
        oi.order_id = order.id
        db.session.add(oi)
    db.session.commit()
    return jsonify({'message': 'Pesanan berhasil dibuat', 'order_id': order.id}), 201

@app.route('/api/orders', methods=['GET'])
@token_required
def get_orders(current_user):
    if current_user.role in ('superadmin', 'admin'):
        orders = Order.query.order_by(Order.created_at.desc()).all()
    else:
        orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return jsonify([serialize_order(o) for o in orders])

@app.route('/api/orders/<int:oid>', methods=['GET'])
@token_required
def get_order(current_user, oid):
    o = Order.query.get_or_404(oid)
    if current_user.role not in ('superadmin', 'admin') and o.user_id != current_user.id:
        return jsonify({'error': 'Akses ditolak'}), 403
    return jsonify(serialize_order(o))

@app.route('/api/orders/<int:oid>/status', methods=['PUT'])
@role_required('superadmin', 'admin')
def update_order_status(current_user, oid):
    o = Order.query.get_or_404(oid)
    data = request.json
    o.status = data.get('status', o.status)
    db.session.commit()
    return jsonify(serialize_order(o))

def serialize_order(o):
    return {
        'id': o.id,
        'user_id': o.user_id,
        'user_name': o.user.name if o.user else '',
        'total': o.total,
        'status': o.status,
        'address': o.address,
        'notes': o.notes,
        'created_at': o.created_at.isoformat(),
        'items': [{
            'product_id': i.product_id,
            'product_name': i.product.name if i.product else '',
            'quantity': i.quantity,
            'size': i.size,
            'price': i.price
        } for i in o.items]
    }

# ==================== ADMIN: USER MANAGEMENT ====================

@app.route('/api/users', methods=['GET'])
@role_required('superadmin')
def get_users(current_user):
    users = User.query.all()
    return jsonify([{'id': u.id, 'name': u.name, 'email': u.email, 'role': u.role, 'created_at': u.created_at.isoformat()} for u in users])

@app.route('/api/users/<int:uid>', methods=['PUT'])
@role_required('superadmin')
def update_user(current_user, uid):
    u = User.query.get_or_404(uid)
    data = request.json
    if 'role' in data:
        u.role = data['role']
    if 'name' in data:
        u.name = data['name']
    db.session.commit()
    return jsonify({'id': u.id, 'name': u.name, 'email': u.email, 'role': u.role})

@app.route('/api/users/<int:uid>', methods=['DELETE'])
@role_required('superadmin')
def delete_user(current_user, uid):
    if uid == current_user.id:
        return jsonify({'error': 'Tidak bisa hapus diri sendiri'}), 400
    u = User.query.get_or_404(uid)
    db.session.delete(u)
    db.session.commit()
    return jsonify({'message': 'User dihapus'})

# ==================== DASHBOARD STATS ====================

@app.route('/api/stats', methods=['GET'])
@role_required('superadmin', 'admin')
def get_stats(current_user):
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_users = User.query.count()
    total_revenue = db.session.query(db.func.sum(Order.total)).filter(Order.status != 'cancelled').scalar() or 0
    pending_orders = Order.query.filter_by(status='pending').count()
    return jsonify({
        'total_products': total_products,
        'total_orders': total_orders,
        'total_users': total_users,
        'total_revenue': total_revenue,
        'pending_orders': pending_orders
    })

# ==================== SERVE FRONTEND ====================

@app.route('/')
@app.route('/<path:path>')
def serve_frontend(path=''):
    frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    if path and os.path.exists(os.path.join(frontend_dir, path)):
        return send_from_directory(frontend_dir, path)
    return send_from_directory(frontend_dir, 'index.html')

# ==================== SEED DATA ====================

def seed_database():
    if User.query.count() == 0:
        users = [
            User(name='CEO SoleStep', email='ceo@solestep.com', password=generate_password_hash('superadmin123'), role='superadmin'),
            User(name='Admin Toko', email='admin@solestep.com', password=generate_password_hash('admin123'), role='admin'),
            User(name='Budi Pembeli', email='user@solestep.com', password=generate_password_hash('user123'), role='user'),
        ]
        db.session.add_all(users)

        cats = [
            Category(name='Running', slug='running'),
            Category(name='Casual', slug='casual'),
            Category(name='Basketball', slug='basketball'),
            Category(name='Futsal', slug='futsal'),
            Category(name='Formal', slug='formal'),
        ]
        db.session.add_all(cats)
        db.session.flush()

        shoe_images = [
            'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600',
            'https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=600',
            'https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?w=600',
            'https://images.unsplash.com/photo-1584735175315-9d5df23be5c9?w=600',
            'https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=600',
            'https://images.unsplash.com/photo-1612902456551-b7c34abc8be9?w=600',
            'https://images.unsplash.com/photo-1600185365483-26d7a4cc7519?w=600',
            'https://images.unsplash.com/photo-1575537302964-96cd47c06b1b?w=600',
        ]

        products_data = [
            ('Nike Air Max 270', 'Nike', 'Sepatu lari dengan teknologi Air Max terbaru, nyaman dan ringan untuk aktivitas sehari-hari.', 1850000, 25, cats[0].id, True, shoe_images[0]),
            ('Adidas Ultraboost 22', 'Adidas', 'Teknologi Boost memberikan energi kembali setiap langkah. Pilihan terbaik para pelari.', 2200000, 18, cats[0].id, True, shoe_images[1]),
            ('New Balance 574', 'New Balance', 'Klasik yang tak lekang waktu. Sempurna untuk gaya kasual modern.', 1350000, 30, cats[1].id, False, shoe_images[2]),
            ('Jordan 1 Retro High', 'Nike', 'Ikon basket yang kini menjadi simbol streetwear global.', 3200000, 12, cats[2].id, True, shoe_images[3]),
            ('Puma Future Z', 'Puma', 'Sepatu futsal dengan grip terbaik, dirancang untuk kecepatan dan kontrol bola.', 980000, 40, cats[3].id, False, shoe_images[4]),
            ('Converse Chuck Taylor', 'Converse', 'Sepatu kanvas ikonik yang cocok untuk segala suasana casual.', 750000, 50, cats[1].id, False, shoe_images[5]),
            ('Reebok Classic Leather', 'Reebok', 'Desain formal modern dengan material kulit premium untuk tampilan profesional.', 1450000, 20, cats[4].id, False, shoe_images[6]),
            ('Vans Old Skool', 'Vans', 'Sepatu skateboard legendaris dengan garis signature side stripe.', 890000, 35, cats[1].id, True, shoe_images[7]),
        ]

        for name, brand, desc, price, stock, cat_id, featured, img in products_data:
            p = Product(name=name, brand=brand, description=desc, price=price, stock=stock, category_id=cat_id, is_featured=featured, image_url=img)
            db.session.add(p)

        db.session.commit()
        print("✅ Database berhasil di-seed!")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_database()
    app.run(debug=True, port=5000)
