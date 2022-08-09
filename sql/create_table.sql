CREATE TABLE precipitation(
    id SERIAL,
    db_timestamp timestamp PRIMARY KEY DEFAULT NOW(),
    observation_timestamp timestamptz,
    zip_code VARCHAR(5),
    precipitation_mms int
);