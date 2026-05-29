# DevMemory 迁移到另一台电脑完整使用说明书

本文档用于把 DevMemory 从当前电脑迁移到另一台电脑。它同时覆盖两种情况：

- 只在新电脑上重新部署一个空的 DevMemory。
- 把旧电脑上的课程、资料、学习记录、聊天历史、思维导图等数据完整迁移到新电脑。

推荐迁移方式是：

1. 在旧电脑备份数据库和上传文件。
2. 在新电脑克隆 DevMemory 项目。
3. 私下复制 `.env.production`。
4. 在新电脑恢复数据库和上传文件。
5. 启动服务并验证产品可用。

## 一、迁移前先理解哪些东西必须搬

完整迁移需要四类内容：

| 内容 | 是否必须 | 说明 |
| --- | --- | --- |
| 项目源码 | 必须 | 推荐从 GitHub 克隆 `https://github.com/mrmi9/DevMemory.git`。 |
| `.env.production` | 必须 | 里面有生产密钥、默认账号、数据库密码、DeepSeek Key 等私密配置。不要提交到 Git。 |
| PostgreSQL 数据库备份 | 完整迁移时必须 | 保存用户、课程、资料记录、文档分块、问答历史、学习卡片、复习进度、思维导图等。 |
| 上传文件备份 | 完整迁移时必须 | 保存原始上传资料。只备份数据库是不完整的。 |

不要复制这些生成目录：

- `.venv/`
- `node_modules/`
- `dist/`
- `.pytest_cache/`
- `__pycache__/`
- `data/`
- `uploads/`
- `postgres_data/`

这些目录要么可以重新生成，要么应通过正式备份恢复流程处理。

## 二、新电脑需要准备什么

新电脑至少需要：

- Windows 10/11、Windows Server、Linux 或 macOS。
- Docker Desktop 或 Docker Engine。
- Docker Compose v2。
- Git。
- 至少 4 GB 可用内存，推荐 8 GB 以上。
- 足够磁盘空间存放 Docker 镜像、数据库、上传资料和备份文件。
- 如果要使用在线 AI 功能，需要能访问 DeepSeek API。

默认访问端口是：

```text
http://localhost:5173
```

如果新电脑的 `5173` 端口被占用，需要修改 `docker-compose.prod.yml` 里的前端端口映射，并同步修改 `.env.production` 中的 `STUDY_CORS_ORIGINS`。

## 三、场景 A：只部署空系统，不迁移旧数据

如果你只想在新电脑上运行一个全新的 DevMemory，按这一节做。

### 1. 克隆项目

```powershell
git clone https://github.com/mrmi9/DevMemory.git
cd DevMemory
```

### 2. 创建生产配置

```powershell
copy .env.production.example .env.production
notepad .env.production
```

至少填写这些配置：

```text
STUDY_ENVIRONMENT=production
STUDY_ACCESS_TOKEN_SECRET=<一段足够长的随机密钥>
STUDY_DEFAULT_USERNAME=<登录用户名>
STUDY_DEFAULT_PASSWORD=<强密码>
STUDY_DEEPSEEK_API_KEY=<DeepSeek Key，可为空>
STUDY_CORS_ORIGINS=http://localhost:5173
STUDY_UPLOAD_DIR=/app/uploads
```

如果不填写 `STUDY_DEEPSEEK_API_KEY`，系统仍然可以启动，但 AI 功能会显示为离线占位模式。

