-- Initial fictional classroom data for a new expedia-copy SQLite database.
-- The transaction and conflict handling make simultaneous first starts safe.
BEGIN IMMEDIATE;

INSERT OR IGNORE INTO hotels
    (hotel_id, hotel_name, city, state, nightly_rate_usd)
VALUES
    ('H001', 'Harbor Lantern Hotel', 'Boston', 'MA', 150),
    ('H002', 'Maple Square Inn', 'Boston', 'MA', 120),
    ('H003', 'Metro Garden Hotel', 'New York', 'NY', 200),
    ('H004', 'Riverside Studio Hotel', 'New York', 'NY', 175),
    ('H005', 'Liberty Lane Inn', 'Philadelphia', 'PA', 110),
    ('H006', 'Museum Walk Hotel', 'Philadelphia', 'PA', 140),
    ('H007', 'Capitol Grove Hotel', 'Washington', 'DC', 160),
    ('H008', 'Valley Trail Inn', 'State College', 'PA', 100);

INSERT OR IGNORE INTO users (user_id, display_name)
VALUES
    ('U001', 'Demo Traveler 1'),
    ('U002', 'Demo Traveler 2'),
    ('U003', 'Demo Traveler 3'),
    ('U004', 'Demo Traveler 4'),
    ('U005', 'Demo Traveler 5'),
    ('U006', 'Demo Traveler 6'),
    ('U007', 'Demo traveler 21457'),
    ('U008', 'Vincenzo Fiorenza'),
    ('U009', 'Jehosaphat Saranghetti'),
    ('U010', 'Tester Lester'),
    ('U011', 'Demo Traveler 45');

INSERT OR IGNORE INTO trips
    (trip_id, hotel_id, trip_name, check_in, check_out)
VALUES
    ('T001', 'H001', 'Boston Harbor Weekend', '2026-09-18', '2026-09-20'),
    ('T002', 'H002', 'Boston City Break', '2026-09-18', '2026-09-21'),
    ('T003', 'H003', 'New York Museum Weekend', '2026-09-25', '2026-09-27'),
    ('T004', 'H004', 'New York Riverside Stay', '2026-09-25', '2026-09-28'),
    ('T005', 'H005', 'Philadelphia History Weekend', '2026-09-18', '2026-09-20'),
    ('T006', 'H006', 'Philadelphia Arts Break', '2026-10-02', '2026-10-05'),
    ('T007', 'H007', 'Washington Museum Weekend', '2026-09-25', '2026-09-27'),
    ('T008', 'H008', 'State College Trail Weekend', '2026-10-02', '2026-10-04'),
    ('T009', 'H001', 'Boston Autumn Weekend', '2026-10-02', '2026-10-04'),
    ('T010', 'H002', 'Boston October Break', '2026-10-09', '2026-10-12'),
    ('T011', 'H003', 'New York October Weekend', '2026-10-09', '2026-10-11'),
    ('T012', 'H007', 'Washington Autumn Break', '2026-10-09', '2026-10-12'),
    ('T013', 'H001', 'Harbor Lantern Hotel stay', '2026-11-21', '2026-11-28'),
    ('T014', 'H005', 'Liberty Lane Inn stay', '2026-09-23', '2026-09-25'),
    ('T015', 'H003', 'Metro Garden Hotel stay', '2026-09-01', '2026-09-03'),
    ('T016', 'H003', 'Metro Garden Hotel stay', '2026-09-01', '2027-08-30'),
    ('T017', 'H003', 'Metro Garden Hotel stay', '2026-09-22', '2026-09-25'),
    ('T018', 'H003', 'Metro Garden Hotel stay', '2026-09-01', '2026-09-30');

INSERT OR IGNORE INTO bookings
    (booking_id, user_id, trip_id, booked_on, status)
VALUES
    ('B001', 'U001', 'T001', '2026-09-01', 'confirmed'),
    ('B002', 'U001', 'T005', '2026-09-02', 'cancelled'),
    ('B003', 'U002', 'T003', '2026-09-03', 'confirmed'),
    ('B004', 'U003', 'T007', '2026-09-04', 'confirmed'),
    ('B005', 'U004', 'T002', '2026-09-05', 'confirmed'),
    ('B006', 'U005', 'T008', '2026-09-07', 'cancelled'),
    ('B007', 'U007', 'T013', '2026-09-16', 'canceled'),
    ('B008', 'U001', 'T014', '2026-09-16', 'canceled'),
    ('B009', 'U008', 'T015', '2026-09-16', 'canceled'),
    ('B010', 'U009', 'T016', '2026-09-16', 'confirmed'),
    ('B011', 'U010', 'T017', '2026-09-21', 'canceled'),
    ('B012', 'U011', 'T018', '2026-09-21', 'canceled');

INSERT OR IGNORE INTO app_metadata (key, value)
VALUES ('initial_seed_v1', 'complete');

COMMIT;
