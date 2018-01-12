<template>
  <div class="app-container calendar-list-container">
    <el-row>
      <el-col :span="4">
        <el-card class="box-card">
          <div slot="header" class="box-card-header">
            <span class="display_name">订单</span>
          </div>
          <div class="info-item" v-for="item in orderinfo">
	    <span>{{item.key}}:</span>
	    <router-link :to="{path:item.path}" target="_blank"><el-button size="mini" type="info">{{item.value}}</el-button></router-link>
          </div>
        </el-card>
      </el-col>

      <el-col :span="4" :offset="1">
        <el-card class="box-card">
          <div slot="header" class="box-card-header">
            <span class="display_name">采购单</span>
          </div>
          <div class="info-item" v-for="item in poinfo">
	    <span>{{item.key}}:</span>
	    <router-link :to="{path:item.path}" target="_blank"><el-button size="mini" type="info">{{item.value}}</el-button></router-link>
          </div>
        </el-card>
      </el-col>

      <el-col :span="10">
        <bar-chart></bar-chart>
      </el-col>
  </el-row>
  </div>
</template>

<script>
 import { fetchOrderAlert } from 'api/orders';
 import { fetchPurchaseOrderAlert } from 'api/purchases';
 export default {
   data() {
     return {
       orderinfo: [],
       poinfo: []
     }
   },
   created() {
     this.getOrder();
     this.getPO()
   },
   methods: {
     getOrder() {
       this.listLoading = true;
       fetchOrderAlert().then(response => {
         this.orderinfo = response.data.results;
         this.listLoading = false;
       })
     },
     getPO() {
       fetchPurchaseOrderAlert().then(response => {
         this.poinfo = response.data.results;
       })
     }
   }
 }

</script>
