-- Create database if missing
IF NOT EXISTS (SELECT 1 FROM sys.databases WHERE name = N'pm')
BEGIN
    PRINT 'Creating database pm...';
    CREATE DATABASE pm;
END
GO

-- Create or reset the login
IF NOT EXISTS (SELECT 1 FROM sys.sql_logins WHERE name = N'pmuser')
BEGIN
    PRINT 'Creating login pmuser...';
    CREATE LOGIN pmuser WITH PASSWORD = 'StrongP@ssw0rd!';
END
ELSE
BEGIN
    PRINT 'Login pmuser already exists. Updating password and default DB...';
    ALTER LOGIN pmuser WITH PASSWORD = 'StrongP@ssw0rd!';
END
GO

-- Ensure default database is pm
ALTER LOGIN pmuser WITH DEFAULT_DATABASE = pm;
GO

-- Map login to user in pm and grant roles
USE pm;
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'pmuser')
BEGIN
    PRINT 'Creating user pmuser in pm...';
    CREATE USER pmuser FOR LOGIN pmuser;
END

-- Grant read (add writer if needed)
EXEC sp_addrolemember 'db_datareader', 'pmuser';
-- EXEC sp_addrolemember 'db_datawriter', 'pmuser'; -- uncomment if writes are needed
GO

-- Drop Party table if it exists
IF OBJECT_ID('dbo.Party', 'U') IS NOT NULL
BEGIN
    DROP TABLE dbo.Party;
END
GO

-- Create Party table if missing (identity key)
IF OBJECT_ID('dbo.Party', 'U') IS NULL
BEGIN
    PRINT 'Creating table dbo.Party...';
    CREATE TABLE dbo.Party (
        Id              INT IDENTITY(1,1) NOT NULL,
        First_Name      NVARCHAR(100)     NOT NULL,
        Last_Name       NVARCHAR(100)     NOT NULL,
        Adress1         NVARCHAR(200)     NULL,
        Adress2         NVARCHAR(200)     NULL,
        Zip             NVARCHAR(20)      NULL,
        City            NVARCHAR(100)     NULL,
        Country         NVARCHAR(100)     NULL,
        [Type]          VARCHAR(16)       NOT NULL CHECK ([Type] IN ('Person','Company')),
        CONSTRAINT PK_Party PRIMARY KEY CLUSTERED (Id)
    );
END
GO

GRANT INSERT ON dbo.Party TO pmuser;
-- or, broader:
-- EXEC sp_addrolemember 'db_datawriter', 'pmu
