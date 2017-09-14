<template>
  <div class="app-container calendar-list-container">
    <div class="filter-container">
      <el-input @keyup.enter.native="handleFilter" style="width: 200px;" class="filter-item" placeholder="商品条码" v-model="listQuery.jancode">
      </el-input>
      <el-select clearable style="width: 200px" class="filter-item" v-model="listQuery.inventory" placeholder="仓库">
        <el-option v-for="item in inventoryOptions" :key="item.id" :label="item.name" :value="item.id">
        </el-option>
      </el-select>

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

      <el-table-column align="center" label="名称" width="280px" show-overflow-tooltip>
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
          <el-input v-show="scope.row.edit" size="small" v-model="scope.row.location"></el-input>
          <span v-show="!scope.row.edit">{{ scope.row.location }}</span>
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
        <el-button type="primary" @click="sync">提交</el-button>
      </div>
    </el-dialog>

  </div>
</template>

<script>
  import { parseTime } from 'utils';
  import { fetchInventory, fetchCategory } from 'api/orders';
  import { fetchStock, updateStock, syncStock } from 'api/stocks';

  export default {
    data() {
      return {
        list: [],
        listLoading: true,
        total: null,
	syncInvOptions: ['贝海', '广州'],
	dialogSyncVisible: false,
	inventoryOptions: [],
        listQuery: {
          page: 1,
          limit: 10,
	  jancode: undefined,
	  inventory: undefined
        },
	temp: {
	  inventory_name: undefined
	}
      }
    },
    created() {
      this.getCategory();
      this.getInventory()
      this.getStock();
    },
    methods: {
      getStock() {
        this.listLoading = true;
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
      handleFilter() {
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
        updateStock(row, '/stock/'+row.id+'/').then(response => {
	  this.$notify({
	    title: '成功',
	    message: '更新成功',
	    type: 'success',
	    duration: 2000
	  });
	  row.edit = false;
        })
      },
      handleSync() {
        this.dialogSyncVisible = true;
	this.temp.inventory_name = null;
      },
      sync() {
        syncStock(this.temp).then(response => {
	  this.$notify({
	    title: '成功',
	    message: '更新成功',
	    type: 'success',
	    duration: 2000
	  });
	  this.dialogSyncVisible = false;
        });
      }
    }
  }
</script>
