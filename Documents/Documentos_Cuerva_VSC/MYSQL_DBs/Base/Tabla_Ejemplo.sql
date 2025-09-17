-- 1. Crear la base de datos (si no existe) y seleccionarla
CREATE DATABASE IF NOT EXISTS `Mediciones_Fotovoltaica_CN_db`
  DEFAULT CHARACTER SET = utf8mb4
  DEFAULT COLLATE = utf8mb4_spanish_ci;
USE `Mediciones_Fotovoltaica_CN_db`;

-- 2. Crear la tabla Mediciones_Sensores
CREATE TABLE IF NOT EXISTS `Mediciones_Sensores` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `fecha` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `Radiacion_Placas` DECIMAL(5,1) NULL DEFAULT NULL,
  `Temperatura_Placas` DECIMAL(4,1) NULL DEFAULT NULL,
  `Radiacion_Sensor` DECIMAL(5,1) NULL DEFAULT NULL,
  `Temperatura_Sensor` DECIMAL(4,1) NULL DEFAULT NULL,
  `Potencia_Activa` DECIMAL(8,1) NULL DEFAULT NULL,
  `Generación_Total` DECIMAL(9,2) NULL DEFAULT NULL,
  `Potencia_Activa_Pos_M1` DECIMAL(9,1) NULL DEFAULT NULL,
  `Potencia_Activa_Neg_M1` DECIMAL(9,1) NULL DEFAULT NULL,
  `Potencia_Activa_Pos_M2` DECIMAL(9,1) NULL DEFAULT NULL,
  `Potencia_Activa_Neg_M2` DECIMAL(9,1) NULL DEFAULT NULL,
  `Potencia_Activa_Pos_M3` DECIMAL(9,1) NULL DEFAULT NULL,
  `Potencia_Activa_Neg_M3` DECIMAL(9,1) NULL DEFAULT NULL,
  `Rendimiento_FV` DECIMAL(5,1) NULL DEFAULT NULL,
  `restaurante_total` DECIMAL(10,1) NULL DEFAULT NULL,
  `restaurante_red` DECIMAL(10,1) NULL DEFAULT NULL,
  `restaurante_fv` DECIMAL(10,1) NULL DEFAULT NULL,
  `coste_red` DECIMAL(10,2) NULL DEFAULT NULL,
  `coste_fv` DECIMAL(10,2) NULL DEFAULT NULL,
  `coste_total` DECIMAL(10,2) NULL DEFAULT NULL,
  `CN_red` DECIMAL(10,1) NULL DEFAULT NULL,
  `CN_fv` DECIMAL(10,1) NULL DEFAULT NULL,
  `CN_Total` DECIMAL(10,1) NULL DEFAULT NULL,
  `coste_CN_fv` DECIMAL(10,2) NULL DEFAULT NULL,
  `mes_restaurante_fv` DECIMAL(10,2) NULL DEFAULT NULL,
  `mes_restaurante_red` DECIMAL(10,2) NULL DEFAULT NULL,
  `mes_restaurante_total` DECIMAL(10,2) NULL DEFAULT NULL,
  `mes_Club_Nautico_fv` DECIMAL(10,2) NULL DEFAULT NULL,
  `mes_Club_Nautico_red` DECIMAL(10,2) NULL DEFAULT NULL,
  `mes_Club_Nautico_total` DECIMAL(10,2) NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_spanish_ci;
