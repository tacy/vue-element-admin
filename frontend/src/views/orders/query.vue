<template>
  <div class="app-container calendar-list-container">
    <div class="filter-container">
      <el-input @keyup.enter.native="handleFilter" style="width: 150px;" class="filter-item" placeholder="订单号" v-model="listQuery.orderid">
      </el-input>

      <el-input @keyup.enter.native="handleFilter" style="width: 150px;" class="filter-item" placeholder="收件人" v-model="listQuery.receiver_name">
      </el-input>

      <el-input @keyup.enter.native="handleFilter" style="width: 150px;" class="filter-item" placeholder="条码" v-model="listQuery.jancode">
      </el-input>

      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.inventory" placeholder="仓库">
        <el-option v-for="item in inventoryOptions" :key="item.id" :label="item.name" :value="item.id">
        </el-option>
      </el-select>

      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.channel_name" placeholder="渠道">
        <el-option v-for="item in channelOptions" :key="item" :label="item" :value="item">
        </el-option>
      </el-select>

      <el-button class="filter-item" type="primary" v-waves icon="search" @click="handleFilter">搜索</el-button>
      <el-button class="filter-item" type="success" style="float:right" v-waves icon="edit" @click="handleCreate">录入订单</el-button>
    </div>

    <el-table :data="list" v-loading.body="listLoading" @selection-change="handleSelect" border fit highlight-current-row style="width: 100%">
      <el-table-column type="expand" width="50px">
	<template scope="scope">
	  <el-form label-position="left" inline class="table-expand">
	    <el-form-item label="商品:" label-width="50px">
	      <span>{{ scope.row.product_title }}</span>
	    </el-form-item>
	    <el-form-item label="数量:" label-width="50px">
	      <span>{{ scope.row.quantity }}</span>
	    </el-form-item>
	    <el-form-item label="规格:" label-width="50px">
	      <span>{{ scope.row.sku_properties_name }}</span>
	    </el-form-item>
	    <el-form-item label="证件:" label-width="50px">
	      <span>{{ scope.row.receiver_idcard }}</span>
	    </el-form-item>
	  </el-form>
	</template>
      </el-table-column>
      <el-table-column align="center" label="订单号" width="100px">
	<template scope="scope">
	  <span>{{scope.row.orderid}}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="渠道" width="80px">
	<template scope="scope">
	  <span>{{scope.row.channel_name}}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="状态" width="100px">
	<template scope="scope">
	  <span>{{scope.row.status}}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="仓库" width="70px">
	<template scope="scope">
	  <span>{{scope.row.inventory_name}}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="发货方式" width="100px">
	<template scope="scope">
	  <span>{{scope.row.shipping_name}}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="收件人" width="95px">
	<template scope="scope">
	  <span>{{scope.row.receiver_name}}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="电话" width="115px" show-overflow-tooltip>
	<template scope="scope">
	  <span>{{scope.row.receiver_mobile}}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="地址" show-overflow-tooltip>
	<template scope="scope">
	  <span>{{scope.row.receiver_address}}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="条码" width="130px" show-overflow-tooltip>
	<template scope="scope">
	  <span>{{scope.row.jancode}}</span>
	</template>
      </el-table-column>
      <!--el-table-column align="center" label="商品名" show-overflow-tooltip>
	<template scope="scope">
	  <span>{{scope.row.product_title}}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="规格" show-overflow-tooltip>
	<template scope="scope">
	  <span>{{scope.row.sku_properties_name}}</span>
	</template>
      </el-table-column-->
      <el-table-column align="center" label="操作" width="100">
	<template scope="scope">
	  <el-button size="small" :disabled="checkShippingdb(scope.row)" type="danger" @click="handleDelete(scope.row)">删 除
	  </el-button>
	</template>
      </el-table-column>
    </el-table>

    <div v-show="!listLoading" class="pagination-container">
      <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange" :current-page.sync="listQuery.page"
        :page-sizes="[10,20,30, 50]" :page-size="listQuery.limit" layout="total, sizes, prev, pager, next, jumper" :total="total">
      </el-pagination>
    </div>

    <el-dialog title="录入订单" size="large" :visible.sync="dialogCreateVisible">
      <el-form class="small-space" :model="temp" label-position="left" label-width="80px">
        <el-row>
	  <el-col :span="6">
	    <el-form-item label="姓名:" label-width="50px">
	      <el-input style="width: 180px" v-model="orderData.receiver_name"></el-input>
	    </el-form-item>
 	  </el-col>
          <el-col :span="6">
	    <el-form-item label="电话:" label-width="50px">
	      <el-input style="width: 180px" v-model="orderData.receiver_mobile"></el-input>
	    </el-form-item>
	  </el-col>
	  <el-col :span="6">
	    <el-form-item label="证件:" label-width="50px">
	      <el-input style="width: 180px" v-model="orderData.receiver_idcard"></el-input>
	    </el-form-item>
 	  </el-col>
          <el-col :span="6">
	    <el-form-item label="邮编:" label-width="50px">
	      <el-input style="width: 180px" v-model="orderData.receiver_zip"></el-input>
	    </el-form-item>
	  </el-col>
	</el-row>
        <el-row>
	  <el-col :span="12">
	    <el-form-item label="地址:" label-width="50px">
	      <el-input style="width: 460px" v-model="orderData.receiver_address"></el-input>
	    </el-form-item>
 	  </el-col>
          <el-col :span="12">
	    <el-form-item label="备注:" label-width="50px">
	      <el-input style="width: 460px" v-model="orderData.seller_memo"></el-input>
	    </el-form-item>
	  </el-col>
	</el-row>
	<el-row v-for="(p, index) in orderData.products">
          <el-col :span="4">
	    <el-form-item label="条码:" label-width="50px">
	      <el-input style="width: 120px" v-model="p.jancode"></el-input>
	    </el-form-item>
	  </el-col>
          <el-col :span="8">
	    <el-form-item label="名称:" label-width="50px">
	      <el-input style="width: 275px" v-model="p.product_title"></el-input>
	    </el-form-item>
	  </el-col>
          <el-col :span="4">
	    <el-form-item label="规格:" label-width="50px">
	      <el-input style="width: 120px" v-model="p.sku_properties_name"></el-input>
	    </el-form-item>
	  </el-col>
          <el-col :span="3">
	    <el-form-item label="数量:" label-width="50px">
	      <el-input style="width: 80px" v-model="p.quantity"></el-input>
	    </el-form-item>
	  </el-col>
          <el-col :span="5">
	    <el-form-item label="价格:" label-width="50px">
	      <el-input style="width: 88px" v-model="p.price"></el-input>
	      <el-button type="danger" icon="delete" @click="deleteProduct(p)"></el-button>
	    </el-form-item>
	  </el-col>
	</el-row>
	<el-form-item align="center" >
	  <el-button type="success" @click="addProduct">新增商品</el-button>
	</el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogCreateVisible=false">取消</el-button>
        <el-button type="primary" @click="createTPROrder">提交</el-button>
      </div>
    </el-dialog>

    <el-dialog title="删除订单" :visible.sync="dialogFormVisible">
      <el-form class="small-space" :model="temp" label-position="left" label-width="70px" style='width: 400px; margin-left:50px;'>
        <el-form-item label="原因">
          <el-input type="textarea" :autosize="{minRows: 2, maxRows: 4}" v-model="temp.conflict_feedback"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogFormVisible=false">取 消</el-button>
        <el-button type="primary" @click="deleteOrder()">确 定</el-button>
      </div>
    </el-dialog>

  </div>
