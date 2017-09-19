select concat('update stock_stock set preallocation=', sum(quantity), ' where inventory_id=', inventory_id, ' and jancode=', jancode, ';') from st
    ock_order where status in ( '待发货',  '待采购',  '需介入',  '已采购') group by jancode, inventory_id;

    source test.sql


select o.orderid, o.status, o.jancode,o.quantity, o.need_purchase, s.quantity, s.inflight, s.preallocation from stock_order o inner join stoc
    k_product p on p.jancode=o.jancode inner join stock_stock s on s.product_id=p.id where o.inventory_id is not null and s.inventory_id=o.inventory_id order by o.jancode;



select o.orderid, o.status, o.inventory_id, o.jancode,o.quantity, o.need_purchase, s.quantity, s.inflight, s.preallocation from stock_order o inner join stock_product p on p.jancode=o.jancode inner join stock_stock s on s.product_id=p.id where o.inventory_id is not null and s.inventory_id=o.inventory_id and o.status in ('待发货','需介入', '待采购', '已采购') order by jancode;

# 查preallocation错误, 计算结果应该是:1. a.preallocation=b.oquantity   2. if a.preallocation-a.quantity-a.inflight>0, 结果等于=b.nquantity
select a.jancode, a.inventory_id,  a.quantity, a.inflight, a.preallocation, b.oquantity, a.preallocation-a.quantity-a.inflight r, b.nquantity from (select p.jancode, s.quantity, s.inflight, s.preallocation, s.inventory_id from stock_stock s inner join stock_product p on p.id=s.product_id) as a inner join (select jancode, inventory_id, sum(quantity) oquantity, sum(need_purchase) nquantity from stock_order where status in ('待发货','待采购', '已采购', '需介入') group by jancode, inventory_id) as b on a.jancode=b.jancode and a.inventory_id=b.inventory_id;

# 判断需采购数据异常
select * from (select a.jancode, a.inventory_id,  a.quantity, a.inflight, a.preallocation, b.oquantity, a.preallocation-a.quantity-a.inflight r, b.nquantity from (select p.jancode, s.quantity, s.inflight, s.preallocation, s.inventory_id from stock_stock s inner join stock_product p on p.id=s.product_id) as a inner join (select jancode, inventory_id, sum(quantity) oquantity, sum(need_purchase) nquantity from stock_order where status in ('待发货','待采购', '已采购', '需介入') group by jancode, inventory_id) as b on a.jancode=b.jancode and a.inventory_id=b.inventory_id) as v where v.r>0 and v.r<>v.nquantity;
