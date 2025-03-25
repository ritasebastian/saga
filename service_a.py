from flask import Flask, request, jsonify
from common import get_db_connection

app = Flask(__name__)
failure_counter = {'count': 0}

@app.route('/invoke', methods=['POST'])
def invoke():
    failure_counter['count'] += 1
    if failure_counter['count'] % 2 == 0:
        return jsonify({'status': 'fail', 'reason': 'Service A failed before DB transaction'}), 500

    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO TABLE_A (username) VALUES (%s)", (data['username'],))
    conn.commit()
    user_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({'status': 'success', 'user_id': user_id})

if __name__ == '__main__':
    app.run(port=5001)