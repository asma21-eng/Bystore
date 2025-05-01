from flask import Blueprint, render_template, flash, redirect, request, jsonify
from flask_login import login_required, current_user
from .models import Product, Cart
from . import db

views = Blueprint('views', __name__)

@views.route('/')
def home():
    items = Product.query.filter_by(flash_sale=True)
    return render_template('home.html', items=items,
        cart=Cart.query.filter_by(customer_link=current_user.id).all()
        if current_user.is_authenticated else []
    )

@views.route('/add-to-cart/<int:item_id>')
@login_required
def add_to_cart(item_id):
    # Admin cannot add to cart
    if current_user.id == 1:
        flash('Admins cannot add products to cart.', 'warning')
        return redirect(request.referrer)

    item_to_add = Product.query.get(item_id)
    item_exists = Cart.query.filter_by(product_link=item_id, customer_link=current_user.id).first()

    if item_exists:
        # Check if adding 1 more exceeds stock
        if item_exists.quantity + 1 > item_to_add.in_stock:
            flash(f'Cannot add more. Only {item_to_add.in_stock} items available in stock.', 'warning')
            return redirect(request.referrer)
        try:
            item_exists.quantity += 1
            db.session.commit()
            flash(f'Quantity of {item_exists.product.product_name} has been updated.', 'success')
        except Exception as e:
            print('Quantity not Updated', e)
            flash('Failed to update quantity.', 'danger')
        return redirect(request.referrer)

    # If no item exists in cart, create new one
    if item_to_add.in_stock >= 1:
        new_cart_item = Cart(
            quantity=1,
            product_link=item_to_add.id,
            customer_link=current_user.id
        )
        try:
            db.session.add(new_cart_item)
            db.session.commit()
            flash(f'{new_cart_item.product.product_name} added to cart.', 'success')
        except Exception as e:
            print('Item not added to cart', e)
            flash('Failed to add item to cart.', 'danger')
    else:
        flash(f'{item_to_add.product_name} is out of stock.', 'danger')

    return redirect(request.referrer)

@views.route('/cart')
@login_required
def show_cart():
    cart = Cart.query.filter_by(customer_link=current_user.id).all()
    amount = sum(item.product.current_price * item.quantity for item in cart)
    return render_template('cart.html', cart=cart, amount=amount, total=amount + 200)

@views.route('/pluscart')
@login_required
def plus_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        product = Product.query.get(cart_item.product_link)

        if cart_item.customer_link != current_user.id:
            return jsonify({'status': 'error', 'message': 'Unauthorized access.'})

        # Check if adding 1 more exceeds stock
        if cart_item.quantity + 1 > product.in_stock:
            return jsonify({
                'status': 'error',
                'message': f'Cannot add more. Only {product.in_stock} items available.'
            })

        cart_item.quantity += 1
        db.session.commit()

        cart = Cart.query.filter_by(customer_link=current_user.id).all()
        amount = sum(item.product.current_price * item.quantity for item in cart)

        return jsonify({
            'status': 'success',
            'quantity': cart_item.quantity,
            'amount': amount,
            'total': amount + 200
        })

@views.route('/minuscart')
@login_required
def minus_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)

        if cart_item.customer_link != current_user.id:
            return jsonify({'status': 'error', 'message': 'Unauthorized access.'})

        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            db.session.commit()
        else:
            # Optional: If quantity reaches 0, remove item
            db.session.delete(cart_item)
            db.session.commit()

        cart = Cart.query.filter_by(customer_link=current_user.id).all()
        amount = sum(item.product.current_price * item.quantity for item in cart)

        return jsonify({
            'status': 'success',
            'quantity': cart_item.quantity if cart_item in db.session else 0,
            'amount': amount,
            'total': amount + 200
        })

@views.route('/removecart')
@login_required
def remove_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)

        if cart_item.customer_link != current_user.id:
            return jsonify({'status': 'error', 'message': 'Unauthorized access.'})

        db.session.delete(cart_item)
        db.session.commit()

        cart = Cart.query.filter_by(customer_link=current_user.id).all()
        amount = sum(item.product.current_price * item.quantity for item in cart)

        return jsonify({
            'status': 'success',
            'amount': amount,
            'total': amount + 200
        })
@views.route('/about')
def about():
    return render_template('about.html')

@views.route('/contact')
def contact():
    return render_template('contact.html')
