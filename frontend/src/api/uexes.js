import fetch from 'utils/fetch';

export function addUexNumber(data) {
  return fetch({
    url: '/uex/addnumber/',
    method: 'post',
    data
  });
}
