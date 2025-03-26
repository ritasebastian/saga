
## 🧩 Saga Pattern: Orchestration vs Choreography

The Saga Pattern is a microservice design pattern used to handle **long-lived transactions** and ensure **data consistency** across distributed systems.

---

### 🧠 What is a Saga?

- A **Saga** is a sequence of local transactions.
- Each service updates its own data and publishes an event or sends a response.
- If one transaction fails, **compensation actions** are triggered to undo the previous steps.

---

## 🏗️ Two Saga Models

---

### 1. **Orchestration-based Saga**

- A **central orchestrator** tells each participant what to do.
- It manages the workflow and handles failures/compensations.

#### ✔️ Pros:
- Easy to manage and debug.
- Clear flow and centralized logic.

#### ❌ Cons:
- Single point of failure.
- Orchestrator can become complex.

#### 🔁 Flow Diagram:

```plaintext
          +-------------+
          | Orchestrator|
          +------+------+ 
                 |
          Step 1 | Call Service A
                 v
          +-------------+
          |  Service A  |
          +-------------+
                 |
          Step 2 | Call Service B
                 v
          +-------------+
          |  Service B  |
          +-------------+
                 |
          Step 3 | Call Service C
                 v
          +-------------+
          |  Service C  |
          +-------------+
```

---

### 2. **Choreography-based Saga**

- No central orchestrator.
- Each service performs its task and publishes an event.
- Other services **listen** for events and act accordingly.

#### ✔️ Pros:
- Fully decoupled.
- Scales well.

#### ❌ Cons:
- Harder to debug.
- Flow is distributed across services.

#### 🔁 Flow Diagram:

```plaintext
+-------------+       Event A Completed     +-------------+
|  Service A  | --------------------------> |  Service B  |
+-------------+                             +-------------+
                                                  |
                                          Event B Completed
                                                  v
                                          +-------------+
                                          |  Service C  |
                                          +-------------+
```

---

## 🧪 Demo Setup Suggestion (For Orchestration)

- Services A, B, and C (Flask apps on ports 5001–5003).
- Central orchestrator on port 5000.
- MySQL backend: `TABLE_A`, `TABLE_B`, `TABLE_C`.
- Add retries, timeouts, compensation logic.
- UI to show logs and saga status.

---

Orchestration-based sagas use a central coordinator to manage distributed transactions across services. When a failure occurs, the orchestrator triggers compensating transactions to undo completed steps. Below are simplified textual diagrams for failure scenarios involving services A, B, and C, based on the Saga pattern's orchestration approach.

---

## **Successful Transaction Flow**
1. **Orchestrator** → **Service A**  
   - Executes Transaction A ✅  
2. **Orchestrator** → **Service B**  
   - Executes Transaction B ✅  
3. **Orchestrator** → **Service C**  
   - Executes Transaction C ✅  
**Final State**: All transactions complete successfully

---

## **Failure Scenarios and Compensation**

### **1. Failure at Service A**
```
Orchestrator → Service A ❌ (Transaction A fails)  
```
**Action**:  
- No compensation needed (no prior successful transactions).  
- Saga aborts immediately[1][6].

---

### **2. Failure at Service B**
```
Orchestrator → Service A ✅  
Orchestrator → Service B ❌ (Transaction B fails)  
```
**Compensation Flow**:  
1. **Orchestrator** → **Service A**  
   - Triggers Compensating Transaction A (undoes Transaction A) ✅  
**Result**: System returns to pre-transaction state

---

### **3. Failure at Service C**
```
Orchestrator → Service A ✅  
Orchestrator → Service B ✅  
Orchestrator → Service C ❌ (Transaction C fails)  
```
**Compensation Flow**:  
1. **Orchestrator** → **Service B**  
   - Triggers Compensating Transaction B (undoes Transaction B) ✅  
2. **Orchestrator** → **Service A**  
   - Triggers Compensating Transaction A (undoes Transaction A) ✅  
**Result**: System returns to pre-transaction state

---

### **Key Components in Diagrams**
| Component                | Role                                                                 |
|--------------------------|----------------------------------------------------------------------|
| **Orchestrator**         | Central coordinator; initiates transactions and compensations|
| **Compensating Transaction** | Reverses effects of a completed transaction (e.g., refunds, rollbacks) |
| **Service (A/B/C)**      | Executes local transactions or compensations as directed.        |

---

## **Failure Recovery Logic**
- **Non-compensable transactions** (e.g., irreversible actions like payments) are placed last to minimize rollback complexity.  
- The orchestrator uses **idempotent operations** to handle retries safely.  
- AWS Step Functions is a common tool for implementing fault-tolerant orchestration.

This structure ensures data consistency by systematically undoing completed steps when failures occur, avoiding partial updates in distributed systems.


In your Flask-based Saga Orchestrator system, HTTP **status codes** indicate the result of each request to services A, B, and C. Here’s a clear breakdown of what status codes you might encounter and what they mean:

---

### ✅ **Most Common HTTP Status Codes Used in Your System**

| **Code** | **Meaning** | **Where/When It Happens** |
|----------|-------------|---------------------------|
| **200 OK** | ✅ Success | - Service A, B, C respond successfully<br>- Orchestrator `/start` route completes all steps |
| **400 Bad Request** | ❌ Client sent invalid data | - Not currently implemented, but could happen if the `request.json` is missing required fields |
| **500 Internal Server Error** | ❌ Failure occurred during service logic | - Service A fails before DB insert (simulated)<br>- Service B fails after DB commit (simulated)<br>- Orchestrator catches exception and rolls back |
| **504 Gateway Timeout** | ❌ Request timeout | - Can occur if a `retry_request()` call exceeds 5s timeout (not seen unless a service hangs) |

---

### 📍Where Requests Are Made in Your Code

#### In `orchestrator.py`
```python
res_a = retry_request('http://localhost:5001/invoke', {...})  # calls Service A
res_b = retry_request('http://localhost:5002/invoke', {...})  # calls Service B
res_c = retry_request('http://localhost:5003/invoke', {...})  # calls Service C
```

- If the service responds successfully → `res.status_code == 200`
- If service fails (simulated or real) → status code will be `500`

---

### 🔁 Retry Logic
Your `retry_request()` function handles **temporary failures**:
- **Retries 2 times** if the service fails (500 or connection error)
- **Raises exception** if all retries fail → this triggers rollback in orchestrator

---

### 🧪 You Can Add a Test Route to See This
If you want to test what status codes you're getting back:

```python
@app.route('/test_status', methods=['POST'])
def test_status():
    res = requests.post('http://localhost:5001/invoke', json={"username": "test"})
    return jsonify({
        'status_code': res.status_code,
        'response': res.json()
    })
```

---
