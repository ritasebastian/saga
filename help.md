lsof -i :5000

'''
select * from table_a;
select * from table_a;
select * from table_a;
select * from saga_log;
'''



---

## 🔥 ACID stands for:
**A** – Atomicity  
**C** – Consistency  
**I** – Isolation  
**D** – Durability

These are the 4 guarantees every good database transaction should follow 💪

---

### 🧨 1. **Atomicity** – “All or Nothing”

👉 Either **full transaction success** or **nothing happens**. No partial updates.

🧠 **Example**:  
Online money transfer. You send ₹500 to your friend.

- ₹500 debit from your account ✅
- ₹500 credit to your friend's account ✅  
If credit fails, your money shouldn’t be gone 💸 ❌

> In short: Either **both actions happen**, or **none**. DB will rollback if there's a failure.

---

### 🛠️ 2. **Consistency** – “Data should follow rules”

👉 Database must always be in a **valid state** before and after the transaction.

🧠 **Example**:  
You can't have a bank account with a negative balance (rule).  
If a transaction breaks this rule, it should fail.

> In short: Database rules (constraints, triggers) must be respected always.

---

### 🚧 3. **Isolation** – “Transactions don’t disturb each other”

👉 One transaction shouldn’t affect another in progress.

🧠 **Example**:  
You and your sibling both withdraw money from same ATM at the same time.  
Each one should **feel like they're alone**. No mixed or dirty data.

> In short: DB ensures operations look like they ran **one after another**, even if parallel.

---

### 🔋 4. **Durability** – “Once done, always done”

👉 If transaction is committed, it **stays saved** even if power fails or server crashes 🔌💥

🧠 **Example**:  
You paid ₹1000 via UPI and got "Payment Successful". Even if system crashes, DB remembers it.

> In short: Once committed, data is **safely stored permanently**.

---

### 💡 Final Summary (Thanglish shortcut):
- **A** – “All or nothing”
- **C** – “Correct data only”
- **I** – “Isolated, no mix-up”
- **D** – “Data never disappears”


