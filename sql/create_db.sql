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

-- Create Party table if missing (identity key, split given/surname)
IF OBJECT_ID('dbo.Party', 'U') IS NULL
BEGIN
    PRINT 'Creating table dbo.Party...';
    CREATE TABLE dbo.Party (
        PartyId         INT IDENTITY(1,1) NOT NULL,
        ExternalRef     NVARCHAR(64)      NULL,
        PartyType       VARCHAR(16)       NOT NULL CHECK (PartyType IN ('Person','Org')),
        GivenName       NVARCHAR(100)     NOT NULL,
        MiddleName      NVARCHAR(100)     NULL,
        Surname         NVARCHAR(100)     NOT NULL,
        CountryCode     CHAR(2)           NOT NULL,
        City            NVARCHAR(100)     NULL,
        PostalCode      NVARCHAR(20)      NULL,
        Email           NVARCHAR(200)     NULL,
        Phone           NVARCHAR(50)      NULL,
        Status          VARCHAR(16)       NOT NULL DEFAULT 'Active' CHECK (Status IN ('Active','Inactive','Closed')),
        CreatedAt       DATETIME2(0)      NOT NULL DEFAULT SYSUTCDATETIME(),
        UpdatedAt       DATETIME2(0)      NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_Party PRIMARY KEY CLUSTERED (PartyId)
    );
END
GO

-- Drop unique constraint on ExternalRef if present (legacy)
IF EXISTS (
    SELECT 1
    FROM sys.objects
    WHERE name = 'UQ_Party_ExternalRef'
      AND type = 'UQ'
      AND parent_object_id = OBJECT_ID('dbo.Party')
)
BEGIN
    ALTER TABLE dbo.Party DROP CONSTRAINT UQ_Party_ExternalRef;
END
GO

-- Keep UpdatedAt fresh
IF OBJECT_ID('dbo.trg_Party_SetUpdated', 'TR') IS NULL
BEGIN
    EXEC('
    CREATE TRIGGER dbo.trg_Party_SetUpdated
    ON dbo.Party
    AFTER UPDATE
    AS
    BEGIN
        SET NOCOUNT ON;
        UPDATE p
        SET UpdatedAt = SYSUTCDATETIME()
        FROM dbo.Party p
        JOIN inserted i ON p.PartyId = i.PartyId;
    END
    ');
END
GO

-- Helpful indexes
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Party_Country' AND object_id = OBJECT_ID(N'dbo.Party'))
    CREATE INDEX IX_Party_Country ON dbo.Party (CountryCode);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Party_Status' AND object_id = OBJECT_ID(N'dbo.Party'))
    CREATE INDEX IX_Party_Status ON dbo.Party (Status);
GO


GRANT INSERT ON dbo.Party TO pmuser;
-- or, broader:
-- EXEC sp_addrolemember 'db_datawriter', 'pmu
