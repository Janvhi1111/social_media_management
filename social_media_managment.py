import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

# Create and connect to SQLite database
conn = sqlite3.connect('social_media_management.db')
cursor = conn.cursor()

# Create tables for Social Media Management System
def create_tables():
    # User table
    cursor.execute('''CREATE TABLE IF NOT EXISTS User (
                        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        first_name TEXT NOT NULL,
                        last_name TEXT NOT NULL,
                        email TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL,
                        role TEXT NOT NULL
                   )''')
    
    # Post table
    cursor.execute('''CREATE TABLE IF NOT EXISTS Post (
                        post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        post_content TEXT NOT NULL,
                        created_date TEXT NOT NULL,
                        updated_date TEXT,
                        FOREIGN KEY(user_id) REFERENCES User(user_id)
                   )''')
    
    # Comment table (weak entity of Post)
    cursor.execute('''CREATE TABLE IF NOT EXISTS Comment (
                        comment_id INTEGER NOT NULL,
                        post_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        comment_content TEXT NOT NULL,
                        comment_date TEXT NOT NULL,
                        FOREIGN KEY(post_id) REFERENCES Post(post_id) ON DELETE CASCADE,
                        FOREIGN KEY(user_id) REFERENCES User(user_id)
                   )''')
    
    # Like table
    cursor.execute('''CREATE TABLE IF NOT EXISTS Likes (
                        like_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        post_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        like_date TEXT NOT NULL,
                        FOREIGN KEY(post_id) REFERENCES Post(post_id),
                        FOREIGN KEY(user_id) REFERENCES User(user_id)
                   )''')

    # Follower relationship table
    cursor.execute('''CREATE TABLE IF NOT EXISTS Follower (
                        follower_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        follower_user_id INTEGER NOT NULL,
                        follow_date TEXT NOT NULL,
                        FOREIGN KEY(user_id) REFERENCES User(user_id),
                        FOREIGN KEY(follower_user_id) REFERENCES User(user_id)
                   )''')

    # Commit table creations
    conn.commit()

    # Triggers
    # Trigger to update the updated_date in Post table
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_post_timestamp
        AFTER UPDATE ON Post
        BEGIN
            UPDATE Post SET updated_date = CURRENT_TIMESTAMP WHERE post_id = NEW.post_id;
        END;
    ''')

    # Trigger to prevent a user from liking the same post multiple times
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS prevent_duplicate_like
        BEFORE INSERT ON Likes
        FOR EACH ROW
        BEGIN
            SELECT CASE
                WHEN (SELECT COUNT(*) FROM Likes WHERE post_id = NEW.post_id AND user_id = NEW.user_id) > 0
                THEN RAISE(ABORT, 'User has already liked this post.')
            END;
        END;
    ''')

    # Trigger to log activity when a user follows another user (you can modify this for actual logging)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS FollowLog (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            follower_user_id INTEGER NOT NULL,
            follow_date TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES User(user_id),
            FOREIGN KEY(follower_user_id) REFERENCES User(user_id)
        )
    ''')

    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS log_follow_activity
        AFTER INSERT ON Follower
        BEGIN
            INSERT INTO FollowLog (user_id, follower_user_id, follow_date)
            VALUES (NEW.user_id, NEW.follower_user_id, NEW.follow_date);
        END;
    ''')

    conn.commit()

# Function to register a user
def register_user(first_name, last_name, email, password, role):
    try:
        cursor.execute('''INSERT INTO User (first_name, last_name, email, password, role)
                          VALUES (?, ?, ?, ?, ?)''', (first_name, last_name, email, password, role))
        conn.commit()
        return True, "User registered successfully!"
    except sqlite3.IntegrityError as e:
        return False, str(e)

# Function to update user information
def update_user(user_id, first_name, last_name, email, password):
    cursor.execute('''UPDATE User SET first_name = ?, last_name = ?, email = ?, password = ?
                      WHERE user_id = ?''', (first_name, last_name, email, password, user_id))
    conn.commit()

# Function to update post information
def update_post(post_id, post_content):
    cursor.execute('''UPDATE Post SET post_content = ? WHERE post_id = ?''', (post_content, post_id))
    conn.commit()

# Function to update comment information
def update_comment(comment_id, comment_content):
    cursor.execute('''UPDATE Comment SET comment_content = ? WHERE comment_id = ?''', (comment_content, comment_id))
    conn.commit()

