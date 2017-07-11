from rest_framework import serializers
from .models import PurchaseOrder, Product, Order


class PurchaseOrderSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = PurchaseOrder
        # fields = ('id', 'order_id', 'delivery_id', 'cost', 'discount', 'status', 'invertory_name', 'supplier_name', 'create_time')
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = Product
        # fields = ('id', 'order_id', 'delivery_id', 'cost', 'discount', 'status', 'invertory_name', 'supplier_name', 'create_time')
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = Order
        # fields = ('id', 'order_id', 'delivery_id', 'cost', 'discount', 'status', 'invertory_name', 'supplier_name', 'create_time')
        fields = '__all__'
