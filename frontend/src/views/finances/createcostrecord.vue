<template>
  <div class="createPost-container">
    <el-form class="form-container" :model="postForm" :rules="rules" ref="postForm">

      <Sticky class="sub-navbar">
        <template v-if="fetchSuccess">
          <el-button v-loading="loading" style="margin-right: 10px;" type="success" @click="submitForm()">提交
          </el-button>
        </template>
        <template v-else>
          <el-tag>发送异常错误,刷新页面,或者联系程序员</el-tag>
        </template>
      </Sticky>

      <div class="createPost-main-container">
        <div class="postInfo-container">
          <el-row>
            <el-col :span="10">
              <el-form-item label-width="50px" label="仓库" class="postInfo-container-item">
                <el-select clearable style="width: 120px" class="filter-item" v-model="postForm.inventory" v-on:change="getCostType()" placeholder="仓库">
                  <el-option v-for="item in inventoryOptions" :key="item.id" :label="item.name" :value="item.id">
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="10">
              <el-form-item label-width="60px" label="日期" class="postInfo-container-item">
		<el-date-picker v-model="pay_time" type="datetime" placeholder="选择日期" :picker-options="pickerOptions0">
		</el-date-picker>
              </el-form-item>
            </el-col>
            <el-col :span="4">
                <el-button class="filter-item" style="margin-left: 60px;" @click="handleAddItem" type="primary" icon="edit">添加支出项</el-button>
            </el-col>
          </el-row>
        </div>

        <el-table :data="postForm.items" border fit highlight-current-row style="width: 100%">
          <el-table-column align="center" label="支出类型" width="160px">
            <template scope="scope">
	      <el-select clearable style="width: 130px" v-model="scope.row.costtype" placeholder="类型">
		<el-option v-for="item in costTypeOptions" :key="item.id" :label="item.name" :value="item.id">
		</el-option>
	      </el-select>
            </template>
          </el-table-column>
          <el-table-column align="center" label="金额" width="150px">
            <template scope="scope">
              <el-input size="small" v-model.number="scope.row.amount" type="number"></el-input>
            </template>
          </el-table-column>
          <el-table-column align="center" label="备注">
            <template scope="scope">
              <el-input size="small" v-model.trim="scope.row.memo"></el-input>
            </template>
          </el-table-column>
          <el-table-column align="center" label="操作" width="120px">
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
  import { createCostRecord, fetchCostType } from 'api/finances';

  export default {
    data() {
      return {
        postForm: {
          inventory: undefined,
          pay_time: undefined,
          items: [
            {
              costtype: undefined,
              amount: undefined,
              memo: undefined
            }
          ]
        },
        pay_time: undefined,
        roles: [],
        fetchSuccess: true,
        loading: false,
        inventoryOptions: [],
        costTypeOptions: [],
        queryCostType: { inventory: undefined, limit: 20, page: 1 }
      }
    },
    created() {
      this.getData()
    },
    methods: {
      getData() {
        this.roles = this.$store.state.user.roles
        if (this.roles[0] === 'supergz') {
          this.inventoryOptions = [{ name: '广州', id: 3 }]
        } else if (this.roles[0] === 'supertokyo') {
          this.inventoryOptions = [{ name: '东京', id: 4 }, { name: '天狗保税', id: 5 }]
        } else if (this.roles[0] === 'super') {
          this.inventoryOptions = [{ name: '东京', id: 4 }, { name: '广州', id: 3 }, { name: '天狗保税', id: 5 }]
        }
      },
      getCostType() {
        this.queryCostType.inventory = this.postForm.inventory
        fetchCostType(this.queryCostType).then(response => {
          this.costTypeOptions = response.data.results
        });
      },
      handleAddItem() {
        this.postForm.items.push(
          {
            costtype: undefined,
            amount: undefined,
            memo: undefined
          }
        )
      },
      transformTime(val) {
        let tdate = val;
        tdate = [
          [tdate.getFullYear(), tdate.getMonth() + 1, tdate.getDate()].join('-'),
          [tdate.getHours(), tdate.getMinutes(), tdate.getSeconds()].join(':')
        ].join(' ').replace(/(?=\b\d\b)/g, '0');
        return tdate
      },
      handleDeleteItem(index) {
        this.postForm.items.splice(index, 1)
      },
      submitForm() {
        this.postForm.pay_time = this.transformTime(this.pay_time)
        createCostRecord(this.postForm).then(() => {
          this.$notify({
            title: '成功',
            message: '提交成功',
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