### 3. 启动系统

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
```

### 4. 打开产品

浏览器访问：

```text
http://localhost:5173
```

使用 `.env.production` 中的：

- `STUDY_DEFAULT_USERNAME`
- `STUDY_DEFAULT_PASSWORD`

登录。

## 四、场景 B：完整迁移旧电脑数据

如果你要把旧电脑已经使用过的 DevMemory 完整搬到新电脑，按这一节做。

### 1. 在旧电脑进入项目目录

```powershell
cd E:\DevMemory
```

如果旧电脑项目不在 `E:\DevMemory`，改成你的真实路径。

### 2. 确认旧服务状态

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

确认 `postgres`、`backend`、`worker`、`frontend` 等服务状态正常。

### 3. 创建备份目录

```powershell
New-Item -ItemType Directory -Force backups
```

### 4. 备份数据库

```powershell
python scripts\ops.py backup-db --output backups\devmemory-db.sql
```

这个文件保存课程、资料索引、聊天记录、学习卡片、复习记录等结构化数据。

### 5. 备份上传文件

```powershell
python scripts\ops.py backup-uploads --output backups\devmemory-uploads.tgz
```

这个文件保存你上传过的 PDF、Word、Markdown、图片等原始资料。

### 6. 记录当前项目版本

```powershell
git rev-parse HEAD
```

把输出的 commit id 保存下来。新电脑最好使用同一版本或更新版本。

### 7. 可选：停止旧电脑服务

如果你希望迁移期间旧电脑不再产生新数据，可以停止旧服务：

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml down
```

如果你还想继续用旧电脑，可以暂时不停止，但要注意：备份完成后新增的数据不会自动出现在新电脑。

## 五、把文件复制到新电脑

需要复制到新电脑的文件：

- `.env.production`
- `backups\devmemory-db.sql`
- `backups\devmemory-uploads.tgz`

推荐不要直接复制整个旧项目目录，而是在新电脑重新克隆 GitHub 仓库。

`.env.production` 和备份文件都包含隐私数据，不要通过公开网盘、公开聊天窗口或 Git 仓库传输。

## 六、在新电脑恢复

### 1. 克隆项目

```powershell
git clone https://github.com/mrmi9/DevMemory.git
cd DevMemory
```

### 2. 放置配置和备份文件

把旧电脑复制来的 `.env.production` 放到项目根目录。

创建备份目录：

```powershell
New-Item -ItemType Directory -Force backups
```

把两个备份文件放进去，最终结构应类似：

```text
DevMemory\
  .env.production
  docker-compose.prod.yml
  backups\
    devmemory-db.sql
    devmemory-uploads.tgz
```

### 3. 先启动数据库

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d postgres
```

检查数据库是否启动：

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

### 4. 恢复数据库

```powershell
python scripts\ops.py restore-db --input backups\devmemory-db.sql --yes
```

### 5. 恢复上传文件

```powershell
python scripts\ops.py restore-uploads --input backups\devmemory-uploads.tgz --yes
```

数据库和上传文件必须都恢复。只恢复数据库会导致课程和资料记录存在，但原始文件缺失。

### 6. 启动完整服务

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
```

查看服务状态：

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

浏览器打开：

```text
http://localhost:5173
```

## 七、迁移后验证

### 1. 检查网页入口

```powershell
Invoke-WebRequest http://127.0.0.1:5173 -UseBasicParsing
```

能返回 HTTP 成功响应，说明前端入口可访问。

### 2. 检查系统状态

```powershell
Invoke-WebRequest http://127.0.0.1:5173/api/system/status -UseBasicParsing
```

重点看这些状态：

- 数据库连接正常。
- 上传目录可写。
- pgvector 可用。
- worker 有心跳或任务状态。
- DeepSeek 配置状态符合预期。
- embedding provider 状态符合预期。

### 3. 运行 smoke 测试

```powershell
python scripts\smoke_test.py --base-url http://127.0.0.1:5173/api --username <你的用户名> --password <你的密码>
```

成功时应完成：

- 登录。
- 创建临时课程。
- 上传 Markdown。
- 等待解析完成。
- 提问并校验引用。
- 生成学习材料。
- 生成思维导图。
- 删除临时课程。

### 4. 手动检查产品数据

登录后逐项确认：

- 课程列表是否完整。
- 每门课程下的资料是否完整。
- 已上传资料是否能用于问答。
- 问答是否能返回答案和引用来源。
- 学习卡片、错题、复习进度是否存在。
- 思维导图是否存在。
- 聊天历史是否符合旧电脑数据。
- 新建课程、上传资料、删除临时课程是否正常。

## 八、登录账号注意事项

