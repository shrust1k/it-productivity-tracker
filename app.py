import sqlalchemy, flask, flask_login, bcrypt
app = flask.Flask(__name__)
app.secret_key = 'CHANGE ME'

conn = sqlalchemy.create_engine(
    'mysql+mysqlconnector://user1:password@localhost:3306/productivity_tracker')
db = conn.connect()

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

users = []

def get_user_by_name(name: str):
    user = db.execute(sqlalchemy.text(f"SELECT * FROM users WHERE name='{name}'")).fetchone()
    if user:
        return User(user)
    return None

def get_records():
    if flask_login.current_user.is_authenticated:
        records = db.execute(sqlalchemy.text(f'SELECT * FROM records WHERE user_id={flask_login.current_user.id}')).fetchall()
        records = Record.sql_arr_to_obj_arr(records)
        return records[::-1] #reverse for getting last records
    else:
        return None

class User(flask_login.UserMixin):
    def __init__(self, sqlrow):
        self.name = sqlrow[0]
        self.password = sqlrow[1]
        self.id = sqlrow[2]
        users.append(self)

    def __str__(self):
        return f"{self.id} | {self.name} | {self.password} "

    def get_user_from_id(user_id: int):
        user_in_db = db.execute(sqlalchemy.text(f"SELECT * FROM users WHERE id={user_id}")).fetchone()
        user_in_db = User(user_in_db)
        if user_in_db.id == user_id:
            return user_in_db
        return None
    

class Record:
    def __init__(self, sqlrow):
        self.id = sqlrow[0]
        self.text = sqlrow[1]
        self.user_id = sqlrow[2]
        self.dateCreated = sqlrow[3]
        
    def sql_arr_to_obj_arr(sql_request) -> list:
        arr = []
        for record in sql_request:
            record_obj = Record(record)
            arr.append(record_obj)
        return arr

@login_manager.user_loader
def load_user(user_id):
    return User.get_user_from_id(int(user_id))


@app.route("/")
def home():
    message = flask.get_flashed_messages()[0] if flask.get_flashed_messages() else ""
    return flask.render_template('index.html',
    is_logged = flask_login.current_user.is_authenticated, 
    records = get_records(),
    message=message) 
    
@app.route("/register", methods=['GET', 'POST'])
def register():
    message = flask.get_flashed_messages()[0] if flask.get_flashed_messages() else ""
    if flask.request.method == 'GET':
        return flask.render_template('register.html', message=message)
    else:
        name = flask.request.form['name']
        password = flask.request.form['password']
        hashed_password = bcrypt.hashpw(bytes(password, encoding='utf-8'), bcrypt.gensalt())
        #check for unique name
        name_is_taken = db.execute(sqlalchemy.text(f"SELECT * FROM users WHERE name='{name}'")).fetchone()
        
        if not name_is_taken:
            db.execute(
                sqlalchemy.text(f"INSERT INTO users (name, password) VALUES (:n, :p)"),
                parameters=dict(n=name, p=hashed_password))
            db.commit()
            user = get_user_by_name(name)
            flask_login.login_user(user)
            return flask.redirect('/')
        else:
            return flask.render_template('register.html', message='name is taken, try another one')


@app.route("/login", methods=['POST'])
def login():
    name = flask.request.form['name']
    password = bytes(flask.request.form['password'], encoding='utf-8')
    user = get_user_by_name(name)
    
    if user:
        if bcrypt.checkpw(password, user.password):
            flask_login.login_user(user)
            return flask.redirect('/')
        else:
            flask.flash('wrong password')
            return flask.redirect("/")

    else:       
        flask.flash('such user doesnt exist')
        return flask.redirect("/register")
        



@app.route('/logout')
def logout():
    flask_login.logout_user()
    return flask.redirect('/')

@app.route('/add_record', methods=['POST'])
@flask_login.login_required
def add_record():
    user_id = int(flask_login.current_user.id)
    text = flask.request.form['text']
    
    db.execute(sqlalchemy.text(f'INSERT INTO records (text, user_id) VALUES ("{text}", {user_id})'))
    db.commit()
    return flask.redirect('/')
    



if __name__ == "__main__":
    app.run(debug=True, port=5000, host="localhost")