select
    id,
    name,
    email
from users
where status = 'active' and created_at >= '2023-01-01'
order by name;

select *
from orders o
join customers c on o.customer_id = c.id
where o.total > 100
order by o.created_at desc;

insert into products (name, price, category) values (
    'Product A', 29.99, 'electronics'
),
('Product B', 19.99, 'books');

update users set last_login = now()
where id in (1, 2, 3, 4, 5);

delete from temp_data
where created_at < '2023-01-01';
