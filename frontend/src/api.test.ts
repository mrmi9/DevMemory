import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiClient } from './api'

const badGatewayHtml = `<html>
<head><title>502 Bad Gateway</title></head>
<body>
<center><h1>502 Bad Gateway</h1></center>
<hr><center>nginx/1.27.5</center>
</body>
</html>`

describe('ApiClient error handling', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('does not expose nginx HTML error pages to users', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(badGatewayHtml, { status: 502 })))

    const client = new ApiClient()

    await expect(client.login('admin', 'password')).rejects.toThrow('服务暂时不可用，请稍后重试')
  })
})
