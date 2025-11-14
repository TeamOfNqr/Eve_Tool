#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PaddleOCR v5 结果解析示例
用于解析和操作 PaddleOCR v5 返回的 JSON 结果
"""

import json
from typing import Dict, List, Tuple, Optional


class PaddleOCRResult:
    """PaddleOCR v5 结果解析类"""
    
    def __init__(self, json_path: str):
        """
        初始化，加载JSON结果文件
        
        Args:
            json_path: JSON结果文件路径
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self._validate()
    
    def _validate(self):
        """验证数据完整性"""
        arrays = [
            'rec_texts', 'rec_scores', 'rec_polys', 
            'rec_boxes', 'textline_orientation_angles', 'dt_polys'
        ]
        lengths = [len(self.data.get(arr, [])) for arr in arrays]
        
        if len(set(lengths)) > 1:
            raise ValueError(f"数组长度不一致: {dict(zip(arrays, lengths))}")
    
    @property
    def input_path(self) -> str:
        """获取输入图片路径"""
        return self.data['input_path']
    
    @property
    def text_type(self) -> str:
        """获取文本类型"""
        return self.data['text_type']
    
    @property
    def num_texts(self) -> int:
        """获取识别到的文本数量"""
        return len(self.data['rec_texts'])
    
    def get_text(self, index: int) -> Dict:
        """
        获取指定索引的完整文本信息
        
        Args:
            index: 文本索引
            
        Returns:
            包含文本、置信度、坐标等信息的字典
        """
        if index < 0 or index >= self.num_texts:
            raise IndexError(f"索引 {index} 超出范围 [0, {self.num_texts-1}]")
        
        return {
            'index': index,
            'text': self.data['rec_texts'][index],
            'score': self.data['rec_scores'][index],
            'box': self.data['rec_boxes'][index],  # [x_min, y_min, x_max, y_max]
            'poly': self.data['rec_polys'][index],  # [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
            'angle': self.data['textline_orientation_angles'][index],
            'dt_poly': self.data['dt_polys'][index]  # 检测阶段的多边形
        }
    
    def get_all_texts(self) -> List[Dict]:
        """获取所有文本信息"""
        return [self.get_text(i) for i in range(self.num_texts)]
    
    def filter_by_score(self, min_score: float = 0.5) -> List[Dict]:
        """
        根据置信度过滤文本
        
        Args:
            min_score: 最小置信度阈值
            
        Returns:
            过滤后的文本列表
        """
        return [
            self.get_text(i) 
            for i in range(self.num_texts) 
            if self.data['rec_scores'][i] >= min_score
        ]
    
    def search_text(self, keyword: str, case_sensitive: bool = False) -> List[Dict]:
        """
        搜索包含关键词的文本
        
        Args:
            keyword: 搜索关键词
            case_sensitive: 是否区分大小写
            
        Returns:
            匹配的文本列表
        """
        results = []
        for i in range(self.num_texts):
            text = self.data['rec_texts'][i]
            if case_sensitive:
                match = keyword in text
            else:
                match = keyword.lower() in text.lower()
            
            if match:
                results.append(self.get_text(i))
        
        return results
    
    def get_texts_in_region(self, x_min: int, y_min: int, x_max: int, y_max: int) -> List[Dict]:
        """
        获取指定区域内的文本
        
        Args:
            x_min, y_min, x_max, y_max: 区域坐标
            
        Returns:
            区域内的文本列表
        """
        results = []
        for i in range(self.num_texts):
            box = self.data['rec_boxes'][i]
            # 检查文本框是否与指定区域有交集
            if not (box[2] < x_min or box[0] > x_max or box[3] < y_min or box[1] > y_max):
                results.append(self.get_text(i))
        
        return results
    
    def export_simple_format(self) -> List[Dict]:
        """
        导出简化格式（只包含文本、置信度和矩形框）
        
        Returns:
            简化格式的文本列表
        """
        return [
            {
                'text': self.data['rec_texts'][i],
                'score': round(self.data['rec_scores'][i], 4),
                'bbox': self.data['rec_boxes'][i]
            }
            for i in range(self.num_texts)
        ]
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        scores = self.data['rec_scores']
        return {
            'total_texts': self.num_texts,
            'avg_score': sum(scores) / len(scores) if scores else 0,
            'min_score': min(scores) if scores else 0,
            'max_score': max(scores) if scores else 0,
            'high_confidence_count': sum(1 for s in scores if s >= 0.9),
            'medium_confidence_count': sum(1 for s in scores if 0.5 <= s < 0.9),
            'low_confidence_count': sum(1 for s in scores if s < 0.5)
        }
    
    def print_summary(self):
        """打印结果摘要"""
        print(f"输入文件: {self.input_path}")
        print(f"文本类型: {self.text_type}")
        print(f"识别文本数量: {self.num_texts}")
        
        stats = self.get_statistics()
        print(f"\n统计信息:")
        print(f"  平均置信度: {stats['avg_score']:.4f}")
        print(f"  最高置信度: {stats['max_score']:.4f}")
        print(f"  最低置信度: {stats['min_score']:.4f}")
        print(f"  高置信度文本 (>0.9): {stats['high_confidence_count']} 个")
        print(f"  中置信度文本 (0.5-0.9): {stats['medium_confidence_count']} 个")
        print(f"  低置信度文本 (<0.5): {stats['low_confidence_count']} 个")
    
    def print_all_texts(self, min_score: Optional[float] = None):
        """
        打印所有文本信息
        
        Args:
            min_score: 可选的最小置信度阈值
        """
        texts = self.filter_by_score(min_score) if min_score else self.get_all_texts()
        
        print(f"\n识别结果 (共 {len(texts)} 个):")
        print("-" * 80)
        for item in texts:
            print(f"[{item['index']}] {item['text']}")
            print(f"    置信度: {item['score']:.4f}")
            print(f"    矩形框: {item['box']}")
            print(f"    方向角度: {item['angle']}")
            print()


def main():
    """示例用法"""
    # 使用示例
    json_file = "output/general_ocr_002_res.json"
    
    try:
        # 加载结果
        result = PaddleOCRResult(json_file)
        
        # 打印摘要
        result.print_summary()
        
        # 打印所有文本
        result.print_all_texts(min_score=0.9)
        
        # 搜索特定文本
        print("\n搜索包含 '航班' 的文本:")
        matches = result.search_text('航班')
        for match in matches:
            print(f"  {match['text']} (置信度: {match['score']:.4f})")
        
        # 导出简化格式
        print("\n导出简化格式 (前3个):")
        simple = result.export_simple_format()
        for item in simple[:3]:
            print(f"  {item}")
        
    except FileNotFoundError:
        print(f"错误: 找不到文件 {json_file}")
    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    main()

