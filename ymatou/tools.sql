select concat('update stock_stock set preallocation=', sum(quantity), ' where inventory_id=', inventory_id, ' and jancode=', jancode, ';') from st
    ock_order where status in ( '待发货',  '待采购',  '需介入',  '已采购') group by jancode, inventory_id;

source test.sql
