DROP TABLE IF EXISTS permissions CASCADE;
DROP TABLE IF EXISTS actions CASCADE;
DROP TABLE IF EXISTS agents CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TYPE IF EXISTS action_category CASCADE;
DROP TYPE IF EXISTS impact_level CASCADE;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TYPE action_category AS ENUM (
    'read',
    'write',
    'deploy',
    'delete',
    'external_api'
);

CREATE TYPE impact_level AS ENUM (
    'low',
    'medium',
    'high',
    'irreversible'
);

CREATE TABLE actions (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category action_category,
    impact_level impact_level
);

CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,
    action_id INTEGER REFERENCES actions(id) ON DELETE CASCADE,
    scope TEXT,
    justification TEXT
);

ALTER TABLE permissions
ADD CONSTRAINT unique_agent_action
UNIQUE (agent_id, action_id);
