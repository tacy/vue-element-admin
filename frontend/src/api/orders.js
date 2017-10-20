import fetch from 'utils/fetch';

export function fetchOrder(query) {
  return fetch({
    url: '/order',
    method: 'get',
    params: query
  });
}

export function fetchInventory(query) {
  return fetch({
    url: '/inventory',
    method: 'get',
    params: query
  });
}

export function fetchShippingDB(query) {
  return fetch({
    url: '/shippingdb',
    method: 'get',
    params: query
  });
}


export function fetchLogistic(query) {
  return fetch({
    url: '/xlobo/getlogistic',
    method: 'get',
    params: query
  });
}

export function fetchPDF(query) {
  return fetch({
    url: '/xlobo/getpdf',
    method: 'get',
    params: query
  });
}

export function fetchCategory(query) {
  return fetch({
    url: '/getcategory',
    method: 'get',
    params: query
  });
}

export function fetchPurchase(query) {
  return fetch({
    url: '/order/needpurchase',
    method: 'get',
    params: query
  });
}

export function fetchOrderItems(query) {
  return fetch({
    url: '/order/items',
    method: 'get',
    params: query
  });
}

export function fetchSupplier(query) {
  return fetch({
    url: '/supplier',
    method: 'get',
    params: query
  });
}

export function fetchStock(query) {
  return fetch({
    url: '/stock',
    method: 'get',
    params: query
  });
}

export function fetchShipping(query) {
  return fetch({
    url: '/shipping',
    method: 'get',
    params: query
  });
}

export function productcreate(data) {
  return fetch({
    url: '/product/',
    method: 'post',
    data
  });
}

export function exportDomesticOrder(data) {
  return fetch({
    url: '/order/exportdomestic/',
    method: 'post',
    data
  });
}

export function outOrder(data) {
  return fetch({
    url: '/order/out/',
    method: 'post',
    data
  });
}

export function orderRollback(data) {
  return fetch({
    url: '/order/rollback/',
    method: 'post',
    data
  });
}

export function createUexDB(data) {
  return fetch({
    url: '/uex/stockout/',
    method: 'post',
    data
  });
}

export function stockOut(data) {
  return fetch({
    url: '/stock/out/',
    method: 'post',
    data
  });
}

export function manualallocatedb(data) {
  return fetch({
    url: '/common/manualallocatedb/',
    method: 'post',
    data
  });
}

export function createNoVerification(data) {
  return fetch({
    url: '/xlobo/createnoverification/',
    method: 'post',
    data
  });
}

export function createfbxbill(data) {
  return fetch({
    url: '/xlobo/createfbxbill/',
    method: 'post',
    data
  });
}

export function deleteDBNumber(data) {
  return fetch({
    url: '/xlobo/deletedbnumber/',
    method: 'post',
    data
  });
}

export function updateOrder(order, url) {
  return fetch({
    url,
    method: 'put',
    data: order
  });
}

export function orderAllocate(data) {
  return fetch({
    url: '/order/allocate/',
    method: 'put',
    data
  });
}

export function orderAllocateUpdate(data) {
  return fetch({
    url: '/order/allocateupdate/',
    method: 'post',
    data
  });
}

export function orderTPRCreate(data) {
  return fetch({
    url: '/order/createtpr/',
    method: 'put',
    data
  });
}

export function orderDelete(data) {
  return fetch({
    url: '/order/delete/',
    method: 'put',
    data
  });
}

export function orderPurchase(data) {
  return fetch({
    url: '/order/purchase/',
    method: 'put',
    data
  });
}

export function orderMarkConflict(data) {
  return fetch({
    url: '/order/markconflict/',
    method: 'put',
    data
  });
}

export function orderConflict(data) {
  return fetch({
    url: '/order/conflict/',
    method: 'put',
    data
  });
}

export function fetchPv(pv) {
  return fetch({
    url: '/article_table/pv',
    method: 'get',
    params: { pv }
  });
}
