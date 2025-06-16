CREATE DATABASE IF NOT EXISTS recofilm;
-- Важно: вернуть 'localhost' для локального доступа, если MySQL запускается на той же машине.
CREATE USER IF NOT EXISTS 'recofilm_user'@'localhost' IDENTIFIED BY 'my_sql_password123';
GRANT ALL PRIVILEGES ON recofilm.* TO 'recofilm_user'@'localhost';
FLUSH PRIVILEGES;