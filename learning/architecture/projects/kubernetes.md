# Kubernetes 架构分析

## 基本信息

| 属性 | 值 |
|------|-----|
| 项目名称 | Kubernetes |
| GitHub | https://github.com/kubernetes/kubernetes |
| 语言 | Go (97.5%), Shell (2.2%) |
| Stars | 121k+ |
| Forks | 42.7k+ |
| 维护方 | CNCF (Cloud Native Computing Foundation) |
| 许可证 | Apache-2.0 |

---

## 项目结构

```
kubernetes/
├── api/                  # API定义 (OpenAPI, Protobuf)
├── build/                # 构建脚本和配置
├── cluster/              # 集群配置示例
├── cmd/                  # 主要二进制入口
│   ├── kube-apiserver/   # API服务器
│   ├── kube-controller-manager/  # 控制器管理器
│   ├── kube-scheduler/   # 调度器
│   ├── kubelet/          # 节点代理
│   └── kubectl/          # CLI工具
├── docs/                 # 文档
├── hack/                 # 开发工具脚本
├── pkg/                  # 核心库代码
│   ├── api/              # API类型定义
│   ├── controller/       # 控制器框架
│   ├── kubelet/          # Kubelet实现
│   ├── scheduler/        # 调度器实现
│   └── ...
├── plugin/               # 插件代码
├── staging/              # 临时staging目录
├── test/                 # 测试代码
├── third_party/          # 第三方代码
└── vendor/               # 依赖 vendoring
```

---

## 整体架构

### 控制平面 (Control Plane)

```
┌─────────────────────────────────────────────────────────────┐
│                    Control Plane (Master Node)              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              kube-apiserver                         │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │   │
│  │  │ REST API│  │AuthN/Z  │  │Admission│             │   │
│  │  │Handler  │  │Webhook  │  │Webhook  │             │   │
│  │  └─────────┘  └─────────┘  └─────────┘             │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                  │
│  ┌────────────────────────┼─────────────────────────────┐   │
│  │                        ↓                             │   │
│  │              ┌─────────────────┐                     │   │
│  │              │      etcd       │                     │   │
│  │              │  (Key-Value DB) │                     │   │
│  │              └─────────────────┘                     │   │
│  │                        ↑                             │   │
│  │  ┌─────────────────────┼─────────────────────┐      │   │
│  │  ↓                     ↓                     ↓      │   │
│  │ ┌────────────┐   ┌────────────┐   ┌────────────┐    │   │
│  │ │Controller  │   │  Scheduler │   │   Cloud    │    │   │
│  │ │Manager     │   │            │   │ Controller │    │   │
│  │ └────────────┘   └────────────┘   └────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Watch/Update
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Worker Node                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    kubelet                          │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │   │
│  │  │Pod      │  │Container│  │Volume   │             │   │
│  │  │Lifecycle│  │Runtime  │  │Manager  │             │   │
│  │  │(CRI)    │  │(CRI)    │  │(CSI)    │             │   │
│  │  └─────────┘  └─────────┘  └─────────┘             │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               kube-proxy                            │   │
│  │         (Network Proxy / Load Balancer)             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心组件详解

### 1. kube-apiserver

**职责**: 
- REST API 入口
- 认证授权 (Authentication/Authorization)
- 准入控制 (Admission Control)
- 数据验证

**关键代码结构**:
```
cmd/kube-apiserver/
├── app/
│   ├── server.go         # 服务器启动逻辑
│   ├── options/          # 命令行选项
│   └── aggregator.go     # API聚合
└── apiserver.go          # 入口

pkg/apiserver/
├── handlers/             # HTTP处理器
├── admission/            # 准入控制器
└── storage/              # 存储接口
```

### 2. etcd

**职责**:
- 集群状态持久化
- 分布式一致性 (Raft协议)
- Watch机制支持

**数据组织**:
```
/registry/
├── pods/
│   └── <namespace>/
│       └── <pod-name>
├── deployments/
├── services/
├── configmaps/
└── secrets/
```

### 3. kube-controller-manager

**职责**:
- 维护集群期望状态
- 故障检测和恢复
- 水平扩缩容

**控制器列表**:
| 控制器 | 职责 |
|--------|------|
| Deployment | 管理ReplicaSet，支持滚动更新 |
| ReplicaSet | 维护Pod副本数 |
| StatefulSet | 有状态应用管理 |
| DaemonSet | 每个节点运行一个Pod |
| Job/CronJob | 批处理任务 |
| Node | 节点健康检查 |
| Service | Endpoint管理 |

**控制器模式**:
```go
// 通用控制器模式
func (c *Controller) syncHandler(key string) error {
    namespace, name, _ := cache.SplitMetaNamespaceKey(key)
    
    // 1. 从Informer获取对象
    obj, err := c.lister.Get(name)
    if err != nil {
        return err
    }
    
    // 2. 对比期望状态vs实际状态
    // 3. 执行调和 (Reconciliation)
    return c.reconcile(obj)
}
```

### 4. kube-scheduler

**调度流程**:
```
┌─────────────────────────────────────────┐
│ 1. Predicates (过滤)                    │
│    - 资源充足性                          │
│    - 节点选择器匹配                       │
│    - 亲和性/反亲和性                      │
│    → 可用节点列表                        │
├─────────────────────────────────────────┤
│ 2. Priorities (打分)                    │
│    - 资源利用率                          │
│    - 负载均衡                            │
│    - 亲和性权重                          │
│    → 节点分数排名                        │
├─────────────────────────────────────────┤
│ 3. 选择最优节点 → 绑定Pod               │
└─────────────────────────────────────────┘
```

### 5. kubelet

**职责**:
- Pod生命周期管理
- 容器运行时接口 (CRI)
- 资源监控 (cAdvisor)
- 健康检查

**代码结构**:
```
pkg/kubelet/
├── kubelet.go           # 主结构体
├── kuberuntime/         # CRI实现
│   ├── kuberuntime_container.go
│   └── kuberuntime_sandbox.go
├── status/              # 状态管理
├── eviction/            # 资源驱逐
├── prober/              # 健康探测
└── server/              # HTTP服务器
```

---

## API 设计

### REST API 规范

```
/apis/<group>/<version>/namespaces/<namespace>/<resource>
/api/v1/namespaces/<namespace>/<resource>
```

### 资源对象结构

```yaml
apiVersion: apps/v1      # API组和版本
kind: Deployment         # 资源类型
metadata:
  name: nginx-deploy
  namespace: default
  labels:
    app: nginx
