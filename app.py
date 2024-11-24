from flask import Flask, flash, redirect, render_template, request, session, g
import os
import psycopg2

app = Flask(__name__)

DATABASE = {
    'dbname': 'w4111',
    'user': 'zx2514',
    'password': 'zx2514',
    'host': 'w4111.cisxo09blonu.us-east-1.rds.amazonaws.com',
    'port': '5432'
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
###
@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn=get_db_connection()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/')
def home():
    if 'userid' in session:
        return redirect('/trx')
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    password=request.form['password']
    username=request.form['username']

    # conn = get_db_connection()
    cursor = g.conn.cursor()
    cursor.execute("select user_id, password from Users where user_name=%s", (username,))
    result = cursor.fetchone()
    cursor.close()
    # conn.close()
    if not result:
        flash("User not found")
    elif result[1]==password:
        session['userid']=result[0]
        return redirect('/trx')
    else:
        flash('wrong password!')
        
    return home()

@app.route("/logout")
def logout():
    session.pop('userid', None)
    return redirect('/')

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
            # conn = get_db_connection()
            cursor = g.conn.cursor()
            cursor.execute("INSERT INTO Users (user_name, email, phone_number, password) VALUES (%s, %s, %s, %s)", (username, email,phone,password))
            g.conn.commit()
            cursor.close()
            # conn.close()
            flash('Account created successfully! You can now log in.')
            return redirect('/')
        except:
            flash('Username already exists!')
            return render_template('create_account.html')
    return render_template('create_account.html')

@app.route("/trx")
def trx():
    userid=session['userid']
    # conn = get_db_connection()
    cursor = g.conn.cursor()
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
    cursor.close()
    # conn.close()
    return render_template('trx.html',trxs=trxs)

@app.route("/acc")
def acc():
    userid=session['userid']
    # conn = get_db_connection()
    cursor = g.conn.cursor()
    cursor.execute("select account_id,name, balance from Account where user_id= %s", (userid,))
    accounts = cursor.fetchall()
    accs=[]
    for row in accounts:
        id, account,balance=row
        accs.append({'id':id,'account':account,'balance':balance})
        if balance < 0:
            has_negative_balance = True
    
    cursor.execute("select category_name, sum(amount)\
                   from Transaction as T LEFT JOIN Category as C on T.category_id=C.category_id\
                   where trx_type='expense' and user_id=%s\
                   group by T.category_id,category_name",(userid,))
    cursor.close()
    # conn.close()
    return render_template('acc.html',accs=accs, has_negative_balance=has_negative_balance)

@app.route("/stat")
def stat():
    userid=session['userid']
    # conn = get_db_connection()
    cursor = g.conn.cursor()
    cursor.execute("select category_name, sum(amount)\
                from Transaction as T LEFT JOIN Category as C on T.category_id=C.category_id\
                where trx_type='expense' and user_id=%s\
                group by T.category_id,category_name",(userid,))
    labels=[]
    values=[]
    sum=0
    for row in cursor.fetchall():
        category,amount=row
        labels.append(category)
        values.append(amount)
        sum+=amount
    if sum==0:
        chart_data={}
    else:    
        chart_data = {
        "labels": labels,
        "values": [i/sum for i in values]
        }
    cursor.close()
    # conn.close()
    return render_template('stat.html',chart_data=chart_data)

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
            # conn = get_db_connection()
            cursor = g.conn.cursor()
            cursor.execute("select account_id from Account where name=%s and user_id=%s",(account, userid))
            accountid=cursor.fetchone()[0]
            cursor.execute("select category_id from Category where category_name=%s",(category,))
            categoryid=cursor.fetchone()[0]
            cursor.execute("INSERT INTO Transaction (user_id, account_id, trx_date, amount, category_id, trx_type) VALUES (%s, %s, %s, %s, %s, %s)", (userid, accountid,date,amount,categoryid,type))
            g.conn.commit()
            cursor.close()
            # conn.close()
            return redirect('/trx')
        except:
            flash('Please fill all blanks!')
            return redirect('/add_trx')
    
    # conn = get_db_connection()
    cursor = g.conn.cursor()
    cursor.execute("select name from Account where user_id= %s", (userid,))
    accounts = cursor.fetchall()
    cursor.execute("select category_name from Category")
    categories = cursor.fetchall()
    cursor.close()
    # conn.close()
    return render_template('add_trx.html',accounts=accounts,categories=categories)

@app.route('/add_acc')
def add_account():
    # conn = get_db_connection()
    cursor = g.conn.cursor()
    cursor.execute("select bank_name from Bank")
    result=cursor.fetchall()
    cursor.close()
    # conn.close()
    return render_template('add_acc.html',banks=result)



@app.route('/add_normal',methods=['POST'])
def add_normal():
    userid=session['userid']
    bank=request.form['bank']
    name=request.form['name']
    balance=request.form['balance']
    # conn = get_db_connection()
    cursor = g.conn.cursor()
    cursor.execute("select bank_id from Bank where bank_name= %s", (bank,))
    bankid = cursor.fetchall()[0]
    cursor.execute("INSERT INTO Account (user_id, bank_id, name, balance) VALUES (%s, %s, %s, %s)", (userid, bankid,name,balance))
    g.conn.commit()
    cursor.close()
    # conn.close()
    return redirect('/acc')


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
    # conn = get_db_connection()
    cursor = g.conn.cursor()
    cursor.execute("select bank_id from Bank where bank_name= %s", (bank,))
    bankid = cursor.fetchall()[0]
    cursor.execute("INSERT INTO Account (user_id, bank_id, name, balance) VALUES (%s, %s, %s, %s)", (userid, bankid,name,balance))
    g.conn.commit()
    cursor.execute("select account_id from Account where user_id=%s and name=%s", (userid,name))
    accountid=cursor.fetchall()[0]
    cursor.execute("INSERT INTO Credit_Card (user_id, account_id, settlement_day, payment_day, available_credit, credit_limit, interest_rate) VALUES (%s, %s, %s, %s, %s, %s, %s)", (userid, accountid,settlement_day, payment_day, available_credit, credit_limit, interest_rate))
    g.conn.commit()
    cursor.close()
    # conn.close()
    return redirect('/acc')

@app.route('/acc_info/<int:id>')
def acc_info(id):
    # conn = get_db_connection()
    cursor = g.conn.cursor()
    cursor.execute("select name,balance from Account where account_id=%s",(id,))
    name,balance=cursor.fetchall()[0]
    cursor.execute("select trx_date, amount, category_name, trx_type\
                    from Transaction as T join Category as C on C.category_id=T.category_id\
                    where account_id=%s",(id,))
    res=cursor.fetchall()
    trxs=[]
    for row in res:
        trx_date, amount, category, trx_type=row
        trxs.append({'date':trx_date,'amount':amount,'category': category,'type':trx_type})
    
    cursor.execute("select settlement_day, payment_day, available_credit, credit_limit, interest_rate from Credit_Card where account_id=%s",(id,))
    res=cursor.fetchall()
    if res!=[]: #credit card
        settlement_day, payment_day, available_credit, credit_limit, interest_rate=res[0]
        cursor.close()
        # conn.close()
        return render_template('credit.html',\
                               name=name,balance=balance,trxs=trxs,\
                               settlement_day=settlement_day, payment_day=payment_day, \
                                available_credit=available_credit, credit_limit=credit_limit, interest_rate= interest_rate)
    cursor.close()
    # conn.close()
    return render_template('normal_acc.html',name=name,balance=balance,trxs=trxs)
    
    


if __name__ == "__main__":
    import click

    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):

    # HOST, PORT = host, port
    # print("running on %s:%d" % (HOST, PORT))
        app.secret_key = os.urandom(12)
        app.run(debug=True,host='0.0.0.0', port=8111)


    run()
    
