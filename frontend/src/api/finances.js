import fetch from 'utils/fetch';

export function fetchCostRecord(query) {
  return fetch({
    url: '/finance/cost/record/',
    method: 'get',
    params: query
  });
}

export function createCostRecord(data) {
  return fetch({
    url: '/finance/cost/createrecord/',
    method: 'put',
    data
  });
}

export function fetchCostType(query) {
  return fetch({
    url: '/finance/cost/type/',
    method: 'get',
    params: query
  });
}

export function fetchIncomeRecord(query) {
  return fetch({
    url: '/finance/income/record/',
    method: 'get',
    params: query
  });
}

export function createIncomeRecord(data) {
  return fetch({
    url: '/finance/income/createrecord/',
    method: 'put',
    data
  });
}

export function updateTransformRecord(transformrecord, url) {
  return fetch({
    url,
    method: 'put',
    data: transformrecord
  });
}

export function createTransformRecord(transformrecord) {
  return fetch({
    url: '/finance/transform/record/',
    method: 'post',
    data: transformrecord
  });
}

export function fetchTransformRecord(query) {
  return fetch({
    url: '/finance/transform/record',
    method: 'get',
    params: query
  });
}
