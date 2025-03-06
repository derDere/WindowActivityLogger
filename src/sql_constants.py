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
MERGE_SIMILAR_TITLES = """/* WARNING: This query modifies data permanently!

   This query merges the log entries of multiple titles together. 
   
   INSTRUCTIONS:
   1. Replace SOURCE_TITLE_ID with the ID of the title you want to merge FROM
   2. Replace TARGET_TITLE_ID with the ID of the title you want to merge INTO
   3. All window logs from the source title will be reassigned to the target title
   4. The source title will be deleted after merging
   
   To find title IDs, run the "Select Titles" query first */

-- First update all window logs to point to the target title
UPDATE WindowLog
SET TitleID = TARGET_TITLE_ID
WHERE TitleID = SOURCE_TITLE_ID;

-- Then delete the source title
DELETE FROM WindowTitles
WHERE ID = SOURCE_TITLE_ID;

/* EXAMPLE:
   To merge "Visual Studio Code" (ID: 123456) into "VS Code" (ID: 789012):
   
   UPDATE WindowLog
   SET TitleID = 789012
   WHERE TitleID = 123456;
   
   DELETE FROM WindowTitles
   WHERE ID = 123456;
*/"""