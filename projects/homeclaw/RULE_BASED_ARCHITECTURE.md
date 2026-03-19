# HomeClaw Pro - 纯规则预判系统架构

> 基于日批学习的无感式智能家居系统
> 无需TinyML，依靠规则匹配实现场景预判

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│  边缘层（树莓派）- 数据采集 + 实时预判                            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │ 传感器读取   │ → │ 特征提取    │ → │ 规则匹配    │ → 执行   │
│  │ 100ms周期   │    │ 简单计算    │    │ O(1)查找    │          │
│  └─────────────┘    └─────────────┘    └─────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↑
                              │ 每日23:00推送规则
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  OpenClaw层 - 日批学习 + 规则生成                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │ 读取今日数据 │ → │ 模式分析    │ → │ 生成规则    │ → 推送   │
│  │ SQLite      │    │ 聚类/统计   │    │ JSON规则文件 │          │
│  └─────────────┘    └─────────────┘    └─────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. 数据采集层

### 1.1 数据表结构

```sql
-- daily_logs.db
CREATE TABLE sensor_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT,              -- 蓝牙Beacon ID
    location_zone TEXT,        -- 区域：desk, sofa, bed, kitchen
    radar_distance REAL,       -- 雷达距离(m)
    radar_speed REAL,          -- 移动速度(m/s)
    pir_active BOOLEAN,        -- PIR是否触发
    env_temp REAL,             -- 温度
    env_humidity REAL,         -- 湿度
    env_light REAL,            -- 光照(lux)
    device_states TEXT,        -- JSON：{light.desk: on, climate.ac: 24}
    manual_override BOOLEAN    -- 是否手动操作
);

CREATE TABLE user_presence (
    timestamp DATETIME,
    user_id TEXT,
    zone TEXT,
    confidence REAL           -- 0-1，蓝牙信号强度换算
);
```

### 1.2 数据采集代码

