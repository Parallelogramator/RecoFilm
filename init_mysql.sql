CREATE DATABASE IF NOT EXISTS recofilm;
-- Важно: вернуть 'localhost' для локального доступа, если MySQL запускается на той же машине.
-- Replace <your_password> with a strong password before running this script.
CREATE USER IF NOT EXISTS 'recofilm_user'@'localhost' IDENTIFIED BY '<your_password>';
GRANT ALL PRIVILEGES ON recofilm.* TO 'recofilm_user'@'localhost';
FLUSH PRIVILEGES;