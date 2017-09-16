select concat('update stock_stock set preallocation=', sum(quantity), ' where inventory_id=', inventory_id, ' and jancode=', jancode, ';') from st
    ock_order where status in ( '待发货',  '待采购',  '需介入',  '已采购') group by jancode, inventory_id;

    source test.sql


select o.orderid, o.status, o.jancode,o.quantity, o.need_purchase, s.quantity, s.inflight, s.preallocation from stock_order o inner join stoc
    k_product p on p.jancode=o.jancode inner join stock_stock s on s.product_id=p.id where o.inventory_id is not null and s.inventory_id=o.inventory_id order by o.jancode;



select o.orderid, o.status, o.inventory_id, o.jancode,o.quantity, o.need_purchase, s.quantity, s.inflight, s.preallocation from stock_order o inner join stock_product p on p.jancode=o.jancode inner join stock_stock s on s.product_id=p.id where o.inventory_id is not null and s.inventory_id=o.inventory_id and o.status in ('待发货','需介入', '待采购', '已采购') order by jancode;

# 查preallocation错误
select oq, sp, inv, pid,) from (select o.jancode j, p.id pid,o.inventory_id inv, o.jancode,sum(o.quantity) oq, sum(s.preallocation) sp from stock_order o inner join stock_product p on p.jancode=o.jancode inner join stock_stock s on s.product_id=p.id where o.inventory_id is not null and s.inventory_id=o.inventory_id and o.status in ('待发货','需介入', '待采购', '已采购') group by o.inventory_id, o.jancode) as t where oq<>sp;

# 更新不正确的preallocation
select concat('update stock_stock set preallocation=', oq, ' where inventory_id=', inv, ' and product_id=', pid, ';') from (select o.jancode j, p.id pid,o.inventory_id inv, o.jancode,sum(o.quantity) oq, sum(s.preallocation) sp from stock_order o inner join stock_product p on p.jancode=o.jancode inner join stock_stock s on s.product_id=p.id where o.inventory_id is not null and s.inventory_id=o.inventory_id and o.status in ('待发货','需介入', '待采购', '已采购') group by o.inventory_id, o.jancode) as t where oq<>sp;
