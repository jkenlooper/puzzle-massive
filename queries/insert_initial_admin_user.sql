-- Insert the anonymous player (ADMIN_USER_ID)
INSERT OR IGNORE INTO User (id, login, password, points, score, m_date) VALUES (1, 'none', 'none', 1300, 0, datetime('now'));
