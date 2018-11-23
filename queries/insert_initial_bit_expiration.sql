DROP TABLE IF EXISTS Bit;

-- Set the BitExpiration table data
-- The bit expiration is updated every day to potentially extend it to the next
-- tier and extended by an hour for active players.

-- Match the existing bit icon expiration setup from 1.6
INSERT INTO BitExpiration (score, extend) VALUES (1, '+1 hour');
INSERT INTO BitExpiration (score, extend) VALUES (5, '+10 hours');
INSERT INTO BitExpiration (score, extend) VALUES (15, '+2 days');
INSERT INTO BitExpiration (score, extend) VALUES (25, '+3 days');
INSERT INTO BitExpiration (score, extend) VALUES (35, '+4 days');
INSERT INTO BitExpiration (score, extend) VALUES (55, '+8 days');
INSERT INTO BitExpiration (score, extend) VALUES (65, '+16 days');
INSERT INTO BitExpiration (score, extend) VALUES (165, '+1 months');
INSERT INTO BitExpiration (score, extend) VALUES (265, '+2 months');
INSERT INTO BitExpiration (score, extend) VALUES (365, '+3 months');
INSERT INTO BitExpiration (score, extend) VALUES (453, '+4 months');
INSERT INTO BitExpiration (score, extend) VALUES (2058, '+5 months');
