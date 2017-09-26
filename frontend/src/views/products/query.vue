<template>
  <div class="app-container calendar-list-container">
    <div class="filter-container">
      <el-input @keyup.enter.native="handleFilter" style="width: 200px;" class="filter-item" placeholder="商品条码" v-model="listQuery.jancode">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 200px;" class="filter-item" placeholder="名称" v-model="listQuery.name">
      </el-input>
      <el-input style="width: 200px;" class="filter-item" placeholder="品牌" v-model="listQuery.brand">
      </el-input>

      <el-button class="filter-item" type="primary" v-waves icon="search" @click="handleFilter">搜索</el-button>
      <el-button class="filter-item" type="success" style="float:right" v-waves icon="edit" @click="handleCreate">新增商品</el-button>
    </div>

    <el-table :data="list" v-loading.body="listLoading" border fit highlight-current-row style="width: 100%">

      <el-table-column align="center" label="条码" width="150px">
	<template scope="scope">
	  <span>{{scope.row.jancode}}</span>
	</template>
      </el-table-column>

      <el-table-column align="center" label="名称" width="300px" show-overflow-tooltip>
	<template scope="scope">
	  <span>{{scope.row.name}}</span>
	</template>
      </el-table-column>

      <el-table-column align="center" width="150px" label="类目" show-overflow-tooltip>
	<template scope="scope">
	  <span>{{scope.row.category_name}}</span>
	</template>
      </el-table-column>

      <el-table-column align="center" label="品牌" width="100px">
	<template scope="scope">
	  <span>{{scope.row.brand}}</span>
	</template>
      </el-table-column>

      <el-table-column align="center" label="规格" show-overflow-tooltip>
	<template scope="scope">
	  <span>{{scope.row.specification}}</span>
	</template>
      </el-table-column>
      <el-table-column align="center" label="重量" width="100px">
	<template scope="scope">
	  <span>{{scope.row.weight}}</span>
	</template>
      </el-table-column>

      <el-table-column align="center" label="操作" width="80">
        <template scope="scope">
          <el-button size="small" type="success" @click="handleUpdate(scope.row)">编辑
	  </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-show="!listLoading" class="pagination-container">
      <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange" :current-page.sync="listQuery.page"
        :page-sizes="[10,20,30, 50]" :page-size="listQuery.limit" layout="total, sizes, prev, pager, next, jumper" :total="total">
      </el-pagination>
    </div>

    <el-dialog :title="textMap[dialogStatus]" size="small" :visible.sync="dialogFormVisible">
      <el-form class="small-space" :model="temp" label-position="left" label-width="80px">
	<el-form-item label="名称:" label-width="50px">
	  <el-input style="width: 500px" v-model.trim="temp.name"></el-input>
	</el-form-item>
	<el-row>
          <el-col :span="12">
	    <el-form-item label="条码:" label-width="50px">
	      <el-input style="width: 200px" v-model.trim="temp.jancode"></el-input>
	    </el-form-item>
	  </el-col>
          <el-col :span="12">
	    <el-form-item label="类目:" label-width="50px">
	      <el-cascader :options="categoryOptions" v-model="selectCategory" style='width: 200px;' filterable show-all-levels placeholder="类目">
              </el-cascader>
	    </el-form-item>
	  </el-col>
	</el-row>
	<el-row>
          <el-col :span="12">
	    <el-form-item label="品牌:" label-width="50px">
	      <el-input style="width: 200px" v-model.trim="temp.brand"></el-input>
	    </el-form-item>
	  </el-col>
          <el-col :span="12">
	    <el-form-item label="规格:" label-width="50px">
	      <el-input style="width: 200px" v-model.trim="temp.specification"></el-input>
	    </el-form-item>
	  </el-col>
	</el-row>
	<el-row>
          <el-col :span="12">
	    <el-form-item label="产地:" label-width="50px">
	      <el-input style="width: 200px" v-model.trim="temp.origin"></el-input>
	    </el-form-item>
	  </el-col>
          <el-col :span="12">
	    <el-form-item label="型号:" label-width="50px">
	      <el-input style="width: 200px" v-model.trim="temp.model"></el-input>
	    </el-form-item>
	  </el-col>
	</el-row>
	<el-row>
          <el-col :span="12">
	    <el-form-item label="材质:" label-width="50px">
	      <el-input style="width: 200px" v-model.trim="temp.size"></el-input>
	    </el-form-item>
	  </el-col>
          <el-col :span="12">
	    <el-form-item label="单位:" label-width="50px">
	      <el-input style="width: 200px" v-model.trim="temp.unit"></el-input>
	    </el-form-item>
	  </el-col>
	</el-row>
	<el-row>
          <el-col :span="12">
	    <el-form-item label="重量:" label-width="50px">
	      <el-input style="width: 200px" v-model.number="temp.weight" type="number"></el-input>
	    </el-form-item>
	  </el-col>
          <el-col :span="12">
	    <el-form-item label="保质期:" label-width="50px">
	      <el-input style="width: 200px" v-model.trim="temp.expired"></el-input>
	    </el-form-item>
	  </el-col>
	</el-row>
        <el-form-item label="描述:" label-width="50px">
          <el-input type="textarea" :autosize="{minRows: 2, maxRows: 4}" style="width: 500px" v-model.trim="temp.proddesc"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogFormVisible=false">取消</el-button>
        <el-button v-if="dialogStatus=='create'" type="primary" @click="create">确定</el-button>
        <el-button v-else type="primary" @click="update">确定</el-button>
      </div>
    </el-dialog>

  </div>
