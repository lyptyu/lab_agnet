import { getToken } from '@/utils/auth'
import request from '@/utils/request'

export function chatApi(data) {
  return request({
    url: '/api/ai/chat',
    method: 'post',
    data,
    timeout: 90000
  })
}

export async function chatStreamApi(data, onEvent) {
  const baseUrl = import.meta.env.VITE_API_BASE_URL
  const token = getToken()
  const res = await fetch(`${baseUrl}/api/ai/chat/stream`, {
    method: "post",
    headers: {

      "Content-Type": "application/json",
      Accept: 'text/event-stream',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(data)

  })
  if (res.status === 401) {
    throw new Error('登录已失效，请重新登录')
  }
  if (!res.ok || !res.body) {
    throw new Error('流式接口请求失败')
  }
  const contentType = res.headers.get('content-type')
  if (!contentType.includes('text/event-stream')) {
    throw new Error('流式接口返回异常')
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  while (true) {

    const { done, value } = await reader.read()
    if (done) {
      break
    }

    buffer += decoder.decode(value, { stream: true })
    const chunks = buffer.split('\n\n')
    buffer = chunks.pop() || ''
    for (const chunk of chunks) {
      // 一帧里可能有多行，只取 data: 那一行
      const line = chunk
        .split('\n')
        .map((item) => item.trim())
        .find((item) => item.startsWith('data:'))
      if (!line) continue
      // 去掉前缀 "data:"，剩下才是 JSON
      const raw = line.slice(5).trim()
      if (!raw || raw === '[DONE]') continue
      try {
        onEvent(JSON.parse(raw))
      } catch {
        // 半包或脏数据：跳过，等下一帧
      }
    }
  }
}
