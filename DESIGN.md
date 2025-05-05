## Final Design Document

### **Project Title:**  
**Luxury Product Authenticator** — Verifying Authenticity of Designer Products via Blockchain

---

### **Overview**  
We built a **decentralized blockchain system** to verify the authenticity and ownership history of luxury goods, such as designer handbags. Each product is registered by an official brand and recorded immutably in a distributed blockchain maintained by peer nodes. Users can verify a product’s legitimacy and view its ownership chain through a simple web interface. There are Verify, Register, Transfer and View Blockchain tabs. 

* **Authenticity** – brands register genuine products on‑chain, preventing counterfeits.  
* **Transparency** – owners and prospective buyers can publicly verify an item’s full provenance.  
* **Decentralization** – no single point of failure; the ledger is replicated across independent nodes.  
* **Immutability** – once a registration or ownership transfer is mined into a block, it cannot be altered without invalidating the entire chain.

End‑users interact through a Flask web interface, while back‑end nodes maintain consensus via a lightweight UDP peer‑to‑peer network and Proof‑of‑Work blockchain.

---
## Verify

The Verify page allows anyone—brand representatives, resellers, or buyers—to confirm whether a serial number exists on the blockchain and view its complete provenance.

| Category | Details |
|----------|---------|
| **Purpose** | Authenticate a product by serial number and return its current ownership plus full transaction history. |
| **User Inputs** | *Serial Number* (single text field). |
| **UI Elements** | • Centered heading “Verify a Product”  • A large, full‑width Bootstrap input box with placeholder text (“Serial Number”).   A green **Verify** button beneath the input. |
| **Workflow** | 1. User enters a serial number and clicks Verify.  2. Browser issues an HTTP POST to Flask; Flask sends a UDP `"verify"` packet to the selected node.  3. Node checks the blockchain and responds with `{registered, owner, history}`.  4. Flask renders: *verify_success.html* with owner + timeline **or** *verify_error.html* explaining the failure. |
| **Error Handling** | • Blank serial numbers are blocked client‑side.  • “Product not registered” page returns if the chain has no matching serial. |

---

## Register

This page is used by approved brands to register new products.

| Category | Details |
|----------|---------|
| **Purpose** | Create an immutable on‑chain record for a brand‑new item before it enters the market. |
| **User Inputs** | *Serial Number*, *Model*, *Brand*, *Select Node* (drop‑down: 5001 / 5002 / 5003 / 5009). |
| **UI Elements** | • Heading “Register a New Product”.  • Three stacked Bootstrap input boxes.  • A custom‑styled Bootstrap select for node choice.  • Blue **Register** button. |
| **Workflow** | 1. Form POST → Flask → UDP `"register"` to chosen node.  2. Node checks that serial is unique. If unique, adds a *register* transaction, mines a block, broadcasts it, sends `{status:"accepted"}`.  3. Flask renders *register_success.html* or *register_error.html*. |
| **Validation** | • Client‑side `required` attribute on all fields.  • Server rejects duplicate serials and returns clear error. |

---

## Transfer

Used by current owners to transfer legal ownership to another party.

| Category | Details |
|----------|---------|
| **Purpose** | Append a transfer transaction to the blockchain, updating current owner metadata. |
| **User Inputs** | *Serial Number*, *From Owner/Brand*, *To Owner*. |
| **UI Elements** | • Heading “Transfer Product Ownership”.  • Three full‑width Bootstrap input boxes.  • Blue **Transfer** button. |
| **Workflow** | 1. POST → Flask → UDP `"transfer"` to node.  2. Node verifies product exists and `from_owner` matches blockchain’s current owner.  3. On success, node mines a block containing the transfer transaction, broadcasts it, returns `{status:"accepted"}`.  4. Flask shows *transfer_success.html* or a descriptive failure page. |
| **Validation** | • Reject if product not registered.  • Reject if `from_owner` does not equal chain’s owner. |

