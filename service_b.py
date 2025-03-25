from flask import Flask, request, jsonify
from common import get_db_connection

app = Flask(__name__)
failure_counter = {'count': 0}

@app.route('/invoke', methods=['POST'])
def invoke():
    failure_counter['count'] += 1
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO TABLE_B (user_id, address) VALUES (%s, %s)", 
                   (data['user_id'], data['address']))
    conn.commit()

    if failure_counter['count'] % 2 == 0:
        exit(1)

    cursor.close()
    conn.close()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(port=5002)