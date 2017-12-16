<template>
  <div class="app-container calendar-list-container">
    <div class="filter-container">
      <el-input @keyup.enter.native="handleFilter" style="width: 150px;" class="filter-item" placeholder="订单号" v-model="listQuery.orderid">
      </el-input>
      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.status" placeholder="状态">
        <el-option v-for="item in statusOptions" :key="item" :label="item" :value="item">
        </el-option>
      </el-select>

      <el-button class="filter-item" type="primary" v-waves icon="search" @click="handleFilter">搜索</el-button>
    </div>

    <el-table :data="list" v-loading.body="listLoading" border fit highlight-current-row style="width: 100%">
      <el-table-column align="center" label="订单号" width="100px">
        <template scope="scope">
          <span>{{scope.row.orderid}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="类型" width="65px">
        <template scope="scope">
          <span>{{scope.row.case_type_name}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="状态" width="100px">
        <template scope="scope">
          <!--span>{{scope.row.status}}</span-->
          <el-tag :type="scope.row.status | statusFilter">{{scope.row.status}}</el-tag>
        </template>
      </el-table-column>
      <el-table-column align="center" label="策略" width="65px">
        <template scope="scope">
          <span>{{scope.row.process_method_name}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="退运条码" width="130px">
        <template scope="scope">
          <span>{{scope.row.return_jancode}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="补发单" width="135px">
        <template scope="scope">
          <span>{{scope.row.orderid2}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="退补款" width="90px">
        <template scope="scope">
          <span>{{scope.row.balance_price}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="条码" width="130px">
        <template scope="scope">
          <span>{{scope.row.jancode}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="商品名" show-overflow-tooltip>
        <template scope="scope">
          <span>{{scope.row.product_title}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="面单" width="100px" show-overflow-tooltip>
        <template scope="scope">
          <span>{{scope.row.db_number}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="数量" width="65">
        <template scope="scope">
          <span>{{scope.row.quantity}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="操作" width="140">
        <template scope="scope">
          <el-button size="small" v-if="scope.row.process_method===null?true:false" type="primary" @click="handleAscProcess(scope.row)">处理
          </el-button>
          <el-button size="small" v-if="scope.row.process_method===null?true:false" type="danger" @click="handleDelete(scope.row)">删除
          </el-button>
          <el-button size="small" v-if="scope.row.balance_price!==null?true:false" :disabled="scope.row.balance_status==='处理中'?false:true" type="primary" @click="balance(scope.row)">退款
          </el-button>
          <el-button size="small" v-if="scope.row.return_product!==null?true:false" :disabled="scope.row.return_status==='处理中'?false:true" type="primary" @click="arrive(scope.row)">退运
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-show="!listLoading" class="pagination-container">
      <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange" :current-page.sync="listQuery.page"
        :page-sizes="[10,20,30, 50]" :page-size="listQuery.limit" layout="total, sizes, prev, pager, next, jumper" :total="total">
      </el-pagination>
    </div>

    <el-dialog title="售后处理" size="small" :visible.sync="dialogAscVisible">
      <el-form :rules="rules" ref="form" class="small-space" :model="ascData" label-position="left" label-width="80px">
        <el-form-item label="处理方式:" prop="process_method">
          <el-select clearable style="width: 150px" class="filter-item" v-model.trim="ascData.process_method" @change="modifyVisible" placeholder="选择方式">
          <el-option v-for="item in asmOptions" :key="item.name" :label="item.name" :value="item.id">
          </el-option>
          </el-select>
        </el-form-item>
        <div>
        <el-row v-if="ascData.needResend">
          <el-col :span="12">
            <el-form-item label="补发商品:" prop="resend_jancode">
              <el-input style="width: 150px" v-model.trim="ascData.resend_jancode" placeholder="输入条码"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="数量:" prop="resend_quantity">
              <el-input style="width: 150px" v-model.number="ascData.resend_quantity" type="number" placeholder="输入数量"></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row v-if="ascData.isRefund">
          <el-col :span="10">
            <el-form-item label="退款商品:" prop="return_jancode">
              <el-input style="width: 150px" v-model.trim="ascData.return_jancode" placeholder="输入条码"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="7">
            <el-form-item label="数量:" label-width="50px" prop="return_quantity">
              <el-input style="width: 100px" v-model.number="ascData.return_quantity" type="number" placeholder="输入数量"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="7">
            <el-form-item label="金额:" label-width="50px" prop="return_amount">
              <el-input style="width: 100px" v-model.number="ascData.return_amount" type="number" placeholder="退款金额"></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row v-if="ascData.needRetention">
          <el-col :span="10">
            <el-form-item label="保留商品:" prop="retention_jancode">
              <el-input style="width: 150px" v-model.trim="ascData.retention_jancode" placeholder="输入条码"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="7">
            <el-form-item label="数量:" label-width="50px" prop="retention_quantity">
              <el-input style="width: 100px" v-model.number="ascData.retention_quantity" type="number" placeholder="输入数量"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="7">
            <el-form-item label="金额:" label-width="50px" prop="retention_amount">
              <el-input style="width: 100px" v-model.number="ascData.retention_amount" type="number" placeholder="差价金额"></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row v-if="ascData.needReturn & !ascData.isRefund">
          <el-col :span="12">
            <el-form-item label="退运商品:" prop="return_jancode">
              <el-input style="width: 150px" v-model.trim="ascData.return_jancode" placeholder="输入条码"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="数量:" prop="return_quantity">
              <el-input style="width: 150px" v-model.number="ascData.return_quantity" type="number" placeholder="输入数量"></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="退运:" v-if="ascData.isDamaged">
          <el-checkbox v-model="ascData.isDamagedNotReturn">无需退运</el-checkbox>
        </el-form-item>
        </div>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogAscVisible=false">取消</el-button>
        <el-button type="primary" @click="ascProcess">提交</el-button>
      </div>
    </el-dialog>

  </div>
</template>

<script>
  import { fetchAfterSaleCase, fetchAfterSaleMeta, afterSaleProcess, afterSaleArrive, afterSaleBalance, afterSaleUpdate } from 'api/orders';

  export default {
    data() {
      return {
        list: [],
        listLoading: true,
        total: null,
        dialogFormVisible: false,
        dialogCreateVisible: false,
        dialogAscVisible: false,
        inventoryOptions: [],
        statusOptions: ['待处理', '处理中', '已完成', '已删除'],
        asmOptions: [],
        listQuery: {
          page: 1,
          limit: 10,
          receiver_name: undefined,
          jancode: undefined,
          orderid: undefined,
          status: undefined,
          product_title: undefined
        },
        ascData: {
          id: undefined,
          process_method: undefined,
          return_jancode: undefined,
          return_quantity: undefined,
          return_amount: undefined,
          resend_jancode: undefined,
          resend_quantity: undefined,
          retention_jancode: undefined,
          retention_quantity: undefined,
          retention_amount: undefined,
          isRefund: false,  // 是否是退款
          isOnlyRefund: false,  // 是否仅仅退款
          isDamaged: false,  // 破损case
          isDamagedNotReturn: false,  // 破损是否需要退运
          needReturn: false,
          needResend: false,
          needRetention: false
        },
        actionData: {
          id: undefined
        },
        temp: {
          jancode: undefined,
          quantity: undefined,
          case_type_name: undefined,
          process_method_name: undefined
        }
      };
    },
    filters: {
      statusFilter(status) {
        const statusMap = {
          已完成: 'success',
          处理中: 'primary',
          待处理: 'warning',
          已删除: 'danger'
        };
        return statusMap[status]
      }
    },
    created() {
      this.getList();
    },
    methods: {
      getList() {
        this.listLoading = true;
        fetchAfterSaleCase(this.listQuery).then(response => {
          this.list = response.data.results;
          this.total = response.data.count;
          this.listLoading = false;
        })
      },
      handleFilter() {
        this.listQuery.page = 1;
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
      resetData() {
        this.ascData.balance_price = undefined
        this.ascData.return_jancode = undefined
        this.ascData.return_quantity = undefined
        this.ascData.return_amount = undefined
        this.ascData.resend_jancode = undefined
        this.ascData.resend_quantity = undefined
        this.ascData.retention_jancode = undefined
        this.ascData.retention_quantity = undefined
        this.ascData.retention_amount = undefined
        this.ascData.isRefund = false
        this.ascData.isOnlyRefund = false
        this.ascData.isDamaged = false
        this.ascData.isDamagedNotReturn = false
        this.ascData.needReturn = false
        this.ascData.needResend = false
        this.ascData.needRetention = false
      },
      modifyVisible(val) {
        this.resetData()
        for (const v of this.asmOptions) {
          if (v.id === val) {
            this.temp.process_method_name = v.name
            break
          }
        }
        if (this.temp.case_type_name === '错发') {
          if (this.temp.process_method_name === '重发') {
            this.ascData.needResend = true
            this.ascData.needReturn = true
            this.ascData.resend_jancode = this.temp.jancode
            this.ascData.resend_quantity = this.temp.quantity
          } else if (this.temp.process_method_name === '退款') {  // 退款退运
            this.ascData.isRefund = true
            this.ascData.needReturn = true
            this.ascData.isOnlyRefund = false
          } else if (this.temp.process_method_name === '保留') {
            this.ascData.needRetention = true
          }
        }
        if (this.temp.case_type_name === '漏发') {
          if (this.temp.process_method_name === '补发') {
            this.ascData.needResend = true
            this.ascData.resend_jancode = this.temp.jancode
          } else if (this.temp.process_method_name === '退款') {  // 仅退款
            this.ascData.isRefund = true
            this.ascData.needReturn = true
            this.ascData.return_jancode = this.temp.jancode
            this.ascData.isOnlyRefund = true
          }
        }
        if (this.temp.case_type_name === '破损') {
          this.ascData.isDamaged = true
          if (this.temp.process_method_name === '重发') {
            this.ascData.needResend = true
            this.ascData.needReturn = true
            this.ascData.resend_jancode = this.temp.jancode
            this.ascData.resend_quantity = this.temp.quantity
            this.ascData.return_jancode = this.temp.jancode
            this.ascData.return_quantity = this.temp.quantity
          } else if (this.temp.process_method_name === '退款') {
            this.ascData.isRefund = true
            this.ascData.needReturn = true
            this.ascData.return_jancode = this.temp.jancode
            this.ascData.return_quantity = this.temp.quantity
          } else if (this.temp.process_method_name === '保留') {
            this.ascData.needRetention = true
          }
        }
        if (this.temp.case_type_name === '退换') {
          if (this.temp.process_method_name === '换货') {
            this.ascData.needResend = true
            this.ascData.needReturn = true
            this.ascData.return_jancode = this.temp.jancode
            this.ascData.return_quantity = this.temp.quantity
          } else if (this.temp.process_method_name === '退款') {  // 退款退运
            this.ascData.isRefund = true
            this.ascData.needReturn = true
            this.ascData.return_jancode = this.temp.jancode
            this.ascData.return_quantity = this.temp.quantity
            this.ascData.isOnlyRefund = false
          }
        }
        if (this.temp.case_type_name === '丢件') {
          if (this.temp.process_method_name === '重发') {
            this.ascData.needResend = true
            this.ascData.resend_jancode = this.temp.jancode
            this.ascData.resend_quantity = this.temp.quantity
          } else if (this.temp.process_method_name === '退款') {  // 仅退款
            this.ascData.isRefund = true
            this.ascData.needReturn = true
            this.ascData.return_jancode = this.temp.jancode
            this.ascData.return_quantity = this.temp.quantity
            this.ascData.isOnlyRefund = false
          }
        }
      },
      handleAscProcess(row) {
        const queryAsm = { parent_id: row.case_type_metaid }
        this.temp = Object.assign({}, row)
        this.ascData.id = row.id
        this.ascData.process_method = undefined
        fetchAfterSaleMeta(queryAsm).then(response => {
          this.asmOptions = response.data.results
        })
        this.dialogAscVisible = true
        this.ascData.isDamaged = false
      },
      ascProcess() {
        afterSaleProcess(this.ascData).then(() => {
          this.handleCurrentChange(this.listQuery.page)
          this.dialogAscVisible = false
        });
      },
      balance(row) {
        this.actionData.id = row.id
        afterSaleBalance(this.actionData).then(() => {
          row.balance_status = '已完成'
          row.status = '已完成'
          if (row.return_product !== null & row.return_status === '处理中') {
            row.status = '处理中'
          }
          for (const v of this.list) {
            if (v.id === row.id) {
              const index = this.list.indexOf(v)
              this.list.splice(index, 1, row)
            }
          }
          this.$notify({
            title: '成功',
            message: '退款完成',
            type: 'success',
            duration: 2000
          });
        });
      },
      arrive(row) {
        this.actionData.id = row.id
        afterSaleArrive(this.actionData).then(() => {
          row.return_status = '已完成'
          row.status = '已完成'
          if (row.balance_price !== null & row.balance_status === '处理中') {
            row.status = '处理中'
          }
          for (const v of this.list) {
            if (v.id === row.id) {
              const index = this.list.indexOf(v)
              this.list.splice(index, 1, row)
            }
          }
          this.$notify({
            title: '成功',
            message: '退运完成',
            type: 'success',
            duration: 2000
          });
        });
      },
      handleDelete(row) {
        row.status = '已删除'
        afterSaleUpdate(row, '/aftersale/case/' + row.id + '/').then(() => {
          this.$notify({
            title: '成功',
            message: '售后单删除成功',
            type: 'success',
            duration: 2000
          });
        });
      }
    }
  }
</script>
