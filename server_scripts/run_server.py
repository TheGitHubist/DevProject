from flask import redirect
from app import app, fetch_and_store_word

if __name__ == '__main__':
    fetch_and_store_word('conquest')
    fetch_and_store_word('despair')
    app.run(host='0.0.0.0', port=5000)
