完整整合測試（需要 Gateway 平台）
Step 1: 先啟動 Gateway 平台（需要另一個 log-analysis-core repo）


cd log-analysis-core
echo "POSTGRES_PASSWORD=localtest" >> .env
docker-compose up -d

# 確認 Gateway 健康
curl http://localhost:80/health
Step 2: 啟動 TixMaster 後端


cd backend
npm install
npm start   # 跑在 http://localhost:3000
Step 3: 啟動 Agent 連到 Gateway


cd agent
# 編輯 config.yaml，確認 gateway_url: "http://localhost:80"
python agent.py --config config.yaml
