# HomeClaw 多传感器融合技术实现详解

## 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        感知层 (Sensors)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ 蓝牙Beacon  │  │ 毫米波雷达   │  │ 环境传感器   │             │
│  │ (身份识别)   │  │ (位置定位)   │  │ (光照/温度)  │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
└─────────┼────────────────┼────────────────┼─────────────────────┘
          │                │                │
          │ BLE广播        │ UART/SPI       │ I2C
          │                │                │
┌─────────▼────────────────┴────────────────┴─────────────────────┐
│                    边缘计算层 (Edge Processor)                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              传感器数据融合引擎 (Fusion Engine)          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │   │
│  │  │ 数据同步模块 │  │ 坐标转换模块 │  │ 置信度计算  │      │   │
│  │  │ (Time Sync) │  │ (Coord Tx)  │  │ (Confidence)│      │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          │                                      │
│  ┌───────────────────────▼───────────────────────────────┐     │
│  │              TinyML 推理引擎 (Inference)                │     │
│  │  输入: [人员ID, 位置坐标, 环境状态, 时间特征]            │     │
│  │  输出: {action, confidence, priority}                   │     │
│  └───────────────────────┬───────────────────────────────┘     │
└──────────────────────────┼─────────────────────────────────────┘
                           │ MQTT/HTTP
                           │
┌──────────────────────────▼─────────────────────────────────────┐
│                      云端控制层 (Cloud)                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              HomeClaw Core Controller                    │   │
│  │  • 设备状态管理  • 场景编排  • 权限控制  • 审计日志       │   │
│  └───────────────────────┬─────────────────────────────────┘   │
└──────────────────────────┼─────────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────────┐
│                      交互层 (Interface)                         │
│         飞书Bot / Home Assistant / 物理开关                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. 蓝牙Beacon身份识别实现

### 1.1 硬件方案

```yaml
# 蓝牙信标 (佩戴端)
设备: 蓝牙Beacon手环/胸牌
协议: iBeacon / Eddystone
频率: 100ms-1s 广播一次
功耗: 1-2年续航 (CR2032电池)
价格: ¥20-50/个

# 蓝牙接收器 (固定端)
主控: ESP32-C3 / ESP32-S3
功能: 扫描BLE广播 → 解析UUID → 发送给边缘节点
通信: UART/WiFi/MQTT
部署: 每个房间/区域1个
```

### 1.2 ESP32接收器代码

