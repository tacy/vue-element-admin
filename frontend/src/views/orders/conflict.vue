<template>
  <div class="app-container calendar-list-container">
    <el-table :key='tableKey' :data="list" v-loading.body="listLoading" border fit highlight-current-row style="width: 100%">
      <el-table-column align="center" label="订单号" width="100">
        <template scope="scope">
          <span>{{scope.row.orderid}}</span>
        </template>
      </el-table-column>

      <el-table-column width="270px" align="center" label="商品名称" show-overflow-tooltip>
        <template scope="scope">
          <span>{{scope.row.product_title}}</span>
        </template>
      </el-table-column>

      <el-table-column width="150px" align="center" label="商品编码" show-overflow-tooltip>
        <template scope="scope">
          <span>{{scope.row.jancode}}</span>
        </template>
      </el-table-column>

      <el-table-column width="80px" align="center" label="协调" show-overflow-tooltip>
        <template scope="scope">
          <span>{{scope.row.conflict}}</span>
        </template>
      </el-table-column>

      <el-table-column width="300px" align="center" label="原因" show-overflow-tooltip>
        <template scope="scope">
          <span>{{scope.row.conflict_memo}}</span>
        </template>
      </el-table-column>

      <el-table-column align="center" label="操作" width="158">
        <template scope="scope">
          <el-button :disabled="scope.row.status !== '需介入'? true:false" size="small" type="success" @click="handleUpdate(scope.row)">更 换
          </el-button>
          <el-button :disabled="scope.row.status !== '需介入'? true:false" size="small" type="danger" @click="handleDelete(scope.row)">退 款
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-show="!listLoading" class="pagination-container">
      <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange" :current-page.sync="listQuery.page"
:page-sizes="[10,20,30, 50]" :page-size="listQuery.limit" layout="total, sizes, prev, pager, next, jumper" :total="total">
      </el-pagination>
    </div>

    <el-dialog :title="textMap[dialogStatus]" :visible.sync="dialogFormVisible">
      <el-form class="small-space" :model="temp" label-position="left" label-width="70px" style='width: 400px; margin-left:50px;'>
        <el-form-item label="商品编码">
          <el-input v-model="temp.jancode"></el-input>
        </el-form-item>
        <el-form-item label="商品名称">
          <el-input v-model="temp.product_title"></el-input>
        </el-form-item>
        <el-form-item label="商品规格">
          <el-input v-model="temp.sku_properties_name"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogFormVisible = false">取 消</el-button>
        <el-button v-if="dialogStatus=='create'" type="primary" @click="create">确 定</el-button>
        <el-button v-else type="primary" @click="conflict">确 定</el-button>
      </div>
    </el-dialog>

    <el-dialog title="退款" :visible.sync="dialogDeleteVisible">
      <el-form class="small-space" :model="temp" label-position="left" label-width="70px" style='width: 400px; margin-left:50px;'>
        <el-form-item label="原因">
          <el-input type="textarea" :autosize="{minRows: 2, maxRows: 4}" v-model="temp.conflict_feedback"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogDeleteVisible=false">取 消</el-button>
        <el-button type="primary" @click="conflict()">确 定</el-button>
      </div>
    </el-dialog>

  </div>
</template>

<script>
  import { fetchOrder, orderConflict } from 'api/orders';

  export default {
    name: 'conflict',
    data() {
      return {
        list: null,
        total: null,
        listLoading: true,
        listQuery: {
          page: 1,
          limit: 10,
          status: '需介入',
          sort: '+id'
        },
        temp: {
          id: undefined,
	  conflict_feedback: undefined,
          inventory: undefined,
          shipping: undefined,
          jancode: undefined,
          status: undefined
        },
        dialogFormVisible: false,
	dialogDeleteVisible: false,
        dialogStatus: '',
        textMap: {
          update: '编辑',
          create: '创建'
        },
        stockData: []
      }
    },
    created() {
      this.getList();
    },
    methods: {
      getList() {
        this.listLoading = true;
        fetchOrder(this.listQuery).then(response => {
          this.list = response.data.results;
          this.total = response.data.count;
          this.listLoading = false;
        })
      },
      handleUpdate(row) {
        this.temp = Object.assign({}, row);
        this.dialogStatus = 'update';
        this.dialogFormVisible = true;
      },
      handleDelete(row) {
        this.temp = Object.assign({}, row);
	this.temp.status = '已删除'
	this.dialogDeleteVisible = true;
      },
      conflict() {
        orderConflict(this.temp).then(response => {
          // 刷新列表数据
          for (const v of this.list) {
            if (v.id === this.temp.id) {
              const index = this.list.indexOf(v);
              this.list.splice(index, 1, this.temp);
              break;
            }
          }

          this.dialogFormVisible = false;
	  this.dialogDeleteVisible = false;
          this.$notify({
            title: '成功',
            message: '操作成功',
            type: 'success',
            duration: 2000
          });
        })
      }
    }
  }
</script>
