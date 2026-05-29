from app.services import nlp_algo
import numpy as np

def check_nlp():
    print("====== NLP Engine Diagnostic ======")
    
    # 1. SnowNLP Test
    print("\n[1] Sentiment Analysis (SnowNLP)")
    cases = [
        ("今天天气真好，我非常开心！", "Positive"),
        ("这真是太糟糕了，我感到绝望。", "Negative"),
        ("今天买了瓶水。", "Neutral")
    ]
    for text, label in cases:
        score = nlp_algo.analyze_sentiment(text)
        print(f"   Text: {text} -> Score: {score} (Expect {label})")

    # 2. Jieba POS Test
    print("\n[2] Style Analysis (Jieba)")
    cases = [
        ("他猛地摔碎了杯子，玻璃渣飞溅到脸上。", "Show (High Ratio)"),
        ("他很生气，非常愤怒，极其痛苦。", "Tell (Low Ratio, High Adj)")
    ]
    for text, label in cases:
        metrics = nlp_algo.analyze_style(text)
        print(f"   Text: {text[:15]}...")
        print(f"   -> Expect: {label}")
        print(f"   -> Result: ShowRatio={metrics['show_ratio']}, AdjDensity={metrics['adj_density']}")

    # 3. Sensory Test
    print("\n[3] Sensory Check")
    text = "我闻到了花香，看见了红色的夕阳，听到了鸟叫。"
    metrics = nlp_algo.analyze_style(text)
    print(f"   Text: {text}")
    print(f"   -> Sensory Score: {metrics['sensory_score']} (Expect > 0)")
    
    print("\n====== Diagnostic Complete ======")

if __name__ == "__main__":
    check_nlp()
