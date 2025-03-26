
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
**Final State**: All transactions complete successfully[1][5].

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
**Result**: System returns to pre-transaction state[2][5].

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
**Result**: System returns to pre-transaction state[1][5].

---

### **Key Components in Diagrams**
| Component                | Role                                                                 |
|--------------------------|----------------------------------------------------------------------|
| **Orchestrator**         | Central coordinator; initiates transactions and compensations[3][5].|
| **Compensating Transaction** | Reverses effects of a completed transaction (e.g., refunds, rollbacks)[1][6]. |
| **Service (A/B/C)**      | Executes local transactions or compensations as directed[7].        |

---

## **Failure Recovery Logic**
- **Non-compensable transactions** (e.g., irreversible actions like payments) are placed last to minimize rollback complexity[6].  
- The orchestrator uses **idempotent operations** to handle retries safely[5].  
- AWS Step Functions is a common tool for implementing fault-tolerant orchestration[5].

This structure ensures data consistency by systematically undoing completed steps when failures occur, avoiding partial updates in distributed systems[1][2].


