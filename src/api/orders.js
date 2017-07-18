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

export function updateOrder(order, url) {
  return fetch({
    url: url,
    method: 'put',
    data: order
  });
}

export function allocateOrder(data) {
  return fetch({
    url: '/order/allocate/',
    method: 'put',
    data: data
  });
}

export function fetchPv(pv) {
  return fetch({
    url: '/article_table/pv',
    method: 'get',
    params: { pv }
  });
}
