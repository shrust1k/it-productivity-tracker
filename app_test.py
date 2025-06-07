import sqlalchemy, flask, flask_login, bcrypt

app = flask.Flask(__name__)
app.secret_key = 'CHANGE_ME'

conn = sqlalchemy.create_engine(
    'mysql+mysqlconnector://user1:password@localhost:3306/productivity_tracker')
db = conn.connect()

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

users = []

class User(flask_login.UserMixin):
    def __init__(self, sqlrow):
        self.name = sqlrow[0]
        self.password = sqlrow[1]
        self.id = sqlrow[2]
        users.append(self)

    def __str__(self):
        return f"{self.id} {self.name} {self.password}"

    def get_user_from_id(user_id: int):
        for user in users:
            if user.id == user_id:
                return user

        return None


vasya = User(['vasya', '123', 1])


@login_manager.user_loader
def load_user(user_id):
    print(type(user_id), user_id)
    return User.get_user_from_id(int(user_id))

@app.route("/")
def home():
    return f"""
    {flask_login.current_user}
    {flask_login.current_user.is_authenticated}
    """
    return flask.render_template('index.html', user=flask_login.current_user)


@app.route("/login")
def login():
    flask_login.login_user(vasya)
    return flask.redirect('/')

if __name__ == "__main__":
    app.run(debug=True, port=5000, host="localhost")