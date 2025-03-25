from flask import Flask, request, jsonify, send_file
import requests
import uuid
import time
from db_utils import get_db_connection

app = Flask(__name__)

@app.route('/')
def index():
    return send_file('ui.html')

@app.route('/logs', methods=['GET'])
def get_logs():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM SAGA_LOG ORDER BY created_at DESC LIMIT 50")
    logs = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(logs)

def log_saga(saga_id, service, status, message):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO SAGA_LOG (saga_id, service, status, message) VALUES (%s, %s, %s, %s)",
                   (saga_id, service, status, message))
    conn.commit()
    cursor.close()
    conn.close()

def retry_request(url, data, retries=2, delay=2):
    for attempt in range(retries + 1):
        try:
            print(f"🔁 Attempt {attempt + 1} - POST {url} with {data}")
            res = requests.post(url, json=data, timeout=5)
            res.raise_for_status()
            return res
        except Exception as e:
            print(f"⚠️ Retry {attempt + 1} failed for {url}: {e}")
            if attempt == retries:
                raise Exception(f"❌ Final failure calling {url}: {e}")
            time.sleep(delay)

def compensate_service_b(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM TABLE_B WHERE user_id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

def compensate_service_a(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM TABLE_A WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/start', methods=['POST'])
def start():
    saga_id = str(uuid.uuid4())
    data = request.json
    user_id = -1  # fallback to ensure rollback executes even if A fails
    service_failed = None

    print("🔥 Saga started")
    print("➡️ Incoming request:", data)

    try:
        try:
            res_a = retry_request('http://localhost:5001/invoke', {'username': data['username']})
            user_id = res_a.json().get('user_id', -1)
            log_saga(saga_id, 'A', 'success', f"User {user_id} created")
        except Exception as e:
            service_failed = 'A'
            raise Exception(f"Service A failed: {e}")

        try:
            res_b = retry_request('http://localhost:5002/invoke', {'user_id': user_id, 'address': data['address']})
            log_saga(saga_id, 'B', 'success', "Address added")
        except Exception as e:
            service_failed = 'B'
            raise Exception(f"Service B failed: {e}")

        try:
            res_c = retry_request('http://localhost:5003/invoke', {'user_id': user_id, 'payment_method': data['payment']})
            log_saga(saga_id, 'C', 'success', "Payment added")
        except Exception as e:
            service_failed = 'C'
            raise Exception(f"Service C failed: {e}")

        return jsonify({'saga': saga_id, 'status': 'success'})

    except Exception as e:
        import traceback
        print(f"❌ Saga failed at Service {service_failed}:", str(e))
        traceback.print_exc()
        print(f"⚠️ Rollback starting for user_id={user_id}")

        # Always attempt rollback
        try:
            print("🧹 Rolling back TABLE_C...")
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM TABLE_C WHERE user_id = %s", (user_id,))
            conn.commit()
            cursor.close()
            conn.close()
            log_saga(saga_id, 'COMPENSATE_C', 'success', f"Rolled back TABLE_C for user {user_id}")
        except Exception as ce:
            print("⚠️ Compensation C failed:", ce)
            traceback.print_exc()
            log_saga(saga_id, 'COMPENSATE_C', 'failed', str(ce))

        try:
            print("🧹 Rolling back TABLE_B...")
            compensate_service_b(user_id)
            log_saga(saga_id, 'COMPENSATE_B', 'success', f"Rolled back TABLE_B for user {user_id}")
        except Exception as ce:
            print("⚠️ Compensation B failed:", ce)
            traceback.print_exc()
            log_saga(saga_id, 'COMPENSATE_B', 'failed', str(ce))

        try:
            print("🧹 Rolling back TABLE_A...")
            compensate_service_a(user_id)
            log_saga(saga_id, 'COMPENSATE_A', 'success', f"Rolled back TABLE_A for user {user_id}")
        except Exception as ce:
            print("⚠️ Compensation A failed:", ce)
            traceback.print_exc()
            log_saga(saga_id, 'COMPENSATE_A', 'failed', str(ce))

        try:
            log_saga(saga_id, 'ROLLBACK', 'triggered', f"Service {service_failed} failure: {e}")
            response = jsonify({
                'saga': saga_id,
                'status': 'rolled back',
                'failed_service': service_failed,
                'user_id': user_id,
                'error': str(e)
            })
            response.status_code = 500
            return response
        except Exception as json_error:
            print("‼️ Failed to return JSON response:", json_error)
            traceback.print_exc()
            return "Saga failed. Rollback attempted. JSON response failed.", 500

    except Exception as e:
        import traceback
        print(f"❌ Saga failed at Service {service_failed}:", str(e))
        traceback.print_exc()

        # Ensure rollback of all 3 services
        try:
            print("🧹 Rolling back TABLE_C...")
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM TABLE_C WHERE user_id = %s", (user_id,))
            conn.commit()
            cursor.close()
            conn.close()
            log_saga(saga_id, 'COMPENSATE_C', 'success', f"Rolled back TABLE_C for user {user_id}")
        except Exception as ce:
            print("⚠️ Compensation C failed:", ce)
            traceback.print_exc()
            log_saga(saga_id, 'COMPENSATE_C', 'failed', str(ce))

        try:
            print("🧹 Rolling back TABLE_B...")
            compensate_service_b(user_id)
            log_saga(saga_id, 'COMPENSATE_B', 'success', f"Rolled back TABLE_B for user {user_id}")
        except Exception as ce:
            print("⚠️ Compensation B failed:", ce)
            traceback.print_exc()
            log_saga(saga_id, 'COMPENSATE_B', 'failed', str(ce))

        try:
            print("🧹 Rolling back TABLE_A...")
            if user_id:
                compensate_service_a(user_id)
                log_saga(saga_id, 'COMPENSATE_A', 'success', f"Rolled back TABLE_A for user {user_id}")
            else:
                log_saga(saga_id, 'COMPENSATE_A', 'skipped', "No user_id available to rollback")
        except Exception as ce:
            print("⚠️ Compensation A failed:", ce)
            traceback.print_exc()
            log_saga(saga_id, 'COMPENSATE_A', 'failed', str(ce))

        log_saga(saga_id, 'ROLLBACK', 'triggered', f"Service {service_failed} failure: {e}")

        try:
            response = jsonify({'saga': saga_id, 'status': 'rolled back', 'failed_service': service_failed, 'error': str(e)})
            response.status_code = 500
            return response
        except Exception as json_error:
            print("‼️ Failed to return JSON response:", json_error)
            traceback.print_exc()
            return "Saga failed. Rollback attempted. JSON response failed.", 500

    except Exception as e:
        print("❌ Saga failure:", str(e))
        try:
            # Always attempt to rollback all 3
            print("🧹 Rolling back TABLE_C...")
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM TABLE_C WHERE user_id = %s", (user_id,))
            conn.commit()
            cursor.close()
            conn.close()
            log_saga(saga_id, 'COMPENSATE_C', 'success', f"Rolled back TABLE_C for user {user_id}")
        except Exception as ce:
            log_saga(saga_id, 'COMPENSATE_C', 'failed', str(ce))

        try:
            print("🧹 Rolling back TABLE_B...")
            compensate_service_b(user_id)
            log_saga(saga_id, 'COMPENSATE_B', 'success', f"Rolled back TABLE_B for user {user_id}")
        except Exception as ce:
            log_saga(saga_id, 'COMPENSATE_B', 'failed', str(ce))

        try:
            print("🧹 Rolling back TABLE_A...")
            compensate_service_a(user_id)
            log_saga(saga_id, 'COMPENSATE_A', 'success', f"Rolled back TABLE_A for user {user_id}")
        except Exception as ce:
            log_saga(saga_id, 'COMPENSATE_A', 'failed', str(ce))

        log_saga(saga_id, 'ROLLBACK', 'triggered', str(e))

        try:
            response = jsonify({'saga': saga_id, 'status': 'rolled back', 'error': str(e)})
            response.status_code = 500
            return response
        except Exception as json_fallback:
            print("‼️ Failed to return JSON:", json_fallback)
            return "Saga failed and rollback attempted. JSON error response also failed.", 500

    except Exception as e:
        print("❌ Saga failure:", str(e))

        # Rollback all three tables if any failure happens
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM TABLE_C WHERE user_id = %s", (user_id,))
            conn.commit()
            cursor.close()
            conn.close()
            log_saga(saga_id, 'COMPENSATE_C', 'success', f"Rolled back TABLE_C for user {user_id}")
        except Exception as ce:
            log_saga(saga_id, 'COMPENSATE_C', 'failed', str(ce))

        try:
            compensate_service_b(user_id)
            log_saga(saga_id, 'COMPENSATE_B', 'success', f"Rolled back TABLE_B for user {user_id}")
        except Exception as ce:
            log_saga(saga_id, 'COMPENSATE_B', 'failed', str(ce))

        try:
            compensate_service_a(user_id)
            log_saga(saga_id, 'COMPENSATE_A', 'success', f"Rolled back TABLE_A for user {user_id}")
        except Exception as ce:
            log_saga(saga_id, 'COMPENSATE_A', 'failed', str(ce))

        log_saga(saga_id, 'ROLLBACK', 'triggered', str(e))
        response = jsonify({'saga': saga_id, 'status': 'rolled back', 'error': str(e)})
        response.status_code = 500
        return response

    except Exception as e:
        print("❌ Saga failure:", str(e))

        # Always rollback all three tables regardless of which service failed
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM TABLE_C WHERE user_id = %s", (user_id,))
            conn.commit()
            cursor.close()
            conn.close()
            log_saga(saga_id, 'COMPENSATE_C', 'success', f"Rolled back TABLE_C for user {user_id}")
        except Exception as ce:
            log_saga(saga_id, 'COMPENSATE_C', 'failed', str(ce))

        try:
            compensate_service_b(user_id)
            log_saga(saga_id, 'COMPENSATE_B', 'success', f"Rolled back TABLE_B for user {user_id}")
        except Exception as ce:
            log_saga(saga_id, 'COMPENSATE_B', 'failed', str(ce))

        try:
            compensate_service_a(user_id)
            log_saga(saga_id, 'COMPENSATE_A', 'success', f"Rolled back TABLE_A for user {user_id}")
        except Exception as ce:
            log_saga(saga_id, 'COMPENSATE_A', 'failed', str(ce))

        log_saga(saga_id, 'ROLLBACK', 'triggered', str(e))
        response = jsonify({'saga': saga_id, 'status': 'rolled back', 'error': str(e)})
        response.status_code = 500
        return response

    except Exception as e:
        print("❌ Saga failure:", str(e))

        # Always rollback in reverse order if anything fails
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM TABLE_C WHERE user_id = %s", (user_id,))
            conn.commit()
            cursor.close()
            conn.close()
            log_saga(saga_id, 'COMPENSATE_C', 'success', f"Rolled back TABLE_C for user {user_id}")
        except Exception as ce:
            log_saga(saga_id, 'COMPENSATE_C', 'failed', str(ce))

        try:
            compensate_service_b(user_id)
            log_saga(saga_id, 'COMPENSATE_B', 'success', f"Rolled back TABLE_B for user {user_id}")
        except Exception as ce:
            log_saga(saga_id, 'COMPENSATE_B', 'failed', str(ce))

        try:
            compensate_service_a(user_id)
            log_saga(saga_id, 'COMPENSATE_A', 'success', f"Rolled back TABLE_A for user {user_id}")
        except Exception as ce:
            log_saga(saga_id, 'COMPENSATE_A', 'failed', str(ce))

        log_saga(saga_id, 'ROLLBACK', 'triggered', str(e))
        response = jsonify({'saga': saga_id, 'status': 'rolled back', 'error': str(e)})
        response.status_code = 500
        return response

    except Exception as e:
        print("❌ Error during saga:", str(e))

        try:
            if c_success:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM TABLE_C WHERE user_id = %s", (user_id,))
                conn.commit()
                cursor.close()
                conn.close()
                log_saga(saga_id, 'COMPENSATE_C', 'success', f"Rolled back TABLE_C for user {user_id}")
        except Exception as ce:
            log_saga(saga_id, 'COMPENSATE_C', 'failed', str(ce))

        try:
            if b_success:
                compensate_service_b(user_id)
                log_saga(saga_id, 'COMPENSATE_B', 'success', f"Rolled back TABLE_B for user {user_id}")
        except Exception as ce:
            log_saga(saga_id, 'COMPENSATE_B', 'failed', str(ce))

        try:
            if a_success:
                compensate_service_a(user_id)
                log_saga(saga_id, 'COMPENSATE_A', 'success', f"Rolled back TABLE_A for user {user_id}")
        except Exception as ce:
            log_saga(saga_id, 'COMPENSATE_A', 'failed', str(ce))

        log_saga(saga_id, 'ROLLBACK', 'triggered', str(e))

        response = jsonify({'saga': saga_id, 'status': 'failed', 'error': str(e)})
        response.status_code = 500
        return response

    except Exception as e:
        print("❌ Error during saga:", str(e))

        if c_success:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM TABLE_C WHERE user_id = %s", (user_id,))
                conn.commit()
                cursor.close()
                conn.close()
                log_saga(saga_id, 'COMPENSATE_C', 'success', f"Rolled back TABLE_C for user {user_id}")
            except Exception as ce:
                log_saga(saga_id, 'COMPENSATE_C', 'failed', str(ce))

        if b_success:
            try:
                compensate_service_b(user_id)
                log_saga(saga_id, 'COMPENSATE_B', 'success', f"Rolled back TABLE_B for user {user_id}")
            except Exception as ce:
                log_saga(saga_id, 'COMPENSATE_B', 'failed', str(ce))

        if a_success:
            try:
                compensate_service_a(user_id)
                log_saga(saga_id, 'COMPENSATE_A', 'success', f"Rolled back TABLE_A for user {user_id}")
            except Exception as ce:
                log_saga(saga_id, 'COMPENSATE_A', 'failed', str(ce))

        log_saga(saga_id, 'ROLLBACK', 'triggered', str(e))
        response = jsonify({'saga': saga_id, 'status': 'rolled back', 'error': str(e)})
        response.status_code = 500
        return response

if __name__ == "__main__":
    print("🚀 Orchestrator service starting on http://localhost:5000 ...")
    app.run(port=5000)


@app.errorhandler(500)
def internal_error(e):
    import traceback
    traceback.print_exc()
    return jsonify({
        "status": "500",
        "message": "Internal Server Error",
        "details": str(e)
    }), 500
