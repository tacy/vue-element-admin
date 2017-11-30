<template>
  <div>
      <div class="filter-container">
        <el-button class="filter-item" style="float:right" @click="handlePurchase" type="primary" icon="edit">保存采购单</el-button>
      </div>
      <el-table :data="postData.data" v-loading.body="listLoading" border fit highlight-current-row style="width: 100%">
        <el-table-column align="center" label="条码" width="120">
          <template scope="scope">
            <span class="link-type" @click="getOrder(scope.row)">{{scope.row.jancode}}</span>
          </template>
        </el-table-column>

        <el-table-column align="center" label="商品名称" width="200px">
          <template scope="scope">
            <span>{{scope.row.product_name}}</span>
            <el-button v-if="scope.row.purchase_link1!==null" type="text" size="small"><a :href="scope.row.purchase_link1" target="_blank">采购1</a></el-button>
            <el-button v-if="scope.row.purchase_link2!==null" type="text" size="small"><a :href="scope.row.purchase_link2" target="_blank">采购2</a></el-button>
            <el-button v-if="scope.row.purchase_link3!==null" type="text" size="small"><a :href="scope.row.purchase_link3" target="_blank">采购3</a></el-button>
          </template>
        </el-table-column>

        <el-table-column align="center" label="规格" width="120px">
          <template scope="scope">
            <span>{{scope.row.sku_properties_name}}</span>
          </template>
        </el-table-column>

        <el-table-column align="center" label="支付时间" width="100px">
          <template scope="scope">
            <span>{{scope.row.piad_time}}</span>
          </template>
        </el-table-column>

        <el-table-column align="center" label="售价" width="65px">
          <template scope="scope">
            <span>{{scope.row.product_price}}</span>
          </template>
        </el-table-column>

        <el-table-column align="center" label="待采" width="65px">
          <template scope="scope">
            <span>{{scope.row.qty}}</span>
          </template>
        </el-table-column>

        <el-table-column align="center" v-if='inventory===3' label="东京仓" width="80px">
          <template scope="scope">
            <span>{{scope.row.tokyo_stock}}</span>
          </template>
        </el-table-column>

        <el-table-column align="center" label="渠道" width="150px">
          <template scope="scope">
            <el-select clearable filterable v-model="scope.row.supplier" placeholder="渠道">
              <el-option v-for="item in supplierOptions" :key="item.id" :label="item.name" :value="item.id">
              </el-option>
            </el-select>
          </template>
        </el-table-column>

        <el-table-column align="center" label="实采" width="100px">
          <template scope="scope">
            <el-input size="small" v-model.number="scope.row.quantity" type="number"></el-input>
          </template>
        </el-table-column>

        <el-table-column align="center" label="价格" width="120px">
          <template scope="scope">
            <el-input size="small" v-model.number="scope.row.price" type="number"></el-input>
          </template>
        </el-table-column>

        <el-table-column align="center" label="注文编号" width="200px">
          <template scope="scope">
            <el-input size="small" v-model.trim="scope.row.purchaseorderid"></el-input>
          </template>
        </el-table-column>

      </el-table>

    <el-dialog title="标记疑难" :visible.sync="dialogConflictVisible" size="small">
      <el-table :data="orderData" border fit highlight-current-row style="width: 100%">
        <el-table-column align="center" label="订单编号">
          <template scope="scope">
            <span>{{scope.row.orderid}}</span>
          </template>
        </el-table-column>

        <el-table-column align="center" label="建议方式">
          <template scope="scope">
            <el-select clearable v-model="scope.row.conflict" placeholder="选择">
              <el-option v-for="item in conflictOptions" :key="item" :label="item" :value="item">
              </el-option>
            </el-select>
          </template>
        </el-table-column>

        <el-table-column align="center" label="备注" width="200px">
          <template scope="scope">
            <el-input type="textarea" :autosize="{minRows: 2, maxRows: 8}" v-model="scope.row.conflict_memo"></el-input>
          </template>
        </el-table-column>
        <el-table-column align="center" label="客服反馈" width="200px">
          <template scope="scope">
            <el-input type="textarea" :disabled="true" :autosize="{minRows: 2, maxRows: 8}" v-model="scope.row.conflict_feedback"></el-input>
          </template>
        </el-table-column>
      </el-table>

      <span slot="footer" class="dialog-footer">
        <el-button @click="dialogConflictVisible=false">取 消</el-button>
        <el-button type="primary" @click="handleConflict">确 定</el-button>
      </span>
    </el-dialog>

  </div>
</template>

<style>
  .el-table .tiangou-row {
    background: #e2f0e4;
  }
</style>

<script>
  import { fetchPurchase, fetchOrder, fetchSupplier, orderPurchase, orderMarkConflict } from 'api/orders';

  export default {
    props: {
      inventory: {
        type: Number
      }
    },
    data() {
      return {
        postData: {
          data: [],
          inventory: this.inventory,
          queryTime: undefined
        },
        listLoading: true,
        queryTime: undefined,
        total: null,
        dialogConflictVisible: false,
        supplierOptions: [],
        listQuery: {
          page: 1,
          limit: 10,
          inventory: this.inventory
        },
        orderQuery: {
          inventory: '',
          jancode: '',
          status: ''
        },
        orderData: [],
        conflictMarkedJancode: '',
        conflictOptions: ['更换', '退款']
      }
    },
    created() {
      this.getSupplier();
      this.getPurchase();
    },
    methods: {
      getPurchase() {
        // this.$emit('create'); // for test
        this.listLoading = true;
        this.postData.data = [];
        fetchPurchase(this.listQuery).then(response => {
          for (const v of response.data.data) {
            v.quantity = v.qty;
            v.supplier = '';
            this.postData.data.push(v);
          }
          this.total = response.data.total;
          this.queryTime = response.data.queryTime;
          this.listLoading = false;
        })
      },
      getSupplier() {
        const query = { limit: 50 }
        fetchSupplier(query).then(response => {
          this.supplierOptions = response.data.results;
        })
      },
      getOrder(row) {
        this.orderQuery.jancode = row.jancode;
        this.orderQuery.inventory = this.inventory;
        this.dialogConflictVisible = true;
        this.orderQuery.status = '待采购';
        fetchOrder(this.orderQuery).then(response => {
          this.orderData = response.data.results;
        })
      },
      tableRowClassName(row, index) {
        if (row.isTiangou === '是') {
          return 'tiangou-row';
        }
        return '';
      },
      handlePurchase() {
        this.postData.queryTime = this.queryTime;
        orderPurchase(this.postData).then(response => {
          this.getPurchase();
        })
      },
      handleConflict() {
        orderMarkConflict(this.orderData).then(response => {
          this.dialogConflictVisible = false;
          for (const v of this.postData.data) {
            if (v.jancode === this.orderQuery.jancode) {
              const index = this.postData.data.indexOf(v);
              this.postData.data.splice(index, 1);
            }
          }
        })
      }
    }
  }
</script>
