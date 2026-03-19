# B站收藏夹获取工具 - 使用指南

## 快速开始

### 1. 安装依赖

```bash
pip install bilibili-api-python
```

### 2. 运行脚本

```bash
cd /root/.openclaw/workspace/tools
python3 bilibili_fav_fetch.py
```

## 获取私密收藏夹（需要登录）

如果你的收藏夹是私密的，需要添加SESSDATA：

### 获取SESSDATA方法：

1. **浏览器登录B站** (https://www.bilibili.com)
2. **按F12打开开发者工具**
3. **切换到Application/应用标签**
4. **左侧找到 Cookies → https://www.bilibili.com**
5. **找到 `SESSDATA` 字段，复制值**
6. **粘贴到脚本中的 `SESSDATA = ""` 处**

### 或者使用环境变量（更安全）：

```bash
export BILI_SESSDATA="你的sessdata"
export BILI_CSRF="你的csrf"
```

然后修改脚本读取环境变量。

## 常见问题

### Q1: 提示 "权限不足" 或 "未登录"
- 收藏夹设置为私密时需要SESSDATA
- 公开收藏夹可以直接获取

### Q2: 获取不到数据
- 检查UID是否正确
- 检查网络连接
- 检查是否被风控（减少请求频率）

### Q3: 请求频率限制
- B站API有频率限制，建议每次请求间隔1-2秒
- 不要频繁大量抓取

## 扩展功能

### 获取所有收藏夹

```python
async def get_all_favorites():
    u = user.User(uid=UID)
    fav_list = await u.get_favorite_list()
    
    all_videos = []
    for fav in fav_list:
        fav_obj = favorite_list.FavoriteList(fav['id'])
        videos = await fav_obj.get_videos(page=1, page_size=20)
        all_videos.extend(videos.get('medias', []))
    
    return all_videos
```

### 获取视频详细信息

```python
from bilibili_api import video

v = video.Video(bvid="BV1xx411c7mD")
info = await v.get_info()
print(info)
```

### 获取视频字幕/弹幕

```python
# 获取字幕
subtitles = await v.get_subtitle()

# 获取弹幕
danmaku = await v.get_danmaku()
```

## 定时自动同步（可选）

创建一个定时任务，每天同步一次：

```bash
# 编辑crontab
crontab -e

# 添加每天凌晨3点运行
0 3 * * * cd /root/.openclaw/workspace/tools && python3 bilibili_fav_fetch.py >> /var/log/bili_sync.log 2>&1
```

## 输出格式

脚本会生成 `bilibili_favorites.json`，格式如下：

```json
[
  {
    "标题": "视频标题",
    "Bvid": "BV1xx411c7mD",
    "链接": "https://www.bilibili.com/video/BV1xx411c7mD",
    "UP主": "UP主名字",
    "UP主ID": 123456,
    "时长": "10:30",
    "播放量": 10000,
    "收藏时间": "2024-01-01",
    "简介": "视频简介..."
  }
]
```

## 相关链接

- [bilibili-api-python 文档](https://github.com/Nemo2011/bilibili-api)
- [B站API限制说明](https://github.com/SocialSisterYi/bilibili-API-collect)
