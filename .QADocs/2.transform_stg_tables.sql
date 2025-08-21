-- 创建用户清洗表
CREATE TABLE IF NOT EXISTS stg_user_cleaned AS
SELECT
    user_id,
    LOWER(user_name) AS user_name,
    email,
    CAST(register_date AS DATE) AS register_date,
    INITCAP(region) AS region  -- 假设函数存在，首字母大写
FROM src_user_info
WHERE user_id IS NOT NULL;

-- 创建订单清洗表（过滤无效状态）
CREATE TABLE IF NOT EXISTS stg_order_cleaned AS
SELECT
    order_id,
    user_id,
    product_name,
    amount,
    CAST(order_date AS DATE) AS order_date,
    status
FROM src_order_detail
WHERE status IN ('completed', 'shipped');

-- 创建用户订单宽表（关联）
CREATE TABLE IF NOT EXISTS stg_user_order_wide AS
SELECT
    o.order_id,
    o.user_id,
    u.user_name,
    u.email,
    u.region,
    o.product_name,
    o.amount,
    o.order_date,
    o.status
FROM stg_order_cleaned o
LEFT JOIN stg_user_cleaned u ON o.user_id = u.user_id;