完整迁移时，建议直接复制旧电脑的 `.env.production`，不要临时改默认账号密码。

原因是：恢复旧数据库后，已有用户的密码以数据库中的记录为准。如果你只在新电脑 `.env.production` 中修改 `STUDY_DEFAULT_PASSWORD`，不一定会改变已经存在的用户密码。

如果登录失败，先用旧电脑原来的用户名和密码登录。

## 九、常见问题处理

### 1. 浏览器打不开 `http://localhost:5173`

先看服务状态：

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

再检查端口 `5173` 是否被占用。如果被占用，修改 `docker-compose.prod.yml` 中前端端口，并同步修改：

```text
STUDY_CORS_ORIGINS
```

### 2. 登录失败

优先检查：

- 是否复制了旧电脑正确的 `.env.production`。
- 是否使用旧数据库里的原账号密码。
- 新电脑是否恢复了旧数据库。

完整迁移后，不要只看新 `.env.production` 中写的默认密码，旧用户通常仍以数据库里的密码为准。

### 3. AI 功能显示离线模式

检查：

```text
STUDY_DEEPSEEK_API_KEY
```

如果为空或无效，系统会进入离线占位 AI 模式。

修改后重启：

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```

### 4. 课程有了，但上传资料打不开或不能解析

通常是上传文件没有恢复，或恢复到了错误的 Docker volume。

重新执行：

```powershell
python scripts\ops.py restore-uploads --input backups\devmemory-uploads.tgz --yes
```

然后重启服务：

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```

### 5. restore 命令找不到容器

确认你在项目根目录执行命令，且目录里存在：

```text
docker-compose.prod.yml
```

先启动数据库：

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml up -d postgres
```

再执行恢复命令。

### 6. 数据库恢复成功，但后端启动失败

查看日志：

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml logs backend
docker compose --env-file .env.production -f docker-compose.prod.yml logs worker
```

常见原因：

- `.env.production` 中密钥太弱或为空。
- `STUDY_DEFAULT_PASSWORD` 为空或过弱。
- `STUDY_CORS_ORIGINS=*` 在生产环境被禁止。
- 数据库密码和 `STUDY_DATABASE_URL` 不一致。
- 上传目录不可写。
- embedding 维度和 pgvector schema 不一致。

## 十、安全要求

迁移过程中请遵守：

- `.env.production` 不要提交到 Git。
- 数据库备份和上传文件备份要加密或私密保存。
- 不要把备份文件长期放在公共 U 盘、共享网盘或聊天下载目录。
- 如果 DeepSeek Key 通过不安全渠道传过，迁移后应更换 Key。
- `STUDY_ACCESS_TOKEN_SECRET` 使用足够长的随机字符串。
- `STUDY_DEFAULT_PASSWORD` 使用强密码。
- 不要把 PostgreSQL 端口直接暴露到公网。

## 十一、完整迁移检查清单

旧电脑：

- [ ] 旧系统可以正常访问。
- [ ] 已备份数据库到 `backups\devmemory-db.sql`。
- [ ] 已备份上传文件到 `backups\devmemory-uploads.tgz`。
- [ ] 已复制 `.env.production`。
- [ ] 已记录当前 Git commit 或发布版本。
- [ ] 如需冻结数据，已停止旧电脑服务。

新电脑：

- [ ] 已安装 Docker。
- [ ] 已安装 Git。
- [ ] 已克隆 `https://github.com/mrmi9/DevMemory.git`。
- [ ] `.env.production` 已放到项目根目录。
- [ ] 两个备份文件已放到 `backups\`。
- [ ] PostgreSQL 已启动。
- [ ] 数据库已恢复。
- [ ] 上传文件已恢复。
- [ ] 完整服务已启动。
- [ ] `http://localhost:5173` 可以打开。
- [ ] `/api/system/status` 状态正常。
- [ ] smoke 测试通过。
- [ ] 人工确认课程、资料、问答、学习卡片、思维导图正常。

完成以上检查后，新电脑就可以作为 DevMemory 的正式使用环境。
