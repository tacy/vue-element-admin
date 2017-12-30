<template>
  <div class="app-container calendar-list-container">
    <div class="filter-container">
      <el-input @keyup.enter.native="handleFilter" style="width: 120px;" class="filter-item"  placeholder="运单号" v-model="listQuery.db_number">
      </el-input>

      <el-select clearable style="width: 90px" class="filter-item" v-model="listQuery.status" placeholder="状态">
        <el-option v-for="item in statusOptions" :key="item" :label="item" :value="item">
        </el-option>
      </el-select>

      <el-button class="filter-item" type="primary" v-waves icon="search" @click="handleFilter">搜索</el-button>
   </div>

    <el-table :data="list" v-loading.body="listLoading" border fit highlight-current-row style="width: 100%">
      <el-table-column align="center" label="DB单号" width="150px">
        <template scope="scope">
          <span>{{scope.row.db_number}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="状态" >
        <template scope="scope">
          <span>{{scope.row.status}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="打印" >
        <template scope="scope">
          <span>{{scope.row.print_status}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="创建时间">
        <template scope="scope">
          <span>{{scope.row.create_time}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="出库时间">
        <template scope="scope">
          <span>{{scope.row.delivery_time}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="备注">
        <template scope="scope">
          <span>{{scope.row.memo}}</span>
        </template>
      </el-table-column>
      <el-table-column align="center" label="操作" width="240">
        <template scope="scope">
          <el-button size="small" type="success" :disabled="disableSubmit2" @click="handleDBPrint(scope.row)">打印
          </el-button>
          <el-button size="small" :disabled="scope.row.status==='待处理'?false:true" type="success" @click="handleTransformOut(scope.row)">出库
          </el-button>
          <el-button size="small" :disabled="scope.row.status==='待处理'?false:true" type="danger" @click="handleDelete(scope.row)">删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog title="出库" :visible.sync="dialogTransformOutVisible">
      <el-form class="small-space" :model="transformOutData" label-position="left" label-width="70px" style='width: 500px; margin-left:50px;'>
        <el-form-item label="备注:">
          <el-input type="textarea" :autosize="{minRows: 4, maxRows: 12}" v-model.trim="transformOutData.memo"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogTransformOutVisible=false">取 消</el-button>
        <el-button type="primary" :disabled="disableSubmit" @click="transformOut">提 交</el-button>
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
 import { fetchPDF, fetchEMSPDF } from 'api/orders';
 import { fetchTransformDB, updateTransformDB } from 'api/purchases';
 export default {
   data() {
     return {
       list: [],
       itemData: [],
       listLoading: true,
       total: null,
       dialogItemVisible: false,
       dialogTransformOutVisible: false,
       disableSubmit: false,
       disableSubmit2: false,
       statusOptions: ['待处理', '已出库', '已删除'],
       listQuery: {
         page: 1,
         limit: 50,
         status: '待处理',
         db_number: undefined
       },
       xloboData: {
         BillCodes: [],
         db_type: 'transform'
       },
       transformOutData: {
         id: undefined,
         memo: undefined,
         delivery_time: undefined,
	 status: undefined
       }
     }
   },
   filters: {
     fmDate(value) {
       if (!value) return ''
       value = value.substr(2, 8) + ' ' + value.substr(11, 5)
       return value
     }
   },
   created() {
     this.getList();
   },
   methods: {
     getList() {
       this.listLoading = true;
       fetchTransformDB(this.listQuery).then(response => {
         this.list = response.data.results;
         this.total = response.data.count;
         this.listLoading = false;
       })
     },
     handleFilter() {
       this.listQuery.page = 1;
       this.getList();
     },
     handleSizeChange(val) {
       this.listQuery.limit = val;
       this.getList();
     },
     handleCurrentChange(val) {
       this.listQuery.page = val;
       this.getList();
     },
     handleTransformOut(row) {
       this.transformOutData = row
       this.dialogTransformOutVisible = true
     },
     transformOut() {
       const today = new Date()
       const date = today.getFullYear() + '-' + (today.getMonth() + 1) + '-' + today.getDate()
       const time = today.getHours() + ':' + today.getMinutes() + ':' + today.getSeconds()
       this.transformOutData.delivery_time = date + ' ' + time
       this.transformOutData.status = '已出库'
       updateTransformDB(this.transformOutData, '/transformdb/' + this.transformOutData.id + '/').then(() => {
         for (const v of this.list) {
           if (v.id === this.transformOutData.id) {
             const index = this.list.indexOf(v)
             this.list[index].delivery_time = this.transformOutData.delivery_time
             this.list[index].memo = this.transformOutData.memo
             this.list[index].status = this.transformOutData.status
             break
           }
         }
         this.$notify({
           title: '成功',
           message: '更新成功',
           type: 'success',
           duration: 2000
         });
         this.dialogTransformOutVisible = false
       })
     },
     handleDelete(row) {
       return
     },
     handleDBPrint(row) {
       this.xloboData.BillCodes = [row.db_number]

       const b64toBlob = (b64Data, contentType = '', sliceSize = 512) => {
         const byteCharacters = atob(b64Data);
         const byteArrays = [];
         for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
           const slice = byteCharacters.slice(offset, offset + sliceSize);
           const byteNumbers = new Array(slice.length);
           for (let i = 0; i < slice.length; i++) {
             byteNumbers[i] = slice.charCodeAt(i);
           }
           const byteArray = new Uint8Array(byteNumbers);
           byteArrays.push(byteArray);
         }
         const blob = new Blob(byteArrays, { type: contentType });
         return blob;
       };

       this.disableSubmit2 = true
       if (!row.db_number.toLowerCase().includes('db')) {
         fetchEMSPDF(this.xloboData).then(response => {
           const blob = b64toBlob(response.data.Result[0].BillPdfLabel, 'application/pdf');
           const link = document.createElement('a')
           link.href = window.URL.createObjectURL(blob)
           link.target = '_blank';
           window.open(link);
           for (const o of this.list) {
             if (o.id === row.id) {
               const index = this.list.indexOf(o);
               this.list[index].print_status = '已打印';
               this.disableSubmit2 = false;
               break;
             }
           }
         }).catch(() => {
           this.disableSubmit2 = false;
         })
       } else {
         fetchPDF(this.xloboData).then(response => {
           const blob = b64toBlob(response.data.Result[0].BillPdfLabel, 'application/pdf');

           const link = document.createElement('a')
           link.href = window.URL.createObjectURL(blob)
           link.target = '_blank';
           window.open(link);
           for (const o of this.list) {
             if (o.id === row.id) {
               const index = this.list.indexOf(o);
               this.list[index].print_status = '已打印';
               this.disableSubmit2 = false;
               break;
             }
           }
         }).catch(error => {
           this.disableSubmit2 = false;
           for (const i of error.response.data.idmis) {
             for (const o of this.list) {
               if (i === o.db_number) {
                 const index = this.list.indexOf(o);
                 this.list[index].print_status = '身份证异常';
                 break;
               }
             }
           }
         })
       }
     }
   }
 }
</script>