```cpp
// ble_receiver.ino
#include <BLEDevice.h>
#include <BLEScan.h>
#include <WiFi.h>
#include <PubSubClient.h>

// WiFi和MQTT配置
const char* ssid = "YOUR_WIFI";
const char* password = "YOUR_PASS";
const char* mqtt_server = "192.168.1.100";

// 已知Beacon映射表 (UUID -> 用户ID)
std::map<String, String> beaconMap = {
    {"e2c56db5-dffb-48d2-b060-d0f5a71096e0", "user_alice"},
    {"e2c56db5-dffb-48d2-b060-d0f5a71096e1", "user_bob"},
};

WiFiClient espClient;
PubSubClient client(espClient);
BLEScan* pBLEScan;

class MyAdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks {
    void onResult(BLEAdvertisedDevice advertisedDevice) {
        // 检查是否是iBeacon
        if (advertisedDevice.haveManufacturerData()) {
            std::string strManufacturerData = advertisedDevice.getManufacturerData();
            
            // iBeacon前缀: 0x4C 0x00 (Apple Company ID)
            if (strManufacturerData.length() >= 25 && 
                strManufacturerData[0] == 0x4C && 
                strManufacturerData[1] == 0x00) {
                
                // 提取UUID
                char uuid[37];
                sprintf(uuid, 
                    "%02x%02x%02x%02x-%02x%02x-%02x%02x-%02x%02x-%02x%02x%02x%02x%02x%02x",
                    strManufacturerData[4], strManufacturerData[5], 
                    strManufacturerData[6], strManufacturerData[7],
                    strManufacturerData[8], strManufacturerData[9],
                    strManufacturerData[10], strManufacturerData[11],
                    strManufacturerData[12], strManufacturerData[13],
                    strManufacturerData[14], strManufacturerData[15], 
                    strManufacturerData[16], strManufacturerData[17],
                    strManufacturerData[18], strManufacturerData[19]
                );
                
                String beaconUUID = String(uuid);
                int rssi = advertisedDevice.getRSSI();
                
                // 查找对应用户
                if (beaconMap.count(beaconUUID)) {
                    String userId = beaconMap[beaconUUID];
                    
                    // RSSI转距离 (粗略估计)
                    float distance = calculateDistance(rssi);
                    
                    // 发布MQTT消息
                    String payload = "{";
                    payload += "\"user_id\":\"" + userId + "\",";
                    payload += "\"beacon_uuid\":\"" + beaconUUID + "\",";
                    payload += "\"rssi\":" + String(rssi) + ",";
                    payload += "\"distance\":" + String(distance) + ",";
                    payload += "\"timestamp\":" + String(millis()) + ",";
                    payload += "\"room\":\"living_room\"";
                    payload += "}";
                    
                    client.publish("homeclaw/sensors/beacon", payload.c_str());
                    
                    Serial.printf("Detected: %s at %.2fm (RSSI: %d)\n", 
                                  userId.c_str(), distance, rssi);
                }
            }
        }
    }
    
    float calculateDistance(int rssi) {
        // 基于RSSI的距离估算
        // RSSI = -10n log10(d) + A
        // n: 环境衰减系数 (2-4)
        // A: 1米处的RSSI值 (-59dBm typical)
        int txPower = -59;
        float n = 2.0;
        return pow(10, (txPower - rssi) / (10 * n));
    }
};

void setup() {
    Serial.begin(115200);
    
    // 连接WiFi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) delay(500);
    
    // 连接MQTT
    client.setServer(mqtt_server, 1883);
    while (!client.connected()) {
        if (client.connect("BLE_Receiver")) break;
        delay(5000);
    }
    
    // 初始化BLE
    BLEDevice::init("HomeClaw_BLE_Receiver");
    pBLEScan = BLEDevice::getScan();
    pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
    pBLEScan->setActiveScan(true);
    pBLEScan->setInterval(100);
    pBLEScan->setWindow(99);
}

void loop() {
    if (!client.connected()) {
        while (!client.connected()) {
            if (client.connect("BLE_Receiver")) break;
            delay(5000);
        }
    }
    client.loop();
    
    // 持续扫描
    BLEScanResults foundDevices = pBLEScan->start(5, false);
    pBLEScan->clearResults();
    delay(100);
}
```

---

## 2. 毫米波雷达位置检测实现

### 2.1 硬件选择

```yaml
推荐型号:
  - LD2410B: 24GHz, 基本存在检测, ¥30-40
  - LD2450: 24GHz, 多人坐标定位, ¥50-80  ★推荐
  - LD6002: 60GHz, 高精度, ¥100+

接口: UART (3.3V)
数据输出: 
  - 距离 (0.4-8m)
  - 角度/坐标 (X, Y)
  - 运动状态 (静止/运动)
  - 目标数量 (多人检测)
```

### 2.2 LD2450雷达驱动代码

