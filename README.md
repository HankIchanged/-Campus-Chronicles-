《Campus Chronicles：校園生活模擬器》 — 完整作業套件
====================================

內容：
- campus_game.py: 主程式，可互動式遊玩
- llm_client.py: LLM 呼叫封裝（若無 API key，會使用離線模擬）
- lab2_config.json: 配置範例
- static/: 靜態資料（prompts, students）
- state/: 遊戲存檔（執行時自動建立）
- runs/: 產生之遊玩紀錄
- requirements.txt

執行：
1. 安裝依賴：pip install -r requirements.txt
2. 執行遊戲：python campus_game.py --config lab2_config.json
   - 若有 OpenAI 金鑰，可在啟動時輸入；若不輸入，程式會使用離線模擬 LLM，方便測試。

注意：
- 若要連接真實 LLM，請在環境變數 OPENAI_API_KEY 設定你的金鑰，或在程式啟動時輸入。
- 遊戲會把每次結局輸出為 runs/run_YYYYMMDD_HHMMSS.json。
