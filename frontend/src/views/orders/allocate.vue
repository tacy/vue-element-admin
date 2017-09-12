<!-- TODO 派单页面需要显示购买数量 -->
<template>
  <div class="app-container calendar-list-container">
    <div class="filter-container">
      <el-input @keyup.enter.native="handleFilter" style="width: 140px;" class="filter-item" placeholder="订单号" v-model="listQuery.orderid">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 140px;" class="filter-item" placeholder="条码" v-model="listQuery.jancode">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 140px;" class="filter-item" placeholder="商品名" v-model="listQuery.product_title">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 140px;" class="filter-item" placeholder="收件人" v-model="listQuery.receiver_name">
      </el-input>
      <el-select clearable style="width: 90px" class="filter-item" v-model="listQuery.channel_name" placeholder="渠道">
        <el-option v-for="item in channelnameOptions" :key="item" :label="item" :value="item">
        </el-option>
      </el-select>

      <el-select @change='handleFilter' style="width: 120px" class="filter-item" v-model="listQuery.sort" placeholder="排序">
        <el-option v-for="item in sortOptions" :key="item.key" :label="item.label" :value="item.key">
        </el-option>
      </el-select>

      <el-button class="filter-item" type="primary" v-waves icon="search" @click="handleFilter">搜索</el-button>
      <el-button class="filter-item" type="primary" icon="document" @click="handleDownload">导出</el-button>
    </div>

    <el-table :key='tableKey' :data="list" v-loading.body="listLoading" border fit highlight-current-row style="width: 100%">
      <el-table-column align="center" label="订单号" width="100">
        <template scope="scope">
          <span>{{scope.row.orderid}}</span>
        </template>
      </el-table-column>

      <el-table-column width="200px" align="center" label="商品名称">
        <template scope="scope">
          <span>{{scope.row.product_title}}</span>
        </template>
      </el-table-column>

      <el-table-column width="120px" align="center" label="条码">
        <template scope="scope">
          <span>{{scope.row.jancode}}</span>
        </template>
      </el-table-column>

      <el-table-column width="70px" align="center" label="数量" show-overflow-tooltip>
        <template scope="scope">
          <span>{{scope.row.quantity}}</span>
        </template>
      </el-table-column>

      <el-table-column width="180px" align="center" label="规格">
        <template scope="scope">
          <span>{{scope.row.sku_properties_name}}</span>
        </template>
      </el-table-column>

      <el-table-column width="100px" align="center" label="收件人" show-overflow-tooltip>
        <template scope="scope">
          <span>{{scope.row.receiver_name}}</span>
        </template>
      </el-table-column>

      <el-table-column label="地址" align="center" show-overflow-tooltip>
        <template scope="scope">
          <span class="link-type" @click="handleUpdate(scope.row)">{{scope.row.receiver_address}}</span>
        </template>
      </el-table-column>

      <el-table-column align="center" label="备注">
        <template scope="scope">
          <span>卖:{{scope.row.seller_memo}}|买:{{scope.row.buyer_remark}}</span>
        </template>
      </el-table-column>

      <el-table-column width="120px" align="center" label="支付时间">
        <template scope="scope">
          <span>{{scope.row.piad_time}}</span>
        </template>
      </el-table-column>

      <el-table-column align="center" label="运输" show-overflow-tooltip>
        <template scope="scope">
          <span>{{scope.row.delivery_type}}</span>
        </template>
      </el-table-column>

      <el-table-column align="center" label="操作" width="150">
        <template scope="scope">
          <el-button v-if="scope.row.inventory===null" :disabled="scope.row.jancode===''?true:false" size="small" type="success" @click="handleFetchStock(scope.row)">派单
          </el-button>
          <el-button v-if="scope.row.inventory != null" size="small" type="danger" @click="handleFetchStock(scope.row)">重派
          </el-button>
          <el-button size="small" type="primary" @click="handleProduct(scope.row)">新产品
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-show="!listLoading" class="pagination-container">
      <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange" :current-page.sync="listQuery.page"
        :page-sizes="[10,20,30, 50]" :page-size="listQuery.limit" layout="total, sizes, prev, pager, next, jumper" :total="total">
      </el-pagination>
    </div>

    <el-dialog :title="textMap[dialogStatus]" :visible.sync="dialogFormVisible">
      <el-form class="small-space" :model="temp" label-position="left" label-width="70px" style='width: 400px; margin-left:50px;'>
        <el-form-item label="条码">
          <el-input v-model="temp.jancode"></el-input>
        </el-form-item>
        <el-form-item label="收件人">
          <el-input v-model="temp.receiver_name"></el-input>
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="temp.receiver_mobile"></el-input>
        </el-form-item>
        <el-form-item label="地址">
          <el-input type="textarea" :autosize="{minRows: 2, maxRows: 4}" v-model="temp.receiver_address"></el-input>
        </el-form-item>
        <el-form-item label="总价">
          <el-input :disabled="temp.channel_name==='京东'?false:true" v-model.number="temp.payment" type="number"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogFormVisible = false">取 消</el-button>
        <el-button v-if="dialogStatus=='create'" type="primary" @click="create">确 定</el-button>
        <el-button v-else type="primary" @click="update">确 定</el-button>
      </div>
    </el-dialog>

    <el-dialog title="产品资料" :visible.sync="dialogProductVisible">
      <el-form class="small-space" :model="temp" label-position="left" label-width="70px" style='width: 400px; margin-left:50px;'>
        <el-form-item label="商品编码">
          <el-input v-model="temp.jancode"></el-input>
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="temp.product_title"></el-input>
        </el-form-item>
        <el-form-item label="品牌">
          <el-input v-model="temp.brand"></el-input>
        </el-form-item>
        <el-form-item label="类目">
	  <el-cascader :options="categoryOptions" v-model="temp.category" style='width: 330px;' filterable show-all-levels clearable placeholder="请选择产品类目">
          </el-cascader>
          <!--el-input v-model="temp.category"></el-input-->
        </el-form-item>
        <el-form-item label="规格">
          <el-input v-model="temp.sku_properties_name"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogProductVisible = false">取 消</el-button>
        <el-button type="primary" @click="createProduct">新 建</el-button>
      </div>
    </el-dialog>

    <el-dialog title="订单分配" :visible.sync="dialogAllocationVisible" size="small">
      <div class="filter-container">
        <el-select clearable style="width: 90px" class="filter-item" v-model="temp.inventory" v-on:change="getShipping()" placeholder="仓库">
          <el-option v-for="item in inventoryOptions" :key="item.id" :label="item.name" :value="item.id">
          </el-option>
        </el-select>

        <el-select clearable class="filter-item" style="width: 130px" v-model="temp.shipping" placeholder="发货方式">
          <el-option v-for="item in  shippingOptions" :key="item.name" :label="item.name" :value="item.id">
          </el-option>
        </el-select>
      </div>

      <el-table :data="stockData" border fit highlight-current-row style="width: 100%">
        <el-table-column prop="inventory_name" label="仓库"> </el-table-column>
        <el-table-column prop="quantity" label="在库"> </el-table-column>
        <el-table-column prop="inflight" label="在途"> </el-table-column>
        <el-table-column prop="preallocation" label="占用"> </el-table-column>
      </el-table>

      <span slot="footer" class="dialog-footer">
        <el-button @click="dialogAllocationVisible=false">取 消</el-button>
        <el-button type="primary" @click="allocate">确 定</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
  import { fetchOrder, fetchInventory, fetchCategory, fetchStock, fetchShipping, updateOrder, orderAllocate, productcreate } from 'api/orders';
  import { parseTime } from 'utils';

  export default {
    name: 'table_demo',
    data() {
      return {
        list: null,
        total: null,
        listLoading: true,
        listQuery: {
          page: 1,
          limit: 10,
	  orderid: undefined,
          channel_name: undefined,
          receiver_name: undefined,
	  jancode: undefined,
          status: '待处理',
          sort: '+id'
        },
        temp: {
          id: undefined,
          inventory: 0,
          shipping: 0,
          jancode: '',
          status: '',
	  brand: undefined,
	  channel_name: undefined,
	  payment: undefined,
	  price: undefined,
	  category: undefined,
	  sku_properties_name: undefined
        },
	tempProduct: {
	  name: undefined,
	  jancode: undefined,
	  category: undefined,
	  brand: undefined,
	  specification: undefined
	},
        listStockQuery: {
          jancode: ''
        },
        listShippingQuery: {
          inventory: ''
        },
        channelnameOptions: ['洋码头', '京东'],
        inventoryOptions: [],
        shippingOptions: [],
	categoryOptions: [],
        sortOptions: [{ label: '按ID升序列', key: '+id' }, { label: '按ID降序', key: '-id' }],
        dialogFormVisible: false,
	dialogProductVisible: false,
        dialogStatus: '',
        textMap: {
          update: '编辑',
          create: '创建'
        },
        dialogAllocationVisible: false,
        stockData: [],
        tableKey: 0
      }
    },
    created() {
      this.getList();
      this.getInventory();
      this.getCategory();
    },
    methods: {
      getList() {
        this.listLoading = true;
        fetchOrder(this.listQuery).then(response => {
          this.list = response.data.results;
          this.total = response.data.count;
          this.listLoading = false;
        })
      },
      getCategory() {
        fetchCategory().then(response => {
	  this.categoryOptions = response.data.results;
	})
      },
      getInventory() {
        fetchInventory().then(response => {
          this.inventoryOptions = response.data.results;
        })
      },
      getShipping() {
        if (this.temp.inventory === null) {
          this.temp.shipping = null;
          return
        }
        this.listShippingQuery.inventory = this.temp.inventory;
        fetchShipping(this.listShippingQuery).then(response => {
          this.shippingOptions = response.data.results;
        })
      },
      handleFilter() {
        this.getList();
      },
      handleSizeChange(val) {
        this.listQuery.limit = val;
        this.getList();
      },
      handleCurrentChange(val) {
        this.listQuery.page = val;
        this.getList();
      },
      timeFilter(time) {
        if (!time[0]) {
          this.listQuery.start = undefined;
          this.listQuery.end = undefined;
          return;
        }
        this.listQuery.start = parseInt(+time[0] / 1000);
        this.listQuery.end = parseInt((+time[1] + 3600 * 1000 * 24) / 1000);
      },
      handleModifyStatus(row, status) {
        this.$message({
          message: '操作成功',
          type: 'success'
        });
        row.status = status;
      },
      handleProduct(row) {
        this.temp = Object.assign({}, row);
        this.dialogProductVisible = true
      },
      createProduct() {
        this.tempProduct.name = this.temp.product_title,
	this.tempProduct.jancode = this.temp.jancode,
	this.tempProduct.brand = this.temp.brand,
	this.tempProduct.category = this.temp.category[1],
	this.tempProduct.specification = this.temp.sku_properties_name,
	productcreate(this.tempProduct).then(response => {
	  this.dialogProductVisible = false;
	  this.$notify({
	    title: '成功',
	    message: '创建成功',
	    type: 'success',
	    duration: 2000
	  });
        })

      },
      handleUpdate(row) {
        this.temp = Object.assign({}, row);
        this.dialogStatus = 'update';
        this.dialogFormVisible = true;
      },
      handleDelete(row) {
        this.$notify({
          title: '成功',
          message: '删除成功',
          type: 'success',
          duration: 2000
        });
        const index = this.list.indexOf(row);
        this.list.splice(index, 1);
      },
      update() {
        for (const v of this.list) {
          if (v.id === this.temp.id) {
	    if (v.payment !== this.temp.payment) {
	      this.temp.price = this.temp.payment/v.quantity;
	    }
            const index = this.list.indexOf(v);
            this.list.splice(index, 1, this.temp);
            break;
          }
        }
        updateOrder(this.temp, '/order/' + this.temp.id + '/').then(response => {
          this.dialogFormVisible = false;
          this.$notify({
            title: '成功',
            message: '更新成功',
            type: 'success',
            duration: 2000
          });
        });
      },
      allocate() {
        orderAllocate(this.temp).then(response => {
          // 刷新列表数据
          for (const v of this.list) {
            if (v.id === this.temp.id) {
              const index = this.list.indexOf(v);
              this.list.splice(index, 1, this.temp);
              break;
            }
          }

          this.dialogAllocationVisible = false;
          this.$notify({
            title: '成功',
            message: '派单成功',
            type: 'success',
            duration: 2000
          });
        })
      },
      resetTemp() {
        this.temp = {
          id: undefined,
          channel_name: 0,
          remark: '',
          title: '',
          status: 'published',
          type: ''
        };
      },
      handleFetchStock(row) {
        this.temp = Object.assign({}, row);
        this.listStockQuery.jancode = this.temp.jancode;
        this.getShipping();
        fetchStock(this.listStockQuery).then(response => {
          this.stockData = response.data.results;
          // this.inventoryOptions = response.data.results;  // 需要优化, 构造{id,name}结构
          this.dialogAllocationVisible = true;
        })
      },
      handleDownload() {
        require.ensure([], () => {
          const { export_json_to_excel } = require('vendor/Export2Excel');
          const tHeader = ['时间', '地区', '类型', '标题', '重要性'];
          const filterVal = ['timestamp', 'province', 'type', 'title', 'channel_name'];
          const data = this.formatJson(filterVal, this.list);
          export_json_to_excel(tHeader, data, 'table数据');
        })
      },
      formatJson(filterVal, jsonData) {
        return jsonData.map(v => filterVal.map(j => {
          if (j === 'timestamp') {
            return parseTime(v[j])
          } else {
            return v[j]
          }
        }))
      }
    }
  }
</script>
