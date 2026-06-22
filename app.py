from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'Mi primer e.commerce :)'

if __name__ == '__main__':
    app.run(debug=True)