```cpp
// ld2450_radar.ino
#include <HardwareSerial.h>

// LD2450使用UART通信
HardwareSerial radarSerial(1);  // ESP32 UART1

// 雷达数据结构
struct RadarTarget {
    uint8_t id;
    float x;           // X坐标 (cm)
    float y;           // Y坐标 (cm)
    float speed;       // 速度 (cm/s)
    uint16_t distance; // 距离 (cm)
    uint8_t resolution;// 分辨率
    bool valid;
};

RadarTarget targets[3];  // LD2450支持最多3个目标

void setup() {
    Serial.begin(115200);
    radarSerial.begin(115200, SERIAL_8N1, 16, 17);  // RX=GPIO16, TX=GPIO17
    
    Serial.println("LD2450 Radar Initialized");
}

void loop() {
    if (readRadarData()) {
        // 打印检测到的目标
        for (int i = 0; i < 3; i++) {
            if (targets[i].valid) {
                Serial.printf("Target %d: X=%.1fcm, Y=%.1fcm, Speed=%.1fcm/s\n",
                    targets[i].id, targets[i].x, targets[i].y, targets[i].speed);
            }
        }
        
        // 发送到MQTT
        sendToMQTT();
    }
    delay(50);
}

bool readRadarData() {
    // LD2450数据帧格式:
    // 帧头: 0xAA 0xFF 0x03 0x00
    // 目标1数据: 8字节
    // 目标2数据: 8字节
    // 目标3数据: 8字节
    // 帧尾: 0x55 0xCC
    
    if (radarSerial.available() < 30) return false;
    
    // 查找帧头
    while (radarSerial.available() >= 4) {
        if (radarSerial.read() == 0xAA) {
            if (radarSerial.read() == 0xFF &&
                radarSerial.read() == 0x03 &&
                radarSerial.read() == 0x00) {
                break;
            }
        }
    }
    
    // 读取3个目标数据
    for (int i = 0; i < 3; i++) {
        uint8_t data[8];
        if (radarSerial.readBytes(data, 8) != 8) return false;
        
        // 解析目标数据
        int16_t x_raw = (data[1] << 8) | data[0];
        int16_t y_raw = (data[3] << 8) | data[2];
        int16_t speed_raw = (data[5] << 8) | data[4];
        uint16_t dist_res = (data[7] << 8) | data[6];
        
        targets[i].id = i + 1;
        targets[i].x = x_raw / 10.0;  // 转换为cm
        targets[i].y = y_raw / 10.0;
        targets[i].speed = speed_raw / 10.0;
        targets[i].distance = dist_res & 0x7FFF;
        targets[i].resolution = (dist_res >> 13) & 0x07;
        targets[i].valid = (targets[i].x != 0 || targets[i].y != 0);
    }
    
    // 读取帧尾
    uint8_t end[2];
    radarSerial.readBytes(end, 2);
    
    return (end[0] == 0x55 && end[1] == 0xCC);
}

void sendToMQTT() {
    // 构造JSON并发送到MQTT broker
    // ... MQTT发布代码
}
```

---

## 3. 多传感器数据融合算法

### 3.1 时间同步

```python
# sensor_fusion.py
import time
from dataclasses import dataclass
from typing import Optional, List
import numpy as np

@dataclass
class SensorReading:
    sensor_type: str      # 'beacon', 'radar', 'light', etc.
    timestamp: float      # 统一时间戳 (ms)
    user_id: Optional[str]
    position: Optional[tuple]  # (x, y) in meters
    data: dict            # 原始传感器数据
    confidence: float     # 0-1

class TimeSynchronizer:
    """时间同步器 - 处理不同传感器的数据时序对齐"""
    
    def __init__(self, window_ms=500):
        self.window_ms = window_ms
        self.buffer = []
        
    def add_reading(self, reading: SensorReading):
        """添加传感器读数到缓冲队列"""
        self.buffer.append(reading)
        self._cleanup_old_data()
        
    def _cleanup_old_data(self):
        """清理过期数据"""
        current_time = time.time() * 1000
        self.buffer = [
            r for r in self.buffer 
            if current_time - r.timestamp < self.window_ms * 2
        ]
        
    def get_synced_frame(self) -> List[SensorReading]:
        """获取时间同步的数据帧"""
        if not self.buffer:
            return []
            
        current_time = time.time() * 1000
        
        # 找到最近的时间窗口
        latest_time = max(r.timestamp for r in self.buffer)
        window_start = latest_time - self.window_ms
        
        # 获取窗口内的所有数据
        frame = [
            r for r in self.buffer 
            if window_start <= r.timestamp <= latest_time
        ]
        
        return frame
```

### 3.2 位置融合（蓝牙 + 雷达）

