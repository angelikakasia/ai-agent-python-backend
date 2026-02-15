INSERT INTO actions (name, category, impact_level)
VALUES
('Read Database', 'read', 'low'),
('Modify Records', 'write', 'medium'),
('Deploy Model', 'deploy', 'high'),
('Delete Files', 'delete', 'irreversible'),
('Call External API', 'external_api', 'medium')
ON CONFLICT DO NOTHING;
