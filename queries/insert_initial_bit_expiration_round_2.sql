DELETE FROM BitExpiration;

-- Set the BitExpiration table data
-- The bit expiration is updated every day to potentially extend it to the next
-- tier and extended by an hour for active players.

-- Set the initial bit expiration for new players
INSERT INTO BitExpiration (score, extend) VALUES (0, '+20 minutes');
INSERT INTO BitExpiration (score, extend) VALUES (1, '+1 day');

INSERT INTO BitExpiration (score, extend) VALUES (50, '+3 days');
INSERT INTO BitExpiration (score, extend) VALUES (400, '+7 days');
INSERT INTO BitExpiration (score, extend) VALUES (800, '+14 days');
INSERT INTO BitExpiration (score, extend) VALUES (1600, '+1 months');
