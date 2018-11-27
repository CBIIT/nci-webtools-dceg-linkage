-- Drop api_users table if exists previously
DROP TABLE IF EXISTS api_users;
-- DROP api_log table if exists previously
DROP TABLE IF EXISTS api_log;
-- Create api_users table
CREATE TABLE api_users (`first_name` TEXT, `last_name` TEXT, `email` TEXT, `institution` TEXT, `token` TEXT, `registered` DATETIME, `blocked` INTEGER);
-- Create api_log table
CREATE TABLE api_log (`token` TEXT, `module` TEXT, `accessed` DATETIME);