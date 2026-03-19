# Ollama 架构分析

## 基本信息

| 属性 | 值 |
|------|-----|
| 项目名称 | Ollama |
| GitHub | https://github.com/ollama/ollama |
| 语言 | Go |
| Stars | 160k+ |
| Forks | 12k+ |
| 维护方 | Ollama Inc. |
| 许可证 | MIT |

---

## 项目概述

Ollama 是一个轻量级、可扩展的框架，用于在本地运行和管理大型语言模型(LLM)。它采用 Docker 式的命令行交互模式，让用户可以像拉取容器镜像一样拉取和运行AI模型。

---

## 项目结构

```
ollama/
├── api/                  # REST API定义和客户端
│   ├── client.go         # API客户端
│   └── types.go          # API类型定义
├── auth/                 # 认证相关
├── cmd/                  # 命令行入口
│   └── ollama/           # main.go
├── docs/                 # 文档
├── examples/             # 使用示例
├── llm/                  # LLM推理引擎接口
│   ├── llama.go          # llama.cpp封装
│   └── payload.go        # 模型加载逻辑
├── model/                # 模型定义和处理
│   ├── model.go          # 模型结构
│   ├── image.go          # 图片处理
│   └── parser.go         # Modelfile解析
├── parser/               # 表达式解析器
├── progress/             # 进度显示
├── server/               # HTTP服务器
│   ├── routes.go         # API路由
│   ├── download.go       # 模型下载
│   └── sched.go          # 调度器
├── scripts/              # 构建脚本
└── format/               # 格式化工具
```

---

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ CLI        │  │ Python SDK │  │ JS SDK     │            │
│  │ (ollama)   │  │            │  │            │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Server Layer                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              HTTP Server (Go)                       │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │   │
│  │  │/api/generate│ │/api/chat│ │/api/pull │             │   │
│  │  │(推理)     │  │(对话)    │  │(下载)    │             │   │
│  │  └─────────┘  └─────────┘  └─────────┘             │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Model Manager                          │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │   │
│  │  │Registry │  │Cache    │  │Version  │             │   │
│  │  │(ollama.com)│ │Manager  │  │Control  │             │   │
│  │  └─────────┘  └─────────┘  └─────────┘             │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Scheduler                              │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │   │
│  │  │Queue    │  │GPU      │  │Memory   │             │   │
│  │  │Manager  │  │Scheduler│  │Manager  │             │   │
│  │  └─────────┘  └─────────┘  └─────────┘             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ C/C++ bindings
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Inference Layer                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              llama.cpp (C/C++)                      │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │   │
│  │  │GGML/GGUF│  │Quantize │  │Sampling │             │   │
│  │  │Loader   │  │Engine   │  │Methods  │             │   │
│  │  └─────────┘  └─────────┘  └─────────┘             │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ CPU (AVX)  │  │ CUDA       │  │ Metal      │            │
│  │            │  │ (NVIDIA)   │  │ (Apple)    │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心组件详解

### 1. HTTP Server (server/routes.go)

**职责**:
- REST API 路由处理
- 请求验证和序列化
- 流式响应处理

**API端点**:

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/generate` | POST | 文本生成 |
| `/api/chat` | POST | 多轮对话 |
| `/api/embed` | POST | 文本向量化 |
| `/api/pull` | POST | 拉取模型 |
| `/api/push` | POST | 推送模型 |
| `/api/create` | POST | 创建模型 |
| `/api/delete` | DELETE | 删除模型 |
| `/api/tags` | GET | 列出本地模型 |
| `/api/show` | GET | 模型信息 |
| `/api/ps` | GET | 运行中模型 |

### 2. 模型管理 (model/)

**Modelfile 格式**:
```dockerfile
FROM llama2:latest

SYSTEM """You are a helpful assistant."""

PARAMETER temperature 0.7
PARAMETER top_p 0.9

TEMPLATE """
[INST] {{ .System }} {{ .Prompt }} [/INST]
"""
```

**模型层定义**:
```go
type Layer struct {
    MediaType string `json:"mediaType"`
    Digest    string `json:"digest"`
    Size      int64  `json:"size"`
    Data      []byte `json:-`
}

