<template>
  <div class="app-container calendar-list-container">
    <div class="filter-container">
      <el-input @keyup.enter.native="handleFilter" style="width: 200px;" class="filter-item" placeholder="订单号" v-model="listQuery.orderid">
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
      <el-button class="filter-item" style="margin-left: 10px;" @click="handleCreate" type="primary" icon="edit">添加</el-button>
      <el-button class="filter-item" type="primary" icon="document" @click="handleDownload">导出</el-button>
      <el-checkbox class="filter-item" @change='tableKey=tableKey+1' v-model="showAuditor">显示审核人</el-checkbox>
    </div>

    <el-table :key='tableKey' :data="list" v-loading.body="listLoading" border fit highlight-current-row style="width: 100%">
      <el-table-column align="center" label="订单号" width="100">
        <template scope="scope">
          <span>{{scope.row.orderid}}</span>
        </template>
      </el-table-column>

      <el-table-column width="200px" align="center" label="商品名称" show-overflow-tooltip>
        <template scope="scope">
          <span>{{scope.row.product_title}}</span>
        </template>
      </el-table-column>

      <el-table-column width="150px" align="center" label="商品编码" show-overflow-tooltip>
        <template scope="scope">
          <span>{{scope.row.jancode}}</span>
        </template>
      </el-table-column>

      <el-table-column width="100px" align="center" label="规格" show-overflow-tooltip>
        <template scope="scope">
          <span>{{scope.row.sku_properties_name}}</span>
        </template>
      </el-table-column>

      <el-table-column width="200px" label="收件人地址" align="center" show-overflow-tooltip>
        <template scope="scope">
          <span class="link-type" @click="handleUpdate(scope.row)">{{scope.row.receiver_address}}</span>
        </template>
      </el-table-column>

      <el-table-column width="130px" align="center" label="备注" show-overflow-tooltip>
        <template scope="scope">
          <span>卖:{{scope.row.seller_memo}}|买:{{scope.row.buyer_remark}}</span>
        </template>
      </el-table-column>

      <el-table-column width="110px" align="center" label="运输" show-overflow-tooltip>
        <template scope="scope">
          <span>{{scope.row.delivery_type}}</span>
        </template>
      </el-table-column>

      <el-table-column width="110px" v-if='showAuditor' align="center" label="审核人">
        <template scope="scope">
          <span style='color:red;'>{{scope.row.auditor}}</span>
        </template>
      </el-table-column>

      <el-table-column align="center" label="操作" width="68">
        <template scope="scope">
          <el-button v-if="scope.row.status=='待处理'" size="small" type="success" @click="handleFetchStock(scope.row)">派 单
          </el-button>
          <el-button v-if="scope.row.status!='待处理'" size="small" type="danger" @click="handleFetchStock(scope.row)">重 派
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
        <el-form-item label="商品编码">
          <el-input v-model="temp.jancode"></el-input>
        </el-form-item>
        <el-form-item label="收件人">
          <el-input v-model="temp.receiver_name"></el-input>
        </el-form-item>
        <el-form-item label="收件人电话">
          <el-input v-model="temp.receiver_mobile"></el-input>
        </el-form-item>
        <el-form-item label="收件人地址">
          <el-input type="textarea" :autosize="{minRows: 2, maxRows: 4}" v-model="temp.receiver_address"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogFormVisible = false">取 消</el-button>
        <el-button v-if="dialogStatus=='create'" type="primary" @click="create">确 定</el-button>
        <el-button v-else type="primary" @click="update">确 定</el-button>
      </div>
    </el-dialog>

    <el-dialog title="订单分配" :visible.sync="dialogAllocationVisible" size="small">
      <div class="filter-container">
        <el-select clearable style="width: 90px" class="filter-item" v-model="temp.order_inventory" v-on:change="getShipping()" placeholder="仓库">
          <el-option v-for="item in inventoryOptions" :key="item" :label="item" :value="item">
          </el-option>
        </el-select>

        <el-select clearable class="filter-item" style="width: 130px" v-model="temp.order_shipping_name" placeholder="发货方式">
          <el-option v-for="item in  shippingOptions" :key="item.name" :label="item.name" :value="item.name">
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
  import { fetchList, fetchStock, fetchShipping, updateOrder, allocateOrder, fetchPv } from 'api/orders';
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
          channel_name: undefined,
          title: undefined,
          type: undefined,
          sort: '+id'
        },
        temp: {
          id: undefined,
          order_inventory: '',
          order_shipping_name: '',
          jancode: '',
          status: ''
        },
        allocateOrderData: {
          order: [],
          stock: []
        },
        listStockQuery: {
          jancode: ''
        },
        listShippingQuery: {
          shipping_inventory: ''
        },
        channelnameOptions: ['洋码头', '天狗'],
        inventoryOptions: ['东京', '贝海', 'UEX', '广州'],
        shippingOptions: [],
        sortOptions: [{ label: '按ID升序列', key: '+id' }, { label: '按ID降序', key: '-id' }],
        dialogFormVisible: false,
        dialogStatus: '',
        textMap: {
          update: '编辑',
          create: '创建'
        },
        dialogPvVisible: false,
        pvData: [],
        dialogAllocationVisible: false,
        stockData: [],
        showAuditor: false,
        tableKey: 0
      }
    },
    created() {
      this.getList();
    },
    methods: {
      getList() {
        this.listLoading = true;
        fetchList(this.listQuery).then(response => {
          this.list = response.data.results;
          this.total = response.data.count;
          this.listLoading = false;
        })
      },
      getShipping() {
        this.listShippingQuery.shipping_inventory = this.temp.order_inventory;
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
      handleCreate() {
        this.resetTemp();
        this.dialogStatus = 'create';
        this.dialogFormVisible = true;
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
      create() {
        this.temp.id = parseInt(Math.random() * 100) + 1024;
        this.temp.timestamp = +new Date();
        this.temp.author = '原创作者';
        this.list.unshift(this.temp);
        this.dialogFormVisible = false;
        this.$notify({
          title: '成功',
          message: '创建成功',
          type: 'success',
          duration: 2000
        });
      },
      update() {
        this.temp.timestamp = +this.temp.timestamp;
        for (const v of this.list) {
          if (v.id === this.temp.id) {
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
        this.allocateOrderData.order = this.temp;
        this.temp.status = '已分配';
        for (const v of this.stockData) {
          if (this.temp.order_inventory === v.inventory_name) {
            this.allocateOrderData.stock = v;
            break;
          }
        }
        allocateOrder(this.allocateOrderData).then(response => {
          this.dialogAllocationVisible = false;
        })
      },
      resetTemp() {
        this.temp = {
          id: undefined,
          channel_name: 0,
          remark: '',
          timestamp: 0,
          title: '',
          status: 'published',
          type: ''
        };
      },
      handleFetchPv(pv) {
        fetchPv(pv).then(response => {
          this.pvData = response.data.pvData;
          this.dialogPvVisible = true;
        })
      },
      handleFetchStock(row) {
        this.temp = Object.assign({}, row);
        this.listStockQuery.jancode = this.temp.jancode;
        fetchStock(this.listStockQuery).then(response => {
          this.stockData = response.data.results;
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
