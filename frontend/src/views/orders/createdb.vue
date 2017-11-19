<template>
  <div class="app-container calendar-list-container">
    <div class="filter-container">
      <el-button class="filter-item" type="success" v-waves icon="edit" @click="handleCreate">生成面单</el-button>
      <el-button class="filter-item" type="danger" v-waves icon="document" @click="handleDBInput">面单回填</el-button>

      <el-select v-model="listQuery.labelVal" style="width: 120px;" class="filter-item" placeholder="请选择">
	<el-option
	    v-for="item in selectedOptions"
	    :label="item.label"
	    :value="item.value">
	</el-option>
      </el-select>
      <el-input @keyup.enter.native="handleFilter" style="width: 200px;" class="filter-item" placeholder="输入订单号" v-model="listQuery.orderid" v-show="listQuery.labelVal == '1'">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 200px;" class="filter-item" placeholder="输入商品名" v-model="listQuery.product_title" v-show="listQuery.labelVal == '2'">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 200px;" class="filter-item"  placeholder="输入商品条码" v-model="listQuery.jancode" v-show="listQuery.labelVal == '3'">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 200px;" class="filter-item"  placeholder="输入收件人" v-model="listQuery.receiver_name" v-show="listQuery.labelVal == '4'">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 200px;" class="filter-item"  placeholder="输入注文编号" v-model="listQuery.purchaseorder__orderid" v-show="listQuery.labelVal == '5'">
      </el-input>

      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.shipping" placeholder="发货方式">
        <el-option v-for="item in shippingOptions" :key="item.id" :label="item.name" :value="item.id">
        </el-option>
      </el-select>
      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.inventory" placeholder="仓库">
        <el-option v-for="item in inventoryOptions" :key="item.id" :label="item.name" :value="item.id">
        </el-option>
      </el-select>
      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.status" placeholder="状态">
        <el-option v-for="item in statusOptions" :key="item" :label="item" :value="item">
        </el-option>
      </el-select>
      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.channel_name" placeholder="渠道">
        <el-option v-for="item in channelOptions" :key="item" :label="item" :value="item">
        </el-option>
      </el-select>

      <el-button class="filter-item" type="primary" v-waves icon="search" @click="handleFilter">搜索</el-button>
      <!--el-button class="filter-item" type="success" style="float:right" v-waves icon="edit" @click="handleCreate">生成面单</el-button>
      <el-button class="filter-item" type="danger" style="float:right" v-waves icon="document" @click="handleDBInput">面单回填</el-button-->
    </div>

    <!--el-table :data="list" v-loading.body="listLoading" ref="ords" @selection-change="handleSelect" border fit highlight-current-row style="width: 100%"-->
    <el-table :data="list" v-loading.body="listLoading" ref="ords" @select="handleSelect" border fit highlight-current-row style="width: 100%">
      <el-table-column type="selection" width="45" :selectable="checkSelectable">
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
	  <!--span>{{scope.row.status}}</span-->
	  <el-tag :type="scope.row.status | statusFilter">{{scope.row.status}}</el-tag>
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
      <el-table-column align="center" label="运输" width="100px" show-overflow-tooltip>
	<template scope="scope">
	  <span>{{scope.row.delivery_type}}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="收件人" width="95px">
        <template scope="scope">
          <span class="link-type" @click="handleUpdate(scope.row)">{{scope.row.receiver_name}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="电话" width="115px" show-overflow-tooltip>
	<template scope="scope">
	  <span>{{scope.row.receiver_mobile}}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="地址" width="150px" show-overflow-tooltip>
	<template scope="scope">
	  <span>{{scope.row.receiver_address}}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="商品编码" width="150px">
	<template scope="scope">
	  <span>{{scope.row.jancode}}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="商品名" show-overflow-tooltip>
	<template scope="scope">
	  <span>{{scope.row.product_title}}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="日期" width="130px">
	<template scope="scope">
	  <span>{{scope.row.piad_time|fmDate}}</span>
	</template>
      </el-table-column>
      <!--el-table-column align="center" label="规格" show-overflow-tooltip>
	<template scope="scope">
	  <span>{{scope.row.sku_properties_name}}</span>
	</template>
      </el-table-column-->
      <el-table-column align="center" label="操作" width="100">
        <template scope="scope">
          <el-button size="small" type="danger" @click="handleRollbackToPreprocess(scope.row)">弹回
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
	<el-table-column align="center" label="商品编码">
	  <template scope="scope">
	    <span>{{scope.row.jancode}}</span>
	  </template>
        </el-table-column>
	<el-table-column align="center" label="数量">
	  <template scope="scope">
	    <span>{{scope.row.quantity}}</span>
	  </template>
        </el-table-column>
	<el-table-column align="center" label="价格">
	  <template scope="scope">
	    <span>{{scope.row.price}}</span>
	  </template>
        </el-table-column>
      </el-table>

      <span slot="footer" class="dialog-footer">
        <el-button type="primary" @click="dialogItemVisible=false">确 定</el-button>
      </span>
    </el-dialog>

    <el-dialog title="生成面单" size="small" :visible.sync="dialogFormVisible">
      <el-form class="small-space" :model="xloboData" label-position="left" label-width="80px">
        <el-row>
	  <el-col :span="12">
	    <el-form-item label="货栈:">
	      <el-select clearable style="width: 180px" v-model="xloboData.LogisticId" placeholder="仓库">
		<el-option v-for="item in logisticOptions" :key="item.key" :label="item.key" :value="item.value">
		</el-option>
	      </el-select>
	    </el-form-item>
 	  </el-col>
          <el-col :span="12">
	    <el-form-item label="代打包:">
	      <el-select clearable style="width: 220px" v-model="xloboData.IsRePacking" placeholder="打包选择">
		<el-option v-for="item in rePackingOptions" :key="item.key" :label="item.key" :value="item.value">
		</el-option>
	      </el-select>
	    </el-form-item>
	  </el-col>
	</el-row>
        <el-form-item label="面单备注">
          <el-input type="textarea" :autosize="{minRows: 2, maxRows: 4}" v-model="xloboData.Comment"></el-input>
        </el-form-item>
        <el-form-item label="订单遗漏">
          <el-checkbox v-model="xloboData.disable_check">无需校验</el-checkbox>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogFormVisible=false">取 消</el-button>
        <el-button type="primary" :disabled="disableSubmit" @click="createShippingDB()">确 定</el-button>
      </div>
    </el-dialog>


    <el-dialog title="生成面单" size="small" :visible.sync="dialogUEXVisible">
      <el-form class="small-space" :model="uexData" label-position="left" label-width="80px">
	<el-form-item label="线路:">
	  <el-select clearable style="width: 180px" v-model="uexData.ship_id" placeholder="线路选择">
	    <el-option v-for="item in shipTypeOptions" :key="item.key" :label="item.key" :value="item.value">
	    </el-option>
	  </el-select>
	</el-form-item>
        <el-form-item label="面单备注">
          <el-input type="textarea" :autosize="{minRows: 2, maxRows: 4}" v-model.trim="uexData.Comment"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogUEXVisible=false">取 消</el-button>
        <el-button type="primary" :disabled="disableSubmit" @click="createUexShippingDB()">确 定</el-button>
      </div>
    </el-dialog>

    <el-dialog title="面单回填" size="small" :visible.sync="dialogDBInputVisible">
      <el-form class="small-space" :model="xloboData" label-position="left" label-width="80px">
        <el-form-item label="面单号">
          <el-input v-model.trim="xloboData.Comment"></el-input>
        </el-form-item>
        <el-row>
	  <el-col :span="12">
	    <el-form-item label="订单遗漏">
	      <el-checkbox v-model="xloboData.disable_check">无需校验</el-checkbox>
	    </el-form-item>
 	  </el-col>
	  <el-col :span="12">
	    <el-form-item label="订单发货">
	      <el-checkbox v-model="xloboData.disable_checkOrderDelivery">无需校验</el-checkbox>
	    </el-form-item>
   	  </el-col>
	</el-row>
        <el-form-item label="后台发货">
          <el-checkbox v-model="xloboData.disable_channel_delivery">无需后台发货</el-checkbox>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogDBInputVisible=false">取 消</el-button>
        <el-button type="primary" :disabled="disableSubmit" @click="manualShippingDB()">确 定</el-button>
      </div>
    </el-dialog>

    <el-dialog title="生成EMS面单" size="tiny" :visible.sync="dialogCreateEMSVisible">
      <el-form class="small-space" :model="xloboData" label-position="left" label-width="80px">
	<el-form-item label="发往:">
	  <el-select clearable style="width: 180px" v-model="xloboData.country" placeholder="选择国家">
	    <el-option v-for="item in countryOptions" :key="item.key" :label="item.key" :value="item.value">
	    </el-option>
	  </el-select>
	</el-form-item>
	<el-form-item label="订单遗漏">
	  <el-checkbox v-model="xloboData.disable_check">无需校验</el-checkbox>
	</el-form-item>
	<el-form-item label="包税通道">
	  <el-checkbox v-model="xloboData.tax_included_channel">包税</el-checkbox>
	</el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogCreateEMSVisible=false">取 消</el-button>
        <el-button type="primary" :disabled="disableSubmit" @click="createEMSShippingDB()">确 定</el-button>
      </div>
    </el-dialog>

    <el-dialog title="弹回待处理" size="tiny" :visible.sync="dialogRollbackToPreprocessVisible">
      <span style="color:red">你的操作将会把该订单弹回到待处理环节(包括购物车订单),  如果该订单已经采购,  采购关联信息也将丢失,  请妥善处理采购单对应商品!
      </span>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogRollbackToPreprocessVisible=false">取 消</el-button>
        <el-button type="primary" :disabled="disableSubmit" @click="rollbackToPreprocess()">确 定</el-button>
      </div>
    </el-dialog>

    <el-dialog title="变更收件人信息" :visible.sync="dialogUpdateVisible">
      <el-form class="small-space" :model="temp" label-position="left" label-width="70px" style='width: 500px; margin-left:50px;'>
        <el-form-item label="收件人">
          <el-input v-model.trim="temp.receiver_name"></el-input>
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model.trim="temp.receiver_mobile"></el-input>
        </el-form-item>
        <el-form-item label="身份证">
          <el-input v-model.trim="temp.receiver_idcard"></el-input>
        </el-form-item>
        <el-form-item label="地址">
          <el-input type="textarea" :autosize="{minRows: 2, maxRows: 4}" v-model.trim="temp.receiver_address"></el-input>
        </el-form-item>
        <el-form-item label="邮编">
          <el-input v-model.trim="temp.receiver_zip"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogUpdateVisible = false">取 消</el-button>
        <el-button type="primary" @click="update">确 定</el-button>
      </div>
    </el-dialog>

  </div>
</template>

<script>
  import { parseTime } from 'utils';
  import { fetchInventory, fetchShipping, fetchOrder, updateOrder, fetchLogistic, orderRollback, createNoVerification, createfbxbill, manualallocatedb, createUexDB, createJapanEMS } from 'api/orders';
  import { fetchPurchaseOrderItem, purchaseOrderDelete } from 'api/purchases';

  export default {
    data() {
      return {
        list: [],
        listLoading: true,
        total: null,
        dialogItemVisible: false,
	dialogFormVisible: false,
	dialogUpdateVisible: false,
	dialogUEXVisible: false,
	dialogDBInputVisible: false,
        dialogRollbackToPreprocessVisible: false,
	dialogCreateEMSVisible: false,
	disableSubmit: false,
        inventoryOptions: [],
	shippingOptions: [],
	channelOptions: ['洋码头', '京东'],
	statusOptions: ['需面单', '待采购', '已采购', '需介入'],
	shipTypeOptions: [
	  {key:'跨境空运杂货线路', value:24},
	  {key:'空运关税补贴线', value:26}
	],
	countryOptions: [
	  {key: '中国', value: 'CN'},
	  {key: '美国', value: 'US'},
	],
        selectedOptions: [{
          value: '1',
	  label: '订单号'
	}, {
	  value: '2',
	  label: '商品名称'
	}, {
	  value: '3',
	  label: '商品条码'
	}, {
	  value: '4',
	  label: '收件人'
	}, {
	  value: '5',
	  label: '注文编号'
	}],
	selectRow: [],
	isUEX: false,
	logisticOptions: [],
	rePackingOptions: [
	  {key: '无需', value: 0},
 	  {key: '简易', value: 1},
	  {key: '加固', value: 2},
	],
	preTaxOptions: [
	  {key: '非预缴税', value: 0},
	  {key: '预缴税', value: 1}
	],
	recTaxOptions: [
	  {key: '商家缴税', value: 0},
	  {key: '收件人缴税', value: 1}
	],
	lineTypeOptions: [
	  {key: '电商快件', value: 3},
	  {key: '个人快件', value: 1}
	],
	containTax: [
	  {key: '包税', value: 0},
	  {key: '不包税', value: 1}
	],
        listQuery: {
          page: 1,
          limit: 10,
	  labelVal: '1',
	  status: "需面单,待采购,已采购,需介入",
          inventory: undefined,
	  purchaseorder__orderid: undefined,
	  channel_name: undefined,
	  receiver_name: undefined,
	  orderid: undefined,
	  shipping: undefined,
	  unshippingdb:2
        },
	xloboData: {
	  Weight: 0.3,
	  Insure: 0,
	  IsRePacking: 0,
	  IsPreTax: 1,
	  IsRecTax: 0,
	  Comment: "",
	  LogisticId: 32,
	  LogisticVersion: "2017-08-04 20:00:00",
	  LineTypeId: 3,
	  IsContainTax: 1,
	  disable_check: false,
	  disable_checkOrderDelivery: false,
	  disable_channel_delivery: false,
	  tax_included_channel: false,
	  country: 'CN',
	  orders: []
	},
	uexData: {
	  ship_id: undefined,
	  Comment: undefined,
	  orders: []
	},
        temp: {
	  id: undefined,
          receiver_name: undefined,
	  receiver_mobile: undefined,
	  receiver_idcard: undefined,
	  receiver_address: undefined,
	  receiver_zip: undefined
        },
	listItem: {
	  purchaseorder: undefined
	},
        itemData: [],
	rollbackOrderData: {
	  orderid: undefined
	}
      }
    },
    filters: {
      statusFilter(status) {
        const statusMap = {
          需面单: 'success',
          已采购: 'primary',
          需介入: 'danger',
	  待采购: 'warning',
        };
        return statusMap[status]
      },
      fmDate(value) {
	if (!value) return ''
	value = value.substr(2, 8) + ' ' + value.substr(11, 5)
	return value
      }
    },
    created() {
      this.getInventory();
      this.getShipping();
      this.getOrder();
      this.getLogistic()
    },
    methods: {
      getOrder() {
        this.listLoading = true;
	if ( this.listQuery.labelVal !== '1' ) {
	  this.listQuery.orderid=undefined
	}
	if ( this.listQuery.labelVal !== '2' ) {
	  this.listQuery.product_title=undefined
	}
	if ( this.listQuery.labelVal !== '3' ) {
	  this.listQuery.jancode=undefined
	}
	if ( this.listQuery.labelVal !== '4' ) {
	  this.listQuery.receiver_name=undefined
	}
	if ( this.listQuery.labelVal !== '5' ) {
	  this.listQuery.purchaseorder__orderid=undefined
	}
	if ( ! this.listQuery.status ) {
	  this.listQuery.status="需面单,待采购,已采购,需介入"
	}
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
      getShipping() {
        fetchShipping().then(response => {
          this.shippingOptions = response.data.results;
        })
      },
      getLogistic() {
        fetchLogistic().then(response => {
          this.logisticOptions = response.data;
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
      handleSelect(val, row) {
	if ( val.length > 0) {
	  var rowIn = false
	  for (const v of val) {
	    if (v.id===row.id) {
	      rowIn = true
	      break
	    }
	  };
	  if (rowIn) {
	    for (const v of this.list) {
	      if (v.id !== row.id && v.shipping === row.shipping && v.receiver_address === row.receiver_address && ['需面单','已采购'].includes(v.status)) {
		val.push(v);
		const index = this.list.indexOf(v);
		this.$refs.ords.toggleRowSelection(this.list[index], true);
	      }
	    };
	  }
	}
        this.selectRow = val;
      },
      handleUpdate(row) {
        this.temp = Object.assign({}, row);
        this.dialogUpdateVisible = true;
      },
      resetXloboData() {
        this.xloboData.disable_check=false
        this.xloboData.disable_checkOrderDelivery=false
        this.xloboData.disable_channel_delivery=false
	this.xloboData.tax_includec_channel=false
        this.xloboData.IsRePacking=0
	this.xloboData.country='CN'
      },
      checkSelectable(row) {
        return row.status !== '待采购' & row.status !== '需介入'
      },
      update() {
        for (const v of this.list) {
          if (v.id === this.temp.id) {
            const index = this.list.indexOf(v);
            this.list.splice(index, 1, this.temp);
            break;
          }
        };
        updateOrder(this.temp, '/order/' + this.temp.id + '/').then(response => {
          this.dialogUpdateVisible = false;
          this.$notify({
            title: '成功',
            message: '更新成功',
            type: 'success',
            duration: 2000
          });
        });
      },
      handleCreate() {
        this.resetXloboData()
	this.disableSubmit=false;
        if (this.selectRow.length===0) {
          this.$message({
            type: 'error',
            message: '请选择发货订单',
            duration: 2000
          });
          return
        };
        if ( this.selectRow.length>1 & !!this.selectRow.reduce(function(a, b){ return (a.shipping !== b.shipping | a.inventory !== b.inventory | a.receiver_address !== b.receiver_address) ? a : NaN; })) {
          this.$message({
            type: 'error',
            message: '选中的订单发货信息不一致',
            duration: 2000
          });
          return
        };
        if ( this.selectRow[0].shipping_name.includes("UEX") ) {
          this.isUEX = true;
          this.dialogUEXVisible = true;
          return
        };

	// 如果是ems,使用japanpost做单
        if ( ["EMS","SAL","EPACK","SURFACE"].includes(this.selectRow[0].shipping_name) ) {
	  this.dialogCreateEMSVisible = true;
	  return
	};

	if ( this.selectRow[0].shipping_name==="虚仓电商" ) {
          this.xloboData.IsRePacking=1;
        };
        this.xloboData.Comment = '';
        for ( const i of this.selectRow ) {
          this.xloboData.Comment += i.product_title+', '
        };
        this.dialogFormVisible = true;
      },
      handleDBInput() {
        this.resetXloboData()
	this.disableSubmit=false
        if (this.selectRow.length===0) {
          this.$message({
            type: 'error',
            message: '请选择面单对应订单',
            duration: 2000
          });
          return
        };
        if ( this.selectRow.length>1 & !!this.selectRow.reduce(function(a, b){ return (a.shipping !== b.shipping | a.inventory !== b.inventory | a.receiver_address !== b.receiver_address) ? a : NaN; })) {
          this.$message({
            type: 'error',
            message: '选中的订单发货信息不一致',
            duration: 2000
          });
          return
        };
        this.xloboData.Comment = '';
        this.dialogDBInputVisible = true;
      },
      createEMSShippingDB() {
	this.disableSubmit=true;
	this.xloboData.orders = this.selectRow;
	createJapanEMS(this.xloboData).then(response => {
	  this.$notify({
	    title: '成功',
	    message: 'EMS面单创建成功',
	    type: 'success',
	    duration: 2000
	  });
	  this.getOrder();
          this.dialogCreateEMSVisible=false;
	}).catch(error => {
	  this.disableSubmit = false;
	})
      },
      createShippingDB() {
        this.disableSubmit=true;
        this.xloboData.orders = this.selectRow;
        let shipping_type = this.selectRow[0].shipping_name;
        if ( shipping_type==='直邮电商' || shipping_type==='贝海直邮电商' ) {
          createNoVerification(this.xloboData).then(response => {
            this.dialogFormVisible = false
            this.getOrder();
          }).catch(error => {
            this.disableSubmit=false;
	  })
        } else {
          createfbxbill(this.xloboData).then(response => {
            this.dialogFormVisible = false
            this.getOrder();
          }).catch(error => {
	    this.disableSubmit = false;
	  })
        }
      },
      createUexShippingDB() {
        this.uexData.orders = this.selectRow;
        createUexDB(this.uexData).then(response => {
          this.dialogUEXVisible = false;
          this.getOrder();
        })
      },
      manualShippingDB() {
        this.disableSubmit=true;
        this.xloboData.orders = this.selectRow;
        manualallocatedb(this.xloboData).then(response => {
	  this.dialogDBInputVisible = false
          this.getOrder();
        }).catch(error => {
            this.disableSubmit=false;
	})
      },
      handleRollbackToPreprocess(row) {
        this.rollbackOrderData.orderid = row.orderid;
        this.dialogRollbackToPreprocessVisible = true;
	this.disableSubmit=false;
      },
      rollbackToPreprocess() {
        this.disableSubmit=true;
        orderRollback(this.rollbackOrderData).then(response => {
	  const process_orderid = this.rollbackOrderData.orderid.split('-')[0]
	  const inds = []
	  for (const v of this.list) {
	    if (v.orderid.includes(process_orderid)) {
	      const index = this.list.indexOf(v);
	      inds.push(index);
	    }
	  };
	  for (var i=inds.length-1; i>=0; i--) {
	    this.list.splice(inds[i],1);
	  };
          this.dialogRollbackToPreprocessVisible = false;
          this.$notify({
            title: '成功',
            message: '弹回成功, 请到预处理重新派单',
            type: 'success',
            duration: 2000
          });
        }).catch(error => {
            this.disableSubmit=false;
	})
      }
    },
  }
</script>
