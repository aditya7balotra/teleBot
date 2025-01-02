-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
-- -----------------------------------------------------
-- Schema telebot
-- -----------------------------------------------------
-- DROP SCHEMA IF EXISTS `telebot` ;

-- -----------------------------------------------------
-- Schema telebot
-- -----------------------------------------------------
-- CREATE SCHEMA IF NOT EXISTS `telebot` DEFAULT CHARACTER SET utf8mb3 ;
-- USE `telebot` ;

-- -----------------------------------------------------
-- Table `telebot`.`all_records`
-- -----------------------------------------------------
-- DROP TABLE IF EXISTS `telebot`.`all_records` ;

CREATE TABLE IF NOT EXISTS `telebot`.`all_records` (
  `sno` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(500) NOT NULL,
  `isMovie` TINYINT NOT NULL,
  PRIMARY KEY (`sno`, `name`),
  UNIQUE INDEX `Name_UNIQUE` (`name` ASC) VISIBLE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `telebot`.`moviesdata`
-- -----------------------------------------------------
-- DROP TABLE IF EXISTS `telebot`.`moviesdata` ;

CREATE TABLE IF NOT EXISTS `telebot`.`moviesdata` (
  `sno` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(500) NOT NULL,
  `year` YEAR NULL,
  `quality` VARCHAR(10) NULL,
  `ref` VARCHAR(200) NOT NULL,
  `language` VARCHAR(45) NULL DEFAULT NULL,
  `subtitle` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`sno`, `name`),
  UNIQUE INDEX `sno_UNIQUE` (`sno` ASC) VISIBLE,
  UNIQUE INDEX `ref_UNIQUE` (`ref` ASC) VISIBLE,
  UNIQUE INDEX `name_quality_UNIQUE` (`name` ASC, `quality` ASC) VISIBLE,
  CONSTRAINT `name_movies`
    FOREIGN KEY (`name`)
    REFERENCES `telebot`.`all_records` (`name`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `telebot`.`seriesdata`
-- -----------------------------------------------------
-- DROP TABLE IF EXISTS `telebot`.`seriesdata` ;

CREATE TABLE IF NOT EXISTS `telebot`.`seriesdata` (
  `sno` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(500) NOT NULL,
  `year` YEAR NULL DEFAULT NULL,
  `season` VARCHAR(10) NOT NULL,
  `quality` VARCHAR(10) NULL,
  `episode` VARCHAR(20) NULL DEFAULT 'complete',
  `ref` VARCHAR(200) NOT NULL,
  `language` VARCHAR(45) NULL,
  `subtitle` VARCHAR(45) NULL,
  PRIMARY KEY (`sno`, `name`),
  UNIQUE INDEX `ref_UNIQUE` (`ref` ASC) VISIBLE,
  UNIQUE INDEX `name_quality_UNIQUE` (`name` ASC, `quality` ASC, `season` ASC, `episode` ASC) VISIBLE,
  INDEX `name_idx` (`name` ASC) VISIBLE,
  CONSTRAINT `name_series`
    FOREIGN KEY (`name`)
    REFERENCES `telebot`.`all_records` (`name`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