</template>

<style>
  .table-expand {
    font-size: 0;
  }
  .table-expand label {
    width: 90px;
    color: #99a9bf;
  }
  .table-expand .el-form-item {
    margin-right: 0;
    margin-bottom: 0;
    width: 50%;
  }
</style>

<script>
  import { parseTime } from 'utils';
  import { fetchInventory, fetchSupplier, fetchOrder, orderDelete, orderTPRCreate } from 'api/orders';

  export default {
    data() {
      return {
        list: [],
        listLoading: true,
        total: null,
	dialogFormVisible: false,
	dialogCreateVisible: false,
        inventoryOptions: [],
	channelOptions: ['洋码头', '京东'],
	statusOptions: ['在途', '删除', '入库'],
        listQuery: {
          page: 1,
          limit: 10,
          inventory: undefined,
	  channel_name: undefined,
	  receiver_name: undefined,
	  jancode: undefined,
	  orderid: undefined
        },
	orderData: {
	  seller_name: '东京彩虹桥',
	  channel_name: '京东',
	  receiver_name: undefined,
	  receiver_address: undefined,
	  receiver_zip: undefined,
	  receiver_mobile: undefined,
	  receiver_idcard: undefined,
	  seller_memo: undefined,
	  products: [
	    {
	      jancode: undefined,
	      quantity: undefined,
	      price: undefined,
	      product_title: undefined,
	      sku_properties_name: undefined
	    },
	  ]
	},
	temp: {
          id: undefined,
	  status: undefined,
	  conflict_feedback: undefined
        }
      }
    },
    created() {
      this.getInventory();
      this.getOrder();
    },
    methods: {
      getOrder() {
        this.listLoading = true;
        fetchOrder(this.listQuery).then(response => {
          this.list = response.data.results;
          this.total = response.data.count;
          this.listLoading = false;
        })
      },
      getInventory() {
        fetchInventory().then(response => {
          this.inventoryOptions = response.data.results;
        })
      },
      handleFilter() {
        this.getOrder();
      },
      handleSizeChange(val) {
        this.listQuery.limit = val;
        this.getOrder();
      },
      handleCurrentChange(val) {
        this.listQuery.page = val;
        this.getOrder();
      },
      //不能删除订单, 如果订单已经分配了DB单号
      checkShippingdb(row) {
        if ( row.shippingdb !== null ) {
	  return true
	};
	if (row.status === '已删除' ) {
	  return true
	};
      },
      deleteProduct(item) {
        var index = this.orderData.products.indexOf(item)
        if (index !== -1) {
          this.orderData.products.splice(index, 1)
        }
      },
      addProduct() {
        this.orderData.products.push({
	  jancode: undefined,
	  quantity: undefined,
	  price: undefined,
	  product_title: undefined,
	  sku_properties_name: undefined
        });
      },
      handleDelete(row) {
        this.temp = Object.assign({}, row);
	this.dialogFormVisible = true;
      },
      handleCreate() {
        this.dialogCreateVisible = true
      },
      createTPROrder() {
        orderTPRCreate(this.orderData).then(response => {
          this.$notify({
            title: '成功',
            message: '订单创建成功',
            type: 'success',
            duration: 2000
          });
	  this.dialogCreateVisible = false
	});
      },
      deleteOrder() {
        orderDelete(this.temp).then(response => {
	  this.temp.status = '已删除';
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
