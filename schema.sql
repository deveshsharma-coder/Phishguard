-- =============================================
-- PhishGuard Database Schema
-- Run: mysql -u root -p < schema.sql
-- =============================================

CREATE DATABASE IF NOT EXISTS phishguard_db
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE phishguard_db;

-- Users table: stores all registered accounts
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name          VARCHAR(100) NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scores table: stores quiz results per user
CREATE TABLE IF NOT EXISTS scores (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT NOT NULL,
    score           INT NOT NULL,
    total_questions INT NOT NULL,
    difficulty      VARCHAR(20) NOT NULL,
    accuracy        DECIMAL(5,2) NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_scores_user ON scores(user_id);
CREATE INDEX IF NOT EXISTS idx_scores_date ON scores(created_at);