// 层类型
const (
    LayerTypeConfig   = "application/vnd.ollama.image.config"
    LayerTypeWeights  = "application/vnd.ollama.image.weights"
    LayerTypeTemplate = "application/vnd.ollama.image.template"
    LayerTypeSystem   = "application/vnd.ollama.image.system"
    LayerTypeParams   = "application/vnd.ollama.image.params"
    LayerTypeMessages = "application/vnd.ollama.image.messages"
)
```

### 3. 调度器 (server/sched.go)

**功能**:
- GPU内存管理
- 并行请求调度
- 模型加载/卸载决策

**调度策略**:
```go
type Scheduler struct {
    loadedMu sync.RWMutex
    loaded   map[string]*loadedModel  // 已加载模型
    
    pendingMu sync.Mutex
    pending   []pendingRequest          // 待处理请求
}

// 调度流程
func (s *Scheduler) processPending() {
    for _, req := range s.pending {
        // 1. 检查模型是否已加载
        if model, ok := s.loaded[req.model]; ok {
            // 复用已加载模型
            s.sendToGPU(model, req)
        } else {
            // 2. 检查GPU内存
            if s.hasEnoughMemory(req.model) {
                // 加载新模型
                s.loadModel(req.model)
            } else {
                // 3. 卸载最少使用的模型
                s.unloadLRU()
                s.loadModel(req.model)
            }
        }
    }
}
```

### 4. 推理引擎 (llm/)

**llama.cpp 集成**:
```go
type LLM interface {
    Predict(ctx context.Context, req PredictRequest, fn func(PredictResponse)) error
    Embedding(ctx context.Context, req EmbeddingRequest) ([]float32, error)
    Tokenize(string) ([]int, error)
    Detokenize([]int) (string, error)
    Close()
}

// 动态库加载
type llama struct {
    *dynExtServer  // C bindings
    options        api.Options
}
```

---

## API 设计

### 生成接口

```go
// 请求
type GenerateRequest struct {
    Model   string `json:"model"`
    Prompt  string `json:"prompt"`
    Stream  *bool  `json:"stream,omitempty"`
    Options Options `json:"options,omitempty"`
    
    // 上下文保持
    Context []int `json:"context,omitempty"`
}

// 响应 (流式)
type GenerateResponse struct {
    Model     string `json:"model"`
    CreatedAt string `json:"created_at"`
    Response  string `json:"response"`
    Done      bool   `json:"done"`
    
    // 统计信息
    TotalDuration      int64 `json:"total_duration,omitempty"`
    LoadDuration       int64 `json:"load_duration,omitempty"`
    PromptEvalCount    int   `json:"prompt_eval_count,omitempty"`
    PromptEvalDuration int64 `json:"prompt_eval_duration,omitempty"`
    EvalCount          int   `json:"eval_count,omitempty"`
    EvalDuration       int64 `json:"eval_duration,omitempty"`
}
```

### 对话接口

```go
type ChatRequest struct {
    Model    string    `json:"model"`
    Messages []Message `json:"messages"`
    Stream   *bool     `json:"stream,omitempty"`
    Options  Options   `json:"options,omitempty"`
}

type Message struct {
    Role    string `json:"role"`    // system, user, assistant
    Content string `json:"content"`
    Images  []ImageData `json:"images,omitempty"`
}
```

---

## 扩展性机制

### 1. Modelfile 自定义

```dockerfile
# 基础模型
FROM llama3

# 系统提示词
SYSTEM "You are Mario from Super Mario Bros."

# 参数调优
PARAMETER temperature 0.8
PARAMETER top_k 40
PARAMETER top_p 0.9
PARAMETER num_ctx 4096
PARAMETER num_gpu 50

# 对话模板
TEMPLATE """{{ if .System }}<|start_header_id|>system<|end_header_id|>

{{ .System }}<|eot_id|>{{ end }}{{ if .Prompt }}<|start_header_id|>user<|end_header_id|>

{{ .Prompt }}<|eot_id|>{{ end }}<|start_header_id|>assistant<|end_header_id|>

{{ .Response }}<|eot_id|>"""

