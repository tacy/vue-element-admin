from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


# Create your models here.
class Supplier(models.Model):
    name = models.CharField(max_length=16, null=False, unique=True)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Inventory(models.Model):
    name = models.CharField(max_length=8, unique=True, null=False)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)

    def __str__(self):
        return self.name


# mysql> select a.category_id, a.category_cn_name, b.category_id, b.category_cn_name,
# a.category_version from stock_category a join stock_category b on (a.category_id=b.category_parent_id);
class Category(models.Model):
    category_id = models.CharField(max_length=18, null=False)
    category_cn_name = models.CharField(max_length=64, null=False)
    category_en_name = models.CharField(max_length=64, null=True)
    category_level = models.IntegerField(null=False)
    category_parent_id = models.CharField(max_length=18, null=False)
    category_version = models.CharField(max_length=18, null=False)


class Product(models.Model):
    name = models.CharField(max_length=255, null=False)
    jancode = models.CharField(max_length=24, null=False, unique=True)
    category = models.ForeignKey(Category, related_name='product')
    brand = models.CharField(max_length=128, null=True)  # 品牌
    origin = models.CharField(max_length=64, null=True)  # 产地
    model = models.CharField(max_length=128, null=True)  # 型号
    specification = models.CharField(max_length=128, null=True)  # 规格
    size = models.CharField(max_length=128, null=True)  # 材质
    proddesc = models.CharField(max_length=255, null=True)
    unit = models.CharField(max_length=2, null=True)
    expired = models.CharField(max_length=8, null=True)
    weight = models.DecimalField(max_digits=5, null=True, decimal_places=2)
    purchase_link1 = models.CharField(max_length=255, null=True)
    purchase_link2 = models.CharField(max_length=255, null=True)
    purchase_link3 = models.CharField(max_length=255, null=True)


class BondedProduct(models.Model):
    product_name = models.CharField(max_length=255, null=False)
    bonded_name = models.CharField(max_length=24, null=False)
    jancode = models.CharField(max_length=24, null=False, unique=True)
    filing_no = models.CharField(max_length=24, null=False, unique=True)


class Stock(models.Model):
    inventory = models.ForeignKey(Inventory, related_name='stock')
    product = models.ForeignKey(Product, related_name='stock')
    quantity = models.IntegerField(null=True, default=0)  # 库存
    inflight = models.IntegerField(null=True, default=0)  # 在途数量
    preallocation = models.IntegerField(null=True, default=0)  # 分配到该仓库商品的订单
    location = models.CharField(max_length=64, null=True)  # 库存位置

    class Meta:
        unique_together = ('inventory', 'product')


class Shipping(models.Model):
    inventory = models.ForeignKey(
        Inventory, related_name='shipping', null=False)
    name = models.CharField(max_length=16, null=False)
    delivery_company = models.CharField(max_length=4, null=True)
    tiangou_company = models.CharField(max_length=4, null=True, default='')

    def __str__(self):
        return '{}:{}'.format(self.inventory.name, self.name)


class ShippingDB(models.Model):
    db_number = models.CharField(
        max_length=32, unique=True,
        null=False)  # xloboDBNumber, uexDBNumber, EMSNumber
    channel_name = models.CharField(max_length=16, null=False)
    order_piad_time = models.DateTimeField(null=True)
    delivery_no = models.CharField(
        max_length=128, null=True)  # delivery number
    shipping = models.ForeignKey(
        Shipping, related_name='shippingdb', null=False)
    inventory = models.ForeignKey(
        Inventory, related_name='shippingdb', null=False)
    status = models.CharField(max_length=8, null=True)  # 待处理/已删除/已出库
    # error_msg = models.CharField(max_length=256, null=True)  # 如果打印面单出错, 需要记录
    delivery_time = models.DateTimeField(null=True)
    print_status = models.CharField(max_length=8, null=True)  # 已打印

    class Meta:
        ordering = ['order_piad_time']


