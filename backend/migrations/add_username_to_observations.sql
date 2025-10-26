-- Add username column to observations table
ALTER TABLE observation ADD COLUMN username VARCHAR(255);

-- Set default username for existing observations
UPDATE observation SET username = 'client' WHERE username IS NULL;

-- Make username column non-nullable
ALTER TABLE observation ALTER COLUMN username SET NOT NULL;

-- Add index on username
CREATE INDEX ix_observation_username ON observation (username);
