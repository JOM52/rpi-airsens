-- Batch pour la création de la base de donnee airsens
-- 10.02.2022 Joseph Metrailler
-- --------------------------------------------------------------
-- si elle existe, supprimer la db mqtt existante et la recreer
-- DROP DATABASE IF EXISTS airsens;
-- CREATE DATABASE airsens;
-- USE airsens;
-- if exists drop tables (remove comment if needed)
-- DROP TABLE IF EXISTS airsens;
-- --------------------------------------------------------------
-- table airsens pour local temp hum pres bat 
CREATE TABLE airsens
(
  id INT NOT NULL AUTO_INCREMENT,
  time_stamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  local VARCHAR(20) NOT NULL,
  temp DOUBLE NOT NULL,
  hum DOUBLE NOT NULL,
  pres DOUBLE NOT NULL,
  ubat double NOT NULL,
  charge_bat DOUBLE NOT NULL,
  PRIMARY KEY (id),
  INDEX i_date (time_stamp),
  INDEX i_id (id),
  UNIQUE(id)
);
