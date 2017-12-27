from django.contrib import admin
from .models import Inventory, ExportOrderLog, Task, Shipping, Supplier, AfterSaleMeta, CostType

# Register your models here.
admin.site.register(Inventory)
admin.site.register(Supplier)
admin.site.register(Shipping)
admin.site.register(ExportOrderLog)
admin.site.register(Task)
admin.site.register(AfterSaleMeta)
admin.site.register(CostType)