```python
# edge/data_collector.py
import sqlite3
import json
import time
from datetime import datetime
from sensors import RadarReader, BLEScanner, PIRSensor, EnvSensor

class DataCollector:
    def __init__(self, db_path="data/daily_logs.db"):
        self.db = sqlite3.connect(db_path)
        self.init_db()
        
        # 传感器
        self.radar = RadarReader(port="/dev/ttyUSB0")
        self.ble = BLEScanner()
        self.pir = PIRSensor(pin=17)
        self.env = EnvSensor()
        
        # 当前状态缓存
        self.current_zone = None
        self.current_user = None
        
    def init_db(self):
        """初始化数据库表"""
        cursor = self.db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                location_zone TEXT,
                radar_distance REAL,
                radar_speed REAL,
                pir_active BOOLEAN,
                env_temp REAL,
                env_humidity REAL,
                env_light REAL,
                device_states TEXT,
                manual_override BOOLEAN DEFAULT 0
            )
        """)
        self.db.commit()
        
    def read_sensors(self):
        """读取所有传感器数据"""
        # 雷达数据
        radar_data = self.radar.read()
        
        # 蓝牙Beacon（身份识别）
        beacons = self.ble.scan(duration=1)
        user_id = self.identify_user(beacons)
        
        # 确定区域（基于雷达距离和预设区域坐标）
        zone = self.locate_zone(radar_data['distance'], radar_data['angle'])
        
        return {
            'timestamp': datetime.now(),
            'user_id': user_id,
            'location_zone': zone,
            'radar_distance': radar_data['distance'],
            'radar_speed': radar_data['speed'],
            'pir_active': self.pir.read(),
            'env_temp': self.env.temperature(),
            'env_humidity': self.env.humidity(),
            'env_light': self.env.light()
        }
        
    def identify_user(self, beacons):
        """根据蓝牙Beacon识别用户"""
        USER_BEACONS = {
            'AC:23:3F:A4:12:89': 'alice',
            'BE:45:1C:D8:33:91': 'bob'
        }
        
        for beacon in beacons:
            if beacon['mac'] in USER_BEACONS and beacon['rssi'] > -70:
                return USER_BEACONS[beacon['mac']]
        return 'unknown'
        
    def locate_zone(self, distance, angle):
        """基于距离和角度确定区域（简单几何判断）"""
        # 预设区域坐标（基于房间布局）
        ZONES = {
            'desk': {'center': (2.0, 1.5), 'radius': 1.0},
            'sofa': {'center': (4.0, 3.0), 'radius': 1.2},
            'bed': {'center': (1.0, 4.0), 'radius': 1.5},
            'kitchen': {'center': (5.0, 1.0), 'radius': 1.5}
        }
        
        # 极坐标转直角坐标
        x = distance * cos(radians(angle))
        y = distance * sin(radians(angle))
        
        # 找到最近的区域
        for zone_name, zone_info in ZONES.items():
            zx, zy = zone_info['center']
            dist = sqrt((x-zx)**2 + (y-zy)**2)
            if dist < zone_info['radius']:
                return zone_name
        return 'unknown'
        
    def get_device_states(self):
        """从Home Assistant获取当前设备状态"""
        # 调用HA API获取设备状态
        import requests
        response = requests.get(
            f"{HA_URL}/api/states",
            headers={"Authorization": f"Bearer {HA_TOKEN}"}
        )
        states = {}
        for entity in response.json():
            states[entity['entity_id']] = entity['state']
        return states
        
    def log(self, sensor_data, device_states, manual_override=False):
        """记录数据到数据库"""
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO sensor_logs 
            (timestamp, user_id, location_zone, radar_distance, radar_speed,
             pir_active, env_temp, env_humidity, env_light, device_states, manual_override)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sensor_data['timestamp'],
            sensor_data['user_id'],
            sensor_data['location_zone'],
            sensor_data['radar_distance'],
            sensor_data['radar_speed'],
            sensor_data['pir_active'],
            sensor_data['env_temp'],
            sensor_data['env_humidity'],
            sensor_data['env_light'],
            json.dumps(device_states),
            manual_override
        ))
        self.db.commit()
        
    def run(self, interval=1.0):
        """主循环：每秒记录一次"""
        print("[DataCollector] 启动数据采集...")
        while True:
            try:
                sensor_data = self.read_sensors()
                device_states = self.get_device_states()
                self.log(sensor_data, device_states)
                
                # 调试输出
                print(f"[{sensor_data['timestamp']}] {sensor_data['user_id']} @ {sensor_data['location_zone']}")
                
            except Exception as e:
                print(f"[Error] 数据采集失败: {e}")
                
            time.sleep(interval)

if __name__ == "__main__":
    collector = DataCollector()
    collector.run()
```

---

## 2. 实时预判层（规则引擎）

### 2.1 规则文件格式

```json
{
  "version": "2024-03-14",
  "generated_by": "openclaw_daily_learning",
  "rules": [
    {
      "id": "rule_001",
      "name": "早晨工作模式",
      "priority": 100,
      "conditions": {
        "time_range": {"start": "08:00", "end": "10:00"},
        "location": "desk",
        "weekdays": [1, 2, 3, 4, 5]
      },
      "confidence": 0.85,
      "actions": [
        {"entity_id": "light.desk", "service": "turn_on", "brightness": 80, "color_temp": 4000},
        {"entity_id": "climate.ac", "service": "set_temperature", "temperature": 24}
      ],
      "notification": "已为您开启专注模式"
    },
    {
      "id": "rule_002", 
      "name": "晚间休闲模式",
      "priority": 90,
      "conditions": {
        "time_range": {"start": "20:00", "end": "23:00"},
        "location": "sofa",
        "env_light": {"operator": "<", "value": 100}
      },
      "confidence": 0.78,
      "actions": [
        {"entity_id": "light.living_room", "service": "turn_on", "brightness": 30, "color_temp": 2700},
        {"entity_id": "media_player.speaker", "service": "play_media", "media_content_id": "lofi_playlist"}
      ]
    },
    {
      "id": "rule_003",
      "name": "睡眠准备",
      "priority": 95,
      "conditions": {
        "time_range": {"start": "22:00", "end": "24:00"},
        "location": "bed",
        "duration_minutes": 5
      },
      "confidence": 0.82,
      "actions": [
        {"entity_id": "light.bedroom", "service": "turn_off"},
        {"entity_id": "light.nightlight", "service": "turn_on", "brightness": 5},
        {"entity_id": "climate.ac", "service": "set_temperature", "temperature": 26}
      ]
    }
  ],
  "user_preferences": {
    "alice": {
      "preferred_temp_work": 24,
      "preferred_temp_sleep": 26,
      "light_sensitivity": "medium"
    }
  },
  "conflict_resolution": {
    "priority_order": ["sleep", "work", "leisure", "cooking"]
  }
}
```

