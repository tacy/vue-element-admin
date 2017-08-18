import fetch from 'utils/fetch';

export function fetchPurchaseOrder(query) {
  return fetch({
    url: '/purchase',
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
