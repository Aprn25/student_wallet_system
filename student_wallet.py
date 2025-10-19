import mysql.connector
from datetime import datetime

# ---------- DATABASE CONNECTION ----------
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",        
        password="root",  
        database="student_wallet"
    )

# ---------- SIGNUP ----------
def signup():
    print("\n----- Student Signup -----\n")
    name = input("Enter your name: ")
    email = input("Enter your email: ")
    password = input("Set your password: ")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE email=%s", (email,))
    if cursor.fetchone():
        print("Email already registered! Try logging in.\n")
        conn.close()
        return

    cursor.execute(
        "INSERT INTO students (name, email, password, balance) VALUES (%s, %s, %s, %s)",
        (name, email, password, 0.00)
    )
    conn.commit()
    conn.close()
    print("Signup successful! You can now log in.\n")

# ---------- LOGIN ----------
def login():
    print("\n----- Student Login -----\n")
    email = input("Enter your email: ")
    password = input("Enter your password: ")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM students WHERE email=%s AND password=%s"
    cursor.execute(query, (email, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        print(f"\nWelcome, {user['name']}!")
        wallet_menu(user)
    else:
        print("Invalid credentials.\n")

# ---------- WALLET MENU ----------
def wallet_menu(user):
    while True:
        print("\n----- Student Wallet Menu -----\n")
        print("1. Check Balance")
        print("2. Deposit Money")
        print("3. Withdraw Money")
        print("4. View Transaction History")
        print("5. View Account Details")
        print("6. Change Password")
        print("7. Transfer Money")
        print("8. Logout")

        choice = input("Enter choice: ")

        if choice == '1':
            check_balance(user)
        elif choice == '2':
            deposit_money(user)
        elif choice == '3':
            withdraw_money(user)
        elif choice == '4':
            view_transactions(user)
        elif choice == '5':
            view_account_details(user)
        elif choice == '6':
            change_password(user)
        elif choice == '7':
            transfer_money(user)
        elif choice == '8':
            print("Logging out...\n")
            break
        else:
            print("Invalid choice. Try again.")

# ---------- CHECK BALANCE ----------
def check_balance(user):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM students WHERE student_id=%s", (user['student_id'],))
    balance = cursor.fetchone()[0]
    conn.close()
    print(f"Your current balance: ₹{balance:.2f}")

# ---------- DEPOSIT ----------
def deposit_money(user):
    try:
        amount = float(input("Enter amount to deposit: "))
    except ValueError:
        print("Invalid input.")
        return

    if amount <= 0:
        print("Amount must be positive.")
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET balance = balance + %s WHERE student_id=%s", (amount, user['student_id']))
    cursor.execute("INSERT INTO transactions (student_id, type, amount) VALUES (%s, %s, %s)", (user['student_id'], 'Deposit', amount))
    conn.commit()
    conn.close()
    print(f"₹{amount:.2f} deposited successfully.")

# ---------- WITHDRAW ----------
def withdraw_money(user):
    try:
        amount = float(input("Enter amount to withdraw: "))
    except ValueError:
        print("Invalid input.")
        return

    if amount <= 0:
        print("Amount must be positive.")
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM students WHERE student_id=%s", (user['student_id'],))
    balance = cursor.fetchone()[0]

    if amount > balance:
        print("Insufficient balance.")
    else:
        cursor.execute("UPDATE students SET balance = balance - %s WHERE student_id=%s", (amount, user['student_id']))
        cursor.execute("INSERT INTO transactions (student_id, type, amount) VALUES (%s, %s, %s)", (user['student_id'], 'Withdraw', amount))
        conn.commit()
        print(f"₹{amount:.2f} withdrawn successfully.")
    conn.close()

# ---------- VIEW TRANSACTION HISTORY ----------
def view_transactions(user):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT type, amount, txn_time FROM transactions WHERE student_id=%s ORDER BY txn_time DESC", (user['student_id'],))
    transactions = cursor.fetchall()
    conn.close()

    if not transactions:
        print("No transactions yet.")
        return

    max_op_len = max(len(txn['type']) for txn in transactions)
    col_width = max(30, max_op_len)  # at least 30 chars

    print("\n----- Transaction History -----")
    print(f"{'DATE and TIME':<20} | {'OPERATION':<{col_width}} | {'AMOUNT':<10}")
    print("-" * (35 + col_width))

    for txn in transactions:
        date_time = str(txn['txn_time'])
        operation = txn['type']
        amount = f"₹{txn['amount']:.2f}"
        print(f"{date_time:<20} | {operation:<{col_width}} | {amount:<10}")


# ---------- VIEW ACCOUNT DETAILS ----------
def view_account_details(user):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT student_id, name, email, balance FROM students WHERE student_id=%s", (user['student_id'],))
    data = cursor.fetchone()
    conn.close()

    print("\n----- Account Details -----\n")
    print(f"Student ID : {data['student_id']}")
    print(f"Name       : {data['name']}")
    print(f"Email      : {data['email']}")
    print(f"Balance    : ₹{data['balance']:.2f}")

# ---------- CHANGE PASSWORD ----------
def change_password(user):
    old_pwd = input("Enter your current password: ")
    new_pwd = input("Enter your new password: ")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM students WHERE student_id=%s", (user['student_id'],))
    current_pwd = cursor.fetchone()[0]

    if old_pwd != current_pwd:
        print("Incorrect current password.")
        conn.close()
        return

    cursor.execute("UPDATE students SET password=%s WHERE student_id=%s", (new_pwd, user['student_id']))
    conn.commit()
    conn.close()
    print("Password changed successfully.")

# ---------- TRANSFER MONEY ----------
def transfer_money(user):
    recipient_email = input("Enter recipient's email: ")
    try:
        amount = float(input("Enter amount to transfer: "))
    except ValueError:
        print("Invalid amount.")
        return

    if amount <= 0:
        print("Amount must be positive.")
        return

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Get sender balance
    cursor.execute("SELECT balance FROM students WHERE student_id=%s", (user['student_id'],))
    sender_balance = cursor.fetchone()['balance']

    if amount > sender_balance:
        print("Insufficient balance.")
        conn.close()
        return

    # Get recipient info
    cursor.execute("SELECT * FROM students WHERE email=%s", (recipient_email,))
    recipient = cursor.fetchone()
    if not recipient:
        print("Recipient not found.")
        conn.close()
        return

    # Deduct from sender
    cursor.execute("UPDATE students SET balance = balance - %s WHERE student_id=%s", (amount, user['student_id']))
    # Add to recipient
    cursor.execute("UPDATE students SET balance = balance + %s WHERE student_id=%s", (amount, recipient['student_id'],))

    # Log transaction for sender
    cursor.execute("INSERT INTO transactions (student_id, type, amount) VALUES (%s, %s, %s)", 
                   (user['student_id'], f'Transfer to {recipient_email}', amount))
    # Log transaction for recipient
    cursor.execute("INSERT INTO transactions (student_id, type, amount) VALUES (%s, %s, %s)", 
                   (recipient['student_id'], f'Transfer from {user["email"]}', amount))

    conn.commit()
    conn.close()

    print(f"₹{amount:.2f} transferred successfully to {recipient['name']} ({recipient_email}).")

# ---------- MAIN MENU ----------
def main_menu():
    while True:
        print("\n===== STUDENT WALLET SYSTEM =====\n")
        print("1. Login")
        print("2. Signup")
        print("3. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            login()
        elif choice == '2':
            signup()
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Try again.")

# ---------- MAIN ----------
if __name__ == "__main__":
    main_menu()
