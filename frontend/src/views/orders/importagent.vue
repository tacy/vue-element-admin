<template>
  <div class="app-container calendar-list-container">
    <el-upload action="" :http-request="uploadOrder" :file-list="fileList">
      <el-button size="small" type="primary">导入EXCEL</el-button>
      <div slot="tip" class="el-upload__tip">导入订单, 订单文件采用Excel</div>
    </el-upload>
  </div>
</template>

<script>
 import { importAgentOrder } from 'api/orders';

 export default {
   data() {
     return {
       fileList: undefined
     }
   },
   methods: {
     uploadOrder(param) {
       const formData = new FormData()
       formData.append('file', param.file)
       importAgentOrder(formData).then(() => {
         this.$notify({
           title: '成功',
           message: '订单导入成功',
           type: 'success',
           duration: 2000
         })
       })
     }
   }
 }
</script>