```python
# position_fusion.py
import numpy as np
from scipy.optimize import minimize

class PositionFusion:
    """位置融合器 - 结合蓝牙和雷达数据精确定位"""
    
    def __init__(self):
        self.beacon_positions = {}  # 蓝牙接收器位置
        self.radar_offset = (0, 0)  # 雷达坐标系偏移
        
    def calibrate_radar_position(self, radar_coords, beacon_coords):
        """
        校准雷达坐标系到房间坐标系
        使用方法: 站在已知位置，记录雷达坐标和实际坐标，计算偏移
        """
        # 简单线性映射
        self.radar_offset = (
            beacon_coords[0] - radar_coords[0],
            beacon_coords[1] - radar_coords[1]
        )
        
    def fuse_position(self, beacon_readings, radar_targets):
        """
        融合蓝牙和雷达数据得到最可能的位置
        
        Args:
            beacon_readings: 多个蓝牙接收器的RSSI读数
            radar_targets: 雷达检测到的目标列表
        
        Returns:
            (x, y, confidence): 融合后的位置和置信度
        """
        # 1. 蓝牙三角定位
        bluetooth_pos = self._trilaterate_beacon(beacon_readings)
        
        # 2. 雷达坐标转换
        radar_positions = [
            (t['x'] + self.radar_offset[0], t['y'] + self.radar_offset[1])
            for t in radar_targets if t['valid']
        ]
        
        # 3. 数据关联 (匹配蓝牙和雷达检测到的同一个人)
        if bluetooth_pos and radar_positions:
            best_match = None
            min_distance = float('inf')
            
            for radar_pos in radar_positions:
                dist = np.sqrt(
                    (bluetooth_pos[0] - radar_pos[0])**2 +
                    (bluetooth_pos[1] - radar_pos[1])**2
                )
                if dist < min_distance and dist < 1.5:  # 1.5米内认为是同一人
                    min_distance = dist
                    best_match = radar_pos
            
            if best_match:
                # 加权融合
                # 雷达精度高但可能有漂移，蓝牙精度低但稳定
                fused_x = 0.7 * best_match[0] + 0.3 * bluetooth_pos[0]
                fused_y = 0.7 * best_match[1] + 0.3 * bluetooth_pos[1]
                confidence = 0.9
            else:
                # 无匹配，以蓝牙为准
                fused_x, fused_y = bluetooth_pos
                confidence = 0.6
        elif radar_positions:
            # 只有雷达
            fused_x, fused_y = radar_positions[0]
            confidence = 0.7
        elif bluetooth_pos:
            # 只有蓝牙
            fused_x, fused_y = bluetooth_pos
            confidence = 0.5
        else:
            return None, 0.0
            
        return (fused_x, fused_y), confidence
        
    def _trilaterate_beacon(self, readings):
        """基于RSSI的多点定位"""
        if len(readings) < 3:
            return None
            
        # 使用最小二乘法求解位置
        # 对每个接收器: (x - xi)^2 + (y - yi)^2 = di^2
        
        def error_function(pos):
            x, y = pos
            error = 0
            for r in readings:
                xi, yi = r['receiver_pos']
                di = r['distance']
                error += (np.sqrt((x - xi)**2 + (y - yi)**2) - di)**2
            return error
        
        # 初始猜测: 接收器的平均位置
        x0 = np.mean([r['receiver_pos'][0] for r in readings])
        y0 = np.mean([r['receiver_pos'][1] for r in readings])
        
        result = minimize(error_function, [x0, y0], method='L-BFGS-B')
        
        if result.success:
            return (result.x[0], result.x[1])
        return None
```

### 3.3 意图推理引擎

