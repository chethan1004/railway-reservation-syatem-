import streamlit as st
import sqlite3
import pandas as pd

# Connect to SQLite database
conn = sqlite3.connect('railway.db')
c = conn.cursor()

# Create tables if they don't exist
def create_db():
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS employees (employee_id TEXT, password TEXT, designation TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS trains (train_number TEXT, train_name TEXT, start_destination TEXT, end_destination TEXT, departure_date TEXT)")


# Helper functions
def search_train(train_number):
    train_query = c.execute("SELECT * FROM trains WHERE train_number = ?", (train_number,))
    return train_query.fetchone()

def train_destination(start_destination, end_destination):
    train_query = c.execute("SELECT * FROM trains WHERE start_destination = ? AND end_destination = ?", (start_destination, end_destination))
    return train_query.fetchall()

def add_train(train_number, train_name, departure_date, start_destination, end_destination):
    c.execute("INSERT INTO trains (train_number, train_name, departure_date, start_destination, end_destination) VALUES (?, ?, ?, ?, ?)",
              (train_number, train_name, departure_date, start_destination, end_destination))
    conn.commit()

def create_seat_table(train_number):
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS seat_{train_number} (
            seat_number INTEGER PRIMARY KEY,
            seat_type TEXT,
            booked INTEGER,
            passenger_name TEXT,
            passenger_age INTEGER,
            passenger_gender TEXT
        )
    """)
    for i in range(1, 51):
        seat_type = categorize_seat(i)
        c.execute(f"INSERT INTO seat_{train_number} (seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender) VALUES (?, ?, ?, ?, ?, ?)",
                  (i, seat_type, 0, '', None, ''))
    conn.commit()

def categorize_seat(seat_number):
    if seat_number % 10 in [0, 4, 5, 9]:
        return "window"
    elif seat_number % 10 in [2, 3, 6, 7]:
        return "aisle"
    else:
        return "middle"

def view_seats(train_number):
    seat_query = c.execute(f"SELECT * FROM seat_{train_number} ORDER BY seat_number ASC")
    return seat_query.fetchall()

def book_ticket(train_number, passenger_name, passenger_age, passenger_gender, seat_type):
    seat_query = c.execute(f"SELECT seat_number FROM seat_{train_number} WHERE booked = 0 AND seat_type = ? ORDER BY seat_number ASC", (seat_type,))
    seat = seat_query.fetchone()
    if seat:
        c.execute(f"UPDATE seat_{train_number} SET booked = 1, passenger_name = ?, passenger_age = ?, passenger_gender = ? WHERE seat_number = ?", 
                  (passenger_name, passenger_age, passenger_gender, seat[0]))
        conn.commit()
        st.success(f"Ticket booked successfully! Seat Number: {seat[0]}")
    else:
        st.error("No available seats of the selected type.")

def cancel_ticket(train_number, seat_number):
    c.execute(f"UPDATE seat_{train_number} SET booked = 0, passenger_name = '', passenger_age = NULL, passenger_gender = '' WHERE seat_number = ?", (seat_number,))
    conn.commit()
    st.success("Ticket cancelled successfully.")

def delete_train(train_number):
    c.execute(f"DROP TABLE IF EXISTS seat_{train_number}")
    c.execute("DELETE FROM trains WHERE train_number = ?", (train_number,))
    conn.commit()
    st.success("Train deleted successfully.")

# Streamlit App
def train_functions():
    st.title("Chethan Train Company")
    functions = st.sidebar.selectbox("Select Train Function", ["Add Train", "View Trains", "Search Train", "Delete Train", "Book Ticket", "Cancel Ticket", "View Seats"])

    if functions == "Add Train":
        st.header("Add New Train")
        with st.form(key='add_train_form'):
            train_number = st.text_input("Train Number")
            train_name = st.text_input("Train Name")
            departure_date = st.date_input("Departure Date")
            start_destination = st.text_input("Start Destination")
            end_destination = st.text_input("End Destination")
            submitted = st.form_submit_button("Add Train")
        if submitted:
            add_train(train_number, train_name, departure_date, start_destination, end_destination)
            create_seat_table(train_number)
            st.success("Train added successfully.")

    elif functions == "View Trains":
        st.header("View All Trains")
        train_query = c.execute("SELECT * FROM trains")
        trains = train_query.fetchall()
        df = pd.DataFrame(trains, columns=["Train Number", "Train Name", "Start Destination", "End Destination", "Departure Date"])
        st.dataframe(df)

    elif functions == "Search Train":
        st.header("Search Train")
        train_number = st.text_input("Enter Train Number")
        if st.button("Search"):
            train = search_train(train_number)
            if train:
                st.write(f"Train Details: {train}")
            else:
                st.error("Train not found.")

    elif functions == "Delete Train":
        st.header("Delete Train")
        train_number = st.text_input("Enter Train Number")
        if st.button("Delete"):
            delete_train(train_number)

    elif functions == "Book Ticket":
        st.header("Book Ticket")
        train_number = st.text_input("Enter Train Number")
        passenger_name = st.text_input("Passenger Name")
        passenger_age = st.number_input("Passenger Age", min_value=1)
        passenger_gender = st.selectbox("Passenger Gender", ["Male", "Female", "Other"])
        seat_type = st.selectbox("Seat Type", ["aisle", "middle", "window"])
        if st.button("Book Ticket"):
            book_ticket(train_number, passenger_name, passenger_age, passenger_gender, seat_type)

    elif functions == "Cancel Ticket":
        st.header("Cancel Ticket")
        train_number = st.text_input("Enter Train Number")
        seat_number = st.number_input("Enter Seat Number", min_value=1)
        if st.button("Cancel Ticket"):
            cancel_ticket(train_number, seat_number)

    elif functions == "View Seats":
        st.header("View Seats")
        train_number = st.text_input("Enter Train Number")
        if st.button("View Seats"):
            seats = view_seats(train_number)
            if seats:
                df = pd.DataFrame(seats, columns=["Seat Number", "Seat Type", "Booked", "Passenger Name", "Passenger Age", "Passenger Gender"])
                st.dataframe(df)
            else:
                st.error("No seats found or train does not exist.")

# Main Execution
if __name__ == "__main__":
    create_db()
    train_functions()
