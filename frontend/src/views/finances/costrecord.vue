<template>
  <div class="app-container calendar-list-container">
    <div class="filter-container">
      <el-select clearable style="width: 120px" class="filter-item" v-model="queryCostType.inventory" v-on:change="getCostType()" placeholder="仓库">
	<el-option v-for="item in inventoryOptions" :key="item.id" :label="item.name" :value="item.id">
	</el-option>
      </el-select>
      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.costtype" placeholder="类目">
	<el-option v-for="item in costTypeOptions" :key="item.id" :label="item.name" :value="item.id">
	</el-option>
      </el-select>
      <el-date-picker class="filter-item" v-model="daterange" @change="transformTime" type="datetimerange" placeholder="选择日期范围"></el-date-picker>

      <el-button class="filter-item" type="primary" v-waves icon="search" @click="handleFilter">搜索</el-button>
    </div>

    <el-table :data="list" v-loading.body="listLoading" border fit highlight-current-row style="width: 100%">
      <el-table-column align="center" label="支出类型" width="150px">
        <template scope="scope">
          <span>{{scope.row.costtype_name}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="仓库" width="100px">
        <template scope="scope">
          <span>{{scope.row.inventory_name}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="记录时间" width="150px">
        <template scope="scope">
          <span>{{scope.row.pay_time|fmDate}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="金额" width="120px">
        <template scope="scope">
          <span>{{scope.row.amount}}</span>
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

    <div v-show="!listLoading" class="pagination-container">
      <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange" :current-page.sync="listQuery.page"
        :page-sizes="[10,20,30, 50]" :page-size="listQuery.limit" layout="total, sizes, prev, pager, next, jumper" :total="total">
      </el-pagination>
    </div>

  </div>
</template>

<script>
  import { fetchCostRecord, fetchCostType } from 'api/finances';

  export default {
    data() {
      return {
        list: [],
        listLoading: true,
        total: null,
        roles: [],
        daterange: [],
        inventoryOptions: [],
        costTypeOptions: [],
        listQuery: {
          page: 1,
          limit: 10,
          pay_time_0: undefined,
          pay_time_1: undefined,
          costtype: undefined,
          inventory_in: undefined
        },
        queryCostType: {
          inventory: undefined
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
      transformTime(val) {
        const tdate = val;
        this.listQuery.pay_time_0 = val.slice(0, 19)
        this.listQuery.pay_time_1 = val.slice(22)
        return tdate
      },
      getOrder() {
        this.roles = this.$store.state.user.roles;
        if (this.roles[0] === 'supergz') {
          this.listQuery.inventory_in = '3'
          this.inventoryOptions = [{ name: '广州', id: 3 }]
        } else if (this.roles[0] === 'supertokyo') {
          this.listQuery.inventory_in = '4,5'
          this.inventoryOptions = [{ name: '东京', id: 4 }, { name: '天狗保税', id: 5 }]
        } else if (this.roles[0] === 'super') {
          this.listQuery.inventory_in = '3,4,5'
          this.inventoryOptions = [{ name: '东京', id: 4 }, { name: '广州', id: 3 }, { name: '天狗保税', id: 5 }]
        }
        this.listLoading = true;
        fetchCostRecord(this.listQuery).then(response => {
          this.list = response.data.results;
          this.total = response.data.count;
          this.listLoading = false;
        })
      },
      getCostType() {
        fetchCostType(this.queryCostType).then(response => {
          this.costTypeOptions = response.data.results
        });
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
      }
    }
  }
</script>
