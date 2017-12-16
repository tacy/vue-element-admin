from rest_framework import serializers
from rest_framework.authtoken.models import Token

from .models import (BondedProduct, Inventory, Order, Product,
                     PurchaseDivergence, PurchaseOrder, PurchaseOrderItem,
                     Shipping, ShippingDB, Stock, StockInRecord,
                     StockOutRecord, Supplier, UexTrack)
from stock.models import AfterSaleCase, AfterSaleMeta


class TokenSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    group = serializers.ReadOnlyField(source='user.first_name')

    class Meta:
        model = Token
        fields = '__all__'


class PurchaseOrderSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    purchaseorderitem = serializers.StringRelatedField(
        many=True, read_only=True)
    supplier_name = serializers.ReadOnlyField(source='supplier.name')
    inventory_name = serializers.ReadOnlyField(source='inventory.name')
    inventory = serializers.PrimaryKeyRelatedField(read_only=True)
    supplier = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = PurchaseOrder
        fields = '__all__'


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    jancode = serializers.ReadOnlyField(source='product.jancode')
    product_name = serializers.ReadOnlyField(source='product.name')
    supplier_name = serializers.ReadOnlyField(
        source='purchaseorder.supplier.name')
    product_specification = serializers.ReadOnlyField(
        source='product.specification')
    orderid = serializers.ReadOnlyField(source='purchaseorder.orderid')
    purchaseorder_createtime = serializers.ReadOnlyField(
        source='purchaseorder.create_time')
    inventory_name = serializers.ReadOnlyField(
        source='purchaseorder.inventory.name')

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = PurchaseOrderItem
        fields = '__all__'


class PurchaseDivergenceSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = PurchaseDivergence
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    category_name = serializers.ReadOnlyField(
        source='category.category_cn_name')
    origin = serializers.CharField(
        read_only=False, required=False, allow_null=True, allow_blank=True)
    model = serializers.CharField(
        read_only=False, required=False, allow_null=True, allow_blank=True)
    size = serializers.CharField(
        read_only=False, required=False, allow_null=True, allow_blank=True)
    proddesc = serializers.CharField(
        read_only=False, required=False, allow_null=True, allow_blank=True)
    unit = serializers.CharField(
        read_only=False, required=False, allow_null=True, allow_blank=True)
    expired = serializers.CharField(
        read_only=False, required=False, allow_null=True, allow_blank=True)
    weight = serializers.CharField(
        read_only=False, required=False, allow_null=True, allow_blank=True)
    purchase_link1 = serializers.CharField(
        read_only=False, required=False, allow_null=True, allow_blank=True)
    purchase_link2 = serializers.CharField(
        read_only=False, required=False, allow_null=True, allow_blank=True)
    purchase_link3 = serializers.CharField(
        read_only=False, required=False, allow_null=True, allow_blank=True)

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = Product
        # fields = ('id', 'order_id', 'delivery_id', 'cost', 'discount', 'status', 'invertory_name', 'supplier_name', 'create_time')
        fields = '__all__'


class BondedProductSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = BondedProduct
        # fields = ('id', 'order_id', 'delivery_id', 'cost', 'discount', 'status', 'invertory_name', 'supplier_name', 'create_time')
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    shipping_name = serializers.ReadOnlyField(source='shipping.name')
    inventory_name = serializers.ReadOnlyField(source='inventory.name')
    db_number = serializers.ReadOnlyField(source='shippingdb.db_number')
    shippingdb_delivery_time = serializers.ReadOnlyField(
        source='shippingdb.delivery_time')
    purchaseorder_orderid = serializers.ReadOnlyField(
        source='purchaseorder.orderid')
    buyer_remark = serializers.CharField(
        read_only=False, required=False, allow_null=True, allow_blank=True)
    receiver_idcard = serializers.CharField(
        read_only=False, required=False, allow_null=True, allow_blank=True)
    jancode = serializers.CharField(
        read_only=False, required=False, allow_null=True, allow_blank=True)
    channel_delivery_status = serializers.CharField(
        read_only=False, required=False, allow_null=True, allow_blank=True)
    product_id = serializers.CharField(
        read_only=False, required=False, allow_null=True, allow_blank=True)
    seller_memo = serializers.CharField(
        read_only=False, required=False, allow_null=True, allow_blank=True)

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = Order
        # fields = ('id', 'order_id', 'delivery_id', 'cost', 'discount', 'status', 'invertory_name', 'supplier_name', 'create_time')
        fields = '__all__'


class StockSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    inventory_name = serializers.ReadOnlyField(source='inventory.name')
    product_name = serializers.ReadOnlyField(source='product.name')
    product_specification = serializers.ReadOnlyField(
        source='product.specification')
    jancode = serializers.ReadOnlyField(source='product.jancode')
    supplier_name = serializers.ReadOnlyField(source='stocking_supplier.name')

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = Stock
        # fields = ('id', 'order_id', 'delivery_id', 'cost', 'discount', 'status', 'invertory_name', 'supplier_name', 'create_time')
        fields = '__all__'


class ShippingSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    inventory_name = serializers.ReadOnlyField(source='inventory.name')

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = Shipping
        # fields = ('id', 'order_id', 'delivery_id', 'cost', 'discount', 'status', 'invertory_name', 'supplier_name', 'create_time')
        fields = '__all__'


class ShippingDBSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    order = serializers.StringRelatedField(many=True)
    shipping_name = serializers.ReadOnlyField(source='shipping.name')
    inventory_name = serializers.ReadOnlyField(source='inventory.name')

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = ShippingDB
        # fields = ('id', 'order_id', 'delivery_id', 'cost', 'discount', 'status', 'invertory_name', 'supplier_name', 'create_time')
        fields = '__all__'


class InventorySerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = Inventory
        # fields = ('id', 'order_id', 'delivery_id', 'cost', 'discount', 'status', 'invertory_name', 'supplier_name', 'create_time')
        fields = '__all__'


class SupplierSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = Supplier
        # fields = ('id', 'order_id', 'delivery_id', 'cost', 'discount', 'status', 'invertory_name', 'supplier_name', 'create_time')
        fields = '__all__'


class StockOutSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = StockOutRecord
        # fields = ('id', 'order_id', 'delivery_id', 'cost', 'discount', 'status', 'invertory_name', 'supplier_name', 'create_time')
        fields = '__all__'


class StockInSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = StockInRecord
        # fields = ('id', 'order_id', 'delivery_id', 'cost', 'discount', 'status', 'invertory_name', 'supplier_name', 'create_time')
        fields = '__all__'


class AfterSaleCaseSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    orderid = serializers.ReadOnlyField(source='order.orderid')
    orderid2 = serializers.ReadOnlyField(source='case_order.orderid')
    jancode = serializers.ReadOnlyField(source='order.jancode')
    product_title = serializers.ReadOnlyField(source='order.product_title')
    quantity = serializers.ReadOnlyField(source='order.quantity')
    case_type_name = serializers.ReadOnlyField(source='case_type.name')
    case_type_metaid = serializers.ReadOnlyField(source='case_type.meta_id')
    process_method_name = serializers.ReadOnlyField(
        source='process_method.name')
    db_number = serializers.ReadOnlyField(source='order.shippingdb.db_number')
    return_jancode = serializers.ReadOnlyField(source='return_product.jancode')

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = AfterSaleCase
        # fields = ('id', 'order_id', 'delivery_id', 'cost', 'discount', 'status', 'invertory_name', 'supplier_name', 'create_time')
        fields = '__all__'


class AfterSaleMetaSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = AfterSaleMeta
        # fields = ('id', 'order_id', 'delivery_id', 'cost', 'discount', 'status', 'invertory_name', 'supplier_name', 'create_time')
        fields = '__all__'


class UexTrackSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = UexTrack
        # fields = ('id', 'order_id', 'delivery_id', 'cost', 'discount', 'status', 'invertory_name', 'supplier_name', 'create_time')
        fields = '__all__'