```python
# intent_engine.py
import json
import numpy as np
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class UserActivity(Enum):
    UNKNOWN = "unknown"
    WALKING_THROUGH = "walking_through"  # 路过
    APPROACHING = "approaching"          # 靠近
    STANDING = "standing"                # 站立停留
    SITTING_WORKING = "sitting_working"  # 坐下工作
    LEAVING = "leaving"                  # 离开

@dataclass
class IntentResult:
    action: str              # "turn_on", "turn_off", "adjust", "none"
    target_device: str       # "desk_lamp", "room_light", etc.
    confidence: float        # 0-1
    activity: UserActivity
    reason: str              # 推理原因

class IntentEngine:
    """意图推理引擎 - 基于融合数据判断用户意图"""
    
    def __init__(self):
        # 定义功能区域
        self.zones = {
            "desk": {
                "center": (3.0, 2.0),  # 书桌中心坐标
                "radius": 0.8,          # 有效区域半径
                "device": "desk_lamp",
                "lux_threshold": 300,
            },
            "bed": {
                "center": (1.5, 4.0),
                "radius": 1.0,
                "device": "bedside_lamp",
                "lux_threshold": 200,
            },
            "entrance": {
                "center": (0.5, 0.5),
                "radius": 0.5,
                "device": "entrance_light",
                "lux_threshold": 100,
            }
        }
        
        # 历史轨迹 (用于行为分析)
        self.trajectory_buffer = []
        self.max_buffer_size = 30  # 保存30个时间点 (约3秒)
        
    def update_trajectory(self, user_id, position, timestamp):
        """更新用户轨迹"""
        self.trajectory_buffer.append({
            "user_id": user_id,
            "position": position,
            "timestamp": timestamp
        })
        
        if len(self.trajectory_buffer) > self.max_buffer_size:
            self.trajectory_buffer.pop(0)
            
    def analyze_activity(self) -> UserActivity:
        """基于轨迹分析当前活动"""
        if len(self.trajectory_buffer) < 5:
            return UserActivity.UNKNOWN
            
        # 计算移动趋势
        recent_positions = [p["position"] for p in self.trajectory_buffer[-10:]]
        
        # 计算位移
        displacements = []
        for i in range(1, len(recent_positions)):
            dx = recent_positions[i][0] - recent_positions[i-1][0]
            dy = recent_positions[i][1] - recent_positions[i-1][1]
            displacements.append(np.sqrt(dx**2 + dy**2))
            
        avg_speed = np.mean(displacements) * 10  # 转换为 m/s (假设100ms采样)
        
        # 判断活动类型
        if avg_speed > 1.0:
            return UserActivity.WALKING_THROUGH
        elif avg_speed > 0.3:
            return UserActivity.APPROACHING
        elif avg_speed < 0.1:
            # 静止时间
            stationary_time = self._calculate_stationary_time()
            if stationary_time > 3.0:
                return UserActivity.SITTING_WORKING
            else:
                return UserActivity.STANDING
        elif self._is_moving_away():
            return UserActivity.LEAVING
            
        return UserActivity.UNKNOWN
        
    def _calculate_stationary_time(self) -> float:
        """计算静止持续时间"""
        if len(self.trajectory_buffer) < 2:
            return 0.0
            
        recent = self.trajectory_buffer[-1]
        for i in range(len(self.trajectory_buffer)-2, -1, -1):
            pos = self.trajectory_buffer[i]["position"]
            dist = np.sqrt(
                (recent["position"][0] - pos[0])**2 +
                (recent["position"][1] - pos[1])**2
            )
            if dist > 0.2:  # 移动超过20cm
                return (recent["timestamp"] - self.trajectory_buffer[i+1]["timestamp"]) / 1000.0
                
        return (recent["timestamp"] - self.trajectory_buffer[0]["timestamp"]) / 1000.0
        
    def _is_moving_away(self) -> bool:
        """判断是否正在离开"""
        if len(self.trajectory_buffer) < 5:
            return False
            
        # 计算距离房间中心的趋势
        room_center = (2.5, 2.5)
        
        old_pos = self.trajectory_buffer[-5]["position"]
        new_pos = self.trajectory_buffer[-1]["position"]
        
        old_dist = np.sqrt(
            (old_pos[0] - room_center[0])**2 +
            (old_pos[1] - room_center[1])**2
        )
        new_dist = np.sqrt(
            (new_pos[0] - room_center[0])**2 +
            (new_pos[1] - room_center[1])**2
        )
        
        return new_dist > old_dist + 0.3
        
    def infer_intent(self, user_id, position, lux, timestamp) -> IntentResult:
        """
        推理用户意图
        
        这是核心决策逻辑，可以后续用TinyML模型替代
        """
        # 更新轨迹
        self.update_trajectory(user_id, position, timestamp)
        
        # 分析活动
        activity = self.analyze_activity()
        
        # 确定当前区域
        current_zone = None
        for zone_name, zone_info in self.zones.items():
            dist = np.sqrt(
                (position[0] - zone_info["center"][0])**2 +
                (position[1] - zone_info["center"][1])**2
            )
            if dist <= zone_info["radius"]:
                current_zone = zone_name
                break
                
        if not current_zone:
            return IntentResult(
                action="none",
                target_device="",
                confidence=0.0,
                activity=activity,
                reason="不在任何功能区域"
            )
            
        zone = self.zones[current_zone]
        
        # 基于活动和环境决策
        if activity == UserActivity.SITTING_WORKING:
            if lux < zone["lux_threshold"]:
                return IntentResult(
                    action="turn_on",
                    target_device=zone["device"],
                    confidence=0.95,
                    activity=activity,
                    reason=f"在工作区域静止超过3秒，光照{lux}lux低于阈值{zone['lux_threshold']}"
                )
            else:
                return IntentResult(
                    action="none",
                    target_device=zone["device"],
                    confidence=0.7,
                    activity=activity,
                    reason="光照充足，不需要开灯"
                )
                
        elif activity == UserActivity.APPROACHING:
            # 预测性开灯
            if lux < zone["lux_threshold"]:
                return IntentResult(
                    action="turn_on",
                    target_device=zone["device"],
                    confidence=0.75,
                    activity=activity,
                    reason="正在靠近工作区域，预开灯"
                )
                
        elif activity == UserActivity.LEAVING:
            # 人走关灯（延迟）
            return IntentResult(
                action="turn_off",
                target_device=zone["device"],
                confidence=0.8,
                activity=activity,
                reason="正在离开区域"
            )
            
        elif activity == UserActivity.WALKING_THROUGH:
            return IntentResult(
                action="none",
                target_device="",
                confidence=0.9,
                activity=activity,
                reason="只是路过，不操作"
            )
            
        return IntentResult(
            action="none",
            target_device="",
            confidence=0.0,
            activity=activity,
            reason="意图不明确"
        )
```

