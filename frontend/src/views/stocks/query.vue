<template>
  <div class="app-container calendar-list-container">
    <div class="filter-container">
      <el-select v-model="listQuery.labelVal" style="width: 110px;" class="filter-item" placeholder="请选择">
        <el-option
            v-for="item in selectedOptions"
            :label="item.label"
            :value="item.value">
        </el-option>
      </el-select>
      <el-input @keyup.enter.native="handleFilter" style="width: 120px;" class="filter-item" placeholder="输入商品条码" v-model="listQuery.jancode" v-show="listQuery.labelVal == '1'">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 120px;" class="filter-item" placeholder="输入商品名称" v-model="listQuery.product_title" v-show="listQuery.labelVal == '2'">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 120px;" class="filter-item"  placeholder="输入规格" v-model="listQuery.sku_properties" v-show="listQuery.labelVal == '3'">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 120px;" class="filter-item" placeholder="品牌" v-model="listQuery.brand">
      </el-input>
      <el-select clearable style="width: 100px" class="filter-item" v-model="listQuery.inventory" placeholder="仓库">
        <el-option v-for="item in inventoryOptions" :key="item.id" :label="item.name" :value="item.id">
        </el-option>
      </el-select>
      <el-select clearable style="width: 100px" class="filter-item" v-model="listQuery.stocking_supplier" placeholder="备货渠道">
        <el-option v-for="item in supplierOptions" :key="item.id" :label="item.name" :value="item.id">
        </el-option>
      </el-select>
      <el-checkbox clearable class="filter-item" size="large" v-model="listQuery.check_alert">库存告警</el-checkbox>
      <el-button class="filter-item" size="large" plain="true" style="width:60px;" type="text">库存:</el-button>
      <el-input @keyup.enter.native="handleFilter" style="width: 80px;" class="filter-item" placeholder="最小值" v-model="listQuery.quantity_l">
      </el-input>
      <i class="el-icon-minus"></i>
      <el-input @keyup.enter.native="handleFilter" style="width: 80px;" class="filter-item" placeholder="最大值" v-model="listQuery.quantity_g">
      </el-input>

      <el-button class="filter-item" type="primary" v-waves icon="search" @click="handleFilter">搜索</el-button>
      <el-button class="filter-item" type="success" style="float:right" v-waves icon="edit" @click="handleSync">同步库存</el-button>
    </div>

    <el-table :data="list" v-loading.body="listLoading" border fit highlight-current-row style="width: 100%">

      <el-table-column align="center" label="条码" width="150px">
        <template scope="scope">
          <span>{{scope.row.jancode}}</span>
        </template>
      </el-table-column>

      <el-table-column align="center" label="仓库" width="80px">
        <template scope="scope">
          <span>{{scope.row.inventory_name}}</span>
        </template>
      </el-table-column>

      <el-table-column align="center" label="名称" width="220px">
        <template scope="scope">
          <span>{{scope.row.product_name}}</span>
        </template>
      </el-table-column>

      <el-table-column align="center" label="规格" show-overflow-tooltip>
        <template scope="scope">
          <span>{{scope.row.product_specification}}</span>
        </template>
      </el-table-column>

      <el-table-column align="center" label="库位号" width="120px" show-overflow-tooltip>
        <template scope="scope">
          <!--span>{{scope.row.location}}</span-->
          <el-input v-show="scope.row.edit" size="small" v-model.trim="scope.row.location"></el-input>
          <span v-show="!scope.row.edit">{{ scope.row.location }}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="备货渠道" width="120px" show-overflow-tooltip>
        <template scope="scope">
          <el-select clearable v-show="scope.row.edit" v-model="scope.row.stocking_supplier">
            <el-option v-for="item in supplierOptions" :key="item.id" :label="item.name" :value="item.id">
            </el-option>
          </el-select>
          <span v-show="!scope.row.edit">{{ scope.row.supplier_name }}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="库存警戒" width="100px" show-overflow-tooltip>
        <template scope="scope">
          <el-input v-show="scope.row.edit" size="small" v-model.number="scope.row.stock_alert" type="number"></el-input>
          <span v-show="!scope.row.edit">{{ scope.row.stock_alert }}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="在库" width="80px">
        <template scope="scope">
          <span>{{scope.row.quantity}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="在途" width="80px">
        <template scope="scope">
          <span>{{scope.row.inflight}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="预占" width="80px">
        <template scope="scope">
          <span>{{scope.row.preallocation}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="操作" width="100">
        <template scope="scope">
          <el-button v-show='!scope.row.edit' type="primary" @click='scope.row.edit=true' size="small" icon="edit">编辑</el-button>
          <el-button v-show='scope.row.edit' type="success" @click='update(scope.row)' size="small" icon="check">完成</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-show="!listLoading" class="pagination-container">
      <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange" :current-page.sync="listQuery.page"
        :page-sizes="[10,20,30, 50]" :page-size="listQuery.limit" layout="total, sizes, prev, pager, next, jumper" :total="total">
      </el-pagination>
    </div>

    <el-dialog title="同步库存" size="small" :visible.sync="dialogSyncVisible">
      <el-form class="small-space" :model="temp" label-position="left" label-width="80px">
        <el-form-item label="仓库:">
          <el-select clearable style="width: 150px" class="filter-item" v-model="temp.inventory_name" placeholder="选择仓库">
          <el-option v-for="item in syncInvOptions" :key="item" :label="item" :value="item">
          </el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogSyncVisible=false">取消</el-button>
        <el-button :disabled="submitting" type="primary" @click="sync">提交</el-button>
      </div>
    </el-dialog>

  </div>
</template>

<script>
 import { fetchInventory, fetchCategory, fetchSupplier } from 'api/orders';
 import { fetchStock, updateStock, syncStock } from 'api/stocks';

 export default {
   data() {
     return {
       list: [],
       listLoading: true,
       total: null,
       syncInvOptions: ['贝海', '广州', '东京'],
       dialogSyncVisible: false,
       inventoryOptions: [],
       supplierOptions: [],
       submitting: false,
       listQuery: {
         page: 1,
         limit: 10,
         labelVal: '1',
         jancode: undefined,
         inventory: undefined,
         product_title: undefined,
         sku_properties: undefined,
         brand: undefined,
         quantity_g: undefined,
         quantity__range: undefined,
         quantity_l: undefined,
         stocking_supplier: undefined,
         check_alert: false,
         alerting: undefined
       },
       selectedOptions: [{
         value: '1',
         label: '商品条码'
       }, {
         value: '2',
         label: '商品名称'
       }, {
         value: '3',
         label: '规格'
       }],
       temp: {
         inventory_name: undefined
       }
     }
   },
   created() {
     this.getCategory();
     this.getInventory();
     this.getSupplier();
     if (this.$route.query.alerting !== undefined) {
       this.listQuery.alerting = this.$route.query.alerting
       this.listQuery.check_alert = true
     }
     this.getStock();
   },
   methods: {
     getStock() {
       this.listLoading = true;
       if (this.listQuery.labelVal !== '1') {
         this.listQuery.jancode = undefined
       }
       if (this.listQuery.labelVal !== '2') {
         this.listQuery.product_title = undefined
       }
       if (this.listQuery.labelVal !== '3') {
         this.listQuery.sku_properties = undefined
       }
       if (this.listQuery.check_alert) {
         this.listQuery.alerting = 'T'
       } else {
         this.listQuery.alerting = undefined
       }
       if (this.listQuery.quantity_g && this.listQuery.quantity_l) {
         this.listQuery.quantity__range = this.listQuery.quantity_l + ',' + this.listQuery.quantity_g
       } else {
         this.listQuery.quantity__range = undefined
       }
       fetchStock(this.listQuery).then(response => {
         // this.list = response.data.results;
         this.list = response.data.results.map(v => {
           v.edit = false;
           return v
         });
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
     getSupplier() {
       const query = { limit: 50 };
       fetchSupplier(query).then(response => {
         this.supplierOptions = response.data.results;
       }).catch(err => {
         this.fetchSuccess = false;
         console.log(err);
       });
     },
     handleFilter() {
       this.listQuery.page = 1;
       this.getStock();
     },
     handleSizeChange(val) {
       this.listQuery.limit = val;
       this.getStock();
     },
     handleCurrentChange(val) {
       this.listQuery.page = val;
       this.getStock();
     },
     update(row) {
       updateStock(row, '/stock/' + row.id + '/').then(() => {
         this.$notify({
           title: '成功',
           message: '更新成功',
           type: 'success',
           duration: 2000
         });
         for (const v of this.list) {
           if (v.id === row.id) {
             const index = this.list.indexOf(v);
             for (const s of this.supplierOptions) {
               if (row.stocking_supplier === s.id) {
                 this.list[index].supplier_name = s.name
                 break
               }
             }
             break
           }
         }
         row.edit = false;
       })
     },
     handleSync() {
       this.dialogSyncVisible = true;
       this.temp.inventory_name = null;
     },
     sync() {
       this.submitting = true;
       syncStock(this.temp).then(() => {
         this.$notify({
           title: '成功',
           message: '更新成功',
           type: 'success',
           duration: 2000
         });
         this.dialogSyncVisible = false;
         this.submitting = false;
       }).catch(() => {
         this.submitting = false;
       })
     }
   }
 }
</script>
