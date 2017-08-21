import fetch from 'utils/fetch';

export function fetchStock(query) {
  return fetch({
    url: '/stock',
    method: 'get',
    params: query
  });
}

export function updateStock(data, url) {
  return fetch({
    url,
    method: 'put',
    data
  });
}