### 2.2 规则引擎代码

```python
# edge/rule_engine.py
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests

class RuleEngine:
    def __init__(self, rules_path="config/rules.json"):
        self.rules_path = rules_path
        self.rules = []
        self.user_presence = {}  # 当前用户位置缓存
        self.zone_entry_time = {}  # 进入区域时间
        self.last_execution = {}   # 上次执行规则（避免重复触发）
        self.load_rules()
        
    def load_rules(self):
        """加载规则文件"""
        try:
            with open(self.rules_path, 'r') as f:
                data = json.load(f)
                self.rules = data.get('rules', [])
                self.user_prefs = data.get('user_preferences', {})
                self.conflict_config = data.get('conflict_resolution', {})
            print(f"[RuleEngine] 加载了 {len(self.rules)} 条规则")
        except FileNotFoundError:
            print("[RuleEngine] 规则文件不存在，等待OpenClaw生成...")
            self.rules = []
            
    def check_condition(self, condition: Dict, context: Dict) -> bool:
        """检查单个条件是否满足"""
        now = datetime.now()
        
        # 时间范围
        if 'time_range' in condition:
            start = datetime.strptime(condition['time_range']['start'], "%H:%M").time()
            end = datetime.strptime(condition['time_range']['end'], "%H:%M").time()
            if not (start <= now.time() <= end):
                return False
                
        # 星期
        if 'weekdays' in condition:
            if now.weekday() + 1 not in condition['weekdays']:
                return False
                
        # 位置
        if 'location' in condition:
            if context.get('location') != condition['location']:
                return False
                
        # 持续时间（在区域停留多久）
        if 'duration_minutes' in condition:
            zone = context.get('location')
            user = context.get('user_id')
            key = f"{user}_{zone}"
            if key not in self.zone_entry_time:
                return False
            duration = (now - self.zone_entry_time[key]).total_seconds() / 60
            if duration < condition['duration_minutes']:
                return False
                
        # 环境条件
        if 'env_light' in condition:
            op = condition['env_light']['operator']
            val = condition['env_light']['value']
            actual = context.get('env_light', 0)
            if op == '<' and actual >= val:
                return False
            if op == '>' and actual <= val:
                return False
                
        return True
        
    def evaluate_rules(self, context: Dict) -> List[Dict]:
        """评估所有规则，返回匹配的规则列表"""
        matched = []
        
        for rule in self.rules:
            if self.check_condition(rule['conditions'], context):
                # 检查冷却时间（避免重复触发）
                rule_id = rule['id']
                if rule_id in self.last_execution:
                    cooldown = timedelta(minutes=30)  # 30分钟冷却
                    if datetime.now() - self.last_execution[rule_id] < cooldown:
                        continue
                matched.append(rule)
                
        # 按优先级排序
        matched.sort(key=lambda x: x.get('priority', 0), reverse=True)
        return matched
        
    def resolve_conflicts(self, matched_rules: List[Dict], context: Dict) -> Optional[Dict]:
        """解决规则冲突"""
        if not matched_rules:
            return None
            
        # 单用户：取优先级最高
        if len(context.get('users', [])) <= 1:
            return matched_rules[0]
            
        # 多用户冲突：根据活动类型优先级
        priority_order = self.conflict_config.get('priority_order', [])
        
        # 找到优先级最高的活动类型
        for activity in priority_order:
            for rule in matched_rules:
                if activity in rule['name'].lower():
                    return rule
                    
        return matched_rules[0]
        
    def execute_actions(self, rule: Dict, user_id: str):
        """执行规则动作"""
        print(f"[RuleEngine] 执行规则: {rule['name']} (置信度: {rule['confidence']})")
        
        for action in rule['actions']:
            try:
                self.call_ha_service(action)
            except Exception as e:
                print(f"[Error] 执行动作失败: {action}, 错误: {e}")
                
        # 记录执行时间
        self.last_execution[rule['id']] = datetime.now()
        
        # 发送通知
        if 'notification' in rule:
            self.send_notification(user_id, rule['notification'])
            
    def call_ha_service(self, action: Dict):
        """调用Home Assistant服务"""
        domain = action['entity_id'].split('.')[0]
        service = action['service']
        
        url = f"{HA_URL}/api/services/{domain}/{service}"
        headers = {
            "Authorization": f"Bearer {HA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # 构建payload
        payload = {"entity_id": action['entity_id']}
        for key in ['brightness', 'color_temp', 'temperature', 'media_content_id']:
            if key in action:
                payload[key] = action[key]
                
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print(f"  ✓ {action['entity_id']} -> {service}")
        else:
            print(f"  ✗ {action['entity_id']} 失败: {response.text}")
            
    def send_notification(self, user_id: str, message: str):
        """发送飞书通知（通过OpenClaw）"""
        # 调用OpenClaw的消息接口
        try:
            requests.post(
                "http://localhost:18789/webhook/notify",
                json={"user": user_id, "message": message}
            )
        except:
            pass  # 通知失败不影响主逻辑
            
    def update_presence(self, user_id: str, zone: str):
        """更新用户位置，记录进入时间"""
        if user_id not in self.user_presence or self.user_presence[user_id] != zone:
            # 区域变化
            self.zone_entry_time[f"{user_id}_{zone}"] = datetime.now()
            self.user_presence[user_id] = zone
            print(f"[Presence] {user_id} 进入 {zone}")
            
    def run(self, data_collector):
        """主循环：与数据采集联动"""
        print("[RuleEngine] 启动规则引擎...")
        
        while True:
            try:
                # 获取最新传感器数据
                sensor_data = data_collector.read_sensors()
                user_id = sensor_data['user_id']
                zone = sensor_data['location_zone']
                
                # 更新位置状态
                self.update_presence(user_id, zone)
                
                # 构建上下文
                context = {
                    'user_id': user_id,
                    'location': zone,
                    'users': list(self.user_presence.keys()),
                    'env_light': sensor_data['env_light'],
                    'env_temp': sensor_data['env_temp']
                }
                
                # 评估规则
                matched = self.evaluate_rules(context)
                if matched:
                    selected = self.resolve_conflicts(matched, context)
                    if selected and selected['confidence'] > 0.7:  # 置信度阈值
                        self.execute_actions(selected, user_id)
                        
            except Exception as e:
                print(f"[Error] 规则引擎错误: {e}")
                
            time.sleep(1)  # 每秒评估一次

if __name__ == "__main__":
    from data_collector import DataCollector
    
    collector = DataCollector()
    engine = RuleEngine()
    engine.run(collector)
```

