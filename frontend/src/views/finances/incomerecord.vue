<template>
  <div class="app-container calendar-list-container">
    <div class="filter-container">
      <el-input @keyup.enter.native="handleFilter" style="width: 120px;" class="filter-item" placeholder="订单号" v-model="listQuery.orderid">
      </el-input>

      <el-button class="filter-item" type="primary" v-waves icon="search" @click="handleFilter">搜索</el-button>
      <el-button class="filter-item" type="success" style="float:right" v-waves icon="edit" @click="handleCreate">新增收入</el-button>
    </div>

    <el-table :data="list" v-loading.body="listLoading" border fit highlight-current-row style="width: 100%">
      <el-table-column align="center" label="订单" width="150px">
        <template scope="scope">
          <span>{{scope.row.orderid}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="金额" width="100px">
        <template scope="scope">
          <span>{{scope.row.amount}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="收款时间" width="150px">
        <template scope="scope">
          <span>{{scope.row.pay_time|fmDate}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="收款渠道" width="120px">
        <template scope="scope">
          <span>{{scope.row.pay_channel}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="收款区域" width="120px">
        <template scope="scope">
          <span>{{scope.row.who}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="收入来源" width="120px">
        <template scope="scope">
          <span>{{scope.row.income_type}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="状态" width="120px">
        <template scope="scope">
          <span>{{scope.row.status}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="备注">
        <template scope="scope">
          <span>{{scope.row.memo}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="操作" width="80px">
        <template scope="scope">
          <el-button size="small" :disabled="scope.row.status==='已删除'?true:false" type="primary" @click="handleDelete(scope.row)">删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog title="新增收入" size="tiny" :visible.sync="dialogCreateVisible">
      <el-form class="small-space" :model="incomeData" label-position="left" label-width="80px">
	<el-form-item label="订单号:" prop="orderid">
	  <el-input style="width: 180px" v-model.trim="incomeData.orderid"></el-input>
	</el-form-item>
	<el-form-item label="收款区域:" prop="who">
	  <el-select clearable style="width: 180px" class="filter-item" v-model.trim="incomeData.who" placeholder="">
	    <el-option v-for="item in whoOptions" :key="item" :label="item" :value="item">
	    </el-option>
	  </el-select>
	</el-form-item>
	<el-form-item label="日期:">
	  <el-date-picker style="width: 180px" v-model="pay_time" type="datetime" placeholder="选择日期" :picker-options="pickerOptions0">
	  </el-date-picker>
	</el-form-item>
	<el-form-item label="收款方式:" prop="pay_channel">
	  <el-select clearable style="width: 180px" class="filter-item" v-model.trim="incomeData.pay_channel" placeholder="">
	    <el-option v-for="item in payChannelOptions" :key="item" :label="item" :value="item">
	    </el-option>
	  </el-select>
	</el-form-item>
	<el-form-item label="收款金额:" prop="amount">
	  <el-input style="width: 180px" v-model.number="incomeData.amount" type="number"></el-input>
	</el-form-item>
	<el-form-item label="币种:" prop="currency">
	  <el-select clearable style="width: 180px" class="filter-item" v-model.trim="incomeData.currency" placeholder="">
	    <el-option v-for="item in currencyOptions" :key="item" :label="item" :value="item">
	    </el-option>
	  </el-select>
	</el-form-item>
	<el-form-item label="备注:" prop="memo">
          <el-input style="width: 180px" type="textarea" :autosize="{minRows: 2, maxRows: 4}" v-model="incomeData.memo"></el-input>
	</el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogCreateVisible=false">取消</el-button>
        <el-button type="primary" @click="createIncome">提交</el-button>
      </div>
    </el-dialog>

    <div v-show="!listLoading" class="pagination-container">
      <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange" :current-page.sync="listQuery.page"
        :page-sizes="[10,20,30, 50]" :page-size="listQuery.limit" layout="total, sizes, prev, pager, next, jumper" :total="total">
      </el-pagination>
    </div>

  </div>
</template>

<script>
  import { fetchIncomeRecord, createIncomeRecord } from 'api/finances';

  export default {
    data() {
      return {
        list: [],
        listLoading: true,
        total: null,
        roles: [],
        listQuery: {
          page: 1,
          limit: 10
        },
        dialogCreateVisible: false,
        payChannelOptions: ['微信', '银行卡'],
        whoOptions: ['广州', '北京', '东京'],
        currencyOptions: ['人民币', '日元'],
        pay_time: undefined,
        incomeData: {
          who: undefined,
          pay_channel: undefined,
          pay_time: undefined,
          orderid: undefined,
          amount: undefined,
          currency: undefined,
          memo: undefined
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
      this.getOrder();
    },
    methods: {
      getOrder() {
        this.listLoading = true;
        fetchIncomeRecord(this.listQuery).then(response => {
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
      transformTime(val) {
        let tdate = val;
        tdate = [
          [tdate.getFullYear(), tdate.getMonth() + 1, tdate.getDate()].join('-'),
          [tdate.getHours(), tdate.getMinutes(), tdate.getSeconds()].join(':')
        ].join(' ').replace(/(?=\b\d\b)/g, '0');
        return tdate
      },
      resetIncomeData() {
        this.incomeData.orderid = undefined
        this.incomeData.who = undefined
        this.incomeData.pay_channel = undefined
        this.incomeData.pay_time = undefined
        this.incomeData.amount = undefined
        this.incomeData.currency = undefined
        this.incomeData.memo = undefined
        this.pay_time = undefined
      },
      handleCreate() {
        this.resetIncomeData()
        this.dialogCreateVisible = true
      },
      createIncome() {
        this.incomeData.pay_time = this.transformTime(this.pay_time)
        createIncomeRecord(this.incomeData).then(() => {
          this.$notify({
            title: '成功',
            message: '创建成功',
            type: 'success',
            duration: 2000
          });
          this.dialogCreateVisible = false
          this.handleCurrentChange(this.listQuery.page)
        })
      }
    }
  }
</script>