---

## View Blockchain (Blockchain Explorer)

The Explorer provides a transparent, human‑readable list of every block and its transactions.

| Category | Details |
|----------|---------|
| **Purpose** | Let users audit the chain, confirm block hashes, and trace transaction chronology. |
| **Data Retrieval** | On page load, Flask sends a UDP `"get_blockchain"` request to a node and receives the full chain (array of block dictionaries). |
| **UI Elements** | • Centered heading “Blockchain Explorer”.  • Each block rendered inside a light‑gray Bootstrap card showing:  &nbsp;&nbsp;– **Block #**  &nbsp;&nbsp;– **Hash** (monospace, truncated by CSS wrapping)  &nbsp;&nbsp;– **Previous Hash**  &nbsp;&nbsp;– **Timestamp** (converted from Unix epoch via Jinja filter)  • “Transactions:” sub‑heading followed by individual white sub‑cards for each transaction. |
| **Navigation** | A persistent navbar remains at the top of every page; a **Back to Home** button appears below the block list. |
| **Styling Notes** | • Cards have subtle shadows and rounded corners to match Bootstrap 5 aesthetic.  • Long hashes wrap to avoid horizontal scrolling.  • A thin vertical connector line separates consecutive cards to emphasize chain linkage. |

---

### **System Architecture**

#### **Socket-Based Peer-to-Peer Network**  
Each node runs a **UDP socket server**, listening on a unique port and identified by its IP and port. Nodes send JSON messages over UDP using three message types:
- `"register"` – to register a new product
- `"transfer"` – to record ownership transfer
- `"verify"` – to query a product's history
- `"new_block"` – to broadcast a newly mined block

#### **Blockchain with Proof of Work**  
- Every node maintains a **local copy of the blockchain**, which contains a chronologically ordered series of product-related transactions.
- Each block includes:
  - Index, Timestamp
  - Previous Block Hash
  - List of Transactions (register, transfer)
  - Nonce & Hash (computed using SHA-256)
- Blocks are mined using a **Proof of Work** system with **dynamic difficulty adjustment**, based on recent mining times, to maintain a target block rate.

---

### **Mining & Consensus**  
- New blocks are mined only when pending transactions exist.
- Each node computes a valid block and broadcasts it to peers.
- Incoming blocks are validated and added to the chain if they pass:
  - Hash validity check
  - Difficulty requirement
  - Correct previous hash reference
- The system supports **fork resolution** by selecting the longest valid chain or the one with more transactions when chains are equal in length.

---

### **User Interface (Flask + Bootstrap)**  
The website is built using Flask and HTML/CSS (Bootstrap) and includes:
- **Home Page:** Overview of the project, navigation to features
- **Register Page:** Brands can enter new product data (serial number, model, brand)
- **Transfer Page:** Owners can submit proof of ownership transfer
- **Verify Page:** Users can query a serial number to check authenticity
- **Blockchain Explorer:** Visualizes all blocks and transactions

Form inputs on each page trigger a POST request, which sends a JSON packet via UDP to a selected node. The system waits for a response (via an ACK mechanism) and renders success/failure pages accordingly.

---

### **Division of Work**
- **Analisa:**  
  Led blockchain implementation, including block structure, transaction validation, mining logic, fork resolution, and dynamic difficulty.
  
- **Michael:**  
  Led frontend development (Flask + Bootstrap), designed all pages and linked them to backend functionality.
  
- **Lyali:**  
  Led networking logic, implemented the UDP socket server and message routing logic between nodes, including block broadcasting and acknowledgment handling.

All team members collaborated across areas to integrate the system and debug the end-to-end flow!

---

### **Enhancements Implemented**
- Real-time UDP communication with live block syncing across nodes
- Dynamic adjustment of mining difficulty
- Blockchain explorer with stylized block and transaction views
- Ownership verification and full transaction history lookup
- Basic fork resolution and protection against invalid blocks

---