class PurchaseOrder(models.Model):
    # 采购单状态: 在途/删除/入库
    # 按单采购流程:
    # 1. 进入订单/待采购页面, 在采购渠道采购, 填入采购信息, 保存采购单, 采购单进入在途状态
    # 2. 包裹到库, 仓库进行入库操作, 采购单状态变更为入库
    # 3. 如果采购单被Cancel, 采购人员进入采购/采购单, 标记该采购单为删除.
    orderid = models.CharField(max_length=64, blank=False)
    supplier = models.ForeignKey(Supplier, related_name='purchaseorder')
    inventory = models.ForeignKey(Inventory, related_name='purchaseorder')
    delivery_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=255, default='create')  # 在途/入库/部分入库
    create_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "{}".format(self.orderid)

    class Meta:
        unique_together = ('orderid', 'supplier')


class PurchaseOrderItem(models.Model):
    purchaseorder = models.ForeignKey(
        PurchaseOrder, related_name='purchaseorderitem')
    product = models.ForeignKey(Product, related_name='purchaseorderitem')
    quantity = models.IntegerField(null=False)
    status = models.CharField(max_length=8, null=True)  # 已入库/东京仓/转运中
    delivery_no = models.CharField(max_length=32, null=True)  # 转运单号
    price = models.DecimalField(max_digits=7, null=True, decimal_places=2)

    class Meta:
        unique_together = ('purchaseorder', 'product')

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "{}@{}@{}@{}@{}@{}".format(
            self.product.jancode, self.product.name,
            self.product.specification, self.quantity, self.price, self.status)


