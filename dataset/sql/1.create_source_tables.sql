-- 创建用户原始表
CREATE TABLE IF NOT EXISTS src_user_info (
    user_id BIGINT,
    user_name STRING,
    email STRING,
    register_date STRING,
    region STRING
);

-- 创建订单原始表
CREATE TABLE IF NOT EXISTS src_order_detail (
    order_id BIGINT,
    user_id BIGINT,
    product_name STRING,
    amount DECIMAL(10,2),
    order_date STRING,
    status STRING
);

-- 插入测试数据
INSERT INTO src_user_info VALUES
(1001, 'Alice', 'alice@example.com', '2023-01-15', 'North'),
(1002, 'Bob', 'bob@example.com', '2023-02-20', 'South'),
(1003, 'Charlie', 'charlie@example.com', '2023-03-10', 'East');

INSERT INTO src_order_detail VALUES
(5001, 1001, 'Laptop', 999.99, '2023-01-16', 'completed'),
(5002, 1001, 'Mouse', 25.50, '2023-01-16', 'completed'),
(5003, 1002, 'Keyboard', 89.99, '2023-02-21', 'shipped'),
(5004, 1003, 'Monitor', 299.00, '2023-03-11', 'completed');