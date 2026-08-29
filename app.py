from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime, timedelta
import json
import os
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Order, Transaction, Message, LawyerDocument, Review
from forms import RegistrationForm, LoginForm, OrderForm, LawyerRegistrationForm

app = Flask(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY'] = 'your-secret-key-here!'

socketio = SocketIO(app, cors_allowed_origins="*")

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

COMMISSION_PERCENT = 10

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ====== Socket.IO ======
@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        room = f"user_{current_user.id}"
        join_room(room)

def send_notification(user_id, title, message, order_id=None):
    room = f"user_{user_id}"
    socketio.emit('new_notification', {
        'title': title,
        'message': message,
        'order_id': order_id,
        'timestamp': datetime.now().strftime('%H:%M')
    }, room=room)

# ====== Маршруты ======
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/client')
def client():
    return render_template('client.html')

@app.route('/lawyer')
def lawyer():
    return render_template('lawyer.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Пользователь с таким email уже существует', 'danger')
            return render_template('register.html', form=form)
        
        user = User(
            email=form.email.data,
            name=form.name.data,
            phone=form.phone.data,
            user_type=form.user_type.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Вход выполнен!', 'success')
            return redirect(url_for('index'))
        flash('Неверный email или пароль', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

@app.route('/client/dashboard')
@login_required
def client_dashboard():
    if current_user.user_type != 'client':
        flash('Доступ только для клиентов', 'danger')
        return redirect(url_for('index'))
    orders = Order.query.filter_by(client_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('client_dashboard.html', orders=orders)

@app.route('/client/new_order', methods=['GET', 'POST'])
@login_required
def new_order():
    if current_user.user_type != 'client':
        flash('Доступ только для клиентов', 'danger')
        return redirect(url_for('index'))
    
    form = OrderForm()
    
    if form.validate_on_submit():
        date_str = request.form.get('order_date')
        time_str = request.form.get('order_time')
        
        if not date_str or not time_str:
            flash('Пожалуйста, выберите дату и время заказа', 'danger')
            return render_template('new_order.html', form=form)
        
        try:
            datetime_str = f"{date_str} {time_str}:00"
            order_date = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            flash('Неверный формат даты или времени', 'danger')
            return render_template('new_order.html', form=form)
        
        if order_date < datetime.now():
            flash('Дата и время не могут быть в прошлом', 'danger')
            return render_template('new_order.html', form=form)
        
        base_price = app.config['BASE_PRICES'].get(form.service_type.data, 1000)
        time_diff = order_date - datetime.now()
        is_urgent = time_diff.total_seconds() < 86400 and time_diff.total_seconds() > 0
        
        if is_urgent:
            price = int(base_price * app.config['URGENCY_MULTIPLIER'])
        else:
            price = base_price
        
        commission = int(price * COMMISSION_PERCENT / 100)
        lawyer_amount = price - commission
        
        order = Order(
            client_id=current_user.id,
            service_type=form.service_type.data,
            description=form.description.data,
            location=form.location.data,
            date=order_date,
            price=price,
            is_urgent=is_urgent,
            status='pending',
            commission=commission,
            lawyer_amount=lawyer_amount
        )
        db.session.add(order)
        db.session.commit()
        
        online_lawyers = User.query.filter_by(
            user_type='lawyer',
            is_online=True
        ).all()
        
        for lawyer in online_lawyers:
            send_notification(
                lawyer.id,
                '📋 Новый заказ!',
                f'Клиент {current_user.name} ищет юриста. {price} ₽',
                order.id
            )
        
        flash(f'Заказ создан! Стоимость: {price} руб.', 'success')
        return redirect(url_for('order_detail', order_id=order.id))
    
    return render_template('new_order.html', form=form)

@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    
    if current_user.user_type == 'lawyer':
        return render_template('order_detail.html', order=order, lawyers=User.query.filter_by(user_type='lawyer', is_online=True).all())
    
    if current_user.user_type == 'client' and order.client_id == current_user.id:
        return render_template('order_detail.html', order=order, lawyers=User.query.filter_by(user_type='lawyer', is_online=True).all())
    
    flash('Нет доступа к этому заказу', 'danger')
    return redirect(url_for('index'))

@app.route('/lawyer/dashboard')
@login_required
def lawyer_dashboard():
    if current_user.user_type != 'lawyer':
        flash('Доступ только для юристов', 'danger')
        return redirect(url_for('index'))
    
    available_orders = Order.query.filter_by(
        status='pending'
    ).order_by(Order.created_at.desc()).all()
    
    my_orders = Order.query.filter_by(lawyer_id=current_user.id).all()
    
    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(Transaction.created_at.desc()).all()
    
    return render_template('lawyer_dashboard.html', 
                         available_orders=available_orders, 
                         my_orders=my_orders,
                         transactions=transactions)

@app.route('/api/online_status', methods=['POST'])
@login_required
def toggle_online():
    if current_user.user_type != 'lawyer':
        return jsonify({'error': 'Только для юристов'}), 403
    
    current_user.is_online = not current_user.is_online
    db.session.commit()
    return jsonify({'online': current_user.is_online})

@app.route('/api/order/<int:order_id>/accept', methods=['POST'])
@login_required
def accept_order(order_id):
    if current_user.user_type != 'lawyer':
        return jsonify({'error': 'Только юристы могут принимать заказы'}), 403
    
    order = Order.query.get_or_404(order_id)
    if order.status != 'pending':
        return jsonify({'error': 'Заказ уже принят'}), 400
    
    order.lawyer_id = current_user.id
    order.status = 'accepted'
    order.amount_held = order.price
    order.is_paid = True
    
    transaction = Transaction(
        order_id=order.id,
        user_id=current_user.id,
        amount=order.price,
        type='hold',
        status='completed',
        description=f'Блокировка средств по заказу #{order.id}'
    )
    db.session.add(transaction)
    db.session.commit()
    
    send_notification(
        order.client_id,
        '✅ Заказ принят!',
        f'Юрист {current_user.name} принял ваш заказ',
        order.id
    )
    
    return jsonify({
        'success': True, 
        'message': f'Заказ #{order.id} принят!',
        'order_id': order.id
    })

@app.route('/api/order/<int:order_id>/lawyer_confirm', methods=['POST'])
@login_required
def lawyer_confirm_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.lawyer_id != current_user.id:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    if order.status != 'accepted':
        return jsonify({'error': 'Заказ не в статусе "Принят"'}), 400
    
    order.lawyer_confirmed = True
    order.status = 'in_progress'
    db.session.commit()
    
    send_notification(
        order.client_id,
        '⚡ Заказ выполняется',
        f'Юрист {current_user.name} подтвердил выполнение заказа.',
        order.id
    )
    
    return jsonify({
        'success': True,
        'message': 'Вы подтвердили выполнение заказа.'
    })

@app.route('/api/order/<int:order_id>/client_confirm', methods=['POST'])
@login_required
def client_confirm_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.client_id != current_user.id:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    if order.lawyer_id is None:
        return jsonify({'error': 'Заказ еще не принят юристом'}), 400
    
    if not order.lawyer_confirmed:
        return jsonify({'error': 'Юрист еще не подтвердил выполнение заказа'}), 400
    
    order.client_confirmed = True
    order.status = 'completed'
    order.completed_at = datetime.now()
    
    lawyer = User.query.get(order.lawyer_id)
    if lawyer:
        lawyer.balance += order.lawyer_amount
        
        transaction_lawyer = Transaction(
            order_id=order.id,
            user_id=order.lawyer_id,
            amount=order.lawyer_amount,
            type='charge',
            status='completed',
            description=f'Оплата по заказу #{order.id}'
        )
        db.session.add(transaction_lawyer)
        
        transaction_commission = Transaction(
            order_id=order.id,
            user_id=1,
            amount=order.commission,
            type='commission',
            status='completed',
            description=f'Комиссия платформы по заказу #{order.id}'
        )
        db.session.add(transaction_commission)
        
        db.session.commit()
        
        send_notification(
            order.lawyer_id,
            '💰 Деньги зачислены!',
            f'Клиент подтвердил заказ #{order.id}. Получено {order.lawyer_amount} ₽',
            order.id
        )
    
    return jsonify({
        'success': True,
        'message': f'Заказ завершен! Юрист получил {order.lawyer_amount} руб.'
    })

@app.route('/api/order/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.client_id != current_user.id:
        return jsonify({'error': 'Только клиент может отменить заказ'}), 403
    
    if order.status not in ['pending', 'accepted']:
        return jsonify({'error': 'Заказ нельзя отменить'}), 400
    
    order.status = 'cancelled'
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Заказ отменен'})

@app.route('/api/lawyer_stats')
@login_required
def lawyer_stats():
    if current_user.user_type != 'lawyer':
        return jsonify({'error': 'Доступ только для юристов'}), 403
    
    balance = current_user.balance or 0
    
    in_progress_orders = Order.query.filter_by(
        lawyer_id=current_user.id,
        status='in_progress'
    ).all()
    potential = sum([o.lawyer_amount for o in in_progress_orders])
    
    completed_orders = Order.query.filter_by(
        lawyer_id=current_user.id,
        status='completed'
    ).all()
    total = sum([o.lawyer_amount for o in completed_orders])
    
    return jsonify({
        'balance': balance,
        'potential': potential,
        'total': total
    })

@app.route('/api/platform_stats')
@login_required
def platform_stats():
    if current_user.id != 1:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    total_orders = Order.query.count()
    total_commission = db.session.query(db.func.sum(Order.commission)).scalar() or 0
    total_lawyer_payments = db.session.query(db.func.sum(Order.lawyer_amount)).filter(Order.status == 'completed').scalar() or 0
    
    return jsonify({
        'total_orders': total_orders,
        'total_commission': total_commission,
        'total_lawyer_payments': total_lawyer_payments
    })

@app.route('/api/order/<int:order_id>/rate', methods=['POST'])
@login_required
def rate_lawyer(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.client_id != current_user.id:
        return jsonify({'error': 'Только клиент может оценивать'}), 403
    
    if order.status != 'completed':
        return jsonify({'error': 'Заказ еще не выполнен'}), 400
    
    existing = Review.query.filter_by(order_id=order.id).first()
    if existing:
        return jsonify({'error': 'Вы уже оценили этого юриста'}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Нет данных'}), 400
    
    score = data.get('score')
    comment = data.get('comment', '')
    
    if score is None or score < 1 or score > 10:
        return jsonify({'error': 'Оценка должна быть от 1 до 10'}), 400
    
    review = Review(
        order_id=order.id,
        lawyer_id=order.lawyer_id,
        client_id=current_user.id,
        score=score,
        comment=comment
    )
    db.session.add(review)
    
    lawyer = User.query.get(order.lawyer_id)
    if lawyer:
        total = lawyer.rating * lawyer.rating_count + score
        lawyer.rating_count += 1
        lawyer.rating = round(total / lawyer.rating_count, 1)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Спасибо за вашу оценку!',
        'rating': lawyer.rating if lawyer else 0,
        'rating_count': lawyer.rating_count if lawyer else 0
    })

@app.route('/api/order/<int:order_id>/messages', methods=['GET'])
@login_required
def get_messages(order_id):
    order = Order.query.get_or_404(order_id)
    if order.client_id != current_user.id and order.lawyer_id != current_user.id:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    messages = Message.query.filter_by(order_id=order_id).order_by(Message.created_at).all()
    return jsonify([{
        'id': m.id,
        'sender_id': m.sender_id,
        'sender_name': m.sender.name,
        'sender_type': m.sender.user_type,
        'text': m.text,
        'created_at': m.created_at.strftime('%H:%M'),
        'is_read': m.is_read
    } for m in messages])

@app.route('/api/order/<int:order_id>/send_message', methods=['POST'])
@login_required
def send_message(order_id):
    order = Order.query.get_or_404(order_id)
    if order.client_id != current_user.id and order.lawyer_id != current_user.id:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    data = request.get_json()
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'Сообщение не может быть пустым'}), 400
    
    message = Message(
        order_id=order_id,
        sender_id=current_user.id,
        text=text
    )
    db.session.add(message)
    db.session.commit()
    
    recipient_id = order.client_id if current_user.id == order.lawyer_id else order.lawyer_id
    if recipient_id:
        send_notification(
            recipient_id,
            f'💬 Новое сообщение от {current_user.name}',
            text[:50] + ('...' if len(text) > 50 else ''),
            order_id
        )
    
    return jsonify({
        'success': True,
        'message': {
            'id': message.id,
            'sender_id': message.sender_id,
            'sender_name': message.sender.name,
            'sender_type': message.sender.user_type,
            'text': message.text,
            'created_at': message.created_at.strftime('%H:%M')
        }
    })

@app.route('/api/order/<int:order_id>/messages/mark_read', methods=['POST'])
@login_required
def mark_messages_read(order_id):
    order = Order.query.get_or_404(order_id)
    if order.client_id != current_user.id and order.lawyer_id != current_user.id:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    messages = Message.query.filter_by(
        order_id=order_id,
        is_read=False
    ).filter(Message.sender_id != current_user.id).all()
    
    for m in messages:
        m.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/lawyer/register', methods=['GET', 'POST'])
def lawyer_register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LawyerRegistrationForm()
    
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Пользователь с таким email уже существует', 'danger')
            return render_template('lawyer_register.html', form=form)
        
        user = User(
            email=form.email.data,
            name=form.name.data,
            phone=form.phone.data,
            user_type='lawyer',
            is_verified=False,
            verification_status='pending'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()
        
        UPLOAD_FOLDER = 'uploads/lawyer_docs'
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        
        def save_file(file, field_name):
            if file and file.filename:
                filename = secure_filename(f"{user.id}_{field_name}_{file.filename}")
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                return filepath
            return None
        
        lawyer_docs = LawyerDocument(
            user_id=user.id,
            passport_path=save_file(form.passport_file.data, 'passport'),
            inn_path=save_file(form.inn_file.data, 'inn'),
            snils_path=save_file(form.snils_file.data, 'snils'),
            diploma_path=save_file(form.diploma_file.data, 'diploma'),
            photo_path=save_file(form.photo_file.data, 'photo')
        )
        
        if form.is_lawyer.data:
            lawyer_docs.lawyer_license_path = save_file(form.lawyer_license_file.data, 'license')
            lawyer_docs.registry_extract_path = save_file(form.registry_extract_file.data, 'registry')
        
        db.session.add(lawyer_docs)
        db.session.commit()
        
        flash('✅ Ваши документы отправлены на проверку. Ожидайте подтверждения!', 'success')
        return redirect(url_for('login'))
    
    return render_template('lawyer_register.html', form=form)

@login_required
def test_rating():
    return render_template('test_rating.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)
