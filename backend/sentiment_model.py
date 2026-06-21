"""财经新闻情感分析模型（轻量级规则模型）。

对新闻标题与摘要进行利好 / 利空 / 中性判定，输出情感标签、置信度分数与触发关键词。
无需外部 API 或大型依赖，适合在资源受限环境运行；未来可无缝替换为 LLM 或 Transformer。
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SentimentResult:
    """单条资讯的情感分析结果。"""

    sentiment: str  # "bullish" | "bearish" | "neutral"
    score: float  # -1.0 ~ 1.0，正值利好、负值利空
    reasons: list[str]  # 触发的关键词/短语（最多 5 个）


class FinancialSentimentModel:
    """基于关键词与简单否定检测的金融情感分析模型。

    支持中英双语，针对记忆体 / 半导体 / 科技股场景调优。
    """

    # 中文利好词（权重 0.3 ~ 1.0）
    POSITIVE_ZH: dict[str, float] = {
        "大涨": 1.0,
        "飙升": 1.0,
        "暴涨": 0.95,
        "翻倍": 0.9,
        "翻三倍": 1.0,
        "翻四倍": 1.0,
        "翻五倍": 1.0,
        "翻了一番": 0.9,
        "翻了两番": 0.95,
        "利好": 1.0,
        "强劲": 0.75,
        "超预期": 0.85,
        "大超预期": 0.95,
        "盈利超预期": 0.85,
        "营收超预期": 0.85,
        "创新高": 0.85,
        "历史新高": 0.9,
        "突破": 0.6,
        "上升": 0.5,
        "增长": 0.5,
        "复苏": 0.6,
        "景气": 0.55,
        "需求旺盛": 0.8,
        "供不应求": 0.85,
        "产能售罄": 0.9,
        "售罄": 0.7,
        "上调": 0.7,
        "上调目标价": 0.85,
        "买入": 0.8,
        "增持": 0.8,
        "看好": 0.7,
        "强烈推荐": 1.0,
        "领跑": 0.7,
        "领先": 0.6,
        "优势": 0.5,
        "激增": 0.8,
        "急增": 0.8,
        "飙升": 1.0,
        "跳涨": 0.85,
        "飙涨": 0.95,
        "猛涨": 0.9,
        "攀升": 0.6,
        "走高": 0.55,
        "上行": 0.6,
        "上涨": 0.6,
        "扩大": 0.45,
        "提升": 0.5,
        "改善": 0.55,
        "优化": 0.5,
        "丰收": 0.65,
        "红利": 0.55,
        "受惠": 0.6,
        "受益": 0.55,
        "引爆": 0.7,
        "超预期": 0.85,
        "盈余惊喜": 0.85,
        "重估": 0.7,
        "价值重估": 0.75,
        "上行空间": 0.75,
        "涨势": 0.65,
        "升势": 0.65,
        "多头": 0.8,
        "牛市": 0.85,
        "超级周期": 0.7,
        "独占": 0.65,
        "垄断": 0.55,
        "领先": 0.6,
        "龙头": 0.65,
        "认证": 0.45,
        "通过认证": 0.55,
        "斩获订单": 0.75,
        "获得订单": 0.65,
        "大单": 0.7,
        "扩产": 0.55,
        "增产": 0.55,
        "追加资本支出": 0.6,
    }

    # 英文利好词
    POSITIVE_EN: dict[str, float] = {
        "surge": 1.0,
        "soar": 1.0,
        "skyrocket": 1.0,
        "rocket": 0.85,
        "jump": 0.8,
        "rally": 0.8,
        "rallied": 0.8,
        "bull run": 0.9,
        "beat": 0.8,
        "beats": 0.8,
        "beaten": 0.8,
        "strong": 0.7,
        "strength": 0.65,
        "growth": 0.55,
        "growing": 0.55,
        "outperform": 0.75,
        "outperforms": 0.75,
        "bullish": 1.0,
        "upgrade": 0.8,
        "upgraded": 0.8,
        "buy": 0.8,
        "overweight": 0.75,
        "record": 0.7,
        "records": 0.7,
        "booking": 0.6,
        "booked": 0.65,
        "sold out": 0.85,
        "fully booked": 0.9,
        "fully subscribed": 0.85,
        "boom": 0.8,
        "booming": 0.8,
        "supercycle": 0.85,
        "super cycle": 0.85,
        "upside": 0.75,
        "rises": 0.6,
        "rising": 0.6,
        "gains": 0.65,
        "gaining": 0.65,
        "higher": 0.55,
        "rallies": 0.8,
        "surges": 1.0,
        "soars": 1.0,
        "jumps": 0.8,
        "climbs": 0.6,
        "accelerate": 0.65,
        "robust": 0.7,
        "solid": 0.6,
        "exceeds": 0.8,
        "exceeded": 0.8,
        "exceed expectations": 0.9,
        "raised guidance": 0.85,
        "raise guidance": 0.85,
        "raised price target": 0.8,
        "raise price target": 0.8,
        "top pick": 0.75,
        "best pick": 0.75,
        "strong buy": 0.95,
        "long-term buy": 0.85,
    }

    # 中文利空词
    NEGATIVE_ZH: dict[str, float] = {
        "大跌": -1.0,
        "暴跌": -0.95,
        "重挫": -0.85,
        "下挫": -0.7,
        "跳水": -0.85,
        "崩盘": -1.0,
        "腰斩": -1.0,
        "亏损": -0.8,
        "转亏": -0.85,
        "亏损扩大": -0.9,
        "利空": -1.0,
        "跌破": -0.7,
        "下滑": -0.55,
        "下降": -0.5,
        "衰退": -0.75,
        "萎缩": -0.65,
        "疲软": -0.65,
        "低迷": -0.6,
        "不振": -0.6,
        "恶化": -0.75,
        "风险": -0.45,
        "高风险": -0.65,
        "担忧": -0.45,
        "担心": -0.45,
        "恐慌": -0.75,
        "抛售": -0.8,
        "卖压": -0.7,
        "减持": -0.8,
        "卖出": -0.8,
        "下调": -0.7,
        "下调目标价": -0.85,
        "看空": -0.75,
        "看跌": -0.75,
        "唱衰": -0.8,
        "空头": -0.8,
        "熊市": -0.85,
        "衰退": -0.75,
        " downturn": -0.75,
        "崩盘": -1.0,
        "暴跌": -0.95,
        "暴跌": -0.95,
        "跌幅": -0.55,
        "走低": -0.55,
        "下行": -0.6,
        "下跌": -0.6,
        "回落": -0.55,
        "不及预期": -0.8,
        " miss": -0.75,
        "逊于预期": -0.8,
        " miss 预期": -0.8,
        "盈利预警": -0.85,
        "财测下修": -0.85,
        "下修财测": -0.85,
        "裁员": -0.7,
        "停产": -0.8,
        "供过于求": -0.8,
        "库存积压": -0.75,
        "库存过高": -0.75,
        "价格战": -0.7,
        "产能过剩": -0.75,
        "延迟": -0.5,
        "推迟": -0.5,
        "取消": -0.55,
        "失去": -0.5,
        "拒绝": -0.5,
        "失败": -0.7,
        "丑闻": -0.75,
        "调查": -0.45,
        "诉讼": -0.55,
        "罚款": -0.6,
        "制裁": -0.7,
        "禁令": -0.75,
    }

    # 英文利空词
    NEGATIVE_EN: dict[str, float] = {
        "plunge": -1.0,
        "plunges": -1.0,
        "plunged": -1.0,
        "crash": -1.0,
        "crashes": -1.0,
        "crashed": -1.0,
        "collapse": -0.95,
        "collapses": -0.95,
        "collapsed": -0.95,
        "tumble": -0.85,
        "tumbles": -0.85,
        "tumbled": -0.85,
        "drop": -0.7,
        "drops": -0.7,
        "dropped": -0.7,
        "fall": -0.6,
        "falls": -0.6,
        "fell": -0.65,
        "falling": -0.6,
        "weak": -0.6,
        "weakness": -0.65,
        "miss": -0.8,
        "misses": -0.8,
        "missed": -0.8,
        "decline": -0.65,
        "declines": -0.65,
        "declining": -0.65,
        "bearish": -1.0,
        "downgrade": -0.8,
        "downgraded": -0.8,
        "sell": -0.8,
        "underweight": -0.75,
        "loss": -0.7,
        "losses": -0.7,
        "lose": -0.65,
        "losing": -0.7,
        "reduced guidance": -0.85,
        "lower guidance": -0.85,
        "cut guidance": -0.9,
        "lower price target": -0.8,
        "cut price target": -0.8,
        "recession": -0.8,
        "oversupply": -0.8,
        "glut": -0.85,
        "inventory buildup": -0.75,
        "price war": -0.75,
        "excess capacity": -0.75,
        "downturn": -0.75,
        "slump": -0.8,
        "slumps": -0.8,
        "slumped": -0.8,
        "worst": -0.65,
        "disappoint": -0.75,
        "disappoints": -0.75,
        "disappointing": -0.75,
        "warning": -0.6,
        "warns": -0.6,
        "warned": -0.6,
        "layoff": -0.7,
        "layoffs": -0.75,
        "halt": -0.6,
        "delay": -0.55,
        "delays": -0.55,
        "delayed": -0.55,
        "cancel": -0.6,
        "cancels": -0.6,
        "canceled": -0.6,
        "lose contract": -0.75,
        "lost contract": -0.8,
        "investigation": -0.5,
        "lawsuit": -0.6,
        "fine": -0.6,
        "sanction": -0.7,
        "ban": -0.75,
    }

    # 否定词（用于简单反转情感）
    NEGATION_WORDS: set[str] = {
        "不", "没有", "未", "无", "并非", "不是", "dont", "don't", "doesnt", "doesn't",
        "didnt", "didn't", "not", "no", "never", "without", "not",
    }

    def __init__(self):
        self.positive = {**self.POSITIVE_ZH, **self.POSITIVE_EN}
        self.negative = {**self.NEGATIVE_ZH, **self.NEGATIVE_EN}

    def analyze(self, title: str, summary: str, tickers: list[str] | None = None) -> SentimentResult:
        """分析单条资讯的情感倾向。

        Args:
            title: 新闻标题
            summary: 新闻摘要
            tickers: 相关标的代码（仅用于记录，不影响评分）

        Returns:
            SentimentResult 包含 sentiment / score / reasons
        """
        text = f"{title or ''} {summary or ''}".strip()
        if not text:
            return SentimentResult("neutral", 0.0, [])

        text_lower = text.lower()
        text_for_negation = text_lower.replace(",", " ").replace(".", " ").replace("；", " ").replace("，", " ").replace("。", " ")
        words = text_for_negation.split()

        score = 0.0
        reasons: list[str] = []

        # 正向匹配
        for keyword, weight in self.positive.items():
            if keyword in text_lower:
                effective = weight
                # 简单否定检测：否定词出现在关键词前 3 个词内，则反转
                if self._is_negated(text_lower, keyword, words):
                    effective = -effective * 0.7
                score += effective
                label = f"+{effective:.1f}" if effective > 0 else f"{effective:.1f}"
                reasons.append(f"{label} {keyword}")

        # 负向匹配
        for keyword, weight in self.negative.items():
            if keyword in text_lower:
                effective = weight
                if self._is_negated(text_lower, keyword, words):
                    effective = -effective * 0.7
                score += effective
                reasons.append(f"{effective:.1f} {keyword}")

        # 去重并截断原因
        reasons = self._dedup_reasons(reasons)

        # 判定标签
        if score > 0.25:
            sentiment = "bullish"
        elif score < -0.25:
            sentiment = "bearish"
        else:
            sentiment = "neutral"

        # 归一化分数到 [-1, 1]，并用命中次数做一定平滑
        hit_count = max(len(reasons), 1)
        normalized = max(-1.0, min(1.0, score / (hit_count ** 0.5)))

        return SentimentResult(
            sentiment=sentiment,
            score=round(normalized, 2),
            reasons=reasons[:5],
        )

    def _is_negated(self, text_lower: str, keyword: str, words: list[str]) -> bool:
        """判断关键词前是否出现否定词（简单实现）。"""
        try:
            # 找到关键词在分词后最近的位置
            keyword_lower = keyword.lower()
            for i, w in enumerate(words):
                if keyword_lower in w or w in keyword_lower:
                    window_start = max(0, i - 3)
                    window = words[window_start:i]
                    if any(n in window for n in self.NEGATION_WORDS):
                        return True
            # 兜底：在原文中检查关键词前 10 个字符内是否有否定词
            idx = text_lower.find(keyword_lower)
            if idx != -1:
                prefix = text_lower[max(0, idx - 12):idx]
                if any(n in prefix for n in self.NEGATION_WORDS):
                    return True
        except Exception:
            pass
        return False

    @staticmethod
    def _dedup_reasons(reasons: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for r in reasons:
            key = re.sub(r"^[+-]?\d+\.\d+", "", r).strip()
            if key not in seen:
                seen.add(key)
                out.append(r)
        return out


# 全局单例（避免重复初始化）
_sentiment_model: FinancialSentimentModel | None = None


def get_model() -> FinancialSentimentModel:
    """获取全局情感分析模型实例。"""
    global _sentiment_model
    if _sentiment_model is None:
        _sentiment_model = FinancialSentimentModel()
    return _sentiment_model


def analyze_news(title: str, summary: str, tickers: list[str] | None = None) -> dict:
    """便捷函数：分析新闻并返回可序列化字典。"""
    result = get_model().analyze(title, summary, tickers)
    return {
        "sentiment": result.sentiment,
        "score": result.score,
        "reasons": result.reasons,
    }
