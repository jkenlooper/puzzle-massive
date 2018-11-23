/* This only makes the bit icons not assigned to the player anymore. It doesn't
 * affect the old 'run' app and how it stores bit icon registration internally.
 * A restart of the 'run' app is required to make these released bit icons
 * available again.
 */
-- Currently, this is executed each time the puzzle starts
update User set icon = '' where icon != '' and (
    (score = 0 and m_date < date('now', '-1 hour')) or
    (score <= 5 and m_date < date('now', '-10 hour')) or
    (score <= 15 and m_date < date('now', '-2 days')) or
    (score <= 25 and m_date < date('now', '-3 days')) or
    (score <= 35 and m_date < date('now', '-4 days')) or
    (score <= 55 and m_date < date('now', '-8 days')) or
    (score <= 65 and m_date < date('now', '-16 days')) or
    (score <= 165 and m_date < date('now', '-1 months')) or
    (score <= 265 and m_date < date('now', '-2 months')) or
    (score <= 365 and m_date < date('now', '-3 months')) or
    (score <= 453 and m_date < date('now', '-4 months')) or
    (score <= (select score from User where icon != '' limit 1 offset 15) and m_date < date('now', '-5 months'))
);
