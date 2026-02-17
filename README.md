<img width="715" height="280" alt="Image" src="https://github.com/user-attachments/assets/188944a1-3ac7-4c14-9f11-fcf13225e23e" />


# Agentic AI (Backend)

A RESTful API for managing users, AI agents, actions, permissions, and impact analysis for the **Agentic AI** application.

Built with Python, Flask, and PostgreSQL.

Agentic AI's backend handles authentication, data persistence, authorization, permission management, and automatic impact calculation to help users understand agent authority before execution.

---

## Frontend Repository

The frontend repository for this project can be found here:  

1) Frontend: [GitHub Repository](https://github.com/angelikakasia/ai-agent-javascript-frontend)

2) Frontend Live: [Agentic AI - Vercel](https://ai-agent-javascript-frontend.vercel.app/) 

---

## Tech Stack

- Python
- Flask
- PostgreSQL
- psycopg2
- JSON Web Tokens (JWT)
- bcrypt
- python-dotenv
- Flask-CORS
- gunicorn

---

## Getting Started

Install dependencies:
pipenv shell
pipenv install flask flask-cors python-dotenv psycopg2-binary pyjwt bcrypt gunicorn
Create a `.env` file:
POSTGRES_DATABASE=your_database_url
JWT_SECRET=your_secret
PORT=5000

## Run the server:
python3 app.py


---

## Features

- User authentication (sign up, sign in)
- JWT-based authorization
- Owner-only access to agent data
- Full CRUD for agents
- Assign and remove actions from agents
- Automatic impact aggregation (low, medium, high, irreversible)
- Authority overview per agent

Guest users cannot create, edit, or delete data.


## Future Plan - Next Steps
- Add threat modeling view (authority path visualization)
- Implement blast radius simulation
- Add environment-based permissions (dev / staging / prod)
- Integrate with cloud IAM for real-world mapping
- Add a test button - “what-if” permission combinations safely
---

## Data Models

### User
- id
- email
- password_hash

### Agent
- id
- name
- description
- user_id

### Action
- id
- name
- category
- impact_level

### Permission
- id
- agent_id
- action_id

---

## Middleware

- JWT verification middleware protects all non-auth routes
- Authorization ensures users can only modify their own agents

---

## This project was built by:

Angelika 
