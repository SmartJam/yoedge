CREATE DATABASE acg_yoedge DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;

-- DROP TABLE IF EXISTS `comics`;
CREATE TABLE `comics` (
  `id` char(32) PRIMARY KEY COMMENT '',
  `name` varchar(128) NOT NULL DEFAULT '' COMMENT '',
  `author` varchar(64) COMMENT '',
  `description` text  COMMENT '',
  `coverUrl` text  COMMENT '',
  `status` char(16) COMMENT 'blocked(不会定期查询)',
  `updatedAt` datetime
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- DROP TABLE IF EXISTS `chapters`;
CREATE TABLE `chapters1` (
  `chapterId` char(32) COMMENT '',
  `comicId` char(32),
  `chapterOrder` int,
  `chapterName` varchar(128) NOT NULL DEFAULT '' COMMENT '',
  `addedAt` datetime,
  `status` char(16) COMMENT 'new|downloading|downloaded',
  `pageCount` int,
  PRIMARY KEY pkey(`chapterId`, `comicId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

