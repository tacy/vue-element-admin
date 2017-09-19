<template>
  <div class="app-container calendar-list-container">
    <div class="filter-container">
      <el-input @keyup.enter.native="handleFilter" style="width: 200px;" class="filter-item" placeholder="注文编号" v-model="listQuery.orderid">
      </el-input>

      <el-input @keyup.enter.native="handleFilter" style="width: 150px;" class="filter-item" placeholder="商品条码" v-model="listQuery.jancode">
      </el-input>

      <el-input @keyup.enter.native="handleFilter" style="width: 200px;" class="filter-item" placeholder="商品名称" v-model="listQuery.product_name">
      </el-input>

      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.inventory" placeholder="仓库">
        <el-option v-for="item in inventoryOptions" :key="item.id" :label="item.name" :value="item.id">
        </el-option>
      </el-select>

      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.supplier" placeholder="采购渠道">
        <el-option v-for="item in supplierOptions" :key="item.id" :label="item.name" :value="item.id">
        </el-option>
      </el-select>

      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.status" placeholder="状态">
        <el-option v-for="item in statusOptions" :key="item" :label="item" :value="item">
        </el-option>
      </el-select>

      <el-button class="filter-item" type="primary" v-waves icon="search" @click="handleFilter">搜索</el-button>
    </div>

    <el-table :data="list" v-loading.body="listLoading" border fit highlight-current-row style="width: 100%">

      <el-table-column align="center" label="注文编号" width="150px">
	<template scope="scope">
	  <span class="link-type" @click="getItem(scope.row)">{{scope.row.orderid}}</span>
	</template>
      </el-table-column>

      <el-table-column align="center" label="仓库" width="150px" show-overflow-tooltip>
	<template scope="scope">
	  <span>{{scope.row.inventory_name}}</span>
	</template>
      </el-table-column>

      <el-table-column align="center" label="采购渠道" show-overflow-tooltip>
	<template scope="scope">
	  <span>{{scope.row.supplier_name}}</span>
	</template>
      </el-table-column>

      <el-table-column align="center" label="状态">
	<template scope="scope">
	  <span>{{scope.row.status}}</span>
	</template>
      </el-table-column>

      <el-table-column align="center" label="采购时间" width="220px">
	<template scope="scope">
	  <span>{{scope.row.create_time}}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="操作" width="180">
        <template scope="scope">
          <el-button size="small" :disabled="scope.row.status === '入库' ? true:false" type="success" @click="handleStockIn(scope.row)">入 库
	  </el-button>
          <el-button size="small" :disabled="scope.row.status === '在途' ? false:true" type="danger" @click="handleDelete(scope.row)">删 除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-show="!listLoading" class="pagination-container">
      <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange" :current-page.sync="listQuery.page"
        :page-sizes="[10,20,30, 50]" :page-size="listQuery.limit" layout="total, sizes, prev, pager, next, jumper" :total="total">
      </el-pagination>
    </div>

    <el-dialog title="订单明细" :visible.sync="dialogItemVisible" size="small">
      <el-table :data="itemData" border fit highlight-current-row style="width: 100%">
	<el-table-column align="center" label="商品编码" width="150px">
	  <template scope="scope">
	    <span>{{scope.row.jancode}}</span>
	  </template>
        </el-table-column>
	<el-table-column align="center" label="商品名称">
	  <template scope="scope">
	    <span>{{scope.row.product_name}}</span>
	  </template>
        </el-table-column>
	<el-table-column align="center" label="数量" width="80px">
	  <template scope="scope">
	    <span>{{scope.row.quantity}}</span>
	  </template>
        </el-table-column>
	<el-table-column align="center" label="价格" width="100px">
	  <template scope="scope">
	    <span>{{scope.row.price}}</span>
	  </template>
        </el-table-column>
      </el-table>

      <span slot="footer" class="dialog-footer">
        <el-button type="primary" @click="dialogItemVisible=false">确 定</el-button>
      </span>
    </el-dialog>

    <el-dialog title="删除采购单" :visible.sync="dialogFormVisible">
      <el-form class="small-space" :model="temp" label-position="left" label-width="70px" style='width: 400px; margin-left:50px;'>
        <el-form-item label="删除原因">
          <el-input type="textarea" :autosize="{minRows: 2, maxRows: 4}" v-model="temp.memo"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogFormVisible=false">取 消</el-button>
        <el-button type="primary" @click="deletePurchaseOrder()">确 定</el-button>
      </div>
    </el-dialog>

    <el-dialog title="采购入库" size="large" :visible.sync="dialogPOItemVisible">
      <el-form class="small-space" :model="poitemp" label-position="left" label-width="80px">
	<el-row v-for="(p, index) in poitemp.pois">
          <el-col :span="4">
	    <el-form-item label="条码:" label-width="50px">
	      <el-input :disabled="true" style="width: 120px" v-model="p.jancode"></el-input>
	    </el-form-item>
	  </el-col>
          <el-col :span="8">
	    <el-form-item label="名称:" label-width="50px">
	      <el-input :disabled="true" style="width: 300px" v-model="p.product_title"></el-input>
	    </el-form-item>
	  </el-col>
          <el-col :span="4">
	    <el-form-item label="规格:" label-width="50px">
	      <el-input :disabled="true" style="width: 120px" v-model="p.sku_properties_name"></el-input>
	    </el-form-item>
	  </el-col>
          <el-col :span="3">
	    <el-form-item label="数量:" label-width="50px">
	      <el-input :disabled="true" style="width: 80px" v-model="p.quantity"></el-input>
	    </el-form-item>
	  </el-col>
          <el-col :span="5">
	    <el-form-item label="实际到库:" label-width="80px">
	      <el-input style="width: 120px" :disabled="p.status" v-model.number="p.qty" type="number"></el-input>
	    </el-form-item>
	  </el-col>
	</el-row>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogPOItemVisible=false">取消</el-button>
        <el-button type="primary" @click="clearPurchaseOrder">提交</el-button>
      </div>
    </el-dialog>

  </div>