# Function to add a post
def add_post(user_id, post_content, created_date):
    cursor.execute('SELECT user_id FROM User WHERE user_id = ?', (user_id,))
    if not cursor.fetchone():
        return False, "User does not exist."
    cursor.execute('''INSERT INTO Post (user_id, post_content, created_date)
                      VALUES (?, ?, ?)''', (user_id, post_content, created_date))
    conn.commit()
    return True, "Post added successfully."

# Function to add a comment
def add_comment(post_id, user_id, comment_content, comment_date):
    cursor.execute('SELECT post_id FROM Post WHERE post_id = ?', (post_id,))
    if not cursor.fetchone():
        return False, "Post does not exist."
    cursor.execute('''INSERT INTO Comment (post_id, user_id, comment_content, comment_date)
                      VALUES (?, ?, ?, ?)''', (post_id, user_id, comment_content, comment_date))
    conn.commit()
    return True, "Comment added successfully."

# Function to like a post
def add_like(post_id, user_id, like_date):
    cursor.execute('SELECT post_id FROM Post WHERE post_id = ?', (post_id,))
    if not cursor.fetchone():
        return False, "Post does not exist."
    cursor.execute('''INSERT INTO Likes (post_id, user_id, like_date)
                      VALUES (?, ?, ?)''', (post_id, user_id, like_date))
    conn.commit()
    return True, "Post liked successfully."

# Function to follow a user
def follow_user(user_id, follower_user_id, follow_date):
    cursor.execute('SELECT user_id FROM User WHERE user_id = ?', (user_id,))
    if not cursor.fetchone():
        return False, "User does not exist."
    cursor.execute('SELECT user_id FROM User WHERE user_id = ?', (follower_user_id,))
    if not cursor.fetchone():
        return False, "Follower does not exist."
    cursor.execute('''INSERT INTO Follower (user_id, follower_user_id, follow_date)
                      VALUES (?, ?, ?)''', (user_id, follower_user_id, follow_date))
    conn.commit()
    return True, "User followed successfully."

# Function to display all data in a tabular format
def display_tables():
    tables = {
        "User": cursor.execute("SELECT * FROM User").fetchall(),
        "Post": cursor.execute("SELECT * FROM Post").fetchall(),
        "Comment": cursor.execute("SELECT * FROM Comment").fetchall(),
        "Likes": cursor.execute("SELECT * FROM Likes").fetchall(),
        "Follower": cursor.execute("SELECT * FROM Follower").fetchall(),
        "FollowLog": cursor.execute("SELECT * FROM FollowLog").fetchall()
    }
    columns = {
        "User": get_columns("User"),
        "Post": get_columns("Post"),
        "Comment": get_columns("Comment"),
        "Likes": get_columns("Likes"),
        "Follower": get_columns("Follower"),
        "FollowLog": get_columns("FollowLog")
    }

    return tables, columns

def display_table_2():
    cursor.execute('''
        CREATE VIEW IF NOT EXISTS UserLikes AS
        SELECT 
            User.user_id, 
            User.first_name, 
            User.last_name, 
            User.email, 
            Likes.like_id, 
            Likes.post_id, 
            Likes.like_date
        FROM 
            User 
        JOIN 
            Likes ON User.user_id = Likes.user_id
    ''')
    conn.commit()

    try:
        # Fetch the data from the UserLikes view
        cursor.execute('SELECT * FROM UserLikes')
        rows = cursor.fetchall()

        # Get column names for the view
        columns = get_columns("UserLikes")

        # Display the results in a Streamlit dataframe
        st.subheader("User Likes")
        df = pd.DataFrame(rows, columns=columns)
        st.dataframe(df)

    except sqlite3.Error as e:
        st.error(f"Error fetching data from UserLikes view: {str(e)}")

    
    # Function to update post information
def update_post(post_id, post_content):
    try:
        cursor.execute('''UPDATE Post SET post_content = ? WHERE post_id = ?''', (post_content, post_id))
        conn.commit()
        return True, "Post updated successfully."
    except Exception as e:
        return False, str(e)

# Function to update comment information
def update_comment(comment_id, comment_content):
    try:
        cursor.execute('''UPDATE Comment SET comment_content = ? WHERE comment_id = ?''', (comment_content, comment_id))
        conn.commit()
        return True, "Comment updated successfully."
    except Exception as e:
        return False, str(e)
    
    # Function to delete a record from a specified table