</template>

<script>
  import { parseTime } from 'utils';
  import { fetchInventory, fetchSupplier, fetchCategory } from 'api/orders';
  import { fetchProduct, createProduct, updateProductJancode } from 'api/products';

  export default {
    data() {
      return {
        list: [],
        listLoading: true,
        total: null,
	categoryOptions: [],
	dialogFormVisible: false,
	dialogStatus: '',
        textMap: {
          update: '编辑',
          create: '创建'
        },
        listQuery: {
          page: 1,
          limit: 10,
	  name: undefined,
	  jancode: undefined,
	  brand: undefined
        },
	selectCategory: [],
        temp: {
          id: undefined,
          jancode: undefined,
          name: undefined,
          category: undefined,
          brand: undefined,
          specification: undefined,
	  origin: undefined,
	  model: undefined,
	  size: undefined,
	  proddesc: undefined,
	  unit: undefined,
	  expired: undefined,
          weight: undefined
        }
      }
    },
    created() {
      this.getCategory();
      this.getProduct();
    },
    methods: {
      getProduct() {
        this.listLoading = true;
        fetchProduct(this.listQuery).then(response => {
          this.list = response.data.results;
          this.total = response.data.count;
          this.listLoading = false;
        })
      },
      getCategory() {
        fetchCategory().then(response => {
	  this.categoryOptions = response.data.results;
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
      handleUpdate(row) {
        this.temp = Object.assign({}, row);
        if ( this.temp.category ) {  // set selectCategory
	  for ( const p of this.categoryOptions ) {
	    for ( const c of p.children ) {
	      if (c.value === ''+this.temp.category) {
		this.selectCategory = [p.value, c.value]
		break;
	      }
	    }
	  }
	}
        this.dialogStatus = 'update';
	this.dialogFormVisible = true;
      },
      handleCreate() {
        this.selectCategory = [],
        this.temp = {
          id: undefined,
          jancode: undefined,
          name: undefined,
          category: undefined,
          brand: undefined,
          specification: undefined,
	  origin: undefined,
	  model: undefined,
	  size: undefined,
	  proddesc: undefined,
	  unit: undefined,
	  expired: undefined,
          weight: undefined
	},
        this.dialogStatus = 'create';
	this.dialogFormVisible = true;
      },
      update() {
        if ( this.selectCategory ) {
          this.temp.category = this.selectCategory[1];
	}
	this.temp.jancode=this.temp.jancode.trim();
        updateProductJancode(this.temp).then(response => {
	  for (const v of this.list) {
	    if (v.id === this.temp.id) {
	      const index = this.list.indexOf(v);
	      this.list.splice(index, 1, this.temp);
	      break;
	    }
	  }
	  this.$notify({
	    title: '成功',
	    message: '更新成功',
	    type: 'success',
	    duration: 2000
	  });
	  this.dialogFormVisible = false
        })
      },
      create() {
        if ( this.selectCategory ) {
          this.temp.category = this.selectCategory[1];
	}
	this.temp.jancode=this.temp.jancode.trim();
        createProduct(this.temp).then(response => {
	  this.$notify({
	    title: '成功',
	    message: '创建成功',
	    type: 'success',
	    duration: 2000
	  });
	  this.dialogFormVisible = false
        })
      }
    }
  }
</script>
