from flask import redirect
from app import app

@app.route('/')
def root():
    return redirect('/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
