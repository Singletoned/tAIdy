select   id,name,email from users where   status='active'and created_at>='2023-01-01'order by name;

SELECT *
FROM orders o
JOIN customers c ON o.customer_id=c.id
WHERE   o.total >100
ORDER BY   o.created_at desc;

INSERT INTO products(name,price,category)VALUES('Product A',29.99,'electronics'),('Product B',19.99,'books');

UPDATE users SET last_login = now() WHERE id IN(1,2,3,4,5);

DELETE FROM temp_data WHERE created_at<'2023-01-01';