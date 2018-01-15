<template>
  <div class="app-container calendar-list-container">
    <div class="filter-container">
      <el-input @keyup.enter.native="handleFilter" style="width: 200px;" class="filter-item" placeholder="商品条码" v-model="listQuery.jancode">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 200px;" class="filter-item" placeholder="输入年" v-model="listQuery.yeah">
      </el-input>
      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.ordering" placeholder="排序字段">
        <el-option v-for="item in sortOptions" :key="item" :label="item" :value="item">
        </el-option>
      </el-select>

      <el-button class="filter-item" type="primary" v-waves icon="search" @click="handleFilter">搜索</el-button>
    </div>

    <el-table :data="list" v-loading.body="listLoading" border fit highlight-current-row style="width: 100%">
      <el-table-column align="center" label="年" width="65px">
        <template scope="scope">
          <span>{{scope.row.yeah}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="条码" width="130px">
        <template scope="scope">
          <span>{{scope.row.jancode}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="名称" show-overflow-tooltip>
        <template scope="scope">
          <span>{{scope.row.product_name}}</span>
        </template>
      </el-table-column>

      <el-table-column align="center" label="一月" width="65px">
        <template scope="scope">
          <span>{{scope.row.january}}</span>
        </template>
      </el-table-column>

      <el-table-column align="center" label="二月" width="65px">
        <template scope="scope">
          <span>{{scope.row.february}}</span>
        </template>
      </el-table-column>

      <el-table-column align="center" label="三月" width="65px">
        <template scope="scope">
          <span>{{scope.row.march}}</span>
        </template>
      </el-table-column>

      <el-table-column align="center" label="四月" width="65px">
        <template scope="scope">
          <span>{{scope.row.april}}</span>
        </template>
      </el-table-column>

      <el-table-column align="center" label="五月" width="65px">
        <template scope="scope">
          <span>{{scope.row.may}}</span>
        </template>
      </el-table-column>

      <el-table-column align="center" label="六月" width="65px">
        <template scope="scope">
          <span>{{scope.row.june}}</span>
        </template>
      </el-table-column>

      <el-table-column align="center" label="七月" width="65px">
        <template scope="scope">
          <span>{{scope.row.july}}</span>
        </template>
      </el-table-column>

      <el-table-column align="center" label="八月" width="65px">
        <template scope="scope">
          <span>{{scope.row.august}}</span>
        </template>
      </el-table-column>

      <el-table-column align="center" label="九月" width="65px">
        <template scope="scope">
          <span>{{scope.row.september}}</span>
        </template>
      </el-table-column>

      <el-table-column align="center" label="十月" width="65px">
        <template scope="scope">
          <span>{{scope.row.october}}</span>
        </template>
      </el-table-column>

      <el-table-column align="center" label="十一" width="65px">
        <template scope="scope">
          <span>{{scope.row.november}}</span>
        </template>
      </el-table-column>

      <el-table-column align="center" label="十二" width="65px">
        <template scope="scope">
          <span>{{scope.row.december}}</span>
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
  import { fetchPurchaseAnalyze } from 'api/analyzes';

  export default {
    data() {
      return {
        list: [],
        listLoading: true,
        total: null,
        sortOptions: ['-january', '-feburary', '-march', '-april', '-may', '-june', '-july', '-august', '-september', '-october', '-november', '-december'],
        listQuery: {
          page: 1,
          limit: 10,
          ordering: undefined,
          jancode: undefined,
          yeah: undefined
        },
        analyzeData: {
          analyze_time: undefined
        }
      }
    },
    created() {
      this.getList();
    },
    methods: {
      getList() {
        this.listLoading = true;
        fetchPurchaseAnalyze(this.listQuery).then(response => {
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
      handleAnalyze() {
        this.dialogAnalyzeVisible = true
        this.analyzeData.analyze_time = undefined
      }
    }
  }
</script>
