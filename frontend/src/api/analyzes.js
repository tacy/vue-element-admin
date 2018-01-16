import fetch from 'utils/fetch';

export function fetchOrderAnalyze(query) {
  return fetch({
    url: '/analyze/order/',
    method: 'get',
    params: query
  });
}

export function fetchPurchaseAnalyze(query) {
  return fetch({
    url: '/analyze/purchase/',
    method: 'get',
    params: query
  });
}

export function analyzeOrderAndPurchase(data) {
  return fetch({
    url: '/analyze/inout/',
    method: 'put',
    data
  });
}
