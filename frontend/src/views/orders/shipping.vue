<template>
  <div class="app-container calendar-list-container">
    <div class="filter-container">
      <el-select v-model="listQuery.labelVal" style="width: 120px;" class="filter-item" placeholder="请选择">
	<el-option
	    v-for="item in selectedOptions"
	    :label="item.label"
	    :value="item.value">
	</el-option>
      </el-select>
      <el-input @keyup.enter.native="handleFilter" style="width: 150px;" class="filter-item" placeholder="输入面单号" v-model="listQuery.db_number" v-show="listQuery.labelVal == '1'">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 150px;" class="filter-item" placeholder="输入商品名称" v-model="listQuery.product_title" v-show="listQuery.labelVal == '2'">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 150px;" class="filter-item"  placeholder="输入商品条码" v-model="listQuery.jancode" v-show="listQuery.labelVal == '3'">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 150px;" class="filter-item"  placeholder="输入运单号" v-model="listQuery.delivery_no" v-show="listQuery.labelVal == '4'">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 150px;" class="filter-item"  placeholder="输入收件人" v-model="listQuery.receiver_name" v-show="listQuery.labelVal == '5'">
      </el-input>

      <el-input @keyup.enter.native="handleFilter" style="width: 120px;" class="filter-item"  placeholder="商品规格" v-model="listQuery.sku_properties_name">
      </el-input>
      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.shipping" placeholder="发货方式">
        <el-option v-for="item in shippingOptions" :key="item.id" :label="item.name" :value="item.id">
        </el-option>
      </el-select>

      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.status" placeholder="状态">
        <el-option v-for="item in statusOptions" :key="item" :label="item" :value="item">
        </el-option>
      </el-select>

      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.inventory" placeholder="仓库">
        <el-option v-for="item in inventoryOptions" :key="item.id" :label="item.name" :value="item.id">
        </el-option>
      </el-select>

      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.channel_name" placeholder="渠道">
        <el-option v-for="item in channelOptions" :key="item" :label="item" :value="item">
        </el-option>
      </el-select>

      <el-button class="filter-item" type="primary" v-waves icon="search" @click="handleFilter">搜索</el-button>
      <el-button class="filter-item" type="success" style="float:right" v-waves icon="document" @click="handleStockOut">出库</el-button>
      <el-button class="filter-item" type="success" style="float:right" v-waves icon="edit" @click="handleDBPrint">打印面单</el-button>
    </div>

    <el-table :data="list" v-loading.body="listLoading" @selection-change="handleSelect" border fit highlight-current-row style="width: 100%">
      <el-table-column type="selection" width="45" :selectable="checkSelectable">
      </el-table-column>
      <el-table-column type="expand">
	<template scope="scope">
          <el-form v-for="(p, index) in scope.row.info" label-position="left" inline class="table-expand">
	    <el-form-item label="订单序号">
	      <span>{{ p.id }}</span>
	    </el-form-item>
	    <el-form-item label="订单号">
	      <span>{{ p.orderid }}</span>
	    </el-form-item>
	    <el-form-item label="状态">
	      <span>{{ p.status }}</span>
	    </el-form-item>
	    <el-form-item label="注文编号">
	      <span>{{ p.purchaseorder }}</span>
	    </el-form-item>
	    <el-form-item label="产品名">
	      <span>{{ p.product_title }}</span>
	    </el-form-item>
	    <el-form-item label="规格">
	      <span>{{ p.sku_properties_name }}</span>
	    </el-form-item>
	    <el-form-item label="收件人">
	      <span>{{ p.receiver_name }}</span>
	    </el-form-item>
	    <el-form-item label="地址">
	      <span>{{ p.receiver_address }}</span>
	    </el-form-item>
	    <el-form-item label="电话">
	      <span>{{ p.receiver_mobile }}</span>
	    </el-form-item>
	    <el-form-item label="邮编">
	      <span>{{ p.receiver_zip }}</span>
	    </el-form-item>
	    <el-form-item label="销售链接">
              <el-button type="text" size="small"><a :href="p.product_id" target="_blank">售卖地址</a></el-button>
	    </el-form-item>
	  </el-form>
	</template>
      </el-table-column>
      <!--el-table-column align="center" label="序号" width="70px">
	<template scope="scope">
	  <span>{{scope.row.id}}</span>
	</template>
      </el-table-column-->
      <el-table-column align="center" label="DB单号" width="150px">
	<template scope="scope">
	  <span>{{scope.row.db_number}}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="渠道" width="80px">
	<template scope="scope">
	  <span>{{scope.row.channel_name}}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="仓库" width='80px'>
	<template scope="scope">
	  <span>{{scope.row.inventory_name}}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="发货方式" width="100px">
	<template scope="scope">
	  <span>{{scope.row.shipping_name}}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="订单时间" width="130px">
	<template scope="scope">
	  <span>{{scope.row.order_piad_time|fmDate}}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="库存" width="100px">
	<template scope="scope">
	  <el-tag :type="scope.row.stockStatus | stockStatusFilter" hit>{{scope.row.stockStatus}}</el-tag>
	</template>
      </el-table-column>
      <el-table-column align="center" label="状态" width="80px">
	<template scope="scope">
	  <span>{{scope.row.status}}</span>
	  <!--el-tag :type="scope.row.status">{{scope.row.status}}</el-tag-->
	</template>
      </el-table-column>
      <el-table-column align="center" label="打印" width="80px">
	<template scope="scope">
	  <span>{{scope.row.print_status}}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="运单号">
	<template scope="scope">
	  <span>{{scope.row.delivery_no}}</span>
	</template>
      </el-table-column>
      <!--el-table-column align="center" label="打印" width="140">
        <template scope="scope">
          <el-button size="small" :disabled="scope.row.shipping_name==='直邮电商'?false:true" type="primary" @click="handlePDF(scope.row)">面单
          </el-button>
          <el-button size="small" type="primary" @click="handleOrderItems(scope.row)">明细
          </el-button>
        </template>p
      </el-table-column-->
      <el-table-column align="center" label="操作" width="100">
        <template scope="scope">
          <!--el-button size="small" :disabled="scope.row.stockStatus==='在库'&&scope.row.status==='待处理'?false:true" type="success" @click="handleStockOut(scope.row)">出库
          </el-button-->
          <el-button size="small" :disabled="scope.row.status==='待处理'?false:true" type="danger" @click="handleDelete(scope.row)">删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-show="!listLoading" class="pagination-container">
      <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange" :current-page.sync="listQuery.page"
        :page-sizes="[10,20,30, 50]" :page-size="listQuery.limit" layout="total, sizes, prev, pager, next, jumper" :total="total">
      </el-pagination>
    </div>

    <el-dialog title="出库" :visible.sync="dialogStockOutVisible">
      <el-form class="small-space" :model="stockOutData" label-position="left" label-width="70px" style='width: 500px; margin-left:50px;'>
        <el-form-item label="运单号:">
          <el-input v-model.trim="stockOutData.delivery_no"></el-input>
        </el-form-item>
        <el-form-item label="面单号:">
          <el-input type="textarea" :autosize="{minRows: 8, maxRows: 12}" v-model.trim="stockOutData.db_numbers"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogStockOutVisible=false">取 消</el-button>
        <el-button type="primary" :disabled="disableSubmit" @click="stockOut">提 交</el-button>
      </div>
    </el-dialog>

    <el-dialog title="发货明细" :visible.sync="dialogItemVisible" size="large">
      <el-table :data="itemData" border fit highlight-current-row style="width: 100%">
	<!--el-table-column align="center" label="订单编号">
	  <template scope="scope">
	    <span>{{scope.row.orderid}}</span>
	  </template>
        </el-table-column-->
	<el-table-column align="center" label="条码" width="130px">
	  <template scope="scope">
	    <span>{{scope.row.jancode}}</span>
	  </template>
        </el-table-column>
	<el-table-column align="center" label="名称">
	  <template scope="scope">
	    <span>{{scope.row.product_title}}</span>
	  </template>
        </el-table-column>
	<el-table-column align="center" label="规格" width="150px">
	  <template scope="scope">
	    <span>{{scope.row.sku_properties_name}}</span>
	  </template>
        </el-table-column>
	<el-table-column align="center" label="数量" width="70px">
	  <template scope="scope">
	    <span>{{scope.row.quantity}}</span>
	  </template>
        </el-table-column>
	<el-table-column align="center" label="收件人" width="80px">
	  <template scope="scope">
	    <span>{{scope.row.receiver_name}}</span>
	  </template>
        </el-table-column>
	<el-table-column align="center" label="地址">
	  <template scope="scope">
	    <span>{{scope.row.receiver_address}}</span>
	  </template>
        </el-table-column>
	<el-table-column align="center" label="货架号" width="100px">
	  <template scope="scope">
	    <span>{{scope.row.location}}</span>
	  </template>
        </el-table-column>
	<el-table-column align="center" label="面单" width="130px">
	  <template scope="scope">
	    <span>{{scope.row.db_number}}</span>
	  </template>
        </el-table-column>
      </el-table>
      <span slot="footer" class="dialog-footer">
        <el-button type="primary" onClick="window.print()">打 印</el-button>
        <el-button type="primary" @click="dialogItemVisible=false">确 定</el-button>
      </span>
    </el-dialog>

    <el-dialog title="打印" size="small" :visible.sync="dialogFormVisible">
      <pdf ref="pdf" :src="pdfsrc"></pdf>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogFormVisible=false">取 消</el-button>
        <el-button type="primary" @click="$refs.pdf.print()">打 印</el-button>
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
  import { fetchInventory, fetchShipping, fetchShippingDB, fetchPDF, fetchOrderItems, stockOut, deleteDBNumber } from 'api/orders';
  import pdf from 'vue-pdf';

  export default {
    components: {
      pdf
    },
    data() {
      return {
        list: [],
	itemData: [],
        listLoading: true,
        total: null,
	pdfsrc: undefined,
        dialogItemVisible: false,
	dialogStockOutVisible: false,
	dialogFormVisible: false,
        inventoryOptions: [],
	disableSubmit: false,
        selectRow: [],
	channelOptions: ['洋码头', '京东'],
	shippingOptions: [],
	statusOptions: ['待处理', '已出库', '已删除'],
        selectedOptions: [{
          value: '1',
	  label: '面单号'
	}, {
	  value: '2',
	  label: '商品名称'
	}, {
	  value: '3',
	  label: '商品条码'
	}, {
	  value: '4',
	  label: '运单号'
	}, {
	  value: '5',
	  label: '收件人'
	}],
        listQuery: {
          page: 1,
          limit: 50,
	  labelVal: '1',
	  status: "待处理",
          inventory: undefined,
	  shipping: undefined,
	  channel_name: undefined,
	  receiver_name: undefined,
	  db_number: undefined,
	  delivery_no: undefined,
	  product_title: undefined,
	  sku_properties_name: undefined,
	  jancode: undefined,
        },
	queryOrderItems: {
	  shippingdb_id: undefined,
	},
	stockOutData: {
	  delivery_no: undefined,
	  db_numbers: undefined
	},
	xloboData: {
	  BillCodes: []
	}
      }
    },
    filters: {
      stockStatusFilter(stockStatus) {
        const stockStatusMap = {
          在库: 'primary',
	  出库: 'success',
	  在途: 'danger'
        };
        return stockStatusMap[stockStatus]
      },
      fmDate(value) {
	if (!value) return ''
	value = value.substr(2, 8) + ' ' + value.substr(11, 5)
	return value
      }
    },
    created() {
      this.getInventory();
      this.getShipping()
      this.getShippingDB();
    },
    methods: {
      getShippingDB() {
        this.listLoading = true;
	if ( this.listQuery.labelVal !== '1' ) {
	  this.listQuery.db_number=undefined
	}
	if ( this.listQuery.labelVal !== '2' ) {
	  this.listQuery.product_title=undefined
	}
	if ( this.listQuery.labelVal !== '3' ) {
	  this.listQuery.jancode=undefined
	}
	if ( this.listQuery.labelVal !== '4' ) {
	  this.listQuery.delivery_no=undefined
	}
	if ( this.listQuery.labelVal !== '5' ) {
	  this.listQuery.receiver_name=undefined
	}
        fetchShippingDB(this.listQuery).then(response => {
	  this.list = response.data.results;
          for (const t of this.list) {
 	    const index = this.list.indexOf(t);
	    this.list[index].stockStatus = '在库';
	    const tmp = [];
	    for (const o of t.order) {
	      const ordinfo = o.split('@');
	      const product_id='http://m.ymatou.com/item/page/index/'+ordinfo[10]
	      if ( ordinfo[10].length<10 ) {
	        product_id='https://m.51tiangou.com/product/listing.html?id='+ordinfo[10]
	      }
	      tmp.push({
		'id': ordinfo[0],
		'orderid': ordinfo[1],
		'status': ordinfo[2],
		'purchaseorder': ordinfo[3],
		'product_title': ordinfo[4],
		'sku_properties_name': ordinfo[5],
		'receiver_name': ordinfo[6],
		'receiver_address': ordinfo[7],
		'receiver_mobile': ordinfo[8],
		'receiver_zip': ordinfo[9],
		'product_id': product_id,
	      });
	      if ( ordinfo[2] === '已采购' ) {
	        this.list[index].stockStatus = '在途';
	      };
	      if ( ordinfo[2] === '已发货' ) {
	        this.list[index].stockStatus = '出库';
	      };
	    };
	    this.list[index].info = tmp;
	  };
          this.total = response.data.count;
          this.listLoading = false;
        })
      },
      getInventory() {
        fetchInventory().then(response => {
          this.inventoryOptions = response.data.results;
        })
      },
      getShipping() {
        fetchShipping().then(response => {
          this.shippingOptions = response.data.results;
        })
      },
      handleFilter() {
        this.listQuery.page=1;
        this.getShippingDB();
      },
      checkSelectable(row) {
        return row.stockStatus !== '在途' && row.status==='待处理'
      },
      handleSelect(val) {
        this.selectRow = val;
      },
      handleSizeChange(val) {
        this.listQuery.limit = val;
        this.getShippingDB();
      },
      handleCurrentChange(val) {
        this.listQuery.page = val;
        this.getShippingDB();
      },
      handleOrderItems(row) {
        this.queryOrderItems.shippingdb_id = row.id
        fetchOrderItems(this.queryOrderItems).then(response => {
	  this.itemData = response.data.results;
	  this.dialogItemVisible = true;
	});
      },
      handleStockOut() {
        this.stockOutData={
	  delivery_no: undefined,
	  db_numbers: undefined
	}
	this.dialogStockOutVisible=true;
      },
      stockOut() {
        this.disableSubmit=true;
        stockOut(this.stockOutData).then(response => {
	  const dbs = this.stockOutData.db_numbers.split('\n')
	  for (const d of dbs) {
	    for (const v of this.list) {
	      if (v.db_number === d) {
		const index = this.list.indexOf(v);
		// this.list.splice(index, 1);
		this.list[index].status='出库'
		this.list[index].delivery_no=this.stockOutData.delivery_no
		break;
	      }
	    };
	  };
	  this.$notify({
	    title: '成功',
	    message: '出库完成',
	    type: 'success',
	    duration: 2000
	  });
	  this.dialogStockOutVisible=false;
	});
	this.disableSubmit=false;
      },
      handleDelete(row) {
        deleteDBNumber(row).then(response => {
	  for (const v of this.list) {
	    if (v.id === row.id) {
	      const index = this.list.indexOf(v);
	      this.list.splice(index, 1);
	      break;
	    }
	  };
	  this.$notify({
	    title: '成功',
	    message: '删除面单成功',
	    type: 'success',
	    duration: 2000
	  });
	});
      },
      handleDBPrint() {
        if (this.selectRow.length===0) {
          this.$message({
            type: 'error',
            message: '请选择面单',
            duration: 2000
          });
          return
        };
        if ( this.selectRow[0].shipping_name.includes("UEX") ) {
          this.isUEX = true;
          this.dialogUEXVisible = true;
          return
        }
	this.pdfsrc = '';
	this.xloboData.BillCodes=[]
	for (const o in this.selectRow ) {
	  this.xloboData.BillCodes.push(this.selectRow[o].db_number)
	}

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

        fetchPDF(this.xloboData).then(response => {
	  // this.pdfsrc = "data:application/pdf;base64," + response.data.Result[0].BillPdfLabel
          // this.dialogFormVisible = true;

          const blob = b64toBlob(response.data.Result[0].BillPdfLabel, "application/pdf");

          // let blob = new Blob([response.data.Result[0].BillPdfLabel], { type: "application/pdf" } )
	  const link = document.createElement('a')
	  link.href = window.URL.createObjectURL(blob)
	  link.target = "_blank";
	  // link.download = "report.pdf"
	  // link.click()
	  window.open(link);
          for (const o of this.list) {
	    for (const s of this.selectRow ) {
	      if (o.id===s.id) {
	        const index = this.list.indexOf(o);
	        this.list[index].print_status = '已打印';
		break;
	      }
	    }
	  }
	});
      },
      handlePDF(row) {
        this.xloboData.BillCodes = row.db_number;
	this.pdfsrc = '';
        fetchPDF(this.xloboData).then(response => {
	  this.pdfsrc = "data:application/pdf;base64," + response.data.Result[0].BillPdfLabel
          this.dialogFormVisible = true;
	});
      }
    }
  }
</script>
