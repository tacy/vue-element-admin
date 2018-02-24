<template>
  <div class="app-container calendar-list-container">
    <div class="filter-container">
      <el-input @keyup.enter.native="handleFilter" style="width: 80px;" class="filter-item" placeholder="订单号" v-model="listQuery.orderid">
      </el-input>

      <el-input @keyup.enter.native="handleFilter" style="width: 80px;" class="filter-item" placeholder="收件人" v-model="listQuery.receiver_name">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 80px;" class="filter-item" placeholder="条码" v-model="listQuery.jancode">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 80px;" class="filter-item" placeholder="产品名" v-model="listQuery.product_title">
      </el-input>

      <el-select style="width: 100px" class="filter-item" v-model="orderType" placeholder="选择订单类型">
        <el-option v-for="item in orderTypeOptions" :key="item" :label="item" :value="item">
        </el-option>
      </el-select>

      <el-select style="width: 100px" class="filter-item" v-model="listQuery.channel_name" placeholder="渠道">
        <el-option v-for="item in channelOptions" :key="item" :label="item" :value="item">
        </el-option>
      </el-select>

      <el-select clearable style="width: 100px" class="filter-item" v-model="listQuery.status" placeholder="状态">
        <el-option v-for="item in statusOptions" :key="item" :label="item" :value="item">
        </el-option>
      </el-select>
      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.export_status" placeholder="导出状态">
        <el-option v-for="item in exportstatusOptions" :key="item" :label="item" :value="item">
        </el-option>
      </el-select>

      <el-button class="filter-item" type="primary" v-waves icon="search" @click="handleFilter">搜索</el-button>
      <el-button class="filter-item" type="success" style="float:right" v-waves icon="edit" @click="domesticOrder">导出拼邮单</el-button>
      <el-button class="filter-item" type="success" style="float:right" v-waves icon="edit" @click="bondedOrder">导出郑州保税</el-button>
    </div>

    <el-table :data="list" v-loading.body="listLoading" @selection-change="handleSelect" border fit highlight-current-row style="width: 100%">
      <el-table-column type="selection" width="45" :selectable="checkSelectable">
      </el-table-column>
      <el-table-column align="center" label="订单号" width="100px">
        <template scope="scope">
          <span>{{scope.row.orderid}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="状态" width="100px">
        <template scope="scope">
          <!--span>{{scope.row.status}}</span-->
          <el-tag :type="scope.row.status | statusFilter">{{scope.row.status}}</el-tag>
        </template>
      </el-table-column>
      <el-table-column align="center" label="导出状态" width="100px">
        <template scope="scope">
          <span>{{scope.row.export_status}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="发货方式" width="100px">
        <template scope="scope">
          <span>{{scope.row.shipping_name}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="运输方式" width="100px">
        <template scope="scope">
          <span>{{scope.row.delivery_type}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="支付时间" width="120px">
        <template scope="scope">
          <span>{{scope.row.piad_time}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="采购单" width="120px">
        <template scope="scope">
          <span>{{scope.row.purchaseorder_orderid}}</span>
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
      <el-table-column align="center" label="地址" width="200px">
        <template scope="scope">
          <span>{{scope.row.receiver_address}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="商品编码" width="100px">
        <template scope="scope">
          <span>{{scope.row.jancode}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="数量" width="80px">
        <template scope="scope">
          <span>{{scope.row.quantity}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="商品名" width="200px">
        <template scope="scope">
          <span>{{scope.row.product_title}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="规格" width="180px">
        <template scope="scope">
          <span>{{scope.row.sku_properties_name}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="操作" width="80">
        <template scope="scope">
          <el-button size="small" :disabled="scope.row.status==='待发货'?false:true" type="primary" @click="handleStockOut(scope.row)">出库
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-show="!listLoading" class="pagination-container">
      <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange" :current-page.sync="listQuery.page"
        :page-sizes="[10,20,30, 50]" :page-size="listQuery.limit" layout="total, sizes, prev, pager, next, jumper" :total="total">
      </el-pagination>
    </div>

    <el-dialog title="订单出库" size="tiny" :visible.sync="dialogStockOutVisible">
      <el-form class="small-space" :model="stockOutData" label-position="left" label-width="70px" style='width: 500px; margin-left:50px;'>
        <el-form-item label="快递公司:" label-width="80px">
          <el-select allow-create filterable style="width: 120px" v-model.trim="stockOutData.domestic_delivery_company" placeholder="快递公司">
            <el-option v-for="item in expressOptions" :key="item" :label="item" :value="item">
            </el-option>
          </el-select>
          <!--el-input style="width: 120px" v-model.trim="stockOutData.domestic_delivery_company"></el-input-->
        </el-form-item>
        <el-form-item label="运单号:" label-width="80px">
          <el-input style="width: 120px" v-model.trim="stockOutData.domestic_delivery_no"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogStockOutVisible=false">取 消</el-button>
        <el-button type="primary" :disabled="disableSubmit" @click="stockOut">提 交</el-button>
      </div>
    </el-dialog>

  </div>
</template>

<script>
  import { fetchOrder, exportDomesticOrder, outOrder, exportBondedOrder } from 'api/orders';

  export default {
    data() {
      return {
        list: [],
        listLoading: true,
        total: null,
        dialogStockOutVisible: false,
        channelOptions: ['洋码头', '京东'],
        statusOptions: ['待发货', '待采购', '已采购', '需介入'],
        orderTypeOptions: ['拼邮', '保税'],
        exportstatusOptions: ['未导出', '已导出'],
        expressOptions: ['圆通', '顺丰', '中通', '中国邮政', '申通', '韵达'],
        selectRow: [],
        orderType: '拼邮',
        stockOutData: {
          id: undefined,
          domestic_delivery_no: undefined,
          domestic_delivery_company: undefined
        },
        listQuery: {
          page: 1,
          limit: 10,
          status: '待发货,待采购,已采购,需介入',
          unshippingdb: 3,
          inventory: undefined,
          shipping: undefined,
          channel_name: undefined,
          jancode: undefined,
          product_title: undefined,
          receiver_name: undefined,
          orderid: undefined,
          export_status: undefined,
          delivery_type: undefined
        }
      }
    },
    filters: {
      statusFilter(status) {
        const statusMap = {
          待发货: 'success',
          已采购: 'primary',
          需介入: 'danger',
          待采购: 'warning'
        };
        return statusMap[status]
      }
    },
    created() {
      this.getOrder();
    },
    methods: {
      getOrder() {
        this.listLoading = true;
        if (this.orderType === '拼邮') {
          this.listQuery.shipping_name = '拼邮'
          this.listQuery.delivery_type = undefined;
          this.listQuery.unshippingdb = 3;
          if (!this.listQuery.status || this.listQuery.status === '待处理') {
            this.listQuery.status = '待发货,待采购,已采购,需介入'
          }
        } else {
          this.listQuery.shipping_name = undefined;
          this.listQuery.status = '待处理';
          this.listQuery.unshippingdb = 2;
          this.listQuery.delivery_type = '第三方保税';
        }
        fetchOrder(this.listQuery).then(response => {
          this.list = response.data.results;
          this.total = response.data.count;
          this.listLoading = false;
        })
      },
      handleFilter() {
        this.listQuery.page = 1;
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
      handleSelect(val) {
        this.selectRow = val;
      },
      checkSelectable(row) {
        return row.status !== '待采购' & row.status !== '需介入'
      },
      handleStockOut(row) {
        this.dialogStockOutVisible = true;
        this.stockOutData.id = row.id;
        this.stockOutData.domestic_delivery_no = undefined
        this.stockOutData.domestic_delivery_company = '圆通'
      },
      stockOut() {
        outOrder(this.stockOutData).then(response => {
          this.dialogStockOutVisible = false;
          for (const v of this.list) {
            if (v.id === this.stockOutData.id) {
              const index = this.list.indexOf(v);
              this.list[index].status = '已发货';
              this.list[index].domestic_delivery_no = this.stockOutData.domestic_delivery_no
              this.list[index].domestic_delivery_company = this.stockOutData.domestic_delivery_company
              break;
            }
          }
          this.$notify({
            title: '成功',
            message: '出库成功',
            type: 'success',
            duration: 2000
          });
        });
      },
      bondedOrder() {
        const b64toBlob = (b64Data, contentType = '', sliceSize = 512) => {
          const byteCharacters = atob(b64Data);
          const byteArrays = [];
          for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
            const slice = byteCharacters.slice(offset, offset + sliceSize);
            const byteNumbers = new Array(slice.length);
            for (let i = 0; i < slice.length; i++) {
              byteNumbers[i] = slice.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);
            byteArrays.push(byteArray);
          }
          const blob = new Blob(byteArrays, { type: contentType });
          return blob;
        };
        exportBondedOrder().then(response => {
          const blob = b64toBlob(response.data.tableData, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
          const link = document.createElement('a')
          link.href = window.URL.createObjectURL(blob)
          link.target = '_blank';
          link.download = 'zhengzhou_bonded_order.xlsx'
          link.click()
          // window.open(link);
          this.getOrder();
        });
      },
      domesticOrder() {
        if (this.selectRow.length === 0) {
          this.$message({
            type: 'error',
            message: '请选择面单对应订单',
            duration: 2000
          });
          return
        }
        const b64toBlob = (b64Data, contentType = '', sliceSize = 512) => {
          const byteCharacters = atob(b64Data);
          const byteArrays = [];
          for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
            const slice = byteCharacters.slice(offset, offset + sliceSize);
            const byteNumbers = new Array(slice.length);
            for (let i = 0; i < slice.length; i++) {
              byteNumbers[i] = slice.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);
            byteArrays.push(byteArray);
          }
          const blob = new Blob(byteArrays, { type: contentType });
          return blob;
        };
        exportDomesticOrder(this.selectRow).then(response => {
          const blob = b64toBlob(response.data.tableData, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
          const link = document.createElement('a')
          link.href = window.URL.createObjectURL(blob)
          link.target = '_blank';
          link.download = 'domestic_order.xlsx'
          link.click()
          // window.open(link);
          this.getOrder();
        });
      }
    }
  }
</script>
