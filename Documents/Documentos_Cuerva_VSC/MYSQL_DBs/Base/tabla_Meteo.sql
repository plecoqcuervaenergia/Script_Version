-- 1. Crear la base de datos (si no existe) y seleccionarla
CREATE DATABASE IF NOT EXISTS `Mediciones_Sensores_Meteo_Cuerva_db`
  DEFAULT CHARACTER SET = utf8mb4
  DEFAULT COLLATE = utf8mb4_spanish_ci;
USE `Mediciones_Sensores_Meteo_Cuerva_db`;

-- 2. Crear la tabla Mediciones_Sensores con comentarios y un índice
CREATE TABLE IF NOT EXISTS `Mediciones_Sensores` (
  `id` INT(11) NOT NULL AUTO_INCREMENT COMMENT 'Identificador único',
  `fecha` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha y hora de la medición',
  `Radiacion_Sucia` DECIMAL(10,2) NULL DEFAULT NULL COMMENT 'Radiación sucia medida',
  `Piranometro` DECIMAL(10,2) NULL DEFAULT NULL COMMENT 'Medición del piranómetro',
  `Temperatura_Ambiente` DECIMAL(10,2) NULL DEFAULT NULL COMMENT 'Temperatura ambiente',
  `Temperatura_Sucia` DECIMAL(10,2) NULL DEFAULT NULL COMMENT 'Temperatura sucia medida',
  `Velocidad_Viento` DECIMAL(10,2) NULL DEFAULT NULL COMMENT 'Velocidad del viento',
  `Humedad` DECIMAL(10,2) NULL DEFAULT NULL COMMENT 'Humedad relativa',
  `Veleta` DECIMAL(10,2) NULL DEFAULT NULL COMMENT 'Dirección del viento medida por la veleta',
  PRIMARY KEY (`id`),
  INDEX idx_fecha (`fecha`)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_spanish_ci
  COMMENT='Tabla para almacenar mediciones de sensores meteorológicos';
