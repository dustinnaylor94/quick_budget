from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Temporary in-memory storage
budgets = []
expenses = []

class Budget:
    def __init__(self, id, name, total_amount):
        self.id = id
        self.name = name
        self.total_amount = total_amount
        
    @property
    def spent_amount(self):
        budget_expenses = [e for e in expenses if e['budget_id'] == self.id]
        return sum(e['amount'] for e in budget_expenses)

# Routes
@app.route('/')
def home():
    return render_template('home.html', budgets=budgets)

@app.route('/add_budget', methods=['GET', 'POST'])
def add_budget():
    if request.method == 'POST':
        name = request.form.get('name')
        total_amount = float(request.form.get('total_amount'))
        budget = Budget(len(budgets) + 1, name, total_amount)
        budgets.append(budget)
        return redirect(url_for('home'))
    return render_template('add_budget.html')

@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        budget_id = int(request.form.get('budget_id'))
        name = request.form.get('name')
        amount = float(request.form.get('amount'))
        date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        
        expense = {
            'id': len(expenses) + 1,
            'name': name,
            'amount': amount,
            'date': date,
            'budget_id': budget_id
        }
        expenses.append(expense)
        return redirect(url_for('home'))
    
    return render_template('add_expense.html', budgets=budgets)

@app.route('/budget/<int:budget_id>')
def view_budget(budget_id):
    budget = next((b for b in budgets if b.id == budget_id), None)
    if budget is None:
        return "Budget not found", 404
    budget_expenses = [e for e in expenses if e['budget_id'] == budget_id]
    return render_template('view_budget.html', budget=budget, expenses=budget_expenses)

@app.route('/expense/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    global expenses
    expenses = [e for e in expenses if e['id'] != expense_id]
    return jsonify({'success': True})

@app.route('/expense/<int:expense_id>', methods=['PUT'])
def update_expense(expense_id):
    data = request.get_json()
    expense = next((e for e in expenses if e['id'] == expense_id), None)
    if expense:
        expense['name'] = data.get('name', expense['name'])
        expense['amount'] = float(data.get('amount', expense['amount']))
        expense['date'] = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
    return jsonify({'success': True})

@app.route('/budget/<int:budget_id>', methods=['PUT'])
def update_budget(budget_id):
    budget = next((b for b in budgets if b.id == budget_id), None)
    if budget:
        data = request.get_json()
        budget.name = data.get('name', budget.name)
        budget.total_amount = float(data.get('total_amount', budget.total_amount))
    return jsonify({'success': True})

@app.route('/budget/<int:budget_id>', methods=['DELETE'])
def delete_budget(budget_id):
    global budgets, expenses
    budgets = [b for b in budgets if b.id != budget_id]
    expenses = [e for e in expenses if e['budget_id'] != budget_id]
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
