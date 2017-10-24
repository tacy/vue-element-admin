<template>
  <div class="app-container">
    <el-tabs v-model="activeName" type="border-card">
      <el-tab-pane v-for="item in tabMapOptions" :label="item.name" :key='item.id' :name="item.id">
        <keep-alive>
          <tab-pane v-if='activeName==item.id' :inventory='item.id'></tab-pane>
        </keep-alive>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script>
  import tabPane from './components/purchasePane';
  import { fetchInventory } from 'api/orders';

  export default {
    name: 'tabDemo',
    components: { tabPane },
    data() {
      return {
        tabMapOptions: [],
        activeName: 4
      }
    },
    created() {
      this.getInventory();
    },
    methods: {
      getInventory() {
        fetchInventory().then(response => {
          this.tabMapOptions = response.data.results;
        })
      }
    }
  }
</script>
