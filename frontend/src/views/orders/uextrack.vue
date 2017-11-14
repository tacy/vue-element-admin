<template>
  <div class="app-container calendar-list-container">
    <div class="filter-container">
      <el-input @keyup.enter.native="handleFilter" style="width: 100px;" class="filter-item" placeholder="订单号" v-model="listQuery.orderid">
      </el-input>

      <el-input @keyup.enter.native="handleFilter" style="width: 100px;" class="filter-item" placeholder="收件人" v-model="listQuery.receiver_name">
      </el-input>

      <el-select style="width: 120px" class="filter-item" v-model="listQuery.channel_name" placeholder="渠道">
        <el-option v-for="item in channelOptions" :key="item" :label="item" :value="item">
        </el-option>
      </el-select>

      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.status" placeholder="状态">
        <el-option v-for="item in statusOptions" :key="item" :label="item" :value="item">
        </el-option>
      </el-select>
      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.export_status" placeholder="导出状态">
        <el-option v-for="item in exportstatusOptions" :key="item" :label="item" :value="item">
        </el-option>
      </el-select>

      <el-button class="filter-item" type="primary" v-waves icon="search" @click="handleFilter">搜索</el-button>
      <el-button class="filter-item" type="success" style="float:right" v-waves icon="edit" @click="handleUexTrack">导出轨迹</el-button>
      <el-button class="filter-item" type="success" style="float:right" v-waves icon="edit" @click="handleAddUexNumber">新增UEX号段</el-button>
      <el-button class="filter-item" type="success" style="float:right" v-waves icon="edit" @click="exportOrder">导出热敏</el-button>
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
      <el-table-column align="center" label="面单" width="120px">
	<template scope="scope">
	  <span>{{scope.row.db_number}}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="收件人" width="95px">
	<template scope="scope">
	  <span>{{scope.row.receiver_name}}</span>
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
      <el-table-column align="center" label="操作" width="80px">
	<template scope="scope">
          <el-button size="small" :disabled="scope.row.status==='待发货'&&scope.row.export_status==='中国海关'?false:true" type="primary" @click="handleStockOut(scope.row)">出库
	  </el-button>
	</template>
      </el-table-column>
    </el-table>

    <div v-show="!listLoading" class="pagination-container">
      <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange" :current-page.sync="listQuery.page"
        :page-sizes="[10,20,30, 50]" :page-size="listQuery.limit" layout="total, sizes, prev, pager, next, jumper" :total="total">
      </el-pagination>
    </div>

    <el-dialog title="导出轨迹" size="tiny" :visible.sync="dialogUexTrackVisible">
      <el-form class="small-space" :model="param" label-position="left" label-width="70px" style='width: 500px; margin-left:50px;'>
        <el-form-item label="轨迹类型:" label-width="80px">
	  <el-select clearable style="width: 150px" class="filter-item" v-model.trim="param.exportType" placeholder="选择类型">
	    <el-option v-for="item in exportTypeOptions" :key="item" :label="item" :value="item">
	    </el-option>
	  </el-select>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogUexTrackVisible=false">取 消</el-button>
        <el-button type="primary" :disabled="disableSubmit" @click="uexTrack">提 交</el-button>
      </div>
    </el-dialog>

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

    <el-dialog title="新增UEX号段" size="tiny" :visible.sync="dialogAddUexNumberVisible">
      <el-form class="small-space" :model="uexNumberData" label-position="left" label-width="70px" style='width: 500px; margin-left:50px;'>
        <el-form-item label="起始号:" label-width="80px">
          <el-input style="width: 120px" v-model.trim="uexNumberData.start"></el-input>
        </el-form-item>
        <el-form-item label="结束号:" label-width="80px">
          <el-input style="width: 120px" v-model.trim="uexNumberData.end"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogAddUexNumberVisible=false">取 消</el-button>
        <el-button type="primary" :disabled="disableSubmit" @click="newUexNumber">提 交</el-button>
      </div>
    </el-dialog>

  </div>
</template>

