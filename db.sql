CREATE DATABASE  IF NOT EXISTS `kindergarten_db` 
USE `kindergarten_db`;

DROP TABLE IF EXISTS `classes`;

CREATE TABLE `classes` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `teacher_id` int unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_classes_teacher` (`teacher_id`),
  CONSTRAINT `fk_classes_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
;



LOCK TABLES `classes` WRITE;
INSERT INTO `classes` VALUES (1,'Lá 1',2),(2,'lớp chồi',3),(3,'lớp mầm',4),(4,'Lớp Chồi 1',5),(5,'Lớp Chồi 2',6),(6,'Lớp Chồi 3',7),(7,'Lớp Chồi 4',8),(8,'Lớp Chồi 5',9);
UNLOCK TABLES;


DROP TABLE IF EXISTS `health_records`;
CREATE TABLE `health_records` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `student_id` int unsigned NOT NULL,
  `record_date` date NOT NULL,
  `weight_kg` decimal(5,2) DEFAULT NULL,
  `temperature_c` decimal(4,1) NOT NULL,
  `note` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_health_student_date` (`student_id`,`record_date`),
  KEY `idx_health_date` (`record_date`),
  CONSTRAINT `fk_health_student` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

LOCK TABLES `health_records` WRITE;
INSERT INTO `health_records` VALUES (1,1,'2025-12-21',15.00,36.8,'Bình thường'),(2,1,'2025-12-19',20.00,39.0,'sốt nặng'),(3,2,'2025-12-19',35.00,35.0,'khỏe');
UNLOCK TABLES;


DROP TABLE IF EXISTS `invoices`;
CREATE TABLE `invoices` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `student_id` int unsigned NOT NULL,
  `billing_month` char(7) NOT NULL,
  `tuition_fee` int unsigned NOT NULL,
  `meal_unit_price` int unsigned NOT NULL,
  `meal_days` int unsigned NOT NULL,
  `total_amount` int unsigned NOT NULL,
  `status` enum('UNPAID','PAID') NOT NULL DEFAULT 'UNPAID',
  `paid_at` datetime DEFAULT NULL,
  `collected_by` int unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_invoice_student_month` (`student_id`,`billing_month`),
  KEY `idx_invoice_month_status` (`billing_month`,`status`),
  KEY `fk_invoices_collected_by` (`collected_by`),
  KEY `idx_invoices_month_status` (`billing_month`,`status`),
  CONSTRAINT `fk_invoice_student` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_invoices_collected_by` FOREIGN KEY (`collected_by`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

LOCK TABLES `invoices` WRITE;
INSERT INTO `invoices` VALUES (1,1,'2025-12',1500000,25000,6,1650000,'PAID','2025-12-21 17:51:47',2),(2,2,'2025-12',1500000,25000,5,1625000,'PAID','2025-12-21 17:50:40',2),(3,1,'2026-1',1500000,25000,0,1500000,'UNPAID',NULL,NULL),(4,1,'2025-11',1500000,25000,0,1500000,'UNPAID',NULL,NULL),(5,51,'2025-12',1500000,25000,0,1500000,'PAID','2025-12-21 20:15:19',2);
UNLOCK TABLES;

DROP TABLE IF EXISTS `meal_logs`;
CREATE TABLE `meal_logs` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `student_id` int unsigned NOT NULL,
  `log_date` date NOT NULL,
  `ate` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_meal_student_date` (`student_id`,`log_date`),
  KEY `idx_meal_date` (`log_date`),
  CONSTRAINT `fk_meal_student` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

LOCK TABLES `meal_logs` WRITE;
INSERT INTO `meal_logs` VALUES (1,1,'2025-12-01',1),(2,2,'2025-12-01',1),(3,1,'2025-12-02',1),(4,2,'2025-12-02',1),(5,1,'2025-12-03',1),(6,2,'2025-12-03',1),(7,1,'2025-12-04',1),(8,2,'2025-12-04',1),(9,1,'2025-12-05',1),(10,2,'2025-12-05',1),(11,1,'2025-12-21',1),(12,2,'2025-12-21',1),(13,1,'2025-12-22',1),(14,2,'2025-12-22',1),(15,1,'2025-12-30',1),(16,2,'2025-12-30',1),(17,3,'2025-12-21',0),(18,11,'2025-12-21',0),(19,19,'2025-12-21',0),(20,27,'2025-12-21',0),(21,35,'2025-12-21',1),(22,43,'2025-12-21',1),(23,51,'2025-12-21',0);
UNLOCK TABLES;

