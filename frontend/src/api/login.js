import fetch from 'utils/fetch';

export function loginByEmail(username, password) {
  const data = {
    username,
    password
  };
  return fetch({
    url: '/login',
    method: 'post',
    data
  });
}

export function logout() {
  return fetch({
    url: '/login/logout',
    method: 'post'
  });
}

export function getInfo(key) {
  return fetch({
    url: '/userinfo',
    method: 'get',
    params: { key }
  });
}
