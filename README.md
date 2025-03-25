## Saga Demo
✅ Orchestrator  
✅ Services A, B, and C  
✅ MySQL setup  
✅ Failure simulation  
✅ No Docker or cloud  
✅ Fully local execution

---

## ✅ STEP 1: Install Requirements on Mac

### 🔹 Install MySQL (if not installed)
```bash
brew install mysql
brew services start mysql
```

### 🔹 Set MySQL root password
```bash
mysql_secure_installation
```

> For simplicity, let’s use `root` as user and `password` as the password (you can change it later).

---

## ✅ STEP 2: Create MySQL Schema and Tables

### 🔹 Connect to MySQL
```bash
mysql -u root -p
```

### 🔹 Run this SQL:
```sql
CREATE DATABASE saga_db;

USE saga_db;

CREATE TABLE TABLE_A (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(255) NOT NULL
);

CREATE TABLE TABLE_B (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  address VARCHAR(255),
  FOREIGN KEY (user_id) REFERENCES TABLE_A(id)
);

CREATE TABLE TABLE_C (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  payment_method VARCHAR(255),
  FOREIGN KEY (user_id) REFERENCES TABLE_A(id)
);

CREATE TABLE SAGA_LOG (
  id INT AUTO_INCREMENT PRIMARY KEY,
  saga_id VARCHAR(100),
  service VARCHAR(100),
  status VARCHAR(20),
  message TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## ✅ STEP 3: Create Python Virtual Environment and Install Flask

```bash
python3 -m venv saga_env
source saga_env/bin/activate
pip install flask mysql-connector-python
```

---

## ✅ STEP 4: Create a File Structure

```
saga_project/
│
├── orchestrator.py       # Port 5000
├── service_a.py          # Port 5001
├── service_b.py          # Port 5002
├── service_c.py          # Port 5003
├── common.py             # Shared DB connection logic
└── ui.html               # UI
```

---

## ✅ STEP 5: Create `common.py`

```python
import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='password',
        database='saga_db'
    )
```

---

## ✅ STEP 6: Create `service_a.py` (PORT 5001)

```python
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
```

---

## ✅ STEP 7: Create `service_b.py` (PORT 5002)

```python
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

    # Simulate crash after commit
    if failure_counter['count'] % 2 == 0:
        exit(1)

    cursor.close()
    conn.close()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(port=5002)
```

---

## ✅ STEP 8: Create `service_c.py` (PORT 5003)

```python
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
```

---

## ✅ STEP 9: Create `orchestrator.py` (PORT 5000)

```python
from flask import Flask, request, jsonify
import requests
import uuid
from common import get_db_connection

app = Flask(__name__)

def log_saga(saga_id, service, status, message):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO SAGA_LOG (saga_id, service, status, message) VALUES (%s, %s, %s, %s)",
                   (saga_id, service, status, message))
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/start', methods=['POST'])
def start():
    saga_id = str(uuid.uuid4())
    data = request.json

    try:
        res_a = requests.post('http://localhost:5001/invoke', json={'username': data['username']})
        res_a.raise_for_status()
        user_id = res_a.json()['user_id']
        log_saga(saga_id, 'A', 'success', f"User {user_id} created")
    except Exception as e:
        log_saga(saga_id, 'A', 'failed', str(e))
        return jsonify({'saga': saga_id, 'status': 'failed at A'}), 500

    try:
        res_b = requests.post('http://localhost:5002/invoke', json={'user_id': user_id, 'address': data['address']})
        res_b.raise_for_status()
        log_saga(saga_id, 'B', 'success', "Address added")
    except Exception as e:
        log_saga(saga_id, 'B', 'failed', str(e))
        return jsonify({'saga': saga_id, 'status': 'failed at B'}), 500

    try:
        res_c = requests.post('http://localhost:5003/invoke', json={'user_id': user_id, 'payment_method': data['payment']})
        res_c.raise_for_status()
        log_saga(saga_id, 'C', 'success', "Payment added")
    except Exception as e:
        log_saga(saga_id, 'C', 'failed', str(e))
        return jsonify({'saga': saga_id, 'status': 'failed at C'}), 500

    return jsonify({'saga': saga_id, 'status': 'success'})

if __name__ == '__main__':
    app.run(port=5000)
```

---

## ✅ STEP 10: Run All Services

In 4 separate terminals:

```bash
# Terminal 1
python service_a.py

# Terminal 2
python service_b.py

# Terminal 3
python service_c.py

# Terminal 4
python orchestrator.py
```

---

## ✅ STEP 11: Trigger Saga via URL http://localhost:5000

### Example CURL:
```bash
Username john_doe
Address  123 Main St
Payment  Visa

```

Create New User (Saga Demo)

Username:


Address:


Payment Method:


Submit
Response:
View Logs
Latest Saga Logs:
Time	Saga ID	Service	Status	Message


---

### ✅ **Base Test Case (Happy Path)**

| ID | Test Case | Steps | Expected Outcome |
|----|-----------|-------|------------------|
| TC-01 | Normal operation | Start all services and orchestrator, then trigger saga | All services A → B → C execute successfully. All three tables are updated. Log entry shows saga success. |

---

### 🛑 **Service Down / Network Failures**

| ID | Test Case | Steps | Expected Outcome |
|----|-----------|-------|------------------|
| TC-02 | Stop Service A | Stop Flask service on port 5001 before saga is triggered | Orchestrator fails to call Service A. Saga logs failure. No data committed. Retry logic may kick in. |
| TC-03 | Stop Service B | Stop Flask service on port 5002 before saga is triggered | Orchestrator calls A successfully. Fails at B. Compensation action (rollback A) should trigger. |
| TC-04 | Stop Service C | Stop Flask service on port 5003 before saga is triggered | A and B succeed. Fails at C. Compensation for B and A should happen. Saga logs failure with rollback. |

---

### 🔁 **Failure After Transaction (Simulated in Code)**

| ID | Test Case | Steps | Expected Outcome |
|----|-----------|-------|------------------|
| TC-05 | Service A fails before DB transaction | Run saga multiple times to trigger "every other" failure in A | A fails as expected. Saga aborts early. Log shows failure at A. No compensation needed. |
| TC-06 | Service B fails after DB commit | Run saga multiple times to hit B's "every other" post-commit failure | A and B partially commit. Orchestrator should detect failure and initiate rollback (manual or via compensator). |

---

### ⌛ **Timeouts & Retries**

| ID | Test Case | Steps | Expected Outcome |
|----|-----------|-------|------------------|
| TC-07 | Simulate Service B timeout | Add delay in Service B > orchestrator timeout value | Orchestrator retries B, then triggers rollback if B continues failing. |
| TC-08 | Retry success scenario | Service A fails first time, succeeds on retry | Orchestrator retries A, then continues saga. Saga ends successfully. |

---

### 📉 **Database Failure**

| ID | Test Case | Steps | Expected Outcome |
|----|-----------|-------|------------------|
| TC-09 | DB goes down mid-saga | Stop MySQL service before or during saga | Services fail to write to DB. Saga fails. Log should reflect database error. |

---

## ✅ STEP 12: View Saga Logs

```sql
USE saga_db;
SELECT * FROM SAGA_LOG ORDER BY created_at DESC;
```

---