class Order(models.Model):
    seller_name = models.CharField(max_length=32, null=False)
    channel_name = models.CharField(max_length=16, null=False)
    orderid = models.CharField(max_length=32, null=False)
    receiver_name = models.CharField(max_length=8, null=False)
    receiver_address = models.CharField(max_length=64, null=False)
    receiver_zip = models.CharField(max_length=6, null=True, default='')
    receiver_mobile = models.CharField(max_length=11, null=False)
    receiver_idcard = models.CharField(max_length=18, null=True)
    seller_memo = models.CharField(max_length=255, null=True, default='')
    buyer_remark = models.CharField(max_length=255, null=True)
    jancode = models.CharField(max_length=24, null=True, default='')
    quantity = models.IntegerField(null=False)
    need_purchase = models.IntegerField(null=True, default=0)
    allocate_time = models.DateTimeField(null=True)  # 需要根据派单时间, 判断采购单是否能关联该订单
    price = models.DecimalField(max_digits=7, null=True, decimal_places=2)
    payment = models.DecimalField(max_digits=7, null=True, decimal_places=2)
    delivery_type = models.CharField(max_length=32, null=False)
    piad_time = models.DateTimeField()
    product_title = models.CharField(max_length=255, null=False)
    product_id = models.CharField(max_length=64, null=False)
    sku_properties_name = models.CharField(
        max_length=64, null=True, default='')
    inventory = models.ForeignKey(Inventory, related_name='order', null=True)
    shipping = models.ForeignKey(Shipping, related_name='order', null=True)
    purchaseorder = models.ForeignKey(
        PurchaseOrder, related_name='order', null=True)
    status = models.CharField(
        max_length=3, null=True, default='待处理')  # 待处理/待发货/已发货
    channel_delivery_status = models.CharField(
        max_length=3, null=True, default='')  # 已发货/null
    importstatus = models.CharField(max_length=3, null=True)  # 是否已经导入贝海后台
    export_status = models.CharField(max_length=3, null=True)  # 导出发货
    domestic_delivery_no = models.CharField(max_length=64, null=True)
    domestic_delivery_company = models.CharField(max_length=64, null=True)
    conflict = models.CharField(max_length=8, null=True)  # 换货/退款
    conflict_memo = models.CharField(max_length=128, null=True)
    conflict_feedback = models.CharField(max_length=128, null=True)
    shippingdb = models.ForeignKey(ShippingDB, related_name='order', null=True)

    class Meta:
        # unique_together = ('channel_name', 'orderid', 'jancode')
        ordering = ['id', 'piad_time', 'receiver_mobile']

    def __str__(self):
        return '%d@%s@%s@%s@%s@%s@%s@%s@%s@%s@%s' % (
            self.id, self.orderid, self.status, self.purchaseorder.orderid
            if self.purchaseorder else 'none', self.product_title,
            self.sku_properties_name, self.receiver_name,
            self.receiver_address, self.receiver_mobile, self.receiver_zip,
            self.product_id)

    # Todo:订单需要拆分
    # 订单状态:
    # 1. 待处理: 完成订单调整, 比如没有jancode需要补充, 客户留言需要处理, 需要编辑订单.
    #            订单处理人员点击分配仓库, 弹出页面显示该商品在库状态, 然后选择仓库, 如果仓库没有库存, 标记待采购.
    #            系统操作: @提交修改. @库存占库同时修改订单状态:待采购/生成渠道信息
    # 2. 待采购: 显示待需采购订单(by仓库), 页面需显示待采购订单和summary信息.
    #            a. 如果商品采购不到, 需协调砍单或调换型号, 标记疑难, 订单从采购列表移除, 进入疑难订单.
    #            b. 采购完成, 新增采购单, 弹出页面, 勾选采购单包括的订单(需要提供过滤框,可以批量选择), 点击下一步生成采购单列表, 输入采购价格.
    #               系统标记选择订单已采购, 在订单标记采购单号, 重复新增.
    # 3. 疑难订单: 如果订单处于疑难状态, 需要客服介入处理, 并根据处理结果让订单进入正常流程: 比如砍单/换货(需要修改订单jancode和商品信息).
    # 4. 生成渠道信息: 显示待发货列表(包括在库和已采购订单), 获取DB单号(或者手填发货单号), 后台生成DB单号记录(里面包括配货信息).
    # 5. 发货: 显示发货列表(分为在库和已采购). 打印DB面单, 根据面单关联配货信息分拣包裹.
    # 6. 入库: 扫描采购单, 自动匹配采购单信息, 核对包裹商品, 销采购单, 同时显示关联到这个采购单的订单, 进行发货操作.
    # Todo: 1. 需要db单号, 需要生成发货信息(db单号对应的商品库位号),
    #       2. 订单金额超过2000, 需分开包裹发
    #       3. 订单导入时, 如果发现产品不在产品表, 自动插入简单产品信息到产品表(前提是jancode不为空)
    #       4. 订单必须要有jancode
    #       5. 补发,订单号-10
    #       6. 第三方发货
    #       7. 直邮转平邮/平邮转直邮
    #       8. 补发/重发订单
    #       9. 补采购单(漏采)
    # 流程: 订单导入, 如果没有jancode, 补jancode,
    # Task: 用来存放后台任务, 一条记录代表一个后台任务.
    #       1. 后台任务进程会读取这个表, 获取任务的执行间隔.
    #       2. 后台进程会定时获取该表的内容, 进行hash对比, 如果发现表的内容发生变化,
    #          进程自动退出, 然后systemd会自动把后台任务重新启动, 完成配置刷新工作.


class Task(models.Model):
    name = models.CharField(max_length=16, null=False)
    interval = models.IntegerField(null=False)

    def __str__(self):
        return 'TaskName: {} / Inteval:{}'.format(self.name, self.interval)


# ExportOrderLog 记录订单导出日志, 定时任务会从这个表中找到最近的订单导出时间, 用
# 它作为导出订单的起始时间.
class ExportOrderLog(models.Model):
    sellerName = models.CharField(max_length=32, null=False)
    start_time = models.DateTimeField(null=True)
    export_time = models.DateTimeField(null=False)
    count = models.IntegerField(null=True, default=0)

    def __str__(self):
        return 'SellerName: {}  / StartTime: {} /  ExportTime: {}  /  Count: {}'.format(
            self.sellerName, self.start_time, self.export_time, self.count)

    class Meta:
        unique_together = ('sellerName', 'export_time')