def delete_record(table_name, record_id):
    id_column_map = {
        "User": "user_id",
        "Post": "post_id",
        "Comment": "comment_id",
        "Likes": "like_id",
        "Follower": "follower_id"
    }

    id_column = id_column_map.get(table_name)
    
    if id_column:
        try:
            cursor.execute(f"DELETE FROM {table_name} WHERE {id_column} = ?", (record_id,))
            conn.commit()
            return True, f"Record with ID {record_id} deleted from {table_name}."
        except Exception as e:
            return False, str(e)
    else:
        return False, "Invalid table name."

    
    # Fetch the data from the view
    cursor.execute('SELECT * FROM UserLikes')
    rows = cursor.fetchall()

    # Get column names
    columns = get_columns("UserLikes")
    
     # Display the results in a Streamlit dataframe
    st.subheader("User Likes")
    df = pd.DataFrame(rows, columns=columns)
    st.dataframe(df)

# Function to get table columns
# Function to get table columns
def get_columns(table_name):
    return [description[1] for description in cursor.execute(f"PRAGMA table_info({table_name})").fetchall()]


# Call create_tables function to initialize the database
create_tables()

# Streamlit UI Code
st.title("Social Media Management System")

# Register a new user
st.header("Register User")
first_name = st.text_input("First Name")
last_name = st.text_input("Last Name")
email = st.text_input("Email")
password = st.text_input("Password", type="password")
role = st.selectbox("Role", ["User", "Admin"])

if st.button("Register"):
    success, message = register_user(first_name, last_name, email, password, role)
    st.success(message)

# Manage Records Section
manage_action = st.selectbox("Manage Records", ["", "Add Records", "Update Records", "Delete Records"])

if manage_action == "Add Records":
    st.header("Add Records")
    action = st.selectbox("Select Record Type", ["Post", "Comment", "Like", "Follow"])

    if action == "Post":
        user_id = st.number_input("User ID", min_value=1)
        post_content = st.text_area("Post Content")
        created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if st.button("Add Post"):
            success, message = add_post(user_id, post_content, created_date)
            st.success(message)

    elif action == "Comment":
        post_id = st.number_input("Post ID", min_value=1)
        user_id = st.number_input("User ID", min_value=1)
        comment_content = st.text_area("Comment Content")
        comment_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if st.button("Add Comment"):
            success, message = add_comment(post_id, user_id, comment_content, comment_date)
            st.success(message)

    elif action == "Like":
        post_id = st.number_input("Post ID", min_value=1)
        user_id = st.number_input("User ID", min_value=1)
        like_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if st.button("Like Post"):
            success, message = add_like(post_id, user_id, like_date)
            st.success(message)

    elif action == "Follow":
        user_id = st.number_input("User ID", min_value=1)
        follower_user_id = st.number_input("Follower User ID", min_value=1)
        follow_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if st.button("Follow User"):
            success, message = follow_user(user_id, follower_user_id, follow_date)
            st.success(message)

# For updating posts
if manage_action == "Update Records":
    st.header("Update Records")
    action = st.selectbox("Select Record Type to Update", ["Post", "Comment"])

    if action == "Post":
        post_id = st.number_input("Post ID", min_value=1)
        post_content = st.text_area("New Post Content")
        if st.button("Update Post"):
            success, message = update_post(post_id, post_content)
            if success:
                st.success(message)
            else:
                st.error(message)

    elif action == "Comment":
        comment_id = st.number_input("Comment ID", min_value=1)
        comment_content = st.text_area("New Comment Content")
        if st.button("Update Comment"):
            success, message = update_comment(comment_id, comment_content)
            if success:
                st.success(message)
            else:
                st.error(message)

# For deleting records
elif manage_action == "Delete Records":
    st.header("Delete Records")

    table_name_to_delete = st.selectbox("Select Table to Delete From", ["User", "Post", "Comment", "Likes", "Follower"])
    record_id_to_delete = st.text_input(f"Enter {table_name_to_delete} ID to delete")

    if st.button(f"Delete from {table_name_to_delete}"):
        if record_id_to_delete:
            success, message = delete_record(table_name_to_delete, int(record_id_to_delete))
            if success:
                st.success(message)
            else:
                st.error(message)
        else:
            st.error("Please enter a valid ID to delete.")

# Display all tables
st.header("Display All Data")
tables, columns = display_tables()
for table in tables.keys():
    st.subheader(table)
    df = pd.DataFrame(tables[table], columns=columns[table])
    st.dataframe(df)
    
if st.button("Show User Likes"):
    display_table_2()


# Close the database connection
conn.close()     