---

## 3. OpenClaw日批学习层

### 3.1 Skill定义

```markdown
# HomeClaw Daily Learning Skill

## 功能
每日分析家庭传感器数据，学习用户习惯，生成预判规则。

## 触发
定时任务：每天 23:00 运行

## 数据输入
读取 SQLite: `data/daily_logs.db`

## 分析流程

### 步骤1：数据清洗
- 去除异常值（如单次短暂停留<2分钟）
- 标记手动操作（manual_override=1）
- 合并连续相同区域记录

### 步骤2：模式提取
- 时间聚类：什么时间段常在什么区域
- 设备关联：该区域通常开启什么设备
- 用户偏好：温度、亮度偏好

### 步骤3：规则生成
- 生成 if-then 规则
- 计算置信度（出现频率）
- 处理冲突（多用户场景）

### 步骤4：推送规则
- 生成 rules.json
- 推送到边缘层
- 发送学习报告到飞书

## 输出
- `config/rules.json` - 新规则文件
- 飞书通知 - 今日学习总结
```

### 3.2 学习算法实现

```python
# .tools/daily_learning.py
import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

class DailyLearning:
    def __init__(self, db_path="data/daily_logs.db"):
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        
    def fetch_today_data(self):
        """获取今日数据"""
        cursor = self.db.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT * FROM sensor_logs 
            WHERE date(timestamp) = ?
            ORDER BY timestamp
        """, (today,))
        return [dict(row) for row in cursor.fetchall()]
        
    def extract_patterns(self, data):
        """提取行为模式"""
        patterns = defaultdict(lambda: defaultdict(list))
        
        # 按用户和区域聚合
        for record in data:
            user = record['user_id']
            zone = record['location_zone']
            hour = datetime.fromisoformat(record['timestamp']).hour
            
            # 记录每个时段的区域分布
            patterns[user][hour].append(zone)
            
        # 统计最常见的区域-时段组合
        user_patterns = {}
        for user, hour_zones in patterns.items():
            user_patterns[user] = {}
            for hour, zones in hour_zones.items():
                # 找出现最频繁的区域
                zone_counts = defaultdict(int)
                for z in zones:
                    zone_counts[z] += 1
                most_common = max(zone_counts.items(), key=lambda x: x[1])
                confidence = most_common[1] / len(zones)
                
                if confidence > 0.6:  # 60%以上时间在该区域
                    user_patterns[user][hour] = {
                        'zone': most_common[0],
                        'confidence': confidence
                    }
                    
        return user_patterns
        
    def analyze_device_preferences(self, data):
        """分析设备使用偏好"""
        prefs = defaultdict(lambda: defaultdict(list))
        
        for record in data:
            zone = record['location_zone']
            devices = json.loads(record['device_states'])
            
            # 记录该区域常用的设备设置
            for entity_id, state in devices.items():
                if state in ['on', 'playing'] or isinstance(state, (int, float)):
                    prefs[zone][entity_id].append(state)
                    
        # 计算平均值或最常用值
        preferences = {}
        for zone, devices in prefs.items():
            preferences[zone] = {}
            for entity_id, values in devices.items():
                if values:
                    if isinstance(values[0], (int, float)):
                        preferences[zone][entity_id] = np.mean(values)
                    else:
                        preferences[zone][entity_id] = max(set(values), key=values.count)
                        
        return preferences
        
    def generate_rules(self, patterns, preferences):
        """生成规则"""
        rules = []
        rule_id = 0
        
        SCENE_MAPPING = {
            'desk': '工作',
            'sofa': '休闲',
            'bed': '睡眠',
            'kitchen': '烹饪'
        }
        
        for user, hour_pattern in patterns.items():
            # 按时段分组（连续小时合并）
            time_ranges = self._merge_hours(hour_pattern)
            
            for time_range in time_ranges:
                start_hour = time_range['start']
                end_hour = time_range['end']
                zone = time_range['zone']
                confidence = time_range['confidence']
                
                if zone == 'unknown':
                    continue
                    
                # 生成规则
                rule_id += 1
                rule = {
                    'id': f'rule_{rule_id:03d}',
                    'name': f"{SCENE_MAPPING.get(zone, zone)}模式",
                    'priority': int(confidence * 100),
                    'conditions': {
                        'time_range': {
                            'start': f'{start_hour:02d}:00',
                            'end': f'{end_hour:02d}:00'
                        },
                        'location': zone,
                        'weekdays': [1, 2, 3, 4, 5]  # 默认工作日
                    },
                    'confidence': round(confidence, 2),
                    'actions': self._generate_actions(zone, preferences.get(zone, {})),
                    'notification': f"检测到{SCENE_MAPPING.get(zone, zone)}场景，已自动调整环境"
                }
                rules.append(rule)
                
        return rules
        
    def _merge_hours(self, hour_pattern):
        """合并连续的小时段"""
        if not hour_pattern:
            return []
            
        hours = sorted(hour_pattern.keys())
        ranges = []
        current_start = hours[0]
        current_zone = hour_pattern[hours[0]]['zone']
        current_confidence = hour_pattern[hours[0]]['confidence']
        
        for i in range(1, len(hours)):
            if hours[i] == hours[i-1] + 1 and hour_pattern[hours[i]]['zone'] == current_zone:
                # 连续且同区域
                current_confidence = min(current_confidence, hour_pattern[hours[i]]['confidence'])
            else:
                # 不连续或不同区域，结束当前段
                ranges.append({
                    'start': current_start,
                    'end': hours[i-1] + 1,
                    'zone': current_zone,
                    'confidence': current_confidence
                })
                current_start = hours[i]
                current_zone = hour_pattern[hours[i]]['zone']
                current_confidence = hour_pattern[hours[i]]['confidence']
                
        # 添加最后一段
        ranges.append({
            'start': current_start,
            'end': hours[-1] + 1,
            'zone': current_zone,
            'confidence': current_confidence
        })
        
        return ranges
        
    def _generate_actions(self, zone, prefs):
        """根据区域和偏好生成动作"""
        actions = []
        
        # 基础设备映射
        ZONE_DEVICES = {
            'desk': [
                {'entity_id': 'light.desk', 'service': 'turn_on', 'brightness': 80, 'color_temp': 4000},
                {'entity_id': 'climate.ac', 'service': 'set_temperature', 'temperature': 24}
            ],
            'sofa': [
                {'entity_id': 'light.living_room', 'service': 'turn_on', 'brightness': 30, 'color_temp': 2700}
            ],
            'bed': [
                {'entity_id': 'light.bedroom', 'service': 'turn_off'},
                {'entity_id': 'light.nightlight', 'service': 'turn_on', 'brightness': 5},
                {'entity_id': 'climate.ac', 'service': 'set_temperature', 'temperature': 26}
            ]
        }
        
        base_actions = ZONE_DEVICES.get(zone, [])
        
        # 应用学习到的偏好
        for action in base_actions:
            entity = action['entity_id']
            if entity in prefs:
                if 'brightness' in action and isinstance(prefs[entity], (int, float)):
                    action['brightness'] = int(prefs[entity])
                if 'temperature' in action and isinstance(prefs[entity], (int, float)):
                    action['temperature'] = int(prefs[entity])
            actions.append(action)
            
        return actions
        
    def save_rules(self, rules, output_path="config/rules.json"):
        """保存规则到文件"""
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        data = {
            'version': datetime.now().strftime("%Y-%m-%d"),
            'generated_by': 'openclaw_daily_learning',
            'rules': rules,
            'metadata': {
                'total_rules': len(rules),
                'generated_at': datetime.now().isoformat()
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"[DailyLearning] 生成了 {len(rules)} 条规则")
        
    def generate_report(self, patterns, rules):
        """生成学习报告"""
        report = "📊 今日学习报告\n\n"
        report += f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        
        report += "发现的行为模式:\n"
        for user, hour_pattern in patterns.items():
            report += f"\n{user}:\n"
            for hour, info in sorted(hour_pattern.items()):
                report += f"  {hour:02d}:00 - 常在 {info['zone']} (置信度{info['confidence']:.0%})\n"
                
        report += f"\n生成了 {len(rules)} 条自动规则:\n"
        for rule in rules:
            report += f"  • {rule['name']}: {rule['conditions']['time_range']['start']}-{rule['conditions']['time_range']['end']} @ {rule['conditions']['location']}\n"
            
        return report
        
    def run(self):
        """主流程"""
        print("[DailyLearning] 开始每日学习...")
        
        # 1. 获取数据
        data = self.fetch_today_data()
        if not data:
            print("[DailyLearning] 今日无数据")
            return
            
        print(f"[DailyLearning] 获取到 {len(data)} 条记录")
        
        # 2. 提取模式
        patterns = self.extract_patterns(data)
        
        # 3. 分析偏好
        preferences = self.analyze_device_preferences(data)
        
        # 4. 生成规则
        rules = self.generate_rules(patterns, preferences)
        
        # 5. 保存规则
        self.save_rules(rules)
        
        # 6. 生成报告
        report = self.generate_report(patterns, rules)
        print(report)
        
        # 7. 发送到飞书（通过OpenClaw）
        self.notify_feishu(report)
        
        return rules
        
    def notify_feishu(self, message):
        """发送飞书通知"""
        # 这里调用OpenClaw的消息发送功能
        # 实际实现取决于OpenClaw的接口
        try:
            import requests
            requests.post(
                "http://localhost:18789/webhook/notify",
                json={"message": message}
            )
        except Exception as e:
            print(f"[DailyLearning] 通知发送失败: {e}")

if __name__ == "__main__":
    learner = DailyLearning()
    learner.run()
```

