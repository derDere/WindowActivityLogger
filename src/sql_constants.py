"""
SQL constants for common database operations.
"""

# Default query shown when opening the SQL window
DEFAULT_QUERY = """/* WARNING: Only modify these SQL queries if you know what you are doing.
   Incorrect queries could potentially damage your database. */

SELECT name FROM sqlite_master;"""

# Query to delete all logs older than a year
DELETE_OLD_LOGS = """/* WARNING: This query deletes data permanently! */

DELETE FROM WindowLog
WHERE StartTimestamp < datetime('now', '-1 year');"""

# Query to delete titles with "DEMO" and their logs
DELETE_DEMO_TITLES = """/* WARNING: This query deletes data permanently! */

-- First delete logs associated with the titles
DELETE FROM WindowLog
WHERE TitleID IN (
    SELECT ID FROM WindowTitles
    WHERE Title LIKE '%DEMO%'
);

-- Then delete the titles themselves
DELETE FROM WindowTitles
WHERE Title LIKE '%DEMO%';"""

# Query to select all projects
SELECT_PROJECTS = """/* List all projects */

SELECT ID, ProjectName
FROM Projects
ORDER BY ProjectName;"""

# Query to select all titles
SELECT_TITLES = """/* List all window titles */

SELECT wt.ID, wt.Title, p.ProjectName
FROM WindowTitles wt
LEFT JOIN Projects p ON wt.ProjectID = p.ID
ORDER BY wt.Title;"""

# Query to select all logs
SELECT_LOGS = """/* List recent window logs */

SELECT wl.ID, wt.Title, wl.StartTimestamp, wl.EndTimestamp,
       CASE
           WHEN wl.EndTimestamp IS NULL THEN 0
           ELSE strftime('%s', wl.EndTimestamp) - strftime('%s', wl.StartTimestamp)
       END as Duration
FROM WindowLog wl
JOIN WindowTitles wt ON wl.TitleID = wt.ID
ORDER BY wl.StartTimestamp DESC
LIMIT 100;"""

# Query to select logs for titles containing "DEMO"
SELECT_DEMO_LOGS = """/* List logs for titles containing "DEMO" */

SELECT wl.ID, wt.Title, wl.StartTimestamp, wl.EndTimestamp,
       CASE
           WHEN wl.EndTimestamp IS NULL THEN 0
           ELSE strftime('%s', wl.EndTimestamp) - strftime('%s', wl.StartTimestamp)
       END as Duration
FROM WindowLog wl
JOIN WindowTitles wt ON wl.TitleID = wt.ID
WHERE wt.Title LIKE '%DEMO%'
ORDER BY wl.StartTimestamp DESC;"""

# Query to merge two similar titles
MERGE_SIMILAR_TITLES = """/* WARNING: This query modifies data! */

/* This query merges two similar titles, transferring all logs
   from the source title to the destination title, then deletes the source title. */

BEGIN TRANSACTION;

-- Parameters: Set these values before running
-- Source title pattern (will be merged into destination)
-- @SourcePattern = '%demo1%'
-- Destination title pattern (will receive logs from source)
-- @DestPattern = '%demo2%'

-- Get IDs of the titles to merge
WITH source_titles AS (
    SELECT ID FROM WindowTitles WHERE Title LIKE '%demo1%'
),
dest_titles AS (
    SELECT ID FROM WindowTitles WHERE Title LIKE '%demo2%' LIMIT 1
)

-- Update logs from source titles to point to destination title
UPDATE WindowLog
SET TitleID = (SELECT ID FROM dest_titles)
WHERE TitleID IN (SELECT ID FROM source_titles);

-- Delete the source titles
DELETE FROM WindowTitles
WHERE ID IN (SELECT ID FROM source_titles);

COMMIT;"""