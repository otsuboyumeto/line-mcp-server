# LINE MCP Server

ManusからLINEグループにメッセージを送信するためのカスタムMCPサーバー

## 機能

- LINEグループへのメッセージ送信
- MCPプロトコル対応
- Render対応

## 環境変数

以下の環境変数を設定する必要があります:

- `LINE_CHANNEL_ACCESS_TOKEN`: LINEチャネルアクセストークン
- `LINE_GROUP_ID`: デフォルトのLINEグループID
- `PORT`: サーバーのポート番号（デフォルト: 8000）

## デプロイ方法（Render）

1. GitHubリポジトリを作成してコードをプッシュ
2. Renderにログイン
3. 「New Web Service」を選択
4. GitHubリポジトリを接続
5. 環境変数を設定:
   - `LINE_CHANNEL_ACCESS_TOKEN`: チャネルアクセストークン
   - `LINE_GROUP_ID`: グループID
6. デプロイ

## ローカルでのテスト

```bash
# 環境変数を設定
export LINE_CHANNEL_ACCESS_TOKEN="your_token_here"
export LINE_GROUP_ID="your_group_id_here"

# 依存関係をインストール
pip install -r requirements.txt

# サーバーを起動
python server.py
```

## Manusでの使用方法

1. Manusの「カスタムMCPサーバー」設定に移動
2. サーバーURLを追加: `https://your-render-url.onrender.com/mcp`
3. Manusで以下のように指示:
   - 「LINEグループに『メールを転送しました』と送信して」
   - 「スタッフに『会議は15時からです』とLINEで通知して」

## API仕様

### ツール: send_line_message

LINEグループにメッセージを送信します。

**パラメータ:**
- `message` (必須): 送信するメッセージ
- `group_id` (任意): グループID（省略時はデフォルトのグループに送信）

**返り値:**
```json
{
  "success": true,
  "message": "Message sent successfully",
  "group_id": "C907a5f13427d06fa58adf5c1920352ad"
}
```
