service_a.py script 
✅ Key Features Implemented:
- **Flask endpoint `/invoke`** that inserts a `username` into `TABLE_A`.
- **Failure simulation**: Fails every alternate request **before DB transaction**, using `failure_counter`.
- **Database logic**: Connects via `get_db_connection()`, inserts the user, commits, and returns `user_id`.

Your `service_b.py` is working exactly as planned for the Saga Pattern demo. Here's a quick breakdown:

---

### ✅ Behavior Summary:
- **Always tries inserting `user_id`, `address` into `TABLE_B`.**
- **Prevents duplicate inserts** by checking existence (`SELECT COUNT(*)...`).
- **Fails every other time _after_ commit** — which is what you wanted to simulate.
- **Rolls back** if an exception is raised (though `rollback()` after a `commit()` has no effect on already-committed data, this matches the intended failure simulation).
- **Logs to console with `[INFO]` and `[ERROR]` prefixes.**

---

Your `service_c.py` is perfectly aligned with your Saga orchestration design:

---

### ✅ Behavior Summary:
- **Receives `user_id` and `payment_method` via `/invoke`**.
- **Inserts into `TABLE_C`**.
- No intentional failure—this service always succeeds as per your requirement.

---

### 🔍 Completeness Checklist:

| Item                      | Status |
|---------------------------|--------|
| Accepts POST requests     | ✅     |
| Uses shared DB connection | ✅     |
| Inserts data into `TABLE_C` | ✅   |
| Commits transaction       | ✅     |
| Clean resource closure    | ✅     |
| Runs on port `5003`       | ✅     |
| No failure injection      | ✅     |

---

Your `orchestrator.py` is an excellent, full-featured implementation of the Saga Pattern — solid work!

---

### ✅ Key Strengths:
- **Retry logic with backoff (`retry_request`)**
- **Full rollback / compensation across all services**
- **Detailed saga logging (`log_saga`)**
- **Resilient JSON error handling**
- **UI ready (`ui.html` and `/logs`)**
- **Readable console logs (`🔥`, `➡️`, `🧹`, etc.)**

---

### ⚠️ Optimization Needed:
You have **many redundant `except Exception` blocks**, repeating the same rollback logic. This can be **consolidated** safely.

---



