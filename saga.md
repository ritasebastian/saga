
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

