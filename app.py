from flask import Flask, flash, redirect, render_template, request, session, abort
import os
import psycopg2

app = Flask(__name__)

DATABASE = {
    'dbname': '',
    'user': '',
    'password': '',
    'host': '',
    'port': ''
}

# Function to create a new database connection
def get_db_connection():
    conn = psycopg2.connect(
        dbname=DATABASE['dbname'],
        user=DATABASE['user'],
        password=DATABASE['password'],
        host=DATABASE['host'],
        port=DATABASE['port']
    )
    return conn


@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    password=request.form['password']
    username=request.form['username']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("select user_id, password from Users where user_name=%s", (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if not result:
        flash("User not found")
    elif result[1]==password:
        session['userid']=result[0]
        return redirect('/profile')
    else:
        flash('wrong password!')
        
    return home()

@app.route("/logout")
def logout():
    # session['logged_in'] = False
    return home()

@app.route("/create_account", methods=['GET', 'POST'])
def create_account():
    # print(request.method)
    if request.method == 'POST':
        # Get the form data
        phone = request.form['phone']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm-password']
        try:
            if password != confirm_password:
                flash('Passwords do not match!')
                return render_template('create_account.html')
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Users (user_name, email, phone_number, password) VALUES (%s, %s, %s, %s)", (username, email,phone,password))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Account created successfully! You can now log in.')
            return redirect('/')
        except:
            flash('Username already exists!')
            return render_template('create_account.html')
    return render_template('create_account.html')

@app.route("/profile")
def transactions():
    userid=session['userid']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("select A.name, trx_date,amount,C.category_name,trx_type\
                    from (select * from Transaction where user_id= %s) as T \
                    join (select * from Account where user_id= %s) as A\
                    on A.account_id=T.account_id\
                    join Category as C on C.category_id=T.category_id", (userid,userid))
    trans = cursor.fetchall()
    trxs=[]
    for row in trans:
        account, date, amount, category, type = row  # Unpack each tuple
        trxs.append({'account':account,'date':date,'amount':amount,'category':category,'type':type})
    
    
    cursor.execute("select name, balance from Account where user_id= %s", (userid,))
    accounts = cursor.fetchall()
    accs=[]
    for row in accounts:
        account,balance=row
        accs.append({'account':account,'balance':balance})
    cursor.close()
    conn.close()
    return render_template('transaction.html',trxs=trxs,accs=accs)

@app.route('/add_trx',methods=['GET', 'POST'])
def add_trx():
    userid=session['userid']
    if request.method == 'POST':
        try:
            date=request.form['date']
            category=request.form['category']
            amount=request.form['amount']
            type=request.form['type']
            account=request.form['account']
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("select account_id from Account where name=%s and user_id=%s",(account, userid))
            accountid=cursor.fetchone()[0]
            cursor.execute("select category_id from Category where category_name=%s",(category,))
            categoryid=cursor.fetchone()[0]
            cursor.execute("INSERT INTO Transaction (user_id, account_id, trx_date, amount, category_id, trx_type) VALUES (%s, %s, %s, %s, %s, %s)", (userid, accountid,date,amount,categoryid,type))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect('/profile')
        except:
            flash('Please fill all blanks!')
            return redirect('/add_trx')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("select name from Account where user_id= %s", (userid,))
    accounts = cursor.fetchall()
    cursor.execute("select category_name from Category")
    categories = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('add_trx.html',accounts=accounts,categories=categories)

@app.route('/add_acc')
def add_account():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("select bank_name from Bank")
    result=cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('add_acc.html',banks=result)



@app.route('/add_normal',methods=['POST'])
def add_normal():
    userid=session['userid']
    bank=request.form['bank']
    name=request.form['name']
    balance=request.form['balance']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("select bank_id from Bank where bank_name= %s", (bank,))
    bankid = cursor.fetchall()[0]
    cursor.execute("INSERT INTO Account (user_id, bank_id, name, balance) VALUES (%s, %s, %s, %s)", (userid, bankid,name,balance))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/profile')


@app.route('/add_credit',methods=['POST'])
def add_credit():
    userid=session['userid']
    bank=request.form['bank']
    name=request.form['name']
    balance=request.form['balance']
    settlement_day=request.form['settlement-day']
    payment_day=request.form['payment-day']
    credit_limit=request.form['credit-limit']
    interest_rate=request.form['interest-rate']
    available_credit=request.form['available-credit']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("select bank_id from Bank where bank_name= %s", (bank,))
    bankid = cursor.fetchall()[0]
    cursor.execute("INSERT INTO Account (user_id, bank_id, name, balance) VALUES (%s, %s, %s, %s)", (userid, bankid,name,balance))
    conn.commit()
    cursor.execute("select account_id from Account where user_id=%s and name=%s", (userid,name))
    accountid=cursor.fetchall()[0]
    cursor.execute("INSERT INTO Credit_Card (user_id, account_id, settlement_day, payment_day, available_credit, credit_limit, interest_rate) VALUES (%s, %s, %s, %s, %s, %s, %s)", (userid, accountid,settlement_day, payment_day, available_credit, credit_limit, interest_rate))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/profile')


if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)
