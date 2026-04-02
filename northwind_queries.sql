-- ============================================================
--  NORTHWIND DATABASE  –  TRAIL PROJECT  |  MS SQL Server
--  Author  : Trail Candidate
--  Purpose : Answer three analytical questions + one stored
--            procedure that wraps all results in a single call.
-- ============================================================


-- ============================================================
-- QUERY 1 – Total Revenue by Product Category
--           (highest to lowest)
-- ============================================================
--  Revenue = UnitPrice * Quantity * (1 - Discount)
--  We join Order Details → Products → Categories so every
--  line item can be rolled up to its parent category.
-- ============================================================

SELECT
    c.CategoryName,
    CAST(
        SUM(od.UnitPrice * od.Quantity * (1.0 - od.Discount))
        AS DECIMAL(12, 2)
    )                                   AS TotalRevenue
FROM
    [Order Details]  AS od
    INNER JOIN Products   AS p  ON p.ProductID   = od.ProductID
    INNER JOIN Categories AS c  ON c.CategoryID  = p.CategoryID
GROUP BY
    c.CategoryName
ORDER BY
    TotalRevenue DESC;          -- highest revenue category first


-- ============================================================
-- QUERY 2 – Top 10 Customers by Lifetime Order Value
--           + their most recent order date
-- ============================================================
--  We aggregate at the customer level:
--    • SUM of revenue across every order they placed
--    • MAX of OrderDate to get the most recent activity
--  Then we keep only the top 10 with TOP + ORDER BY.
-- ============================================================

SELECT TOP 10
    c.CustomerID,
    c.CompanyName,
    c.ContactName,
    CAST(
        SUM(od.UnitPrice * od.Quantity * (1.0 - od.Discount))
        AS DECIMAL(12, 2)
    )                                   AS LifetimeOrderValue,
    CONVERT(DATE, MAX(o.OrderDate))     AS MostRecentOrderDate
FROM
    Customers    AS c
    INNER JOIN Orders        AS o  ON o.CustomerID  = c.CustomerID
    INNER JOIN [Order Details] AS od ON od.OrderID  = o.OrderID
GROUP BY
    c.CustomerID,
    c.CompanyName,
    c.ContactName
ORDER BY
    LifetimeOrderValue DESC;    -- highest-value customer first


-- ============================================================
-- QUERY 3 – Delayed Orders
--           (ShippedDate > OrderDate + 7 days)
-- ============================================================
--  DATEDIFF returns the day gap between order and shipment.
--  We exclude NULL ShippedDate rows (not yet shipped) because
--  an unshipped order is not yet confirmed delayed.
--  A computed column [DaysToShip] is included for transparency.
-- ============================================================

SELECT
    o.OrderID,
    o.CustomerID,
    c.CompanyName,
    CONVERT(DATE, o.OrderDate)          AS OrderDate,
    CONVERT(DATE, o.ShippedDate)        AS ShippedDate,
    DATEDIFF(DAY, o.OrderDate, o.ShippedDate)
                                        AS DaysToShip,
    'DELAYED'                           AS ShipmentStatus   -- flag column
FROM
    Orders    AS o
    INNER JOIN Customers AS c ON c.CustomerID = o.CustomerID
WHERE
    o.ShippedDate IS NOT NULL           -- only look at shipped orders
    AND DATEDIFF(DAY, o.OrderDate, o.ShippedDate) > 7
ORDER BY
    DaysToShip DESC;                    -- worst delays at the top


-- ============================================================
-- STORED PROCEDURE – usp_NorthwindAnalyticsReport
--
--  Wraps all three queries above into a single callable
--  procedure so reports can be generated with one EXEC call.
--  Returns three result sets in the order defined below.
-- ============================================================

-- Drop the procedure first if it already exists (idempotent deploy)
IF OBJECT_ID('dbo.usp_NorthwindAnalyticsReport', 'P') IS NOT NULL
    DROP PROCEDURE dbo.usp_NorthwindAnalyticsReport;
GO

CREATE PROCEDURE dbo.usp_NorthwindAnalyticsReport
    -- Optional parameter: restrict delayed-order flag threshold
    -- Default is 7 days; caller can pass a different value.
    @DelayThresholdDays INT = 7
AS
BEGIN
    SET NOCOUNT ON;     -- suppress row-count messages for cleaner output

    -- --------------------------------------------------------
    -- Result Set 1 : Revenue by Category
    -- --------------------------------------------------------
    SELECT
        c.CategoryName,
        CAST(
            SUM(od.UnitPrice * od.Quantity * (1.0 - od.Discount))
            AS DECIMAL(12, 2)
        ) AS TotalRevenue
    FROM
        [Order Details]  AS od
        INNER JOIN Products   AS p  ON p.ProductID  = od.ProductID
        INNER JOIN Categories AS c  ON c.CategoryID = p.CategoryID
    GROUP BY
        c.CategoryName
    ORDER BY
        TotalRevenue DESC;

    -- --------------------------------------------------------
    -- Result Set 2 : Top 10 Customers by Lifetime Value
    -- --------------------------------------------------------
    SELECT TOP 10
        c.CustomerID,
        c.CompanyName,
        c.ContactName,
        CAST(
            SUM(od.UnitPrice * od.Quantity * (1.0 - od.Discount))
            AS DECIMAL(12, 2)
        )                               AS LifetimeOrderValue,
        CONVERT(DATE, MAX(o.OrderDate)) AS MostRecentOrderDate
    FROM
        Customers    AS c
        INNER JOIN Orders          AS o  ON o.CustomerID = c.CustomerID
        INNER JOIN [Order Details] AS od ON od.OrderID   = o.OrderID
    GROUP BY
        c.CustomerID,
        c.CompanyName,
        c.ContactName
    ORDER BY
        LifetimeOrderValue DESC;

    -- --------------------------------------------------------
    -- Result Set 3 : Delayed Orders (parameterised threshold)
    -- --------------------------------------------------------
    SELECT
        o.OrderID,
        o.CustomerID,
        c.CompanyName,
        CONVERT(DATE, o.OrderDate)      AS OrderDate,
        CONVERT(DATE, o.ShippedDate)    AS ShippedDate,
        DATEDIFF(DAY, o.OrderDate, o.ShippedDate)
                                        AS DaysToShip,
        'DELAYED'                       AS ShipmentStatus
    FROM
        Orders    AS o
        INNER JOIN Customers AS c ON c.CustomerID = o.CustomerID
    WHERE
        o.ShippedDate IS NOT NULL
        AND DATEDIFF(DAY, o.OrderDate, o.ShippedDate) > @DelayThresholdDays
    ORDER BY
        DaysToShip DESC;

END;
GO

-- ============================================================
-- HOW TO CALL THE STORED PROCEDURE
-- ============================================================
--  Default threshold (7 days):
--      EXEC dbo.usp_NorthwindAnalyticsReport;
--
--  Custom threshold (e.g. 10 days):
--      EXEC dbo.usp_NorthwindAnalyticsReport @DelayThresholdDays = 10;
-- ============================================================
