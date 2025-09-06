from flask import Flask, jsonify, request
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



# Ensures the server runs only when this script is executed
if __name__ == "__main__":
    app.run(debug=True)

