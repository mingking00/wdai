# B站收藏夹浏览器自动化导出 - 使用指南

## 方法一：使用OpenClaw Browser工具 (推荐)

OpenClaw内置了browser工具，可以直接控制浏览器。

### 步骤1：启动浏览器
```bash
openclaw browser start
```

### 步骤2：访问B站收藏夹
```bash
openclaw browser open "https://space.bilibili.com/3461564002732313/favlist"
```

### 步骤3：手动登录后，使用JavaScript提取数据

在浏览器控制台运行：
```javascript
// 提取收藏夹列表
const favorites = [];
document.querySelectorAll('.fav-list-item').forEach(item => {
    const title = item.querySelector('.text')?.textContent?.trim();
    const count = item.querySelector('.num')?.textContent?.trim();
    const link = item.querySelector('a')?.href;
    const id = link?.match(/fid=(\d+)/)?.[1];
    favorites.push({id, title, count});
});
console.log(JSON.stringify(favorites, null, 2));
```

### 步骤4：导出视频列表
切换到目标收藏夹后运行：
```javascript
// 提取当前收藏夹的所有视频
const videos = [];
let hasNext = true;
let page = 1;

async function extractAllVideos() {
    while (hasNext) {
        console.log(`提取第 ${page} 页...`);
        
        // 提取当前页视频
        document.querySelectorAll('.fav-video-list .small-item').forEach(item => {
            const title = item.querySelector('.title')?.textContent?.trim();
            const up = item.querySelector('.up-name')?.textContent?.trim();
            const link = item.querySelector('a')?.href;
            const bvid = link?.match(/BV\w+/)?.[0];
            videos.push({bvid, title, owner: up});
        });
        
        // 检查是否有下一页
        const nextBtn = document.querySelector('.be-pager-next:not(.be-pager-disabled)');
        if (nextBtn) {
            nextBtn.click();
            await new Promise(r => setTimeout(r, 2000)); // 等待加载
            page++;
        } else {
            hasNext = false;
        }
    }
    
    console.log(`共提取 ${videos.length} 个视频`);
    console.log(JSON.stringify(videos, null, 2));
    
    // 复制到剪贴板
    copy(JSON.stringify(videos, null, 2));
    console.log('数据已复制到剪贴板');
}

extractAllVideos();
```

### 步骤5：保存到文件
将复制的JSON数据保存到：
```
/root/.openclaw/workspace/.knowledge/bilibili/export_3461564002732313.json
```

## 方法二：使用Playwright自动化脚本

### 安装依赖
```bash
cd /root/.openclaw/workspace/.knowledge/bilibili
chmod +x install_browser_exporter.sh
./install_browser_exporter.sh
```

### 运行导出工具
```bash
# 显示浏览器窗口（推荐首次使用）
python3 browser_exporter.py --visible

# 无头模式（后台运行）
python3 browser_exporter.py --headless

# 导出特定收藏夹
python3 browser_exporter.py --fav 'q'
```

## 方法三：手动复制

### 最简单的方法：
1. 打开 https://space.bilibili.com/3461564002732313/favlist
2. 切换到"q"收藏夹
3. 复制所有视频标题和BV号
4. 粘贴到以下文件：
   ```
   /root/.openclaw/workspace/.knowledge/bilibili/export_3461564002732313.txt
   ```
5. 格式：
   ```
   BVxxxxx | 视频标题 | UP主名称
   ```

## 导出后自动溯源

导出完成后，运行溯源分析：
```bash
cd /root/.openclaw/workspace/.knowledge/bilibili
python3 tracer_v2.py 3461564002732313
```

这将：
- 分析所有收藏视频
- 提取技术关键词
- 溯源相关论文和开源项目
- 生成个性化学习报告

## 自动化集成

可以将浏览器导出加入自动执行循环：
```bash
# 每天自动导出并分析
0 3 * * * cd ~/.openclaw/workspace/.knowledge/bilibili && python3 browser_exporter.py --headless
```

## 注意事项

1. **登录状态**：浏览器导出需要B站登录状态
2. **频率限制**：避免频繁访问，建议每天一次
3. **数据安全**：导出的收藏数据仅保存在本地