DROP TABLE IF EXISTS `settings`;
CREATE TABLE `settings` (
  `id` tinyint unsigned NOT NULL,
  `tuition_fee_monthly` int unsigned NOT NULL,
  `meal_price_per_day` int unsigned NOT NULL,
  `max_students_per_class` int unsigned NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

LOCK TABLES `settings` WRITE;
INSERT INTO `settings` VALUES (1,1500000,25000,25);
UNLOCK TABLES;

DROP TABLE IF EXISTS `students`;
CREATE TABLE `students` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `class_id` int unsigned NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `dob` date NOT NULL,
  `gender` enum('M','F') NOT NULL,
  `parent_name` varchar(100) NOT NULL,
  `parent_phone` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_students_class` (`class_id`),
  KEY `idx_students_class_id` (`class_id`),
  CONSTRAINT `fk_students_class` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=53 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

LOCK TABLES `students` WRITE;
INSERT INTO `students` VALUES (1,1,'Nguyễn Gia Hân','2020-08-10','F','Nguyễn Triều Nguyệt','0965544789'),(2,1,'Trần Minh Khang','2020-03-05','M','Trần Thị Hoa','0901234567'),(3,1,'Học sinh 01','2021-12-24','M','Phụ huynh 01','0910000001'),(4,2,'Học sinh 02','2021-12-17','F','Phụ huynh 02','0910000002'),(5,3,'Học sinh 03','2021-12-10','M','Phụ huynh 03','0910000003'),(6,4,'Học sinh 04','2021-12-03','F','Phụ huynh 04','0910000004'),(7,5,'Học sinh 05','2021-11-26','M','Phụ huynh 05','0910000005'),(8,6,'Học sinh 06','2021-11-19','F','Phụ huynh 06','0910000006'),(9,7,'Học sinh 07','2021-11-12','M','Phụ huynh 07','0910000007'),(10,8,'Học sinh 08','2021-11-05','F','Phụ huynh 08','0910000008'),(11,1,'Học sinh 09','2021-10-29','M','Phụ huynh 09','0910000009'),(12,2,'Học sinh 10','2021-10-22','F','Phụ huynh 10','0910000010'),(13,3,'Học sinh 11','2021-10-15','M','Phụ huynh 11','0910000011'),(14,4,'Học sinh 12','2021-10-08','F','Phụ huynh 12','0910000012'),(15,5,'Học sinh 13','2021-10-01','M','Phụ huynh 13','0910000013'),(16,6,'Học sinh 14','2021-09-24','F','Phụ huynh 14','0910000014'),(17,7,'Học sinh 15','2021-09-17','M','Phụ huynh 15','0910000015'),(18,8,'Học sinh 16','2021-09-10','F','Phụ huynh 16','0910000016'),(19,1,'Học sinh 17','2021-09-03','M','Phụ huynh 17','0910000017'),(20,2,'Học sinh 18','2021-08-27','F','Phụ huynh 18','0910000018'),(21,3,'Học sinh 19','2021-08-20','M','Phụ huynh 19','0910000019'),(22,4,'Học sinh 20','2021-08-13','F','Phụ huynh 20','0910000020'),(23,5,'Học sinh 21','2021-08-06','M','Phụ huynh 21','0910000021'),(24,6,'Học sinh 22','2021-07-30','F','Phụ huynh 22','0910000022'),(25,7,'Học sinh 23','2021-07-23','M','Phụ huynh 23','0910000023'),(26,8,'Học sinh 24','2021-07-16','F','Phụ huynh 24','0910000024'),(27,1,'Học sinh 25','2021-07-09','M','Phụ huynh 25','0910000025'),(28,2,'Học sinh 26','2021-07-02','F','Phụ huynh 26','0910000026'),(29,3,'Học sinh 27','2021-06-25','M','Phụ huynh 27','0910000027'),(30,4,'Học sinh 28','2021-06-18','F','Phụ huynh 28','0910000028'),(31,5,'Học sinh 29','2021-06-11','M','Phụ huynh 29','0910000029'),(32,6,'Học sinh 30','2021-06-04','F','Phụ huynh 30','0910000030'),(33,7,'Học sinh 31','2021-05-28','M','Phụ huynh 31','0910000031'),(34,8,'Học sinh 32','2021-05-21','F','Phụ huynh 32','0910000032'),(35,1,'Học sinh 33','2021-05-14','M','Phụ huynh 33','0910000033'),(36,2,'Học sinh 34','2021-05-07','F','Phụ huynh 34','0910000034'),(37,3,'Học sinh 35','2021-04-30','M','Phụ huynh 35','0910000035'),(38,4,'Học sinh 36','2021-04-23','F','Phụ huynh 36','0910000036'),(39,5,'Học sinh 37','2021-04-16','M','Phụ huynh 37','0910000037'),(40,6,'Học sinh 38','2021-04-09','F','Phụ huynh 38','0910000038'),(41,7,'Học sinh 39','2021-04-02','M','Phụ huynh 39','0910000039'),(42,8,'Học sinh 40','2021-03-26','F','Phụ huynh 40','0910000040'),(43,1,'Học sinh 41','2021-03-19','M','Phụ huynh 41','0910000041'),(44,2,'Học sinh 42','2021-03-12','F','Phụ huynh 42','0910000042'),(45,3,'Học sinh 43','2021-03-05','M','Phụ huynh 43','0910000043'),(46,4,'Học sinh 44','2021-02-26','F','Phụ huynh 44','0910000044'),(47,5,'Học sinh 45','2021-02-19','M','Phụ huynh 45','0910000045'),(48,6,'Học sinh 46','2021-02-12','F','Phụ huynh 46','0910000046'),(49,7,'Học sinh 47','2021-02-05','M','Phụ huynh 47','0910000047'),(50,8,'Học sinh 48','2021-01-29','F','Phụ huynh 48','0910000048'),(51,1,'Học sinh 49','2021-01-22','M','Phụ huynh 49','0910000049'),(52,2,'Học sinh 50','2021-01-15','F','Phụ huynh 50','0910000050');
UNLOCK TABLES;

DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` enum('ADMIN','TEACHER') NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

LOCK TABLES `users` WRITE;
INSERT INTO `users` VALUES (1,'admin','scrypt:32768:8:1$nnDGwLPDOtBYsPEC$e64764f6aa3cde202d6a378e018d243fe1a683b44504aa93ebc90d0093b19b3b89dbf62f1cec0c56416e75a8d35e26cdd5cde5217641a7970571b30567ef32b0','ADMIN','Administrator','0900000000'),(2,'teacher1','scrypt:32768:8:1$l3LSHAfTDV4sd7Rf$6a8d6b8b5fd287ece626eb5aeb97f93bf68bfa4d4f71cb1ae6060abd4b231b8510ded186fd4e4b7c45d42863564f58b8f1b5fb57ba352a729bcb295f51749f5a','TEACHER','Teacher One','0911111111'),(3,'teacher2','scrypt:32768:8:1$l3LSHAfTDV4sd7Rf$6a8d6b8b5fd287ece626eb5aeb97f93bf68bfa4d4f71cb1ae6060abd4b231b8510ded186fd4e4b7c45d42863564f58b8f1b5fb57ba352a729bcb295f51749f5a','TEACHER','thien','012345678'),(4,'teacher3','scrypt:32768:8:1$l3LSHAfTDV4sd7Rf$6a8d6b8b5fd287ece626eb5aeb97f93bf68bfa4d4f71cb1ae6060abd4b231b8510ded186fd4e4b7c45d42863564f58b8f1b5fb57ba352a729bcb295f51749f5a','TEACHER','danh','0392941671'),(5,'teacher4','scrypt:32768:8:1$l3LSHAfTDV4sd7Rf$6a8d6b8b5fd287ece626eb5aeb97f93bf68bfa4d4f71cb1ae6060abd4b231b8510ded186fd4e4b7c45d42863564f58b8f1b5fb57ba352a729bcb295f51749f5a','TEACHER','Giáo viên 4','0900000004'),(6,'teacher5','scrypt:32768:8:1$l3LSHAfTDV4sd7Rf$6a8d6b8b5fd287ece626eb5aeb97f93bf68bfa4d4f71cb1ae6060abd4b231b8510ded186fd4e4b7c45d42863564f58b8f1b5fb57ba352a729bcb295f51749f5a','TEACHER','Giáo viên 5','0900000005'),(7,'teacher6','scrypt:32768:8:1$l3LSHAfTDV4sd7Rf$6a8d6b8b5fd287ece626eb5aeb97f93bf68bfa4d4f71cb1ae6060abd4b231b8510ded186fd4e4b7c45d42863564f58b8f1b5fb57ba352a729bcb295f51749f5a','TEACHER','Giáo viên 6','0900000006'),(8,'teacher7','scrypt:32768:8:1$l3LSHAfTDV4sd7Rf$6a8d6b8b5fd287ece626eb5aeb97f93bf68bfa4d4f71cb1ae6060abd4b231b8510ded186fd4e4b7c45d42863564f58b8f1b5fb57ba352a729bcb295f51749f5a','TEACHER','Giáo viên 7','0900000007'),(9,'teacher8','scrypt:32768:8:1$l3LSHAfTDV4sd7Rf$6a8d6b8b5fd287ece626eb5aeb97f93bf68bfa4d4f71cb1ae6060abd4b231b8510ded186fd4e4b7c45d42863564f58b8f1b5fb57ba352a729bcb295f51749f5a','TEACHER','Giáo viên 8','0900000008'),(10,'teacher9','scrypt:32768:8:1$l3LSHAfTDV4sd7Rf$6a8d6b8b5fd287ece626eb5aeb97f93bf68bfa4d4f71cb1ae6060abd4b231b8510ded186fd4e4b7c45d42863564f58b8f1b5fb57ba352a729bcb295f51749f5a','TEACHER','Giáo viên 9','0900000009'),(11,'teacher10','scrypt:32768:8:1$l3LSHAfTDV4sd7Rf$6a8d6b8b5fd287ece626eb5aeb97f93bf68bfa4d4f71cb1ae6060abd4b231b8510ded186fd4e4b7c45d42863564f58b8f1b5fb57ba352a729bcb295f51749f5a','TEACHER','Giáo viên 10','0900000010'),(12,'teacher11','scrypt:32768:8:1$l3LSHAfTDV4sd7Rf$6a8d6b8b5fd287ece626eb5aeb97f93bf68bfa4d4f71cb1ae6060abd4b231b8510ded186fd4e4b7c45d42863564f58b8f1b5fb57ba352a729bcb295f51749f5a','TEACHER','Giáo viên 11','0900000011'),(13,'teacher12','scrypt:32768:8:1$l3LSHAfTDV4sd7Rf$6a8d6b8b5fd287ece626eb5aeb97f93bf68bfa4d4f71cb1ae6060abd4b231b8510ded186fd4e4b7c45d42863564f58b8f1b5fb57ba352a729bcb295f51749f5a','TEACHER','Giáo viên 12','0900000012'),(14,'teacher13','scrypt:32768:8:1$l3LSHAfTDV4sd7Rf$6a8d6b8b5fd287ece626eb5aeb97f93bf68bfa4d4f71cb1ae6060abd4b231b8510ded186fd4e4b7c45d42863564f58b8f1b5fb57ba352a729bcb295f51749f5a','TEACHER','Giáo viên 13','0900000013');
UNLOCK TABLES;
