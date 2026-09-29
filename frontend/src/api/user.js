import request from '@/utils/request'

/**
 * 获取当前登录用户
 */
export function getUserInfo() {
  return request({
    url: '/api/user/me',
    method: 'get',
  })
}

/**
 * 修改当前登录用户个人信息
 */
export function updateUserInfo(data) {
  return request({
    url: '/api/user/me',
    method: 'put',
    data
  })
}
/**
 * 修改密码
 */
export function updatePassword(data) {
  return request({
    url: '/api/user/password',
    method: 'put',
    data
  })
}
/**
 * 分页模糊查询用户列表
 */
export function getUserPageList(params) {
  return request({
    url: '/api/user/list',
    method: 'get',
    params
  })
}