</template>

<script>
  import { parseTime } from 'utils';
  import { fetchInventory, fetchSupplier } from 'api/orders';
  import { fetchPurchaseOrder, fetchPurchaseOrderItem, purchaseOrderDelete, purchaseOrderClear } from 'api/purchases';

  export default {
    data() {
      return {
        list: [],
        listLoading: true,
        total: null,
        dialogItemVisible: false,
	dialogPOItemVisible: false,
	dialogFormVisible: false,
        inventoryOptions: [],
	supplierOptions: [],
	statusOptions: ['在途', '部分入库', '删除', '入库'],
        listQuery: {
          page: 1,
          limit: 10,
	  status: undefined,
          inventory: undefined,
	  supplier: undefined,
	  orderid: undefined,
	  jancode: undefined,
	  product_name: undefined,
        },
	temp: {
          id: undefined,
	  status: undefined
        },
	poitemp: {
	  id: undefined,
	  inventory: undefined,
	  pois: [],
	},
	listItem: {
	  purchaseorder: undefined
	},
        itemData: [],
      }
    },
    created() {
      this.getInventory();
      this.getSupplier();
      this.getPurchaseOrder();
    },
    methods: {
      getPurchaseOrder() {
        this.listLoading = true;
        fetchPurchaseOrder(this.listQuery).then(response => {
          this.list = response.data.results;
          for (const t of this.list) {
 	    const index = this.list.indexOf(t);
	    const tmp = [];
	    for (const o of t.purchaseorderitem) {
	      const poi = o.split('@')
	      const qty = null
	      const disabledStatus = false
	      if ( poi[5]==='已入库' ) {
	        qty = poi[3]
		disabledStatus = true
	      }
	      tmp.push({
	        jancode: poi[0],
		product_title: poi[1],
		sku_properties_name: poi[2],
		quantity: poi[3],
		price: poi[4],
		qty: qty,
		status: disabledStatus
	      });
	    }
	    this.list[index].pois = tmp;
	  }
          this.total = response.data.count;
          this.listLoading = false;
        })
      },
      getInventory() {
        fetchInventory().then(response => {
          this.inventoryOptions = response.data.results;
        })
      },
      getSupplier() {
        fetchSupplier().then(response => {
          this.supplierOptions = response.data.results;
        })
      },
      handleFilter() {
        this.listQuery.page=1;
        this.getPurchaseOrder();
      },
      handleSizeChange(val) {
        this.listQuery.limit = val;
        this.getPurchaseOrder();
      },
      handleCurrentChange(val) {
        this.listQuery.page = val;
        this.getPurchaseOrder();
      },
      getItem(row) {
        this.dialogItemVisible = true;
	this.listItem.purchaseorder = row.id,
        fetchPurchaseOrderItem(this.listItem).then(response => {
          this.itemData = response.data.results;
        })
      },
      handleDelete(row) {
        this.temp = Object.assign({}, row);
	this.dialogFormVisible = true;
      },
      handleStockIn(row) {
        this.poitemp = row;
	this.dialogPOItemVisible = true;
      },
      clearPurchaseOrder() {
        purchaseOrderClear(this.poitemp).then(response => {
	  this.$notify({
	    title: '成功',
	    message: '入库成功',
	    type: 'success',
	    duration: 2000
	  });
	  this.dialogPOItemVisible = false;
	  this.handleFilter();
	});
      },
      deletePurchaseOrder() {
        purchaseOrderDelete(this.temp).then(response => {
          this.temp.status = '删除';
	  for (const v of this.list) {
	    if (v.id === this.temp.id) {
	      const index = this.list.indexOf(v);
	      this.list.splice(index, 1, this.temp);
	      break;
	    }
          }
	  this.dialogFormVisible = false
        })
      }
    }
  }
</script>
