# Agent AI (Backend)

A RESTful API for managing users, AI agents, actions, permissions, and impact analysis for the **Agent AI** application.

Built with Python, Flask, and PostgreSQL.

Agentic AI's backend handles authentication, data persistence, authorization, permission management, and automatic impact calculation to help users understand agent authority before execution.

---

## Frontend Repository

The frontend repository for this project can be found here:  
Frontend:[Agentic AI](https://ai-agent-javascript-frontend.vercel.app/) 

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
