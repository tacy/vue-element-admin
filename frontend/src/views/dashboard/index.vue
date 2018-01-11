<template>
  <div class="app-container calendar-list-container">
    <el-row>
      <el-col :span="6">
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

      <el-col :span="8">
        <pie-chart></pie-chart>
      </el-col>

      <el-col :span="10">
        <bar-chart></bar-chart>
      </el-col>
  </el-row>
  </div>
</template>

<script>
  import { fetchOrderAlert } from 'api/orders';
  export default {
    data() {
      return {
        orderinfo: []
      }
    },
    created() {
      this.getOrder();
    },
    methods: {
      getOrder() {
        this.listLoading = true;
        fetchOrderAlert().then(response => {
          this.orderinfo = response.data.results;
          this.listLoading = false;
        })
      }
    }
  }

</script>
