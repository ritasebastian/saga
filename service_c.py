from flask import Flask, request, jsonify
from common import get_db_connection

app = Flask(__name__)

@app.route('/invoke', methods=['POST'])
def invoke():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO TABLE_C (user_id, payment_method) VALUES (%s, %s)",
                   (data['user_id'], data['payment_method']))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(port=5003)