---

## 4. 云端与边缘通信

### 4.1 MQTT消息格式

```yaml
# 传感器原始数据主题
homeclaw/sensors/beacon:
  user_id: "user_alice"
  beacon_uuid: "e2c56db5-dffb-48d2-b060-d0f5a71096e0"
  rssi: -65
  distance: 2.3
  room: "living_room"
  receiver_id: "ble_001"
  timestamp: 1701234567890

homeclaw/sensors/radar:
  room: "living_room"
  targets:
    - id: 1
      x: 320.5  # cm
      y: 145.2
      speed: 0.0
      valid: true
  timestamp: 1701234567890

homeclaw/sensors/environment:
  room: "living_room"
  lux: 180
  temperature: 24.5
  humidity: 58
  timestamp: 1701234567890

# 融合数据主题
homeclaw/fusion/presence:
  user_id: "user_alice"
  position: [3.2, 1.45]  # 融合后的位置
  zone: "desk"
  activity: "sitting_working"
  confidence: 0.92
  timestamp: 1701234567890

# 控制指令主题
homeclaw/control/light:
  device: "desk_lamp"
  action: "turn_on"
  brightness: 80
  triggered_by: "ai_intent"
  user_id: "user_alice"
  confidence: 0.95
```

### 4.2 边缘到云端的命令转发

