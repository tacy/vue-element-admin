import Vue from 'vue';
import Router from 'vue-router';
const _import = require('./_import_' + process.env.NODE_ENV);
// in development env not use Lazy Loading,because Lazy Loading large page will cause webpack hot update too slow.so only in production use Lazy Loading

/* layout */
import Layout from '../views/layout/Layout';

/* login */
const Login = _import('login/index');
const authRedirect = _import('login/authredirect');

/* dashboard */
const dashboard = _import('dashboard/index');

/* Introduction */
/* const Introduction = _import('introduction/index'); */

/* order */
const ordersQuery = _import('orders/query');
const ordersAllocate = _import('orders/allocate');
const ordersPurchase = _import('orders/purchase');
const ordersConflict = _import('orders/conflict');
const ordersCreateDB = _import('orders/createdb');
const ordersShipping = _import('orders/shipping');
const ordersNeedExport = _import('orders/needexport');
const ordersUexTrack = _import('orders/uextrack');
const afterSale = _import('orders/aftersale');
const importAgent = _import('orders/importagent');

/* purchase */
const purchasesorder = _import('purchases/order');
const purchasescreate = _import('purchases/create');
const purchasestransform = _import('purchases/transform');
const purchasesstockin = _import('purchases/orderstockin');
const transformdb = _import('purchases/shipping');

/* product */
const productsquery = _import('products/query');
const bondedproductsquery = _import('products/bondedquery');

/* stock */
const stocksquery = _import('stocks/query');

/* finance */
const costRecord = _import('finances/costrecord');
const createCostRecord = _import('finances/createcostrecord');
const incomeRecord = _import('finances/incomerecord');
const transformRecord = _import('finances/transformrecord');

/* analyze */
const orderAnalyze = _import('analyzes/order');
const purchaseAnalyze = _import('analyzes/purchase');

/* error page */
const Err404 = _import('error/404');
const Err401 = _import('error/401');

/* theme  */
/* const Theme = _import('theme/index'); */

/* permission */
// const Permission = _import('permission/index');

Vue.use(Router);

/**
 * icon : the icon show in the sidebar
 * hidden : if hidden:true will not show in the sidebar
 * redirect : if redirect:noredirect will not redirct in the levelbar
 * noDropdown : if noDropdown:true will not has submenu
 * meta : { role: ['admin'] }  will control the page role
 **/

export const constantRouterMap = [
  { path: '/login', component: Login, hidden: true },
  { path: '/authredirect', component: authRedirect, hidden: true },
  { path: '/404', component: Err404, hidden: true },
  { path: '/401', component: Err401, hidden: true },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard/index',
    name: '首页',
    hidden: true
    // children: [{ path: 'index', component: dashboard }]
  },
  {
    path: '/dashboard',
    component: Layout,
    redirect: '/dashboard/index',
    icon: 'xinrenzhinan',
    noDropdown: true,
    children: [{ path: 'index', component: dashboard, name: '仪表盘' }]
  }
];

export default new Router({
  // mode: 'history', //后端支持可开
  scrollBehavior: () => ({ y: 0 }),
  routes: constantRouterMap
});

