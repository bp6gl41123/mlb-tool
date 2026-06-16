# VIP 齊聚眾選 預測端 — 問題追蹤

測試帳號：牛棚偵查員  
開始日期：2026-06-14

---

## 問題列表

### #001 — POST API 回應為 Google Drive 404 HTML 而非 JSON
- **日期**：2026-06-14
- **嚴重性**：高
- **類別**：後端 / API
- **描述**：所有 POST 請求（註冊 addUser、提交預測 savePickAndBet）回傳的不是 JSON，而是 Google Drive 的「Page Not Found」HTML 頁面。這導致前端 `fetch().then(r => r.json())` 解析失敗，落入 `catch(e)` 顯示「連線失敗，請重試」toast。
- **影響**：使用者看到失敗提示，但操作實際上有執行（腳本 doPost() 正常運作）。造成混淆。
- **重現步驟**：任何 POST 到 API_URL 的操作
- **建議**：檢查 Google Apps Script 部署設定，確認 doPost() 回傳 `ContentService.createTextOutput(JSON.stringify(result)).setMimeType(ContentService.MimeType.JSON)`

### #002 — 註冊成功無明確回饋
- **日期**：2026-06-14
- **嚴重性**：中
- **類別**：UX
- **描述**：承 #001，註冊 POST 失敗 toast 讓新使用者以為註冊失敗，但其實已成功。需手動切回登入頁嘗試登入才知道。
- **建議**：短期：在註冊按鈕的 catch 區塊加一段「若持續失敗，請嘗試直接登入」提示。長期：修復 #001。

### #003 — 瀏覽器端載入逾時（headless / CDP）
- **日期**：2026-06-14
- **嚴重性**：中
- **類別**：效能
- **描述**：headless Chrome（CDP protocol）連續 4 次導航到首頁都 timeout（60s+）。59KB HTML + 12 external JS + Google Fonts。可能原因：某個 JS blocking render、font loading 卡住、或 Vercel edge function cold start。
- **影響**：一般使用者的舊手機 / 慢網路可能偶爾遇到白畫面
- **建議**：考慮將 Google Fonts 改成 `font-display: swap` + 本地 fallback；檢查 vip-data2.js 的載入邏輯是否阻斷 render

### #004 — 缺少登出功能
- **日期**：2026-06-14
- **嚴重性**：低
- **類別**：UX / 功能缺失
- **描述**：登入後沒有任何登出按鈕或機制。只能手動清除 localStorage。
- **建議**：在 header 或 user bar 增加登出按鈕，清除 token + nickname + 重整頁面

### #005 — 新帳號限制提示不明確
- **日期**：2026-06-14
- **嚴重性**：低
- **類別**：UX / 文件
- **描述**：新使用者不知道「為什麼我只能選 5 場」、「什麼時候可以解鎖更多」。平台沒有顯示觸發條件的進度。
- **建議**：在規則區或送出預測時顯示「目前上限 5 場｜10 天後依勝率解鎖更多」

---

## 狀態摘要
| 狀態 | 數量 |
|------|------|
| 待修 | 5 |
| 已修 | 0 |
| 觀察中 | 0 |
