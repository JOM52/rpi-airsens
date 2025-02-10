-- Batch pour la création de la base de donnee airsens
-- 10.02.2022 Joseph Metrailler
USE airsens;
-- if exists drop tables (remove comment if needed)
DROP TABLE IF EXISTS airsens_v3;
-- --------------------------------------------------------------
-- table airsens pour local temp hum pres bat 
CREATE TABLE airsens_v3
(
  id INT NOT NULL AUTO_INCREMENT,
  time_stamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  sensor_mac VARCHAR(20) NOT NULL,
  sensor_name VARCHAR(20) NOT NULL,
  sensor_type VARCHAR(20) NOT NULL,
  measure VARCHAR(20) NOT NULL, 
  value DOUBLE NOT NULL,
  PRIMARY KEY (id),
  INDEX i_date (time_stamp),
  INDEX i_id (id),
  UNIQUE(id)
);