# 适配器支持 (LoRA)
ADAPTER ./custom-lora.bin
```

### 2. 多模态支持

```go
// 图片处理
type ImageData []byte

func (i ImageData) ToInput() (llm.Input, error) {
    // 1. 解码图片
    img, _, err := image.Decode(bytes.NewReader(i))
    if err != nil {
        return nil, err
    }
    
    // 2. 预处理 (resize, normalize)
    processed := preprocess(img)
    
    // 3. 转换为模型输入格式
    return llm.ImageInput(processed), nil
}
```

### 3. 嵌入模型支持

```go
// 文本向量化
func (s *Server) EmbedHandler(c *gin.Context) {
    var req EmbedRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(400, gin.H{"error": err.Error()})
        return
    }
    
    // 加载嵌入模型
    llm, err := s.getLLM(req.Model)
    if err != nil {
        c.JSON(500, gin.H{"error": err.Error()})
        return
    }
    
    // 生成嵌入向量
    embedding, err := llm.Embedding(c.Request.Context(), req.Input)
    if err != nil {
        c.JSON(500, gin.H{"error": err.Error()})
        return
    }
    
    c.JSON(200, EmbedResponse{
        Embedding: embedding,
    })
}
```

---

## 依赖管理

### Go Modules

```go
// go.mod
module github.com/ollama/ollama

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/spf13/cobra v1.8.0
    github.com/docker/go-units v0.5.0
    golang.org/x/sync v0.5.0
)
```

### CGO 依赖

```go
// llm/llama.cpp 绑定
// #cgo CXXFLAGS: -std=c++11
// #cgo LDFLAGS: -L${SRCDIR} -lllama -lm
import "C"
```

---

## 测试策略

### 测试结构

```
├── api/
│   └── client_test.go    # API客户端测试
├── model/
│   └── parser_test.go    # Modelfile解析测试
├── server/
│   └── routes_test.go    # HTTP路由测试
└── llm/
    └── llm_test.go       # 推理引擎测试
```

### 集成测试

```go
func TestGenerate(t *testing.T) {
    // 启动测试服务器
    srv := testutil.StartServer(t)
    defer srv.Close()
    
    client := api.NewClient(srv.URL)
    
    // 执行生成
    var generated string
    err := client.Generate(context.Background(), &api.GenerateRequest{
        Model:  "test-model",
        Prompt: "Hello,",
    }, func(resp api.GenerateResponse) error {
        generated += resp.Response
        return nil
    })
    
    if err != nil {
        t.Fatal(err)
    }
    
    if generated == "" {
        t.Error("expected non-empty response")
    }
}
```

---

## 架构亮点

### 1. 模型即文件
- 借鉴 Docker 镜像分层概念
- 每个模型版本独立存储
- 支持增量更新

### 2. 零配置设计
- 自动检测 GPU/CPU
- 自动内存管理
- 自动量化选择

### 3. 多平台支持
```
Platforms:
- macOS (ARM64/x86_64, Metal)
- Linux (x86_64/ARM64, CUDA/ROCm)
- Windows (x86_64, CUDA)
```

### 4. 流式响应
```go
// Server-Sent Events
func (s *Server) Generate(c *gin.Context) {
    c.Stream(func(w io.Writer) bool {
        select {
        case chunk, ok := <-chunks:
            if !ok {
                return false
            }
            c.SSEvent("message", chunk)
            return true
        case <-c.Request.Context().Done():
            return false
        }
    })
}
```

---

## 最佳实践提取

1. **Docker式UX**: 熟悉的命令行交互降低学习成本
2. **分层存储**: 模型复用，节省磁盘空间
3. **延迟加载**: 按需加载模型，优化资源使用
4. **流式处理**: 实时返回结果，提升用户体验
5. **REST API**: 标准化的HTTP接口，易于集成

---

## 参考链接

- [官方文档](https://github.com/ollama/ollama/blob/main/docs/README.md)
- [Modelfile参考](https://github.com/ollama/ollama/blob/main/docs/modelfile.md)
- [API文档](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [SDK列表](https://github.com/ollama/ollama/tree/main/docs)