<script>
  import { fetchOrder, exportDomesticOrder, outOrder, exportUexTrack, exportPrint } from 'api/orders';
  import { addUexNumber, } from 'api/uexes';

  export default {
    data() {
      return {
        list: [],
        listLoading: true,
        total: null,
	dialogUexTrackVisible: false,
        dialogStockOutVisible: false,
        dialogAddUexNumberVisible: false,
	channelOptions: ['洋码头', '京东'],
	statusOptions: ['待发货', '待采购', '已采购', '需介入'],
	exportstatusOptions: ['待导出', '日本海关', '中国海关', '已出库'],
	exportTypeOptions: ['日本海关', '中国海关'],
	expressOptions: ['圆通', '顺丰', '中通', '中国邮政', '申通', '韵达'],
	selectRow: [],
	param: {
	  'exportType': undefined
	},
	stockOutData: {
	  id: undefined,
	  domestic_delivery_no: undefined,
	  domestic_delivery_company: undefined,
	},
	uexNumberData: {
	  start: undefined,
	  end: undefined,
	},
        listQuery: {
          page: 1,
          limit: 10,
	  status: "待发货,待采购,已采购,需介入",
          inventory: undefined,
	  shipping: undefined,
	  channel_name: undefined,
	  shipping_name: '轨迹',
	  export_status: undefined,
	  receiver_name: undefined,
	  orderid: undefined,
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
	  待采购: 'warning',
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
	if ( ! this.listQuery.status ) {
	  this.listQuery.status="待发货,待采购,已采购,需介入,已发货"
	};
        fetchOrder(this.listQuery).then(response => {
          this.list = response.data.results;
          this.total = response.data.count;
          this.listLoading = false;
        })
      },
      handleFilter() {
        this.listQuery.page=1;
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
      checkSelectable(row) {
        return row.status !== '已出库' || row.status !== '已删除'
      },
      handleSelect(val) {
        this.selectRow = val;
      },
      handleUexTrack() {
        this.dialogUexTrackVisible = true;
	this.param.exportType=undefined
      },
      handleAddUexNumber() {
        this.dialogAddUexNumberVisible = true
        this.uexNumberData.start=undefined
        this.uexNumberData.end=undefined
      },
      handleStockOut(row) {
        this.dialogStockOutVisible = true;
	this.stockOutData.id = row.id;
	this.stockOutData.domestic_delivery_no = undefined
	this.stockOutData.domestic_delivery_company = '圆通'
      },
      newUexNumber() {
        addUexNumber(this.uexNumberData).then(response => {
          this.dialogAddUexNumberVisible = false;
          this.$notify({
            title: '成功',
            message: '新增号段成功',
            type: 'success',
            duration: 2000
          });
        });
      },
      exportOrder() {
        if (this.selectRow.length===0) {
          this.$message({
            type: 'error',
            message: '请选择导出订单',
            duration: 2000
          });
          return
        };
	const b64toBlob = (b64Data, contentType='', sliceSize=512) => {
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
	  const blob = new Blob(byteArrays, {type: contentType});
	  return blob;
	};
        exportPrint(this.selectRow).then(response => {
          const blob = b64toBlob(response.data.tableData, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
	  const link = document.createElement('a')
	  link.href = window.URL.createObjectURL(blob)
	  link.target = "_blank";
	  link.download = "thermal_order.xlsx"
	  link.click()
	  // window.open(link);
          this.getOrder();
	});
      },
      stockOut() {
        outOrder(this.stockOutData).then(response => {
          this.dialogStockOutVisible = false;
	  for (const v of this.list) {
	    if (v.id === this.stockOutData.id) {
	      const index = this.list.indexOf(v);
	      this.list[index].status='已发货';
	      this.list[index].domestic_delivery_no = this.stockOutData.domestic_delivery_no
	      this.list[index].domestic_delivery_company = this.stockOutData.domestic_delivery_company
	      break;
	    }
	  };
          this.$notify({
            title: '成功',
            message: '出库成功',
            type: 'success',
            duration: 2000
          });
        });
      },
      uexTrack() {
	const b64toBlob = (b64Data, contentType='', sliceSize=512) => {
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
	  const blob = new Blob(byteArrays, {type: contentType});
	  return blob;
	};
        exportUexTrack(this.param).then(response => {
          const blob = b64toBlob(response.data.tableData, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
	  const link = document.createElement('a')
	  link.href = window.URL.createObjectURL(blob)
	  link.target = "_blank";
	  link.download = "uextrack.xlsx"
	  link.click()
	  this.dialogUexTrackVisible=false
          this.getOrder();
	});
      }
    }
  }
</script>
