import fetch from 'utils/fetch';

export function fetchPurchaseOrder(query) {
  return fetch({
    url: '/purchase/',
    method: 'get',
    params: query
  });
}

export function fetchPurchaseOrderItem(query) {
  return fetch({
    url: '/purchase/item',
    method: 'get',
    params: query
  });
}

export function purchaseOrderDelete(data) {
  return fetch({
    url: '/purchase/delete/',
    method: 'put',
    data
  });
}

export function purchaseOrderTransform(data) {
  return fetch({
    url: '/purchase/transform/',
    method: 'post',
    data
  });
}

export function PurchaseOrderItemStockIn(data) {
  return fetch({
    url: '/purchase/itemstockin/',
    method: 'post',
    data
  });
}

export function purchaseOrderClear(data) {
  return fetch({
    url: '/purchase/clear/',
    method: 'put',
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

export function noOrderPurchase(data) {
  return fetch({
    url: '/purchase/noorderpurchase/',
    method: 'put',
    data
  });
}

export function createTransformDB(data) {
  return fetch({
    url: '/transformdb/create/',
    method: 'post',
    data
  });
}

export function fetchTransformDB(query) {
  return fetch({
    url: '/transformdb/',
    method: 'get',
    params: query
  });
}

export function updateTransformDB(transformdb, url) {
  return fetch({
    url,
    method: 'put',
    data: transformdb
  });
}

export function fetchPurchaseOrderAlert(query) {
  return fetch({
    url: '/purchase/alert',
    method: 'get',
    params: query
  });
}
