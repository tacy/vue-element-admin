<template>
  <div class="createPost-container">
    <el-form class="form-container" :model="postForm" :rules="rules" ref="postForm">

      <Sticky class="sub-navbar">
        <template v-if="fetchSuccess">
          <el-button v-loading="loading" style="margin-right: 10px;" type="success" @click="submitForm()">提交采购
          </el-button>
        </template>
        <template v-else>
          <el-tag>发送异常错误,刷新页面,或者联系程序员</el-tag>
        </template>
      </Sticky>

      <div class="createPost-main-container">
	<div class="postInfo-container">
	  <el-row>
	    <el-col :span="6">
	      <el-form-item label-width="50px" label="仓库" class="postInfo-container-item">
		<el-select clearable style="width: 120px" class="filter-item" v-model="postForm.inventory" v-on:change="getInventory()" placeholder="仓库">
		  <el-option v-for="item in inventoryOptions" :key="item.id" :label="item.name" :value="item.id">
		  </el-option>
		</el-select>
	      </el-form-item>
	    </el-col>
	    <el-col :span="6">
	      <el-form-item label-width="60px" label="供应商" class="postInfo-container-item">
		<el-select clearable style="width: 120px" class="filter-item" v-model="postForm.supplier" v-on:change="getSupplier()" placeholder="供应商">
		  <el-option v-for="item in supplierOptions" :key="item.id" :label="item.name" :value="item.id">
		  </el-option>
		</el-select>
	      </el-form-item>
	    </el-col>
	    <el-col :span="8">
	      <el-form-item label-width="80px" label="注文编号" class="postInfo-container-item">
		<el-input placeholder="请输入" style='min-width:150px;' v-model.trim="postForm.orderid">
		</el-input>
	      </el-form-item>
	    </el-col>
	    <el-col :span="4">
		<el-button class="filter-item" style="margin-left: 60px;" @click="handleAddItem" type="primary" icon="edit">添加商品</el-button>
	    </el-col>
	  </el-row>
	</div>

	<el-table :data="postForm.items" border fit highlight-current-row style="width: 100%">
	  <el-table-column align="center" label="商品编号">
	    <template scope="scope">
	      <el-input size="small" v-model.trim="scope.row.jancode"></el-input>
	    </template>
	  </el-table-column>
	  <el-table-column align="center" label="采购数量">
	    <template scope="scope">
	      <el-input size="small" v-model.number="scope.row.quantity" type="number"></el-input>
	    </template>
	  </el-table-column>
	  <el-table-column align="center" label="价格">
	    <template scope="scope">
	      <el-input size="small" v-model.number="scope.row.price" type="number"></el-input>
	    </template>
          </el-table-column>
  	  <el-table-column align="center" label="操作">
	    <template scope="scope">
              <el-button size="small" type="danger" @click="handleDeleteItem(scope.$index)">删除</el-button>
	    </template>
	  </el-table-column>
	</el-table>
      </div>

    </el-form>
  </div>
</template>

<script>
  import { fetchInventory, fetchSupplier } from 'api/orders';
  import { noOrderPurchase } from 'api/purchases';

  export default {
    name: 'articleDetail',
    data() {
      const validateRequire = (rule, value, callback) => {
        if (value === '') {
          this.$message({
            message: rule.field + '为必传项',
            type: 'error'
          });
          callback(null)
        } else {
          callback()
        }
      };
      return {
        postForm: {
          inventory: undefined,
          supplier: undefined,
          orderid: '',
          items: [
            {
              jancode: undefined,
              quantity: undefined,
              price: undefined
            }
          ]
        },
        fetchSuccess: true,
        loading: false,
        inventoryOptions: [],
        supplierOptions: [],
        rules: {
          title: [{ validator: validateRequire }]
        }
      }
    },
    created() {
      this.getData()
    },
    methods: {
      getData() {
        fetchInventory().then(response => {
          this.inventoryOptions = response.data.results;
        }).catch(err => {
          this.fetchSuccess = false;
          console.log(err);
        });
        fetchSupplier().then(response => {
          this.supplierOptions = response.data.results;
        }).catch(err => {
          this.fetchSuccess = false;
          console.log(err);
        });
      },
      handleAddItem() {
        this.postForm.items.push(
          {
            jancode: undefined,
            quantity: undefined,
            price: undefined
          }
	)
      },
      handleDeleteItem(index) {
        this.postForm.items.splice(index, 1)
      },
      submitForm() {
        console.log(this.postForm)
        this.$refs.postForm.validate(valid => {
          if (valid) {
            this.loading = true;
          } else {
            console.log('error submit!!');
            return false;
          }
        });
        noOrderPurchase(this.postForm).then(response => {
          this.$notify({
            title: '成功',
            message: '采购单创建成功',
            type: 'success',
            duration: 2000
          });
        });
        this.loading = false;
      }
    }
  }
</script>
<style rel="stylesheet/scss" lang="scss" scoped>
  @import "src/styles/mixin.scss";
  .createPost-container {
    position: relative;
    .createPost-main-container {
      padding: 40px 45px 20px 50px;
      .postInfo-container {
        position: relative;
        @include clearfix;
        margin-bottom: 10px;
        .postInfo-container-item {
          float: left;
        }
      }
    }
  }
</style>
