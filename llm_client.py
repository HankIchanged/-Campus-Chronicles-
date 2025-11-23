import os
import json
import random
try:
    import openai
except Exception:
    openai = None

# Simple wrapper that uses OpenAI if OPENAI_API_KEY present; otherwise uses a deterministic mock LLM.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def call_chat(model, messages, max_tokens=400, temperature=0.7):
    '''
    messages: list of {"role":..., "content":...}
    '''
    if OPENAI_API_KEY and openai:
        openai.api_key = OPENAI_API_KEY
        resp = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            n=1
        )
        return resp.choices[0].message.content
    else:
        # Mock deterministic responses for offline demo.
        user = messages[-1]["content"] if messages else ""
        # Basic heuristics:
        if "聊天" in user or "talk" in user or "chat" in user:
            return "（模擬回覆）很開心遇見你！我們可以一起去社團或聊聊作品。一起去的話可以更熟。建議：一起參加社團活動。"
        if "回答學生的問題" in user or "請教" in user or "回答學生的問題" in user:
            # Return an example answer plus a "滿意" marker randomly
            ans = "（模擬回答）這個問題可以從基礎概念出發，首先... 最後請多練習。回答是否令人滿意：是"
            return ans
        if "邀你加入" in user or "邀約" in user:
            return "（模擬回覆）我很有興趣，想試試看，可以一起討論時間。接受"
        if "請扮演一位大學生生活評論家" in user or "遊戲回顧" in user:
            # return JSON review
            review = {
                "comment": "模擬評論：努伊特本學期積極互動、展現同理心，成功建立了兩段深度友誼。遊戲節奏與回饋良好。",
                "score": 88,
                "highlight": "與 Ben 成功合作專案的段落最為亮眼。",
                "replay_tips": [
                    "嘗試更多不同類型的互動（請教/邀約/活動）",
                    "集中在一位NPC上多次互動，能觸發特殊分支。"
                ]
            }
            return json.dumps(review, ensure_ascii=False)
        # Fallback
        return "（模擬回覆）我聽到了你的話，讓我們繼續。"
