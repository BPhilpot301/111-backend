from flask import Flask, jsonify, request, render_template
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Date,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import date


#create a flask app instance
app = Flask(__name__)

#database setup
engine = create_engine("sqlite:///budget_manager.db")#way to connect to the database
Base = declarative_base()#base to define models, all models ingerit from this
Session = sessionmaker(bind=engine)#session factory, prepares sessions
session = Session()#create a session instance to interact with the db (add, commit,...)

#define models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer,primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(30), nullable=False)
    expenses = relationship("Expense", back_populates="user")#user.expenses, list all

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(String(200))
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False, default=date.today)
    category = Column(Enum("Food", "Education", "Entertainment"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="expenses")#user.expenses.username
    # Foreign key to link to user


# create tables
Base.metadata.create_all(engine)

#health check route
@app.get('/api/health')
def health_check():
    return jsonify({"status": "OK"}), 200


#user routes
@app.post('/api/register')
def register():
    data = request.get_json()
    username = data.get("username")#way to extract or get username from the json
    password = data.get("password")#same as previous line

    #validation
    existing_user = session.query(User).filter_by(username=username).first()
    if existing_user is not None:
        return jsonify({"error": "Username already exists"}), 400

    print(data)
    print(username)
    print(password)

    new_user = User(username=username, password=password)#create new user
    session.add(new_user)#add to the session
    session.commit()#commit to the database

    return jsonify({"message": "User registered successfully"})

#login
@app.post("/api/login")
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    user = session.query(User).filter_by(username=username).first()
    if user and user.password == password:
        return jsonify({"message": "Login successful"}), 200 #successful login
    
    return jsonify({"Error": "Invalid username or password"}), 401 #unauthorized

@app.get("/api/users/<user_id>")
def get_user(user_id):
    user = session.query(User).filter_by(id=user_id).first()

    if not user :
        return jsonify({"error": "User not found"}), 404
    
    user_data = {"id": user.id, "username": user.username}
    return jsonify(user_data), 200


#update a user
@app.put("/api/users/<user_id>")
def update_user(user_id):
    data = request.get_json()
    new_username = data.get("username")
    new_password = data.get("password")

    user = session.query(User).filter_by(id=user_id).first()

    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if new_username:
        user.username = new_username
    if new_password:
        user.password = new_password

    session.commit()
    return jsonify({"message": "User updated successfully"}), 200

#delete user
@app.delete('/api/users/<user_id>')
def delete_user(user_id):
    user = session.query(User).filter_by(id=user_id).first()

    if not user:
        return jsonify({"message": "User not found"}), 404
    
    session.delete(user)
    session.commit()

    return jsonify({"Message": "User deleted successfully"}), 200
    
#expense routes
@app.post('/api/expenses')
def add_expense():
    data = request.get_json()
    title = data.get("title")
    description = data.get("description")
    amount = data.get("amount")
    category =data.get("category")
    user_id = data.get("user_id")

#validate category
    allowed_categories = {"Food", "Education", "Entertainment"}#set, not allowed duplicates

    if category not in allowed_categories:
        return jsonify({"error": f"Invalid Category{category}"}), 400
    
    new_expense = Expense(title=title, description=description, amount=amount, category=category, user_id=user_id)
    session.add(new_expense)
    session.commit()

    return jsonify({"message": "Expense added successfully"}), 201


@app.get("/api/expenses/<expense_id>")
def get_expense(expense_id):
    expense = session.query(Expense).filter_by(id=expense_id).first()

    if not expense :
        return jsonify({"error": "Expense not found"}), 404
    
    expense_data = {
        "id": expense.id,
        "title": expense.title,
        "description": expense.description,
        "amount": float(expense.amount) if expense.amount is not None else None,
        "category": expense.category
    }

    return jsonify(expense_data), 200
    #user_data = {id=id, }
    #return jsonify(user_data), 200



@app.put("/api/expenses/<expense_id>")
def update_expense(expense_id):
    expense = session.query(Expense).filter_by(id=expense_id).first()
    
    if not expense:
        return jsonify({"error": "Expense not found"}), 404
    
    data = request.get_json()

    if "title" in data:
        expense.title = data["title"]
    if "description" in data:
        expense.description = data["description"]
    if "amount" in data:
        expense.amount = data["amount"]
    if "category" in data:
        allowed_categories = ["Food", "Education", "Entertainment"]
        if data["category"] not in allowed_categories:
            return jsonify({"error": "Invalid category"}), 400
        expense.category = data["category"]
    
    session.commit()

    return jsonify({"message": "Expense updated successfully"}), 200

@app.delete("/api/expenses/<expense_id>")
def delete_expense(expense_id):
    expense = session.query(Expense).filter_by(id=expense_id).first()

    if not expense:
        return jsonify({"error": "Expense not found"}), 404
    
    session.delete(expense)
    session.commit()

    return jsonify({"message": "Expense deleted successfully"}), 200


#frontend endpoints
@app.get("/")
@app.get("/home")
@app.get("/index")
def home():
    return render_template("home.html")


@app.get("/about")
def about():
    my_student = {"name": "Britney", "cohort": 59, "year": 2025}
    return render_template("about.html", student=my_student)


@app.get("/students")
def students_list():
    students = [
        {
            "name": "John Ramos",
            "age": 33,
            "cohort": "59",
            "color": "RGB(206, 0, 0)",
            "year": "2025",
            "program": "Full Stack",
        },
        {
            "name": "Courtney Phillips",
            "age": 26,
            "cohort": "59",
            "color": "RGB(8, 150, 55)",
            "year": "2025",
            "program": "Full Stack"
        },
        {
            "name": "Tara Shnider",
            "age": 37,
            "cohort": "59",
            "color": "RGB(28, 8, 209)",
            "year": "2025",
            "program": "Mobile App Development/IOS"
        },
        {
            "name": "Oma Bounds",
            "age": 59,
            "cohort": "59",
            "color": "RGB(255, 0, 221)",
            "year": "2025",
            "program": "Mobile App Development/Android"
        },
    ]

    return render_template("students-list.html", students=students)


# Ensures the server runs only when this script is executed
if __name__ == "__main__":
    app.run(debug=True)

