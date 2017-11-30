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
      <el-input @keyup.enter.native="handleFilter" style="width: 150px;" class="filter-item" placeholder="输入注文编号" v-model="listQuery.orderid" v-show="listQuery.labelVal == '1'">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 150px;" class="filter-item" placeholder="输入商品名称" v-model="listQuery.product_name" v-show="listQuery.labelVal == '2'">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 150px;" class="filter-item"  placeholder="输入商品规格" v-model="listQuery.product_specification" v-show="listQuery.labelVal == '3'">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 150px;" class="filter-item"  placeholder="输入转运单号" v-model="listQuery.delivery_no" v-show="listQuery.labelVal == '4'">
      </el-input>

      <el-input @keyup.enter.native="handleFilter" style="width: 120px;" class="filter-item"  placeholder="商品条码" v-model="listQuery.jancode">
      </el-input>

      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.status" placeholder="状态">
        <el-option v-for="item in statusOptions" :key="item" :label="item" :value="item">
        </el-option>
      </el-select>

      <el-button class="filter-item" type="primary" v-waves icon="search" @click="handleFilter">搜索</el-button>
      <el-button class="filter-item" type="success" style="float:right" v-waves icon="document" @click="handleTransform">转运</el-button>
    </div>

    <el-table :data="list" v-loading.body="listLoading" @selection-change="handleSelect" border fit highlight-current-row style="width: 100%">
      <el-table-column type="selection" width="45" :selectable="checkSelectable">
      </el-table-column>
      <el-table-column align="center" label="注文编号" width="120px">
        <template scope="scope">
          <span>{{scope.row.orderid}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="商品名称" width="200px">
        <template scope="scope">
          <span>{{scope.row.product_name}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="规格" width='150px'>
        <template scope="scope">
          <span>{{scope.row.product_specification}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="条码" width="150px">
        <template scope="scope">
          <span>{{scope.row.jancode}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="数量" width="80px">
        <template scope="scope">
          <span>{{scope.row.quantity}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="状态" width="80px">
        <template scope="scope">
          <span>{{scope.row.status}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="采购时间" width="130px">
        <template scope="scope">
          <span>{{scope.row.purchaseorder_createtime|fmDate}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="运单号">
        <template scope="scope">
          <span>{{scope.row.delivery_no}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="操作" width="100">
        <template scope="scope">
          <el-button size="small" :disabled="scope.row.status==='转运中'?false:true" type="primary" @click="handleStockIn(scope.row)">入库
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-show="!listLoading" class="pagination-container">
      <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange" :current-page.sync="listQuery.page"
        :page-sizes="[10,20,30, 50]" :page-size="listQuery.limit" layout="total, sizes, prev, pager, next, jumper" :total="total">
      </el-pagination>
    </div>

    <el-dialog title="转运国内" size="small" :visible.sync="dialogTransformVisible">
      <el-form class="small-space" :model="transformData" label-position="left" label-width="80px">
        <el-form-item label="运单号">
          <el-input v-model.trim="transformData.delivery_no"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogTransformVisible=false">取 消</el-button>
        <el-button type="primary" @click="transform()">确 定</el-button>
      </div>
    </el-dialog>

    <el-dialog title="入库" size="tiny" :visible.sync="dialogStockInVisible">
      <el-form class="small-space" :model="stockInData" label-position="left" label-width="80px">
        <el-form-item label="采购数量">
          <el-input :disabled="true" v-model.number="stockInData.quantity" type="number"></el-input>
        </el-form-item>
        <el-form-item label="到库数量">
          <el-input v-model.number="stockInData.qty" type="number"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogStockInVisible=false">取 消</el-button>
        <el-button type="primary" @click="stockIn">确 定</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
  import { fetchPurchaseOrderItem, purchaseOrderTransform, domesticStockIn } from 'api/purchases';

  export default {
    data() {
      return {
        list: [],
        listLoading: true,
        total: null,
        statusOptions: ['东京仓', '转运中', '已入库'],
        selectRow: [],
        dialogTransformVisible: false,
        dialogStockInVisible: false,
        selectedOptions: [{
          value: '1',
          label: '注文编号'
        }, {
          value: '2',
          label: '商品名称'
        }, {
          value: '3',
          label: '商品规格'
        }, {
          value: '4',
          label: '转运单号'
        }],
        listQuery: {
          page: 1,
          limit: 50,
          labelVal: '1',
          inventory: 3,
          status: undefined,
          product_name: undefined,
          product_specification: undefined,
          orderid: undefined,
          jancode: undefined,
          delivery_no: undefined
        },
        transformData: {
          purchaseorderitems: undefined,
          delivery_no: undefined
        },
        stockInData: {
          id: undefined,
          quantity: undefined,
          qty: undefined
        }
      }
    },
    filters: {
      fmDate(value) {
        if (!value) return ''
        value = value.substr(2, 8) + ' ' + value.substr(11, 5)
        return value
      }
    },
    created() {
      this.getPurchaseOrderItem();
    },
    methods: {
      getPurchaseOrderItem() {
        this.listLoading = true;
        if (this.listQuery.labelVal !== '1') {
          this.listQuery.orderid = undefined
        }
        if (this.listQuery.labelVal !== '2') {
          this.listQuery.product_title = undefined
        }
        if (this.listQuery.labelVal !== '3') {
          this.listQuery.product_specification = undefined
        }
        if (this.listQuery.labelVal !== '4') {
          this.listQuery.delivery_no = undefined
        }
        fetchPurchaseOrderItem(this.listQuery).then(response => {
          this.list = response.data.results;
          this.total = response.data.count;
          this.listLoading = false;
        })
      },
      handleFilter() {
        this.listQuery.page = 1;
        this.getPurchaseOrderItem();
      },
      checkSelectable(row) {
        return row.status === '东京仓'
      },
      handleSelect(val) {
        this.selectRow = val;
      },
      handleSizeChange(val) {
        this.listQuery.limit = val;
        this.getPurchaseOrderItem();
      },
      handleCurrentChange(val) {
        this.listQuery.page = val;
        this.getPurchaseOrderItem();
      },
      handleTransform() {
        if (this.selectRow.length === 0) {
          this.$message({
            type: 'error',
            message: '请选择转运商品',
            duration: 2000
          });
          return;
        }
        this.transformData.delivery_no = null;
        this.dialogTransformVisible = true;
      },
      transform() {
        this.transformData.purchaseorderitems = this.selectRow
        purchaseOrderTransform(this.transformData).then(response => {
          this.$notify({
            title: '成功',
            message: '转运完成',
            type: 'success',
            duration: 2000
          });
          for (const o of this.list) {
            for (const s of this.selectRow) {
              if (o.id === s.id) {
                const index = this.list.indexOf(o);
                // this.list[index].status = '转运中';
                // this.list[index].delivery_no = this.transformData.delivery_no;
                this.list.splice(index, 1);
                break;
              }
            }
          }
          this.selectRow = [];
          this.dialogTransformVisible = false;
        });
      },
      handleStockIn(row) {
        this.stockInData = row;
        this.dialogStockInVisible = true;
      },
      stockIn() {
        domesticStockIn(this.stockInData).then(response => {
          this.dialogStockInVisible = false;
          this.$notify({
            title: '成功',
            message: '入库完成',
            type: 'success',
            duration: 2000
          });
          for (const o of this.list) {
            if (o.id === row.id) {
              const index = this.list.indexOf(o);
              this.list[index].status = '已入库';
              break;
            }
          }
        });
      }
    }
  }
</script>