spec:                    # 期望状态
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.19
status:                  # 实际状态 (由系统填充)
  replicas: 3
  availableReplicas: 3
```

### 声明式API优势

1. **期望状态管理**: 用户声明期望，系统负责实现
2. **自愈合**: 实际状态偏离时自动纠正
3. **版本控制**: YAML文件可版本化管理
4. **幂等性**: 多次应用相同配置结果一致

---

## 扩展性机制

### 1. CRD (Custom Resource Definition)

```yaml
# 定义自定义资源
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: databases.example.com
spec:
  group: example.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              databaseType:
                type: string
              replicas:
                type: integer
  scope: Namespaced
  names:
    plural: databases
    singular: database
    kind: Database
```

### 2. Operator 模式

```
┌─────────────────────────────────────────┐
│           Operator                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │CRD      │ │Custom   │ │Business │   │
│  │Definition│ │Controller│ │Logic    │   │
│  └─────────┘ └─────────┘ └─────────┘   │
│         ↑ Watch CR changes              │
│         ↓ Reconcile state               │
│  ┌─────────────────────────────────┐   │
│  │         Kubernetes API          │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**Operator SDK框架**:
- Operator Framework
- Kubebuilder
- KUDO

### 3. CNI/CSI/CRI 插件接口

| 接口 | 全称 | 用途 | 示例实现 |
|------|------|------|----------|
| CNI | Container Network Interface | 容器网络 | Calico, Cilium, Flannel |
| CSI | Container Storage Interface | 持久化存储 | AWS EBS, Ceph, NFS |
| CRI | Container Runtime Interface | 容器运行时 | containerd, CRI-O |

### 4. Admission Webhook

```go
// 变异Webhook示例
func (a *Admitter) mutatePod(pod *corev1.Pod) (*admission.AdmissionResponse, error) {
    // 自动注入sidecar
    if shouldInjectSidecar(pod) {
        pod.Spec.Containers = append(pod.Spec.Containers, sidecarContainer)
    }
    
    return &admission.AdmissionResponse{
        Allowed: true,
        Patch:   createPatch(pod),
    }, nil
}
```

---

## 依赖管理

### Go Modules

```go
// go.mod
module k8s.io/kubernetes

go 1.21

require (
    k8s.io/api v0.29.0
    k8s.io/apimachinery v0.29.0
    k8s.io/client-go v0.29.0
    google.golang.org/grpc v1.59.0
    github.com/spf13/cobra v1.8.0
)
```

### Staging 目录

```
staging/
├── src/
│   ├── k8s.io/
│   │   ├── api/           # API定义
│   │   ├── apimachinery/  # 通用机制
│   │   ├── client-go/     # Go客户端
│   │   ├── code-generator/# 代码生成
│   │   └── ...
```

---

## 测试策略

### 测试类型

| 类型 | 工具 | 说明 |
|------|------|------|
| 单元测试 | Go testing | go test ./pkg/... |
| 集成测试 | kind/k3d | 真实集群测试 |
| E2E测试 | kubetest | 完整流程测试 |
| 压力测试 | ClusterLoader | 性能基准测试 |
| 一致性测试 | sonobuoy | CNCF认证测试 |

### E2E测试示例

```go
var _ = framework.KubeDescribe("Pods", func() {
    f := framework.NewDefaultFramework("pods")
    
    It("should be submitted and removed", func() {
        // 创建Pod
        pod := createPod(f.ClientSet, f.Namespace.Name)
        
        // 验证运行状态
        err := e2epod.WaitForPodRunningInNamespace(c, pod)
        framework.ExpectNoError(err)
        
        // 删除Pod
        err = c.CoreV1().Pods(f.Namespace.Name).Delete(context.TODO(), pod.Name, metav1.DeleteOptions{})
        framework.ExpectNoError(err)
    })
})
```

---

## 架构亮点

### 1. 控制器模式 (Controller Pattern)
```
Desired State (etcd)
       ↓
   Informer (Watch)
       ↓
   Work Queue
       ↓
   Reconcile Loop
       ↓
Actual State (Cluster)
       ↓
   Update Status
```

### 2. List-Watch 机制
- **List**: 初始全量数据获取
- **Watch**: 增量变更监听
- **Cache**: 本地缓存减少API压力

### 3. 水平扩展设计
- 无状态控制平面组件
- 工作节点独立扩缩容
- API Server支持水平扩展

---

## 最佳实践提取

1. **声明式配置**: 状态管理优于命令式操作
2. **最终一致性**: 接受短暂不一致，保证最终正确
3. **优雅降级**: 部分故障不影响整体服务
4. **可观测性**: 全面的指标、日志、追踪
5. **扩展点设计**: 清晰的接口便于生态扩展

---

## 参考链接

- [官方文档](https://kubernetes.io/docs/)
- [设计文档](https://github.com/kubernetes/design-proposals-archive)
- [Enhancements](https://github.com/kubernetes/enhancements)
- [社区](https://github.com/kubernetes/community)