---

## 4. 系统集成

### 4.1 目录结构

```
homeclaw-pro/
├── edge/                          # 边缘层（树莓派）
│   ├── data_collector.py         # 数据采集
│   ├── rule_engine.py            # 规则引擎
│   ├── sensors/                  # 传感器驱动
│   │   ├── __init__.py
│   │   ├── radar.py              # 毫米波雷达
│   │   ├── ble.py                # 蓝牙扫描
│   │   ├── pir.py                # 红外传感器
│   │   └── env.py                # 环境传感器
│   ├── config/                   # 配置文件
│   │   └── rules.json            # 生成的规则
│   ├── data/                     # 数据库
│   │   └── daily_logs.db
│   └── main.py                   # 边缘层入口
│
├── openclaw/                      # OpenClaw层
│   ├── skills/
│   │   └── homeclaw_learning/    # 日批学习Skill
│   │       └── SKILL.md
│   └── tools/
│       └── daily_learning.py     # 学习算法
│
├── homeassistant/                 # HA配置
│   └── automations.yaml          # 基础自动化（备份）
│
├── docs/
│   └── ARCHITECTURE.md
│
└── README.md
```

### 4.2 边缘层入口

```python
# edge/main.py
import threading
from data_collector import DataCollector
from rule_engine import RuleEngine

def main():
    """边缘层主程序"""
    print("="*50)
    print("HomeClaw Pro Edge - 启动")
    print("="*50)
    
    # 初始化组件
    collector = DataCollector()
    engine = RuleEngine()
    
    # 启动数据采集线程
    collector_thread = threading.Thread(
        target=collector.run,
        kwargs={'interval': 1.0}
    )
    collector_thread.daemon = True
    collector_thread.start()
    
    # 启动规则引擎（主线程）
    try:
        engine.run(collector)
    except KeyboardInterrupt:
        print("\n[Main] 系统关闭")

if __name__ == "__main__":
    main()
```

