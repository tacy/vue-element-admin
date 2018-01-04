<template>
  <div class="app-container calendar-list-container">
    <div class="filter-container">
      <el-input @keyup.enter.native="handleFilter" style="width: 120px;" class="filter-item" placeholder="订单号" v-model="listQuery.orderid">
      </el-input>

      <el-button class="filter-item" type="primary" v-waves icon="search" @click="handleFilter">搜索</el-button>
      <el-button class="filter-item" type="success" style="float:right" v-waves icon="edit" @click="handleCreate">新增转账</el-button>
    </div>

    <el-table :data="list" v-loading.body="listLoading" border fit highlight-current-row style="width: 100%">
      <el-table-column align="center" label="转账时间" width="150px">
        <template scope="scope">
          <span>{{scope.row.transform_time|fmDate}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="资金来源" width="100px">
        <template scope="scope">
          <span>{{scope.row.channel_name}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="金额">
        <template scope="scope">
          <span>{{scope.row.amount}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="转账费用" width="120px">
        <template scope="scope">
          <span>{{scope.row.transform_fee}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="收款时间" width="150px">
        <template scope="scope">
          <span>{{scope.row.accept_time|fmDate}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="收款金额">
        <template scope="scope">
          <span>{{scope.row.amount_jp}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="收款费用" width="120px">
        <template scope="scope">
          <span>{{scope.row.accept_fee}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="操作" width="120px">
        <template scope="scope">
          <el-button size="small" :disabled="scope.row.accept_jp===null?false:true" type="primary" @click="handleUpdate(scope.row)">收款
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog title="新增转账" size="tiny" :visible.sync="dialogCreateVisible">
      <el-form class="small-space" :model="transformData" label-position="left" label-width="80px">
        <el-form-item label="资金来源:" prop="who">
          <el-select clearable style="width: 180px" class="filter-item" v-model.trim="transformData.channel_name" placeholder="">
            <el-option v-for="item in channelnameOptions" :key="item" :label="item" :value="item">
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="转账日期:">
          <el-date-picker style="width: 180px" v-model="transform_time" type="datetime" placeholder="选择日期" :picker-options="pickerOptions0">
          </el-date-picker>
        </el-form-item>
        <el-form-item label="转账金额:" prop="amount">
          <el-input style="width: 180px" v-model.number="transformData.amount" type="number"></el-input>
        </el-form-item>
        <el-form-item label="转账费用:" prop="transform_fee">
          <el-input style="width: 180px" v-model.number="transformData.transform_fee" type="number"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogCreateVisible=false">取消</el-button>
        <el-button type="primary" @click="createTransform">提交</el-button>
      </div>
    </el-dialog>

    <el-dialog title="确认收款" size="tiny" :visible.sync="dialogUpdateVisible">
      <el-form class="small-space" :model="transformData" label-position="left" label-width="80px">
        <el-form-item label="到帐日期:">
          <el-date-picker style="width: 180px" v-model="accept_time" type="datetime" placeholder="选择日期" :picker-options="pickerOptions0">
          </el-date-picker>
        </el-form-item>
        <el-form-item label="到帐金额:" prop="amount">
          <el-input style="width: 180px" v-model.number="transformData.amount_jp" type="number"></el-input>
        </el-form-item>
        <el-form-item label="收款费用:" prop="transform_fee">
          <el-input style="width: 180px" v-model.number="transformData.accept_fee" type="number"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogUpdateVisible=false">取消</el-button>
        <el-button type="primary" @click="updateTransform">提交</el-button>
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
  import { fetchTransformRecord, createTransformRecord, updateTransformRecord } from 'api/finances';

  export default {
    data() {
      return {
        list: [],
        listLoading: true,
        total: null,
        listQuery: {
          page: 1,
          limit: 10
        },
        dialogCreateVisible: false,
        channelnameOptions: ['洋码头', '天狗'],
        transform_time: undefined,
        accept_time: undefined,
        transformData: {
          id: undefined,
          transform_time: undefined,
          channel_name: undefined,
          amount: undefined,
          transform_fee: undefined,
          amount_jp: undefined,
          accept_fee: undefined,
          accept_time: undefined
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
        fetchTransformRecord(this.listQuery).then(response => {
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
      resetTransformData() {
        this.transformData.id = undefined
        this.transformData.transform_time = undefined
        this.transformData.channel_name = undefined
        this.transformData.amount = undefined
        this.transformData.transform_fee = undefined
        this.transformData.amount_jp = undefined
        this.transformData.accept_fee = undefined
        this.transformData.accept_time = undefined
        this.accept_time = undefined
        this.transform_time = undefined
      },
      transformTime(val) {
        let tdate = val;
        tdate = [
          [tdate.getFullYear(), tdate.getMonth() + 1, tdate.getDate()].join('-'),
          [tdate.getHours(), tdate.getMinutes(), tdate.getSeconds()].join(':')
        ].join(' ').replace(/(?=\b\d\b)/g, '0');
        return tdate
      },
      handleCreate() {
        this.resetTransformData()
        this.dialogCreateVisible = true
      },
      createTransform() {
        this.transformData.transform_time = this.transformTime(this.transform_time)
        createTransformRecord(this.transformData).then(() => {
          this.$notify({
            title: '成功',
            message: '创建成功',
            type: 'success',
            duration: 2000
          });
          this.dialogCreateVisible = false
          this.handleCurrentChange(this.listQuery.page)
        })
      },
      handleUpdate(row) {
        this.resetTransformData()
        this.transformData = Object.assign({}, row);
        this.dialogUpdateVisible = true
      },
      updateTransform() {
        this.transformData.accept_time = this.transformTime(this.accept_time)
        updateTransformRecord(this.transformData, '/finance/transform/record/' + this.transformData.id + '/').then(() => {
          this.$notify({
            title: '成功',
            message: '确认收款成功',
            type: 'success',
            duration: 2000
          });
          this.dialogUpdateVisible = false
          this.handleCurrentChange(this.listQuery.page)
        })
      }
    }
  }
</script>
