<template>
  <div class="app-container calendar-list-container">
    <div class="filter-container">
      <el-select v-model="listQuery.labelVal" style="width: 120px;" class="filter-item" placeholder="请选择">
        <el-option
            v-for="item in selectedOptions"
            :label="item.label"
            :value="item.value">
        </el-option>
      </el-select>
      <el-input @keyup.enter.native="handleFilter" style="width: 150px;" class="filter-item" placeholder="输入订单号" v-model="listQuery.orderid" v-show="listQuery.labelVal == '1'">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 150px;" class="filter-item" placeholder="输入商品名称" v-model="listQuery.product_title" v-show="listQuery.labelVal == '2'">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 150px;" class="filter-item"  placeholder="输入商品条码" v-model="listQuery.jancode" v-show="listQuery.labelVal == '3'">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 150px;" class="filter-item"  placeholder="输入收件人" v-model="listQuery.receiver_name" v-show="listQuery.labelVal == '4'">
      </el-input>
      <el-input @keyup.enter.native="handleFilter" style="width: 150px;" class="filter-item"  placeholder="输入采购单" v-model="listQuery.purchaseorder__orderid" v-show="listQuery.labelVal == '5'">
      </el-input>

      <el-input @keyup.enter.native="handleFilter" style="width: 150px;" class="filter-item" placeholder="商品规格" v-model="listQuery.sku_properties_name">
      </el-input>
      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.status" placeholder="订单状态">
        <el-option v-for="item in statusOptions" :key="item" :label="item" :value="item">
        </el-option>
      </el-select>
      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.delivery_type" placeholder="运输方式">
        <el-option v-for="item in deliveryTypeOptions" :key="item" :label="item" :value="item">
        </el-option>
      </el-select>
      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.inventory" placeholder="仓库">
        <el-option v-for="item in inventoryOptions" :key="item.id" :label="item.name" :value="item.id">
        </el-option>
      </el-select>

      <el-select clearable style="width: 120px" class="filter-item" v-model="listQuery.channel_name" placeholder="渠道">
        <el-option v-for="item in channelOptions" :key="item" :label="item" :value="item">
        </el-option>
      </el-select>

      <el-button class="filter-item" type="primary" v-waves icon="search" @click="handleFilter">搜索</el-button>
      <el-button class="filter-item" type="success" style="float:right" v-waves icon="edit" @click="handleCreate">录入订单</el-button>
    </div>

    <el-table :data="list" v-loading.body="listLoading" @selection-change="handleSelect" border fit highlight-current-row style="width: 100%">
      <el-table-column type="expand" width="50px">
        <template scope="scope">
          <el-form label-position="left" inline class="table-expand">
            <!--el-form-item label="商品:" label-width="50px">
              <span>{{ scope.row.product_title }}</span>
            </el-form-item>
            <el-form-item label="数量:" label-width="50px">
              <span>{{ scope.row.quantity }}</span>
            </el-form-item>
            <el-form-item label="规格:" label-width="50px">
              <span>{{ scope.row.sku_properties_name }}</span>
            </el-form-item-->
            <el-form-item label="收件人:" label-width="80px">
              <span>{{ scope.row.receiver_name }}</span>
            </el-form-item>
            <el-form-item label="地址:" label-width="80px">
              <span>{{ scope.row.receiver_address }}</span>
            </el-form-item>
            <el-form-item label="身份证:" label-width="80px">
              <span>{{ scope.row.receiver_idcard }}</span>
            </el-form-item>
            <el-form-item label="支付时间:" label-width="80px">
              <span>{{ scope.row.piad_time }}</span>
            </el-form-item>
            <el-form-item label="单价:" label-width="50px">
              <span>{{ scope.row.price }}</span>
            </el-form-item>
            <el-form-item label="总价:" label-width="50px">
              <span>{{ scope.row.payment }}</span>
            </el-form-item>
            <el-form-item label="面单:" label-width="50px">
              <span>{{ scope.row.db_number }}</span>
            </el-form-item>
            <el-form-item label="出库时间:" label-width="80px">
              <span>{{ scope.row.shippingdb_delivery_time }}</span>
            </el-form-item>
            <el-form-item label="注文编号:" label-width="80px">
              <span>{{ scope.row.purchaseorder_orderid }}</span>
            </el-form-item>
            <el-form-item label="仓库:" label-width="50px">
              <span>{{ scope.row.inventory_name }}</span>
            </el-form-item>
            <el-form-item label="发货方式:" label-width="80px">
              <span>{{ scope.row.shipping_name }}</span>
            </el-form-item>
            <el-form-item label="证件:" label-width="50px">
              <span>{{ scope.row.receiver_idcard }}</span>
            </el-form-item>
            <el-form-item label="介入:" label-width="50px">
              <span>{{ scope.row.conflict_memo }}</span>
            </el-form-item>
            <el-form-item label="反馈:" label-width="50px">
              <span>{{ scope.row.conflict_feedback }}</span>
            </el-form-item>
            <el-form-item label="渠道发货:" label-width="80px">
              <span>{{ scope.row.channel_delivery_status }}</span>
            </el-form-item>
            <el-form-item label="国内运单:" label-width="80px">
              <span>{{ scope.row.domestic_delivery_no }}</span>
            </el-form-item>
            <el-form-item label="国内物流:" label-width="80px">
              <span>{{ scope.row.domestic_delivery_company }}</span>
            </el-form-item>
          </el-form>
        </template>
      </el-table-column>
      <el-table-column align="center" label="订单号" width="100px">
        <template scope="scope">
          <span>{{scope.row.orderid}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="渠道" width="80px">
        <template scope="scope">
          <span>{{scope.row.channel_name}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="状态" width="100px">
        <template scope="scope">
          <!--span>{{scope.row.status}}</span-->
          <el-tag :type="scope.row.status | statusFilter">{{scope.row.status}}</el-tag>
        </template>
      </el-table-column>
      <!--el-table-column align="center" label="仓库" width="70px">
        <template scope="scope">
          <span>{{scope.row.inventory_name}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="发货方式" width="95px">
        <template scope="scope">
          <span>{{scope.row.shipping_name}}</span>
        </template>
      </el-table-column-->
      <el-table-column align="center" label="收件人" width="95px">
        <template scope="scope">
          <span>{{scope.row.receiver_name}}</span>
        </template>
      </el-table-column>
      <!--el-table-column align="center" label="电话" width="115px" show-overflow-tooltip>
        <template scope="scope">
          <span>{{scope.row.receiver_mobile}}</span>
        </template>
      </el-table-column-->
      <el-table-column align="center" label="运输" show-overflow-tooltip>
        <template scope="scope">
          <span>{{scope.row.delivery_type}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="条码" width="140px" show-overflow-tooltip>
        <template scope="scope">
          <span>{{scope.row.jancode}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="商品名" width="250px">
        <template scope="scope">
          <span>{{scope.row.product_title}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="规格" show-overflow-tooltip width="150px">
        <template scope="scope">
          <span>{{scope.row.sku_properties_name}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="数量" width="65">
        <template scope="scope">
          <span>{{scope.row.quantity}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="操作" width="150">
        <template scope="scope">
          <el-button size="small" :disabled="scope.row.status === '已删除'?true:false" type="primary" @click="handleMark(scope.row)">标 记
          </el-button>
          <el-button size="small" :disabled="scope.row.status === '已删除'?true:false" type="danger" @click="handleDelete(scope.row)">删 除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-show="!listLoading" class="pagination-container">
      <el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange" :current-page.sync="listQuery.page"
        :page-sizes="[10,20,30, 50]" :page-size="listQuery.limit" layout="total, sizes, prev, pager, next, jumper" :total="total">
      </el-pagination>
    </div>

    <el-dialog title="录入订单" size="large" :visible.sync="dialogCreateVisible">
      <el-form :rules="rules" ref="form" class="small-space" :model="orderData" label-position="left" label-width="80px">
        <el-row>
          <el-col :span="6">
            <el-form-item label="订单号:" prop="orderid">
              <el-input style="width: 150px" v-model.trim="orderData.orderid"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="卖家:" prop="seller_name">
              <el-select clearable style="width: 150px" class="filter-item" v-model.trim="orderData.seller_name" placeholder="渠道">
              <el-option v-for="item in sellerOptions" :key="item" :label="item" :value="item">
              </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="渠道:" prop="channel_name">
              <el-select clearable style="width: 150px" class="filter-item" v-model.trim="orderData.channel_name" placeholder="渠道">
                <el-option v-for="item in channelOptions" :key="item" :label="item" :value="item">
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="运输:" prop="delivery_type">
              <el-select clearable style="width: 150px" class="filter-item" v-model.trim="orderData.delivery_type" placeholder="运输方式">
                <el-option v-for="item in deliveryTypeOptions" :key="item" :label="item" :value="item">
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="6">
            <el-form-item label="姓名:" prop="receiver_name">
              <el-input style="width: 150px" v-model.trim="orderData.receiver_name"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="电话:" prop="receiver_mobile">
              <el-input style="width: 150px" v-model.trim="orderData.receiver_mobile"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="邮编:" prop="receiver_zip">
              <el-input style="width: 150px" v-model.trim="orderData.receiver_zip"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="证件:" prop="receiver_idcard">
              <el-input style="width: 150px" v-model.trim="orderData.receiver_idcard"></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="12">
            <el-form-item label="地址:" prop="receiver_address">
              <el-input style="width: 430px" v-model.trim="orderData.receiver_address"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="备注:" prop="seller_memo">
              <el-input style="width: 430px" v-model.trim="orderData.seller_memo"></el-input>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row v-for="(p, index) in orderData.products">
          <el-col :span="4">
            <el-form-item label="条码:" label-width="55px" prop="jancode" required="true">
              <el-input style="width: 120px" v-model.trim="p.jancode"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="名称:" label-width="55px" prop="product_title" required="true">
              <el-input style="width: 275px" v-model.trim="p.product_title"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label="规格:" label-width="55px" prop="sku_properties_name" required="true">
              <el-input style="width: 120px" v-model.trim="p.sku_properties_name"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="3">
            <el-form-item label="数量:" label-width="55px" prop="quantity" required="true">
              <el-input style="width: 80px" v-model.number="p.quantity" type="number"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="5">
            <el-form-item label="价格:" label-width="55px" required="true">
              <el-input style="width: 82px" v-model.number="p.price" type="number"></el-input>
              <el-button type="danger" icon="delete" @click="deleteProduct(p)"></el-button>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item align="center" >
          <el-button type="success" @click="addProduct">新增商品</el-button>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogCreateVisible=false">取消</el-button>
        <el-button type="primary" @click="createTPROrder">提交</el-button>
      </div>
    </el-dialog>

    <el-dialog title="删除订单" :visible.sync="dialogFormVisible">
      <el-form class="small-space" :model="temp" label-position="left" label-width="70px" style='width: 400px; margin-left:50px;'>
        <el-form-item label="原因">
          <el-input type="textarea" :autosize="{minRows: 2, maxRows: 4}" v-model="temp.conflict_feedback"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogFormVisible=false">取 消</el-button>
        <el-button type="primary" @click="deleteOrder()">确 定</el-button>
      </div>
    </el-dialog>
     <el-dialog title="标记订单" :visible.sync="dialogMarkVisible">
      <el-form class="small-space" :model="temp" label-position="left" label-width="70px" style='width: 400px; margin-left:50px;'>
        <el-form-item label="卖家备注">
          <el-input type="textarea" :autosize="{minRows: 2, maxRows: 4}" v-model="temp.seller_memo"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogMarkVisible=false">取 消</el-button>
        <el-button type="primary" @click="markOrder()">确 定</el-button>
      </div>
    </el-dialog>

  </div>
</template>

<style>
  .table-expand {
    font-size: 0;
  }
  .table-expand label {
    width: 90px;
    color: #99a9bf;
  }
  .table-expand .el-form-item {
    margin-right: 0;
    margin-bottom: 0;
    width: 50%;
  }
</style>

<script>
  import { parseTime } from 'utils';
  import { fetchInventory, fetchSupplier, fetchOrder, orderDelete, updateOrder, orderTPRCreate } from 'api/orders';

  export default {
    data() {
      return {
        list: [],
        listLoading: true,
        total: null,
        dialogFormVisible: false,
        dialogCreateVisible: false,
        dialogMarkVisible: false,
        inventoryOptions: [],
        statusOptions: ['待处理', '需面单', '待采购', '待发货', '已采购', '需介入', '已发货', '已删除'],
        channelOptions: ['洋码头', '京东', 'AMZN', 'YHOO', 'TOKYOWH'],
        sellerOptions: ['东京彩虹桥', '妈妈宝宝日本馆', '天狗'],
        deliveryTypeOptions: ['直邮', '官方（贝海）直邮', '第三方保税', '官方（贝海）保税', '拼邮'],
        selectedOptions: [{
          value: '1',
          label: '订单号'
        }, {
          value: '2',
          label: '商品名称'
        }, {
          value: '3',
          label: '商品条码'
        }, {
          value: '4',
          label: '收件人'
        }, {
          value: '5',
          label: '采购单'
        }],
        listQuery: {
          page: 1,
          limit: 10,
          labelVal: '1',
          inventory: undefined,
          channel_name: undefined,
          receiver_name: undefined,
          jancode: undefined,
          orderid: undefined,
          status: undefined,
          product_title: undefined,
          purchaseorder__orderid: undefined,
          sku_properties_name: undefined,
          delivery_type: undefined
        },
        orderData: {
          orderid: undefined,
          seller_name: undefined,
          channel_name: undefined,
          delivery_type: undefined,
          receiver_name: undefined,
          receiver_address: undefined,
          receiver_zip: undefined,
          receiver_mobile: undefined,
          receiver_idcard: undefined,
          seller_memo: undefined,
          products: [
            {
              jancode: undefined,
              quantity: undefined,
              price: undefined,
              product_title: undefined,
              sku_properties_name: undefined
            }
          ]
        },
        temp: {
          id: undefined,
          status: undefined,
          seller_memo: undefined,
          conflict_feedback: undefined
        },
        rules: {
          orderid: [
            { required: true, message: '请输入订单号', trigger: 'blur' }
          ],
          seller_name: [
              { required: true, message: '请选择卖家', trigger: 'blur' }
          ],
          channel_name: [
              { required: true, message: '请选择渠道', trigger: 'blur' }
          ],
          delivery_type: [
              { required: true, message: '请选择运输方式', trigger: 'blur' }
          ],
          receiver_name: [
              { required: true, message: '请输入买家姓名', trigger: 'blur' }
          ],
          receiver_mobile: [
              { required: true, message: '请输入买家电话', trigger: 'blur' }
          ],
          receiver_zip: [
              { required: true, message: '请输入买家邮编', trigger: 'blur' }
          ],
          receiver_address: [
              { required: true, message: '请输入买家地址', trigger: 'blur' }
          ]
        }
      };
    },
    filters: {
      statusFilter(status) {
        const statusMap = {
          待发货: 'success',
          需面单: 'primary',
          已采购: 'primary',
          待处理: 'primary',
          已删除: 'danger',
          需介入: 'danger',
          待采购: 'warning'
        };
        return statusMap[status]
      }
    },
    created() {
      this.getInventory();
      this.getOrder();
    },
    methods: {
      getOrder() {
        this.listLoading = true;
        if (this.listQuery.labelVal !== '1') {
          this.listQuery.orderid = undefined
        }
        if (this.listQuery.labelVal !== '2') {
          this.listQuery.product_title = undefined
        }
        if (this.listQuery.labelVal !== '3') {
          this.listQuery.jancode = undefined
        }
        if (this.listQuery.labelVal !== '4') {
          this.listQuery.receiver_name = undefined
        }
        if (this.listQuery.labelVal !== '5') {
          this.listQuery.purchaseorder__orderid = undefined
        }
        fetchOrder(this.listQuery).then(response => {
          this.list = response.data.results;
          this.total = response.data.count;
          this.listLoading = false;
        })
      },
      getInventory() {
        fetchInventory().then(response => {
          this.inventoryOptions = response.data.results;
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
      // 不能删除订单, 如果订单已经分配了DB单号
      // checkShippingdb(row) {
      //   if ( row.shippingdb !== null ) {
      //          return true
      //        };
      //        if (row.status === '已删除' ) {
      //          return true
      //        };
      // },
      deleteProduct(item) {
        const index = this.orderData.products.indexOf(item)
        if (index !== -1) {
          this.orderData.products.splice(index, 1)
        }
      },
      addProduct() {
        this.orderData.products.push({
          jancode: undefined,
          quantity: undefined,
          price: undefined,
          product_title: undefined,
          sku_properties_name: undefined
        });
      },
      handleDelete(row) {
        if (row.shippingdb !== null && !['拼邮', '轨迹'].includes(row.shipping_name)) {
          this.$notify({
            title: '警告',
            message: '订单已经出面单, 需先在系统删除对应面单',
            type: 'error',
            duration: 2000
          });
          return
        }
        this.temp = Object.assign({}, row);
        this.dialogFormVisible = true;
      },
      handleCreate() {
        this.orderData = {
          orderid: undefined,
          seller_name: undefined,
          channel_name: undefined,
          delivery_type: undefined,
          receiver_name: undefined,
          receiver_address: undefined,
          receiver_zip: undefined,
          receiver_mobile: undefined,
          receiver_idcard: undefined,
          seller_memo: undefined,
          products: [
            {
              jancode: undefined,
              quantity: undefined,
              price: undefined,
              product_title: undefined,
              sku_properties_name: undefined
            }
          ]
        },
        this.dialogCreateVisible = true
      },
      handleMark(row) {
        this.temp = Object.assign({}, row);
        this.dialogMarkVisible = true;
      },
      markOrder() {
        updateOrder(this.temp, '/order/' + this.temp.id + '/').then(response => {
          for (const v of this.list) {
            if (v.id === this.temp.id) {
              const index = this.list.indexOf(v);
              this.list.splice(index, 1, this.temp);
              break;
            }
          }
          this.$notify({
            title: '成功',
            message: '订单标记成功',
            type: 'success',
            duration: 2000
          });
          this.dialogMarkVisible = false
        })
      },
      createTPROrder() {
        this.$refs.form.validate(valid => {
          if (!valid) {
            return false;
          } else {
            orderTPRCreate(this.orderData).then(response => {
              this.$notify({
                title: '成功',
                message: '订单创建成功',
                type: 'success',
                duration: 2000
              });
              this.dialogCreateVisible = false
            });
          }
        });
      },
      deleteOrder() {
        orderDelete(this.temp).then(response => {
          this.temp.status = '已删除';
          for (const v of this.list) {
            if (v.id === this.temp.id) {
              const index = this.list.indexOf(v);
              this.list.splice(index, 1, this.temp);
              break;
            }
          }
          this.$notify({
            title: '成功',
            message: '订单删除成功',
            type: 'success',
            duration: 2000
          });
          this.dialogFormVisible = false
        })
      }
    }
  }
</script>
