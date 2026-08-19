import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

db = SQLAlchemy(app)

class Dish(db.Model):
    __tablename__ = 'dishes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    image = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DishForm(FlaskForm):
    title = StringField('Назва страви', validators=[
        DataRequired(message="Введіть назву страви"),
        Length(min=2, max=100, message="Назва має бути від 2 до 100 символів")
    ])
    category = SelectField('Категорія', choices=[
        ('pizza', 'Піца'),
        ('main', 'Основні страви'),
        ('salad', 'Салати'),
        ('drink', 'Напої')
    ], validators=[DataRequired(message="Оберіть категорію")])
    description = TextAreaField('Опис', validators=[
        DataRequired(message="Введіть опис страви"),
        Length(min=10, max=500, message="Опис має бути від 10 до 500 символів")
    ])
    price = FloatField('Ціна (грн)', validators=[
        DataRequired(message="Введіть ціну"),
        NumberRange(min=0.01, message="Ціна має бути більше 0")
    ])
    is_available = BooleanField('Страва доступна', default=True)
    image = FileField('Зображення', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Дозволені формати: JPG, PNG, WEBP')
    ])
    submit = SubmitField('Додати страву')

@app.route('/')
def index():
    dishes = Dish.query.order_by(Dish.created_at.desc()).limit(4).all()
    return render_template('index.html', dishes=dishes)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/add-event', methods=['GET', 'POST'])
def add_dish():
    form = DishForm()
    if form.validate_on_submit():
        filename = None
        if form.image.data and form.image.data.filename:
            file = form.image.data
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{secrets.token_hex(8)}.{ext}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
        
        dish = Dish(
            title=form.title.data,
            category=form.category.data,
            description=form.description.data,
            price=form.price.data,
            is_available=form.is_available.data,
            image=filename
        )
        db.session.add(dish)
        db.session.commit()
        flash('Страву успішно додано до меню!', 'success')
        return redirect(url_for('events'))
    return render_template('add_event.html', form=form)

@app.route('/events')
def events():
    dishes = Dish.query.order_by(Dish.category, Dish.title).all()
    categories = {
        'pizza': [],
        'main': [],
        'salad': [],
        'drink': []
    }
    for dish in dishes:
        if dish.category in categories:
            categories[dish.category].append(dish)
    
    category_names = {
        'pizza': 'Піца',
        'main': 'Основні страви',
        'salad': 'Салати',
        'drink': 'Напої'
    }
    return render_template('events.html', categories=categories, category_names=category_names)

@app.route('/add-sample-dishes')
def add_sample_dishes():
    if Dish.query.count() == 0:
        dishes = [
            Dish(
                title='Піца Карбонара',
                category='pizza',
                description='Піца з беконом, пармезаном, яйцем пашот та вершковим соусом',
                price=285.00,
                is_available=True,
                image='pizza_carbonara.jpg'
            ),
            Dish(
                title='Піца 4 Сири',
                category='pizza',
                description='Ніжна піца з моцарелою, пармезаном, горгонзолою та рікоттою',
                price=275.00,
                is_available=True,
                image='pizza_4cheese.jpg'
            ),
            Dish(
                title='Яйце Пашот',
                category='main',
                description='Яйце пашот на тості з авокадо, голландським соусом та зеленню',
                price=165.00,
                is_available=True,
                image='egg_poached.jpg'
            ),
            Dish(
                title='Салат Цезар',
                category='salad',
                description='Класичний салат з куркою-гриль, пармезаном, крутонами та соусом Цезар',
                price=195.00,
                is_available=True,
                image='caesar_salad.jpg'
            )
        ]
        for dish in dishes:
            db.session.add(dish)
        db.session.commit()
        flash('Зразкові страви додано!', 'success')
    else:
        flash('Страви вже існують!', 'info')
    return redirect(url_for('index'))

@app.template_filter('category_label')
def category_label(category):
    labels = {
        'pizza': 'Піца',
        'main': 'Основна страва',
        'salad': 'Салат',
        'drink': 'Напій'
    }
    return labels.get(category, category)

@app.template_filter('category_emoji')
def category_emoji(category):
    emojis = {
        'pizza': '🍕',
        'main': '🍽️',
        'salad': '🥗',
        'drink': '🥤'
    }
    return emojis.get(category, '🍴')

@app.template_filter('color_from_name')
def color_from_name(name):
    hash_val = sum(ord(c) for c in name) % 360
    return f"hs1({hash_val}, 70%, 55%)"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()      
        app.run(debug=True)  