import fetch from 'utils/fetch';

export function fetchProduct(query) {
  return fetch({
    url: '/product',
    method: 'get',
    params: query
  });
}

export function updateProduct(data, url) {
  return fetch({
    url,
    method: 'put',
    data
  });
}

export function createProduct(data) {
  return fetch({
    url: '/product/',
    method: 'post',
    data
  });
}
