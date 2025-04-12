from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Use PostgreSQL in production (Railway) or SQLite in development
if 'DATABASE_URL' in os.environ:
    # Fix for Railway's postgres:// URLs
    database_url = os.environ['DATABASE_URL']
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///budget.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

db = SQLAlchemy(app)

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expenses = db.relationship('Expense', backref='budget', lazy=True, cascade='all, delete-orphan')

    @property
    def spent_amount(self):
        return sum(expense.amount for expense in self.expenses)

    @property
    def remaining_amount(self):
        return self.total_amount - self.spent_amount

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

@app.route('/')
def home():
    budgets = Budget.query.all()
    return render_template('home.html', budgets=budgets)

@app.route('/add_budget', methods=['GET', 'POST'])
def add_budget():
    if request.method == 'POST':
        name = request.form.get('name')
        total_amount = float(request.form.get('total_amount'))
        budget = Budget(name=name, total_amount=total_amount)
        db.session.add(budget)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('add_budget.html')

@app.route('/budget/<int:budget_id>')
def view_budget(budget_id):
    budget = Budget.query.get_or_404(budget_id)
    return render_template('view_budget.html', budget=budget, expenses=budget.expenses)

@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        budget_id = int(request.form.get('budget_id'))
        budget = Budget.query.get_or_404(budget_id)
        
        expense = Expense(
            description=request.form.get('name'),  # Using 'name' from the form as description
            amount=float(request.form.get('amount')),
            date=datetime.strptime(request.form.get('date'), '%Y-%m-%d').date(),
            budget_id=budget_id
        )
        db.session.add(expense)
        db.session.commit()
        return redirect(url_for('view_budget', budget_id=budget_id))
    
    budgets = Budget.query.all()
    return render_template('add_expense.html', budgets=budgets)

@app.route('/expense/<int:expense_id>', methods=['PUT', 'DELETE'])
def manage_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    
    if request.method == 'DELETE':
        db.session.delete(expense)
        db.session.commit()
        return jsonify({'success': True})
    
    data = request.get_json()
    expense.description = data.get('name', expense.description)  # Frontend sends 'name'
    expense.amount = float(data.get('amount', expense.amount))
    expense.date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/budget/<int:budget_id>', methods=['PUT'])
def update_budget(budget_id):
    budget = Budget.query.get_or_404(budget_id)
    data = request.get_json()
    
    budget.name = data.get('name', budget.name)
    budget.total_amount = float(data.get('total_amount', budget.total_amount))
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/budget/<int:budget_id>', methods=['DELETE'])
def delete_budget(budget_id):
    budget = Budget.query.get_or_404(budget_id)
    db.session.delete(budget)
    db.session.commit()
    return jsonify({'success': True})

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)

if __name__ == '__main__':
    app.run(debug=True)
