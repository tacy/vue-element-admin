<template>
  <div class="app-container calendar-list-container">
    <div class="filter-container">
      <el-input @keyup.enter.native="handleFilter" style="width: 200px;" class="filter-item" placeholder="商品条码" v-model="listQuery.jancode">
      </el-input>
      <el-select clearable style="width: 200px" class="filter-item" v-model="listQuery.bonded_name" placeholder="保税仓">
        <el-option v-for="item in inventoryOptions" :key="item.id" :label="item.name" :value="item.id">
        </el-option>
      </el-select>

      <el-button class="filter-item" type="primary" v-waves icon="search" @click="handleFilter">搜索</el-button>
      <el-button class="filter-item" type="success" style="float:right" v-waves icon="edit" @click="handleCreate">新增商品</el-button>
    </div>

    <el-table :data="list" v-loading.body="listLoading" border fit highlight-current-row style="width: 100%">

      <el-table-column align="center" label="条码" width="150px">
	<template scope="scope">
	  <span>{{scope.row.jancode}}</span>
	</template>
      </el-table-column>

      <el-table-column align="center" label="保税仓" width="120px">
	<template scope="scope">
	  <span>{{scope.row.bonded_name}}</span>
	</template>
      </el-table-column>

      <el-table-column align="center" label="名称">
	<template scope="scope">
          <el-input v-show="scope.row.edit" size="small" v-model="scope.row.product_name"></el-input>
          <span v-show="!scope.row.edit">{{ scope.row.product_name }}</span>
	</template>
      </el-table-column>

      <el-table-column align="center" label="备案号" width="200px">
	<template scope="scope">
          <el-input v-show="scope.row.edit" size="small" v-model="scope.row.filing_no"></el-input>
          <span v-show="!scope.row.edit">{{ scope.row.filing_no }}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="操作" width="100">
        <template scope="scope">
          <el-button v-show='!scope.row.edit' type="primary" @click='scope.row.edit=true' size="small" icon="edit">编辑</el-button>
          <el-button v-show='scope.row.edit' type="success" @click='update(scope.row)' size="small" icon="check">完成</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog title="保税产品资料" :visible.sync="dialogCreateVisible">
      <el-form class="small-space" :model="temp" label-position="left" label-width="70px" style='width: 400px; margin-left:50px;'>
        <el-form-item label="商品编码">
          <el-input v-model="temp.jancode"></el-input>
        </el-form-item>
        <el-form-item label="商品名">
          <el-input v-model="temp.product_name"></el-input>
        </el-form-item>
        <el-form-item label="保税仓">
	  <el-select clearable style="width: 330px" class="filter-item" v-model="temp.bonded_name" placeholder="选择保税仓">
	    <el-option v-for="item in bondednameOptions" :key="item" :label="item" :value="item">
	    </el-option>
	  </el-select>
	</el-form-item>
        <el-form-item label="备案号">
          <el-input v-model="temp.filing_no"></el-input>
        </el-form-item>
      </el-form>

      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogCreateVisible = false">取 消</el-button>
        <el-button type="primary" @click="createProduct">新 建</el-button>
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
  import { parseTime } from 'utils';
  import { fetchBondedProduct, updateBondedProduct, createBondedProduct } from 'api/products';

  export default {
    data() {
      return {
        list: [],
        listLoading: true,
        total: null,
	inventoryOptions: [],
	dialogCreateVisible: false,
	bondednameOptions: ['郑州保税', '宁波保税'],
	temp: {
	  jancode: undefined,
	  product_name: undefined,
	  bonded_name: undefined,
	  filing_no: undefined
	},
        listQuery: {
          page: 1,
          limit: 10,
	  jancode: undefined,
	  bonded_name: undefined
        }
      }
    },
    created() {
      this.getProduct();
    },
    methods: {
      getProduct() {
        this.listLoading = true;
        fetchBondedProduct(this.listQuery).then(response => {
          // this.list = response.data.results;
          this.list = response.data.results.map(v => {
            v.edit = false;
            return v
          });
          this.total = response.data.count;
          this.listLoading = false;
        })
      },
      handleFilter() {
        this.listQuery.page=1;
        this.getProduct();
      },
      handleSizeChange(val) {
        this.listQuery.limit = val;
        this.getProduct();
      },
      handleCurrentChange(val) {
        this.listQuery.page = val;
        this.getProduct();
      },
      handleCreate(row) {
        this.temp = {
	  jancode: undefined,
	  product_name: undefined,
	  bonded_name: undefined,
	  filing_no: undefined
	},
        this.dialogCreateVisible = true
      },
      createProduct() {
	createBondedProduct(this.temp).then(response => {
	  this.dialogCreateVisible = false;
	  this.$notify({
	    title: '成功',
	    message: '创建成功',
	    type: 'success',
	    duration: 2000
	  });
        })
        this.getProduct();
      },
      update(row) {
        updateBondedProduct(row, '/bondedproduct/'+row.id+'/').then(response => {
	  this.$notify({
	    title: '成功',
	    message: '更新成功',
	    type: 'success',
	    duration: 2000
	  });
	  row.edit = false;
        })
      }
    }
  }
</script>