```python
# edge_gateway.py
import paho.mqtt.client as mqtt
import json
import requests

class EdgeGateway:
    """边缘网关 - 连接本地传感器和云端HomeClaw"""
    
    def __init__(self, mqtt_broker, homeclaw_url):
        self.mqtt_broker = mqtt_broker
        self.homeclaw_url = homeclaw_url
        
        # 本地组件
        self.time_sync = TimeSynchronizer()
        self.position_fusion = PositionFusion()
        self.intent_engine = IntentEngine()
        
        # MQTT客户端
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        
    def _on_connect(self, client, userdata, flags, rc):
        print(f"Connected to MQTT broker: {rc}")
        # 订阅传感器主题
        client.subscribe("homeclaw/sensors/#")
        
    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = json.loads(msg.payload.decode())
        
        # 路由到对应处理器
        if "beacon" in topic:
            self._handle_beacon(payload)
        elif "radar" in topic:
            self._handle_radar(payload)
        elif "environment" in topic:
            self._handle_environment(payload)
            
        # 尝试融合数据
        self._try_fusion()
        
    def _handle_beacon(self, data):
        """处理蓝牙数据"""
        reading = SensorReading(
            sensor_type="beacon",
            timestamp=data["timestamp"],
            user_id=data["user_id"],
            position=None,  # 蓝牙只提供距离，需要三角定位
            data=data,
            confidence=0.6  # 蓝牙单独精度较低
        )
        self.time_sync.add_reading(reading)
        
    def _handle_radar(self, data):
        """处理雷达数据"""
        for target in data["targets"]:
            if target["valid"]:
                reading = SensorReading(
                    sensor_type="radar",
                    timestamp=data["timestamp"],
                    user_id=None,  # 雷达不知道身份
                    position=(target["x"]/100, target["y"]/100),  # cm to m
                    data=target,
                    confidence=0.85
                )
                self.time_sync.add_reading(reading)
                
    def _handle_environment(self, data):
        """处理环境数据"""
        self.last_environment = data
        
    def _try_fusion(self):
        """尝试数据融合和意图推理"""
        frame = self.time_sync.get_synced_frame()
        
        if not frame:
            return
            
        # 分离不同传感器数据
        beacon_readings = [r for r in frame if r.sensor_type == "beacon"]
        radar_targets = [r for r in frame if r.sensor_type == "radar"]
        
        if not beacon_readings or not radar_targets:
            return
            
        # 位置融合
        fused_pos, pos_confidence = self.position_fusion.fuse_position(
            beacon_readings, 
            [{"x": r.position[0], "y": r.position[1], "valid": True} for r in radar_targets]
        )
        
        if fused_pos is None:
            return
            
        # 获取环境数据
        lux = self.last_environment.get("lux", 500) if hasattr(self, "last_environment") else 500
        
        # 意图推理
        user_id = beacon_readings[0].user_id
        intent = self.intent_engine.infer_intent(
            user_id, fused_pos, lux, beacon_readings[0].timestamp
        )
        
        # 发布融合结果
        self._publish_fusion_result(user_id, fused_pos, intent)
        
        # 如果置信度高，发送到云端执行
        if intent.confidence > 0.7:
            self._send_to_cloud(intent)
            
    def _publish_fusion_result(self, user_id, position, intent):
        """发布融合结果到MQTT"""
        payload = {
            "user_id": user_id,
            "position": position,
            "activity": intent.activity.value,
            "intent": intent.action,
            "target_device": intent.target_device,
            "confidence": intent.confidence,
            "reason": intent.reason,
            "timestamp": int(time.time() * 1000)
        }
        self.client.publish("homeclaw/fusion/presence", json.dumps(payload))
        
    def _send_to_cloud(self, intent):
        """发送控制指令到云端HomeClaw"""
        if intent.action == "none":
            return
            
        command = {
            "device": intent.target_device,
            "action": intent.action,
            "params": {
                "brightness": 80 if intent.action == "turn_on" else 0
            },
            "source": "edge_ai",
            "confidence": intent.confidence,
            "timestamp": int(time.time() * 1000)
        }
        
        try:
            response = requests.post(
                f"{self.homeclaw_url}/api/v1/control",
                json=command,
                timeout=2
            )
            if response.status_code == 200:
                print(f"Command sent: {intent.action} {intent.target_device}")
            else:
                print(f"Failed to send command: {response.status_code}")
        except Exception as e:
            print(f"Error sending to cloud: {e}")
            # 可以在这里添加本地应急控制逻辑
            
    def run(self):
        self.client.connect(self.mqtt_broker, 1883, 60)
        self.client.loop_forever()

# 启动
if __name__ == "__main__":
    gateway = EdgeGateway(
        mqtt_broker="localhost",
        homeclaw_url="http://192.168.1.100:8080"
    )
    gateway.run()
```

