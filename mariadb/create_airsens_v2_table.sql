-- Batch pour la création de la base de donnee airsens
-- 10.02.2022 Joseph Metrailler
USE airsens;
-- if exists drop tables (remove comment if needed)
-- DROP TABLE IF EXISTS airsens_v2;
-- --------------------------------------------------------------
-- table airsens pour local temp hum pres bat 
CREATE TABLE airsens_v2
(
  id INT NOT NULL AUTO_INCREMENT,
  time_stamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  loc VARCHAR(20) NOT NULL,
  name VARCHAR(20) NOT NULL, 
  val DOUBLE NOT NULL,
  PRIMARY KEY (id),
  INDEX i_date (time_stamp),
  INDEX i_id (id),
  UNIQUE(id)
);
