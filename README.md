# 🌊 Odyssey ROV HMI

We’ve just heard word there’s a new deep-sea bioluminescent sea slug, *Bathydevius caudactylus*, spotted off the coast of California, 2000m deep in a trench!
Apparently, it has a starry, mesmerizing effect.

<img src="docs/assets/slug.png" alt="Bathydevius caudactylus" width="100" height="100" />

We need to FIND THIS SLUG!! for *science*, of course.

The mission: Using a HMI to control a ROV, the Odyssey, navigate to and collect a rare bioluminescent sea slug (*Bathydevius caudactylus*), and return it to a collection pod. 

---

## 📂 Project Structure
```
odyssey-rov-hmi/
├── backend/             # FastAPI app
├── docs/                # HMI Philosophy, Design and Overview
├── frontend/            # React + Vite + TS + Tailwind v4 app
├── proto/               # gRPC contract files
├── docker-compose.yml   # Dev orchestrator (backend + frontend with hot reload)
└── .dockerignore
```
---

## 🔑 Docs

- **[Philosophy](docs/philosophy.md)**: The "why" — mission, operator goals, and design principles.
- **[Style Guide](docs/style-guide.md)**: The "how" — colors, typography, icons, and layout rules.
- **[Toolkit](docs/toolkit.md)**: The "what" - Reusable UI components, core objects, and gRPC services.

---

## 🔑 Backend

(Subject to change)

---

## 🔑 Frontend

(Subject to change)

---

## 🔑 Protocol Buffers

(Subject to change)

---

## 🔑 Docker & Dev Environment

- **Compose services**:  
  - **backend** → Python 3.11 slim, runs FastAPI with autoreload  
  - **frontend** → Node 22 alpine, runs Vite dev server with hot reload  
- **Access**:  
  - Frontend → [http://localhost:5173](http://localhost:5173)  
  - Backend → [http://localhost:8000](http://localhost:8000)  

---

## 🚀 Quickstart
Ensure you have docker installed

```bash
# Start both backend + frontend with hot reload
docker compose up

```
⸻
