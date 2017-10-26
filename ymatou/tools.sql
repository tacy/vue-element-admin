select concat('update stock_stock set preallocation=', sum(quantity), ' where inventory_id=', inventory_id, ' and jancode=', jancode, ';') from st
    ock_order where status in ( '待发货',  '待采购',  '需介入',  '已采购') group by jancode, inventory_id;

    source test.sql


select o.orderid, o.status, o.jancode,o.quantity, o.need_purchase, s.quantity, s.inflight, s.preallocation from stock_order o inner join stoc
    k_product p on p.jancode=o.jancode inner join stock_stock s on s.product_id=p.id where o.inventory_id is not null and s.inventory_id=o.inventory_id order by o.jancode;



select o.orderid, o.status, o.inventory_id, o.jancode,o.quantity, o.need_purchase, s.quantity, s.inflight, s.preallocation from stock_order o inner join stock_product p on p.jancode=o.jancode inner join stock_stock s on s.product_id=p.id where o.inventory_id is not null and s.inventory_id=o.inventory_id and o.status in ('待发货','需介入', '待采购', '已采购') order by jancode;

# 查preallocation错误, 计算结果应该是:1. a.preallocation=b.oquantity   2. if a.preallocation-a.quantity-a.inflight>0, 结果等于=b.nquantity
select a.jancode, a.inventory_id,  a.quantity, a.inflight, a.preallocation, b.oquantity, a.preallocation-a.quantity-a.inflight r, b.nquantity from (select p.jancode, s.quantity, s.inflight, s.preallocation, s.inventory_id from stock_stock s inner join stock_product p on p.id=s.product_id) as a inner join (select jancode, inventory_id, sum(quantity) oquantity, sum(need_purchase) nquantity from stock_order where status in ('待发货','待采购', '已采购', '需介入') group by jancode, inventory_id) as b on a.jancode=b.jancode and a.inventory_id=b.inventory_id;

# 修正库存表preallocation数据
select concat('update stock_stock set preallocation=', b.oquantity, ' where inventory_id=',b.inventory_id, ' and product_id=', a.product_id, ';')  from (select p.jancode, s.quantity, s.inflight, s.preallocation, s.inventory_id, s.product_id from stock_stock s inner join stock_product p on p.id=s.product_id) as a inner join (select jancode, inventory_id, sum(quantity) oquantity, sum(need_purchase) nquantity from stock_order where status in ('待发货','待采购', '已采购', '需介入') group by jancode, inventory_id) as b on a.jancode=b.jancode and a.inventory_id=b.inventory_id;


############ 计算在途
select p.jancode, product_id, inventory_id, inflight from stock_purchaseorderitem poi inner join stock_product p on poi.product_id=p.id

# 判断需采购数据异常
select * from (select a.jancode, a.inventory_id,  a.quantity, a.inflight, a.preallocation, b.oquantity, a.preallocation-a.quantity-a.inflight r, b.nquantity from (select p.jancode, s.quantity, s.inflight, s.preallocation, s.inventory_id from stock_stock s inner join stock_product p on p.id=s.product_id) as a inner join (select jancode, inventory_id, sum(quantity) oquantity, sum(need_purchase) nquantity from stock_order where status in ('待发货','待采购', '已采购', '需介入') group by jancode, inventory_id) as b on a.jancode=b.jancode and a.inventory_id=b.inventory_id) as v where v.r>0 and v.r<>v.nquantity;


# 改派
MariaDB [ymatou]> desc stock_stock;
+---------------+-------------+------+-----+---------+----------------+
| Field         | Type        | Null | Key | Default | Extra          |
+---------------+-------------+------+-----+---------+----------------+
| id            | int(11)     | NO   | PRI | NULL    | auto_increment |
| quantity      | int(11)     | YES  |     | NULL    |                |
| inflight      | int(11)     | YES  |     | NULL    |                |
| preallocation | int(11)     | YES  |     | NULL    |                |
| location      | varchar(8)  | YES  |     | NULL    |                |
| inventory_id  | int(11)     | NO   | MUL | NULL    |                |
| jancode       | varchar(24) | NO   |     | NULL    |                |
| product_id    | int(11)     | NO   | MUL | NULL    |                |
+---------------+-------------+------+-----+---------+----------------+
8 rows in set (0.00 sec)

MariaDB [ymatou]> select s.id, s.inventory_id, p.id, p.jancode, s.quantity, s.inflight, s.preallocation from stock_stock s inner join stock_product p on s.product_id=p.id where s.inventory_id=1 and p.jancode in ('4969527118253','4971710359114');
+------+--------------+------+---------------+----------+----------+---------------+
| id   | inventory_id | id   | jancode       | quantity | inflight | preallocation |
+------+--------------+------+---------------+----------+----------+---------------+
| 1494 |            1 | 2849 | 4969527118253 |        0 |        0 |             3 |
| 1234 |            1 | 1527 | 4971710359114 |        1 |        0 |             4 |
+------+--------------+------+---------------+----------+----------+---------------+
2 rows in set (0.00 sec)

MariaDB [ymatou]> select s.id, s.inventory_id, p.id, p.jancode, s.quantity, s.inflight, s.preallocation from stock_stock s inner join stock_product p on s.product_id=p.id where s.inventory_id=3 and p.jancode in ('4969527118253','4971710359114');
Empty set (0.00 sec)

MariaDB [ymatou]> select orderid, jancode, quantity, need_purchase, shipping_id, inventory_id from stock_order where orderid in ('20414051','20414149');
+----------+---------------+----------+---------------+-------------+--------------+
| orderid  | jancode       | quantity | need_purchase | shipping_id | inventory_id |
+----------+---------------+----------+---------------+-------------+--------------+
| 20414051 | 4969527118253 |        1 |             1 |           1 |            1 |
| 20414149 | 4971710359114 |        1 |             1 |           1 |            1 |
+----------+---------------+----------+---------------+-------------+--------------+
2 rows in set (0.00 sec)

MariaDB [ymatou]> insert into stock_stock (quantity,preallocation, inventory_id, product_id) values (0,1,3,2849);
Query OK, 1 row affected, 1 warning (0.00 sec)

MariaDB [ymatou]> insert into stock_stock (quantity,preallocation, inventory_id, product_id) values (0,1,3,1527);
Query OK, 1 row affected, 1 warning (0.00 sec)

MariaDB [ymatou]> update stock_order set shipping_id=5,inventory_id=3 where orderid=20414051 and jancode=4969527118253;
Query OK, 1 row affected, 2 warnings (0.00 sec)
Rows matched: 1  Changed: 1  Warnings: 2

MariaDB [ymatou]> update stock_order set shipping_id=5,inventory_id=3 where orderid=20414149 and jancode=4971710359114;
Query OK, 1 row affected, 2 warnings (0.00 sec)
Rows matched: 1  Changed: 1  Warnings: 2
