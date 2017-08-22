<template>
  <div>
      <div class="filter-container">
	<el-button class="filter-item" style="float:right" @click="handlePurchase" type="primary" icon="edit">保存采购单</el-button>
      </div>
      <el-table :data="postData.data" v-loading.body="listLoading" border fit highlight-current-row style="width: 100%">

	<el-table-column align="center" label="条码" width="150">
	  <template scope="scope">
	    <span class="link-type" @click="getOrder(scope.row)">{{scope.row.jancode}}</span>
	  </template>
	</el-table-column>

	<!--el-table-column min-width="300px" label="标题">
	  <template scope="scope">
	    <span class="link-type" @click="handleUpdate(scope.row)">{{scope.row.title}}</span>
	    <el-tag>{{scope.row.type}}</el-tag>
	  </template>
	</el-table-column-->

	<el-table-column align="center" label="商品名称" width="250" show-overflow-tooltip>
	  <template scope="scope">
	    <span>{{scope.row.product_name}}</span>
	  </template>
	</el-table-column>

	<el-table-column align="center" label="规格" show-overflow-tooltip>
	  <template scope="scope">
	    <span>{{scope.row.sku_properties_name}}</span>
	  </template>
	</el-table-column>

	<el-table-column align="center" label="待采" width="65">
	  <template scope="scope">
	    <span>{{scope.row.qty}}</span>
	  </template>
	</el-table-column>

	<el-table-column align="center" label="渠道" width="100">
	  <template scope="scope">
	    <el-select clearable v-model="scope.row.supplier" placeholder="渠道">
	      <el-option v-for="item in supplierOptions" :key="item.id" :label="item.name" :value="item.id">
	      </el-option>
	    </el-select>
	  </template>
	</el-table-column>

	<el-table-column align="center" label="实采" width="100">
	  <template scope="scope">
	    <el-input size="small" v-model.number="scope.row.quantity"></el-input>
	  </template>
	</el-table-column>

	<el-table-column align="center" label="价格" width="100">
	  <template scope="scope">
	    <el-input size="small" v-model.number="scope.row.price" placeholder=""></el-input>
	  </template>
	</el-table-column>

	<el-table-column align="center" label="注文编号" width="150">
	  <template scope="scope">
	    <el-input size="small" v-model="scope.row.purchaseorderid" placeholder=""></el-input>
	  </template>
	</el-table-column>

      </el-table>

    <el-dialog title="标记疑难" :visible.sync="dialogConflictVisible" size="small">
      <el-table :data="orderData" border fit highlight-current-row style="width: 100%">
	<el-table-column align="center" label="订单编号">
	  <template scope="scope">
	    <span>{{scope.row.orderid}}</span>
	  </template>
        </el-table-column>

        <el-table-column align="center" label="建议方式">
  	  <template scope="scope">
	    <el-select clearable v-model="scope.row.conflict" placeholder="选择">
	      <el-option v-for="item in conflictOptions" :key="item" :label="item" :value="item">
	      </el-option>
	    </el-select>
  	  </template>
        </el-table-column>

	<el-table-column align="center" label="备注" width="350px">
	  <template scope="scope">
    	    <el-input size="small" v-model="scope.row.conflict_memo"></el-input>
	  </template>
	</el-table-column>
      </el-table>

      <span slot="footer" class="dialog-footer">
        <el-button @click="dialogConflictVisible=false">取 消</el-button>
        <el-button type="primary" @click="handleConflict">确 定</el-button>
      </span>
    </el-dialog>

  </div>
</template>

<script>
  import { fetchPurchase, fetchOrder, fetchSupplier, orderPurchase, orderMarkConflict } from 'api/orders';

  export default {
    props: {
      inventory: {
        type: Number
      }
    },
    data() {
      return {
        postData: {
	  data: [],
	  inventory: this.inventory,
	  queryTime: undefined
	},
        listLoading: true,
	queryTime: undefined,
        total: null,
        dialogConflictVisible: false,
        supplierOptions: [],
        listQuery: {
          page: 1,
          limit: 10,
          inventory: this.inventory
        },
        orderQuery: {
          inventory: '',
          jancode: '',
          status: ''
        },
        orderData: [],
	conflictMarkedJancode: '',
        conflictOptions: ['更换', '退款'],
      }
    },
    created() {
      this.getSupplier();
      this.getPurchase();
    },
    methods: {
      getPurchase() {
        // this.$emit('create'); // for test
        this.listLoading = true;
        this.postData.data = [];
        fetchPurchase(this.listQuery).then(response => {
          for (const v of response.data.data) {
            v.quantity = v.qty;
            v.supplier = '';
            this.postData.data.push(v);
          }
          this.total = response.data.total;
	  this.queryTime = response.data.queryTime;
          this.listLoading = false;
        })
      },
      getSupplier() {
        fetchSupplier().then(response => {
          this.supplierOptions = response.data.results;
        })
      },
      getOrder(row) {
        this.orderQuery.jancode = row.jancode;
        this.orderQuery.inventory = this.inventory;
        this.dialogConflictVisible = true;
        this.orderQuery.status = '待采购';
        fetchOrder(this.orderQuery).then(response => {
          this.orderData = response.data.results;
        })
      },
      handlePurchase() {
        this.postData.queryTime = this.queryTime;
        orderPurchase(this.postData).then(response => {
          this.getPurchase();
        })
      },
      handleConflict() {
        orderMarkConflict(this.orderData).then(response => {
          this.dialogConflictVisible = false;
	  for (const v of this.postData.data) {
	    if (v.jancode === this.orderQuery.jancode) {
	      const index = this.postData.data.indexOf(v);
	      this.postData.data.splice(index, 1);
	    }
	  }
        })
      }
    }
  }
</script>
