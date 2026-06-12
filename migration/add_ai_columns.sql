-- Run this on your existing symphony database to add AI analysis columns.
-- Safe to run multiple times (uses IF NOT EXISTS pattern via stored procedure).
-- Usage: mysql -u root -p symphony < migration/add_ai_columns.sql

DELIMITER $$

DROP PROCEDURE IF EXISTS add_ai_columns$$
CREATE PROCEDURE add_ai_columns()
BEGIN
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'call_log'
                   AND COLUMN_NAME = 'transcript') THEN
        ALTER TABLE call_log ADD COLUMN transcript TEXT AFTER duration;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'call_log'
                   AND COLUMN_NAME = 'ai_category') THEN
        ALTER TABLE call_log ADD COLUMN ai_category VARCHAR(50) DEFAULT NULL;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'call_log'
                   AND COLUMN_NAME = 'ai_sentiment') THEN
        ALTER TABLE call_log ADD COLUMN ai_sentiment VARCHAR(20) DEFAULT NULL;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'call_log'
                   AND COLUMN_NAME = 'ai_model_mentioned') THEN
        ALTER TABLE call_log ADD COLUMN ai_model_mentioned VARCHAR(150) DEFAULT NULL;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'call_log'
                   AND COLUMN_NAME = 'ai_resolved') THEN
        ALTER TABLE call_log ADD COLUMN ai_resolved TINYINT(1) DEFAULT 0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'call_log'
                   AND COLUMN_NAME = 'ai_summary') THEN
        ALTER TABLE call_log ADD COLUMN ai_summary TEXT DEFAULT NULL;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'call_log'
                   AND COLUMN_NAME = 'ai_confidence') THEN
        ALTER TABLE call_log ADD COLUMN ai_confidence DECIMAL(4,2) DEFAULT NULL;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'call_log'
                   AND COLUMN_NAME = 'ai_analyzed_at') THEN
        ALTER TABLE call_log ADD COLUMN ai_analyzed_at DATETIME DEFAULT NULL;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'call_log'
                   AND COLUMN_NAME = 'ai_error') THEN
        ALTER TABLE call_log ADD COLUMN ai_error TEXT DEFAULT NULL;
    END IF;
END$$

DELIMITER ;
CALL add_ai_columns();
DROP PROCEDURE add_ai_columns;

SELECT 'Migration complete.' AS status;
SHOW COLUMNS FROM call_log LIKE 'ai_%';