### 4.3 OpenClaw Cron配置

```yaml
# .openclaw/cron.yaml
jobs:
  daily_learning:
    name: "每日学习习惯分析"
    schedule: "0 23 * * *"  # 每天23:00
    command: "python3 .tools/daily_learning.py"
    working_dir: "/home/pi/homeclaw-pro"
    
  weekly_report:
    name: "每周学习报告"
    schedule: "0 9 * * 1"  # 每周一9:00
    command: "python3 .tools/weekly_report.py"
```

---

## 5. 运行流程

### 第一天（冷启动）

```
09:00 系统启动
  └─> 数据采集开始，只记录不预判
  └─> 规则文件为空，无自动操作
  
23:00 OpenClaw日批学习
  └─> 分析今日数据
  └─> 发现：09:00-12:00 alice常在desk
  └─> 生成规则1：早晨工作模式
  └─> 推送规则到边缘层
  
次日 规则生效
  └─> 09:00 alice到desk
  └─> 规则匹配，自动开灯、调温
  └─> 飞书通知："已为您开启专注模式"
```

### 第七天（模式成熟）

```
23:00 OpenClaw学习
  └─> 分析7天数据
  └─> 发现稳定模式：
      • 工作日08:00-10:00 desk（工作）
      • 工作日12:00-13:00 kitchen（午餐）
      • 每日20:00-22:00 sofa（休闲）
      • 工作日23:00后 bed（睡眠）
  └─> 生成4条高置信度规则（>80%）
  └─> 学习alice偏好：工作温度24°，睡眠温度26°
```

---

## 6. 关键设计决策

| 决策 | 选择 | 理由 |
|-----|------|------|
| 实时预判 vs 日批学习 | 日批学习 | 符合OpenClaw架构，计算资源可控 |
| TinyML vs 规则引擎 | 规则引擎 | 无需训练数据，可解释，边际收益足够 |
| 云端推理 vs 本地规则 | 本地规则 | 延迟低，隐私保护，无网络依赖 |
| 单人 vs 多人支持 | 多人（基础） | 规则冲突处理简单，优先级排序即可 |
| 自动执行 vs 询问确认 | 自动执行（高置信度） | 置信度>80%自动，否则询问 |

---

**这是完整的纯规则方案，不需要TinyML，依靠日批学习+规则匹配实现无感智能。**

要我补充传感器驱动的具体实现，或者HA集成的详细配置吗？