-- 用户订单明细表（带衍生字段）
CREATE TABLE IF NOT EXISTS dwd_user_order_detail AS
SELECT
    order_id,
    user_id,
    user_name,
    region,
    product_name,
    amount,
    order_date,
    status,
    -- 衍生字段：订单金额等级
    CASE
        WHEN amount >= 500 THEN 'High'
        WHEN amount >= 100 THEN 'Medium'
        ELSE 'Low'
    END AS amount_level,
    -- 计算下单距今天数（假设当前为 '2023-04-01'）
    DATEDIFF('2023-04-01', order_date) AS days_since_order
FROM stg_user_order_wide;