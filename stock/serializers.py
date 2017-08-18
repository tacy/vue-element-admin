from rest_framework import serializers
# from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from .models import PurchaseOrder, Product, Order, Stock, Shipping, Inventory, PurchaseOrderItem, Supplier, ShippingDB


class TokenSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    group = serializers.ReadOnlyField(source='user.first_name')

    class Meta:
        model = Token
        fields = '__all__'


class PurchaseOrderSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    purchaseorderitem = serializers.StringRelatedField(many=True)
    supplier_name = serializers.ReadOnlyField(source='supplier.name')
    inventory_name = serializers.ReadOnlyField(source='inventory.name')

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = PurchaseOrder
        # fields = ('id', 'order_id', 'delivery_id', 'cost', 'discount', 'status', 'invertory_name', 'supplier_name', 'create_time')
        fields = '__all__'


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = PurchaseOrderItem
        # fields = ('id', 'order_id', 'delivery_id', 'cost', 'discount', 'status', 'invertory_name', 'supplier_name', 'create_time')
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    category_name = serializers.ReadOnlyField(
        source='category.category_cn_name')

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = Product
        # fields = ('id', 'order_id', 'delivery_id', 'cost', 'discount', 'status', 'invertory_name', 'supplier_name', 'create_time')
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    shipping_name = serializers.ReadOnlyField(source='shipping.name')
    inventory_name = serializers.ReadOnlyField(source='inventory.name')

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = Order
        # fields = ('id', 'order_id', 'delivery_id', 'cost', 'discount', 'status', 'invertory_name', 'supplier_name', 'create_time')
        fields = '__all__'


class StockSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""
    inventory_name = serializers.ReadOnlyField(source='inventory.name')

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
