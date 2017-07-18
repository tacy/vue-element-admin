派单流程: 派单分为派单和重派, 如果订单的order_inventory字段为空, 定位为派单;
          如果该字段非空, 定义为重派.
需要根据传入订单号, 查询数据库表中对应订单, 判断order_inventory字段内容:
1. dborder.order_inventory is null, 派单
2. dborder.order_inventory != paramorder.order_inventory, 重派
3. dborder.order_inventory == paramorder.order_inventory, 忽略操作, 直接返回
派单需要更新库存占库字段; 重派需要先从之前指派的仓库回滚占库数据, 再更新库存占
库字段
