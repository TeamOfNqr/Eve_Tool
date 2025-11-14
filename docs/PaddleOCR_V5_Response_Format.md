# PaddleOCR v5 返回结果格式说明

## 概述
本文档详细说明 PaddleOCR v5 OCR识别结果的JSON格式标准，便于其他程序调用和解析。

## JSON 结构总览

```json
{
    "input_path": string,
    "page_index": number | null,
    "model_settings": object,
    "dt_polys": array,
    "text_det_params": object,
    "text_type": string,
    "textline_orientation_angles": array,
    "text_rec_score_thresh": number,
    "return_word_box": boolean,
    "rec_texts": array,
    "rec_scores": array,
    "rec_polys": array,
    "rec_boxes": array
}
```

---

## 字段详细说明

### 1. `input_path` (string)
- **类型**: 字符串
- **说明**: 输入图片的路径或文件名
- **示例**: `"general_ocr_002.png"`

### 2. `page_index` (number | null)
- **类型**: 整数或null
- **说明**: 页面索引（多页文档时使用，单页时为null）
- **示例**: `null` 或 `0`, `1`, `2`...

### 3. `model_settings` (object)
- **类型**: 对象
- **说明**: 模型配置参数
- **结构**:
  ```json
  {
      "use_doc_preprocessor": boolean,      // 是否使用文档预处理器
      "use_textline_orientation": boolean   // 是否使用文本行方向检测
  }
  ```
- **示例**:
  ```json
  {
      "use_doc_preprocessor": false,
      "use_textline_orientation": false
  }
  ```

### 4. `dt_polys` (array)
- **类型**: 三维数组
- **说明**: 文本检测阶段检测到的多边形框坐标（检测框）
- **格式**: `[[[x1, y1], [x2, y2], [x3, y3], [x4, y4]], ...]`
  - 每个元素是一个四边形，由4个点组成
  - 每个点是 `[x, y]` 坐标对
  - 通常按左上、右上、右下、左下的顺序排列
- **示例**:
  ```json
  [
      [[152, 22], [357, 16], [358, 71], [153, 77]],
      [[419, 20], [659, 14], [660, 61], [420, 66]]
  ]
  ```

### 5. `text_det_params` (object)
- **类型**: 对象
- **说明**: 文本检测参数配置
- **结构**:
  ```json
  {
      "limit_side_len": number,      // 限制边长（像素）
      "limit_type": string,           // 限制类型："min" 或 "max"
      "thresh": number,               // 阈值（0-1之间）
      "max_side_limit": number,       // 最大边长限制
      "box_thresh": number,           // 框阈值（0-1之间）
      "unclip_ratio": number          // 反裁剪比例
  }
  ```
- **示例**:
  ```json
  {
      "limit_side_len": 64,
      "limit_type": "min",
      "thresh": 0.3,
      "max_side_limit": 4000,
      "box_thresh": 0.6,
      "unclip_ratio": 1.5
  }
  ```

### 6. `text_type` (string)
- **类型**: 字符串
- **说明**: 文本类型标识
- **可能值**: `"general"`（通用文本）、`"doc"`（文档）等
- **示例**: `"general"`

### 7. `textline_orientation_angles` (array)
- **类型**: 一维数组（整数）
- **说明**: 每个文本行的方向角度（度）
  - `-1` 表示未检测或未使用方向检测
  - 其他值表示文本行的旋转角度
- **长度**: 与 `dt_polys`、`rec_texts` 等数组长度相同
- **示例**: `[-1, -1, -1, ...]`

### 8. `text_rec_score_thresh` (number)
- **类型**: 浮点数
- **说明**: 文本识别置信度阈值（0-1之间）
- **示例**: `0.0`（表示不过滤，返回所有识别结果）

### 9. `return_word_box` (boolean)
- **类型**: 布尔值
- **说明**: 是否返回单词级别的框（当前为false，只返回文本行级别）
- **示例**: `false`

### 10. `rec_texts` (array)
- **类型**: 一维数组（字符串）
- **说明**: 识别出的文本内容列表
- **长度**: 与 `dt_polys`、`rec_scores`、`rec_polys` 等数组长度相同
- **索引对应**: `rec_texts[i]` 对应 `rec_scores[i]`、`rec_polys[i]`、`rec_boxes[i]`
- **示例**:
  ```json
  [
      "登机牌",
      "BOARDING",
      "PASS",
      "日期DATE"
  ]
  ```

### 11. `rec_scores` (array)
- **类型**: 一维数组（浮点数）
- **说明**: 每个文本的识别置信度分数（0-1之间，越接近1表示置信度越高）
- **长度**: 与 `rec_texts` 数组长度相同
- **索引对应**: `rec_scores[i]` 对应 `rec_texts[i]`
- **示例**:
  ```json
  [
      0.997111976146698,
      0.9802993535995483,
      0.9757216572761536
  ]
  ```

### 12. `rec_polys` (array)
- **类型**: 三维数组
- **说明**: 文本识别阶段的多边形框坐标（识别框，通常与 `dt_polys` 相同或相近）
- **格式**: 与 `dt_polys` 相同，`[[[x1, y1], [x2, y2], [x3, y3], [x4, y4]], ...]`
- **长度**: 与 `rec_texts` 数组长度相同
- **索引对应**: `rec_polys[i]` 对应 `rec_texts[i]`
- **示例**:
  ```json
  [
      [[152, 22], [357, 16], [358, 71], [153, 77]],
      [[419, 20], [659, 14], [660, 61], [420, 66]]
  ]
  ```

