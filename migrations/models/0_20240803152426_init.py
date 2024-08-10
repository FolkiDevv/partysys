from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `servers` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `dis_id` BIGINT NOT NULL,
    `dis_adv_channel_id` BIGINT NOT NULL,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `creatorchannels` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `dis_id` BIGINT NOT NULL,
    `dis_category_id` BIGINT NOT NULL,
    `def_name` VARCHAR(32) NOT NULL  DEFAULT '{user}',
    `def_user_limit` SMALLINT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `server_id` INT NOT NULL,
    CONSTRAINT `fk_creatorc_servers_291b69e2` FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `tcbans` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `dis_creator_id` BIGINT NOT NULL,
    `dis_banned_id` BIGINT NOT NULL,
    `banned` BOOL NOT NULL  DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `server_id` INT NOT NULL,
    CONSTRAINT `fk_tcbans_servers_e5a27309` FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `tempchannels` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `dis_id` BIGINT NOT NULL,
    `dis_creator_id` BIGINT NOT NULL,
    `dis_owner_id` BIGINT NOT NULL,
    `dis_adv_msg_id` BIGINT,
    `deleted` BOOL NOT NULL  DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `server_id` INT NOT NULL,
    CONSTRAINT `fk_tempchan_servers_09c6afc8` FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