---

## 5. 系统时序图

```
时间 ──────────────────────────────────────────────────────────►

用户 Alice
  │    走进房间，携带蓝牙手环
  │         │
  │         ▼
  │    [佩戴蓝牙Beacon]
  │         │
  │         │  BLE广播 (100ms间隔)
  │         │         │
  │         │         ▼
ESP32      │    扫描到Beacon
接收器     │    解析UUID → user_alice
  │         │    计算RSSI → 距离估算
  │         │         │
  │         │         │ MQTT
  │         │         ▼
  │         │    ┌─────────────┐
  │         │    │ MQTT Broker │
  │         │    └──────┬──────┘
  │         │           │
  │         │           │
LD2450     │           │
雷达       │    检测到人体
  │         │    输出坐标 (x=3.2, y=1.45)
  │         │         │
  │         │         │ MQTT
  │         │         ▼
  │         │    ┌─────────────┐
  │         └────┤ MQTT Broker │◄────┐
  │              └──────┬──────┘     │
  │                     │            │
  │                     ▼            │
树莓派/              边缘计算层      │
边缘节点         (TimeSynchronizer)  │
  │                     │            │
  │                     ▼            │
  │              时间对齐 + 数据融合   │
  │                     │            │
  │                     ▼            │
  │            PositionFusion
  │            蓝牙RSSI + 雷达坐标
  │                     │
  │                     ▼
  │            IntentEngine
  │            推理: sitting_working
  │            环境: lux=180 < 300
  │            决策: turn_on_desk_lamp
  │            置信度: 0.92
  │                     │
  │         高置信度(>0.7) │ HTTP/HTTPS
  │                     ▼
  │              ┌─────────────┐
  │              │ HomeClaw    │
  │              │ Cloud       │
  │              └──────┬──────┘
  │                     │
  │                     ▼
  │              调用Home Assistant API
  │                     │
  │                     ▼
Home         ◄─── 开灯指令
Assistant            desk_lamp on, brightness=80%
  │                     │
  │                     │ WebSocket
  │                     ▼
智能灯具    ◄─────── 灯亮 (80%亮度)
  │
  ▼
Alice 看到灯亮了，不需要任何操作

同时:
  │                     │
  │                     ▼
飞书Bot   ◄─────── 静默通知
  │         "💡 已为您打开书桌灯"
```

---

## 6. 关键参数配置

```yaml
# config/homeclaw.yaml

# 蓝牙配置
bluetooth:
  scan_interval_ms: 100      # 扫描间隔
  beacon_tx_power: -59       # 1米处RSSI参考值
  rssi_filter_alpha: 0.3     # 低通滤波系数 (平滑RSSI)
  
# 雷达配置
radar:
  model: "LD2450"
  uart_baudrate: 115200
  detection_range_m: 8.0     # 检测范围
  stationary_threshold: 0.1  # 静止判断阈值 (m/s)
  
# 融合配置
fusion:
  time_window_ms: 500        # 时间同步窗口
  bluetooth_weight: 0.3      # 蓝牙权重
  radar_weight: 0.7          # 雷达权重
  min_confidence: 0.7        # 最低执行置信度
  
# 意图推理
intent:
  stationary_time_threshold: 3.0  # 静止判断时间(秒)
  approach_distance_m: 0.5       # 接近判断距离
  leave_distance_m: 0.3          # 离开判断距离
  
# 区域定义
zones:
  desk:
    center: [3.0, 2.0]       # 房间坐标系中的位置
    radius: 0.8              # 有效半径
    device: "light.desk_lamp"
    lux_threshold: 300
    lux_target: 500          # 目标照度
```

---

这就是HomeClaw多传感器融合的完整技术实现。核心思想是：**各传感器各司其职 → 时间同步对齐 → 位置融合 → 意图推理 → 云端执行**。