export const asyncRouterMap = [
  // {
  //   path: '/permission',
  //   component: Layout,
  //   redirect: '/permission/index',
  //   name: '权限测试',
  //   icon: 'quanxian',
  //   meta: { role: ['admin'] },
  //   noDropdown: true,
  //   children: [{ path: 'index', component: Permission, name: '权限测试页', meta: { role: ['admin'] } }]
  // },
  {
    path: '/orders',
    component: Layout,
    redirect: '/orders/index',
    name: '订单',
    icon: 'zujian',
    children: [
      { path: 'query',
        component: ordersQuery,
        name: '查订单',
        meta: { role: ['supergz', 'supertokyo', 'super', 'normal', 'tokyo', 'normal-big'] }
      },
      {
        path: 'allocate',
        component: ordersAllocate,
        name: '预处理',
        meta: { role: ['supergz', 'supertokyo', 'super', 'normal-big'] }
      },
      {
        path: 'purchase',
        component: ordersPurchase,
        name: '待采购',
        meta: { role: ['supergz', 'supertokyo', 'super', 'normal-big'] }
      },
      {
        path: 'conflict',
        component: ordersConflict,
        name: '需介入',
        meta: { role: ['supergz', 'supertokyo', 'super', 'normal', 'normal-big'] }
      },
      {
        path: 'createdb',
        component: ordersCreateDB,
        name: '出面单',
        meta: { role: ['supergz', 'supertokyo', 'super', 'tokyo', 'normal-big'] }
      },
      {
        path: 'shipping',
        component: ordersShipping,
        name: '待发货',
        meta: { role: ['supergz', 'supertokyo', 'super', 'tokyo', 'normal-big'] }
      },
      {
        path: 'needexport',
        component: ordersNeedExport,
        name: '拼邮&保税',
        meta: { role: ['supergz', 'supertokyo', 'super', 'normal', 'normal-big'] }
      },
      {
        path: 'uextrack',
        component: ordersUexTrack,
        name: '轨迹单',
        meta: { role: ['supergz', 'supertokyo', 'super', 'normal', 'normal-big'] }
      },
      { path: 'aftersale',
        component: afterSale,
        name: '售后单',
        meta: { role: ['supergz', 'supertokyo', 'super', 'normal', 'tokyo', 'normal-big'] }
      },
      { path: 'importagent', component: importAgent, name: '代理订单' }
    ]
  },
  {
    path: '/purchases',
    component: Layout,
    redirect: '/purchases/index',
    name: '采购',
    icon: 'zujian',
    children: [
      {
        path: 'order',
        component: purchasesorder,
        name: '采购单',
        meta: { role: ['supergz', 'supertokyo', 'super', 'tokyo', 'normal-big'] }
      },
      {
        path: 'stockin',
        component: purchasesstockin,
        name: '采购入库',
        meta: { role: ['supergz', 'supertokyo', 'super', 'tokyo', 'normal-big'] }
      },
      {
        path: 'transform',
        component: purchasestransform,
        name: '转运国内',
        meta: { role: ['supergz', 'supertokyo', 'super', 'tokyo', 'normal-big'] }
      },
      {
        path: 'transformdb',
        component: transformdb,
        name: '待转运',
        meta: { role: ['supergz', 'supertokyo', 'super', 'tokyo', 'normal-big'] }
      },
      {
        path: 'create',
        component: purchasescreate,
        name: '新采购',
        meta: { role: ['supergz', 'supertokyo', 'super', 'tokyo', 'normal-big'] }
      }
    ]
  },
  {
    path: '/products',
    component: Layout,
    redirect: '/products/index',
    name: '商品',
    icon: 'zujian',
    children: [
      { path: 'query', component: productsquery, name: '查商品' },
      { path: 'bondedquery', component: bondedproductsquery, name: '保税仓' }
    ]
  },
  {
    path: '/stocks',
    component: Layout,
    redirect: '/stocks/index',
    name: '仓库',
    icon: 'zujian',
    children: [
      {
        path: 'query',
        component: stocksquery,
        name: '查库存',
        meta: { role: ['supergz', 'supertokyo', 'super', 'normal', 'tokyo', 'normal-big'] }
      }
    ]
  },
  {
    path: '/finances',
    component: Layout,
    redirect: '/finances/index',
    name: '财务',
    icon: 'zujian',
    children: [
      { path: 'costrecord', component: costRecord, name: '查支出', meta: { role: ['supergz', 'supertokyo', 'super'] } },
      { path: 'incomerecord', component: incomeRecord, name: '查收入', meta: { role: ['supergz', 'supertokyo', 'super'] } },
      { path: 'createcostrecord', component: createCostRecord, name: '新支出', meta: { role: ['supergz', 'supertokyo', 'super'] } },
      { path: 'transformrecord', component: transformRecord, name: '转账日本', meta: { role: ['supertokyo', 'super'] } }
    ]
  },
  {
    path: '/analyzes',
    component: Layout,
    redirect: '/analyzes/index',
    name: '统计',
    icon: 'zujian',
    children: [
      { path: 'order', component: orderAnalyze, name: '销售统计', meta: { role: ['super'] } },
      { path: 'purchase', component: purchaseAnalyze, name: '采购统计', meta: { role: ['super'] } }
    ]
  },
  { path: '*', redirect: '/404', hidden: true }
];