### 13. `rec_boxes` (array)
- **类型**: 二维数组
- **说明**: 文本识别阶段的矩形框坐标（轴对齐边界框，AABB格式）
- **格式**: `[[x_min, y_min, x_max, y_max], ...]`
  - `[x_min, y_min, x_max, y_max]` 表示左上角和右下角坐标
- **长度**: 与 `rec_texts` 数组长度相同
- **索引对应**: `rec_boxes[i]` 对应 `rec_texts[i]`
- **示例**:
  ```json
  [
      [152, 16, 358, 77],
      [419, 14, 660, 66]
  ]
  ```

---

## 数据关联关系

### 数组索引对应关系
所有结果数组的长度相同，通过索引关联：

```
索引 i 对应的完整信息：
- 文本内容: rec_texts[i]
- 置信度: rec_scores[i]
- 多边形框: rec_polys[i] 或 dt_polys[i]
- 矩形框: rec_boxes[i]
- 方向角度: textline_orientation_angles[i]
```

### 示例：获取第0个文本的完整信息
```python
index = 0
text = result["rec_texts"][index]           # "登机牌"
score = result["rec_scores"][index]         # 0.997111976146698
poly = result["rec_polys"][index]           # [[152, 22], [357, 16], [358, 71], [153, 77]]
box = result["rec_boxes"][index]            # [152, 16, 358, 77]
angle = result["textline_orientation_angles"][index]  # -1
```

---

## 坐标系统说明

### 坐标系
- **原点**: 图片左上角为 (0, 0)
- **X轴**: 向右为正方向
- **Y轴**: 向下为正方向

### 多边形框 (poly) 格式
- 4个点组成一个四边形
- 点的顺序通常是：左上 → 右上 → 右下 → 左下
- 格式：`[[x1, y1], [x2, y2], [x3, y3], [x4, y4]]`

### 矩形框 (box) 格式
- 轴对齐边界框（Axis-Aligned Bounding Box）
- 格式：`[x_min, y_min, x_max, y_max]`
- `x_min, y_min`: 左上角坐标
- `x_max, y_max`: 右下角坐标

---

## 使用示例

### Python 解析示例
```python
import json

# 读取JSON结果
with open('general_ocr_002_res.json', 'r', encoding='utf-8') as f:
    result = json.load(f)

# 获取识别结果数量
num_texts = len(result['rec_texts'])
print(f"识别到 {num_texts} 个文本区域")

# 遍历所有识别结果
for i in range(num_texts):
    text = result['rec_texts'][i]
    score = result['rec_scores'][i]
    box = result['rec_boxes'][i]
    poly = result['rec_polys'][i]
    
    print(f"\n文本 {i+1}:")
    print(f"  内容: {text}")
    print(f"  置信度: {score:.4f}")
    print(f"  矩形框: {box}")
    print(f"  多边形框: {poly}")

# 过滤高置信度结果
high_confidence_texts = [
    (result['rec_texts'][i], result['rec_scores'][i])
    for i in range(num_texts)
    if result['rec_scores'][i] > 0.9
]
print(f"\n高置信度文本 (>0.9): {len(high_confidence_texts)} 个")
```

### JavaScript 解析示例
```javascript
// 读取JSON结果
const fs = require('fs');
const result = JSON.parse(fs.readFileSync('general_ocr_002_res.json', 'utf8'));

// 获取识别结果数量
const numTexts = result.rec_texts.length;
console.log(`识别到 ${numTexts} 个文本区域`);

// 遍历所有识别结果
result.rec_texts.forEach((text, i) => {
    const score = result.rec_scores[i];
    const box = result.rec_boxes[i];
    const poly = result.rec_polys[i];
    
    console.log(`\n文本 ${i+1}:`);
    console.log(`  内容: ${text}`);
    console.log(`  置信度: ${score.toFixed(4)}`);
    console.log(`  矩形框: [${box.join(', ')}]`);
});

// 过滤高置信度结果
const highConfidenceTexts = result.rec_texts
    .map((text, i) => ({ text, score: result.rec_scores[i] }))
    .filter(item => item.score > 0.9);
console.log(`\n高置信度文本 (>0.9): ${highConfidenceTexts.length} 个`);
```

---

## 注意事项

1. **数组长度一致性**: 所有结果数组（`rec_texts`、`rec_scores`、`rec_polys`、`rec_boxes`、`textline_orientation_angles`）的长度必须相同，通过索引关联。

2. **坐标格式**: 
   - `rec_polys` 和 `dt_polys` 使用多边形格式（4个点）
   - `rec_boxes` 使用矩形格式（4个数值：x_min, y_min, x_max, y_max）

3. **置信度阈值**: `text_rec_score_thresh` 为0.0时表示不过滤，所有识别结果都会返回。

4. **方向角度**: `textline_orientation_angles` 为-1时表示未使用方向检测功能。

5. **编码**: JSON文件应使用UTF-8编码，以支持中文字符。

---

## 版本信息
- **OCR引擎**: PaddleOCR v5
- **文档版本**: 1.0
- **最后更新**: 基于实际返回结果分析

