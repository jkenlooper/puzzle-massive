-- The bit expiration is updated every day to potentially extend it to the next
-- tier. These values are inserted from the BIT_ICON_EXPIRATION value in site.cfg
INSERT INTO BitExpiration (score, extend) VALUES (:score, :extend);
