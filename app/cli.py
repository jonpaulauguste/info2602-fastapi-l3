import typer
from app.database import create_db_and_tables, get_session, drop_all
from app.models import Category, User, Todo
from fastapi import Depends
from sqlmodel import select
from sqlalchemy.exc import IntegrityError

cli = typer.Typer()

@cli.command(help="Initialize the database by creating tables and adding a sample user and todo.")
def initialize():
    with get_session() as db: # Get a connection to the database
        drop_all() # delete all tables
        create_db_and_tables() #recreate all tables
        
        bob = User(username='bob', email='bob@mail.com') # Create a new user (in memory)
        bob.set_password("bobpass")

        db.add(bob) # Tell the database about this new data
        db.commit() # Tell the database persist the data
        db.refresh(bob) # Update the user (we use this to get the ID from the db)

        new_todo = Todo(text='Wash dishes', user_id=bob.id)

        db.add(new_todo) # Tell the database about this new data
        db.commit() # Tell the database persist the data
        db.refresh(new_todo) # Update the user (we use this to get the ID from the db)

        print("Database Initialized")

@cli.command(help="Add a task for a given user.")
def add_task(username:str, task:str):
    # Task 4.1 code here. Remove the line with "pass" below once completed
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).one_or_none()
        if not user:
            print("User doesn't exist")
            return
        user.todos.append(Todo(text=task))
        db.add(user)
        db.commit()
        print("Task added for user")

@cli.command(help="Toggle the done state of a todo for a given user.")
def toggle_todo(todo_id:int, username:str):
    # Task 4.2 code here. Remove the line with "pass" below once completed
    with get_session() as db:
        todo = db.exec(select(Todo).where(Todo.id == todo_id)).one_or_none()
        if not todo:
            print("This todo doesn't exist")
            return
        if todo.user.username != username:
            print(f"This todo doesn't belong to {username}")
            return

        todo.toggle()
        db.add(todo)
        db.commit()

        print(f"Todo item's done state set to {todo.done}")


@cli.command(help="List all categories for a given todo.")
def list_todo_categories(todo_id:int, username:str):
    # Task 5.3 code here. Remove the line with "pass" below once completed
    with get_session() as db: # Get a connection to the database
        todo = db.exec(select(Todo).where(Todo.id == todo_id)).one_or_none()
        if not todo:
            print("Todo doesn't exist")
        elif not todo.user.username == username:
            print("Todo doesn't belong to that user")
        else:
            print(f"Categories: {todo.categories}")
    pass

@cli.command(help="Create a new category for a given user.")
def create_category(username:str, cat_text:str):        
    # Task 5.4 code here. Remove the line with "pass" below once completed
    with get_session() as db: # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).one_or_none()
        if not user:
            print("User doesn't exist")
            return

        category = db.exec(select(Category).where(Category.text== cat_text, Category.user_id == user.id)).one_or_none()
        if category:
            print("Category exists! Skipping creation")
            return
        
        category = Category(text=cat_text, user_id=user.id)
        db.add(category)
        db.commit()

        print("Category added for user")
    pass

@cli.command(help="List all categories for a given username.")
def list_user_categories(username:str):
    # Task 5.5 code here. Remove the line with "pass" below once completed
     with get_session() as db: # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).one_or_none()
        if not user:
            print("User doesn't exist")
            return
        categories = db.exec(select(Category).where(Category.user_id == user.id)).all()
        print([category.text for category in categories])
    # pass

@cli.command(help="Assign a category to a todo. If the category doesn't exist, it will be created.")
def assign_category_to_todo(username:str, todo_id:int, category_text:str):
    # Task 5.6 code here. Remove the line with "pass" below once completed
    with get_session() as db: # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).one_or_none()
        if not user:
            print("User doesn't exist")
            return
        
        category = db.exec(select(Category).where(Category.text == category_text, Category.user_id==user.id)).one_or_none()
        if not category:
            category = Category(text=category_text, user_id=user.id)
            db.add(category)
            db.commit()
            print("Category didn't exist for user, creating it")
        
        todo = db.exec(select(Todo).where(Todo.id == todo_id, Todo.user_id==user.id)).one_or_none()
        if not todo:
            print("Todo doesn't exist for user")
            return
        
        todo.categories.append(category)
        db.add(todo)
        db.commit()
        print("Added category to todo")

@cli.command(help="List all todos with ID, text, username, and done status.")
def list_todos():
    with get_session() as db:
        todos = db.exec(select(Todo)).all()

        if not todos:
            print("No todos found.")
            return

        for todo in todos:
            username = todo.user.username if todo.user else "Unknown"
            print(f"ID={todo.id} | text='{todo.text}' | user={username} | done={todo.done}")


@cli.command(help="Delete a todo by its ID.")
def delete_todo(todo_id: int = typer.Argument(..., help="The ID of the todo to delete.")):
    with get_session() as db:
        todo = db.exec(select(Todo).where(Todo.id == todo_id)).one_or_none()

        if not todo:
            print("Todo doesn't exist")
            return

        db.delete(todo)
        db.commit()
        print(f"Deleted todo {todo_id}")


@cli.command(help="Mark all todos for a given username as complete.")
def complete_user_todos(
    username: str = typer.Argument(..., help="Username whose todos should be marked complete.")
):
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).one_or_none()
        if not user:
            print("User doesn't exist")
            return

        todos = db.exec(select(Todo).where(Todo.user_id == user.id)).all()
        if not todos:
            print(f"No todos found for {username}")
            return

        for todo in todos:
            todo.done = True
            db.add(todo)

        db.commit()
        print(f"Marked {len(todos)} todos as complete for {username}")


if __name__ == "__main__":
    cli()
