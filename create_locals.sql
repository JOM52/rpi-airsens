USE airsens;
DROP TABLE IF EXISTS locals;
-- CREATE TABLE locals
(
  id INT NOT NULL AUTO_INCREMENT,
  time_stamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  local_short VARCHAR(5) NOT NULL,
  local_name VARCHAR(20) NOT NULL,
  PRIMARY KEY (id),
  INDEX i_date (time_stamp),
  INDEX i_id (id),
  UNIQUE(id)
);
