#!/usr/bin/env python3
"""
LINE Messaging API MCP Server
ManusからLINEグループにメッセージを送信するためのMCPサーバー
"""

import os
import json
import logging
from typing import Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション
app = FastAPI(title="LINE MCP Server", version="2.0.0")

# 環境変数から認証情報を取得
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
GROUP_ID = os.getenv("LINE_GROUP_ID")
PERSONAL_USER_ID = os.getenv("LINE_PERSONAL_USER_ID")

if not CHANNEL_ACCESS_TOKEN:
    logger.warning("LINE_CHANNEL_ACCESS_TOKEN is not set")
if not GROUP_ID:
    logger.warning("LINE_GROUP_ID is not set")
if not PERSONAL_USER_ID:
    logger.warning("LINE_PERSONAL_USER_ID is not set")


def send_line_message(message: str, group_id: str = None) -> dict:
    """
    LINEグループにメッセージを送信
    
    Args:
        message: 送信するメッセージ
        group_id: グループID（省略時は環境変数のGROUP_IDを使用）
    
    Returns:
        送信結果の辞書
    """
    target_group_id = group_id or GROUP_ID
    
    if not target_group_id:
        return {
            "success": False,
            "error": "GROUP_ID is not configured"
        }
    
    if not CHANNEL_ACCESS_TOKEN:
        return {
            "success": False,
            "error": "CHANNEL_ACCESS_TOKEN is not configured"
        }
    
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": target_group_id,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        return {
            "success": True,
            "message": "Message sent successfully",
            "group_id": target_group_id
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send LINE message: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "name": "LINE MCP Server",
        "version": "2.0.0",
        "description": "MCP server for sending messages to LINE groups and personal chats"
    }


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "healthy",
        "channel_token_configured": bool(CHANNEL_ACCESS_TOKEN),
        "group_id_configured": bool(GROUP_ID),
        "personal_user_id_configured": bool(PERSONAL_USER_ID)
    }


@app.post("/webhook")
async def webhook(request: Request):
    """
    LINE Webhook エンドポイント
    ユーザーからのメッセージを受信してUser IDをログに記録
    """
    try:
        body = await request.json()
        logger.info(f"Webhook received: {json.dumps(body, ensure_ascii=False)}")
        
        # イベント処理
        events = body.get("events", [])
        for event in events:
            event_type = event.get("type")
            source = event.get("source", {})
            
            if event_type == "message":
                user_id = source.get("userId")
                group_id = source.get("groupId")
                message_text = event.get("message", {}).get("text", "")
                
                logger.info(f"===== USER ID DETECTED =====")
                logger.info(f"User ID: {user_id}")
                if group_id:
                    logger.info(f"Group ID: {group_id}")
                logger.info(f"Message: {message_text}")
                logger.info(f"============================")
                
                # 自動返信（オプション）
                if user_id and "userid" in message_text.lower():
                    reply_token = event.get("replyToken")
                    if reply_token:
                        reply_message = f"あなたのUser IDは: {user_id}"
                        reply_url = "https://api.line.me/v2/bot/message/reply"
                        reply_headers = {
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
                        }
                        reply_payload = {
                            "replyToken": reply_token,
                            "messages": [{"type": "text", "text": reply_message}]
                        }
                        requests.post(reply_url, headers=reply_headers, json=reply_payload)
        
        return JSONResponse({"status": "ok"})
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """
    MCPプロトコルのメインエンドポイント
    """
    try:
        body = await request.json()
        method = body.get("method")
        
        if method == "initialize":
            # MCPプロトコルの初期化
            return JSONResponse({
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "LINE MCP Server",
                    "version": "2.0.0"
                }
            })
        
        elif method == "tools/list":
            # 利用可能なツールのリストを返す
            return JSONResponse({
                "tools": [
                    {
                        "name": "send_line_message",
                        "description": "LINEグループまたは個人にメッセージを送信します",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "description": "送信するメッセージ"
                                },
                                "target": {
                                    "type": "string",
                                    "description": "送信先: 'group'（グループ）または 'personal'（個人）。省略時はグループ",
                                    "enum": ["group", "personal"]
                                },
                                "group_id": {
                                    "type": "string",
                                    "description": "グループID（targetがgroupの場合に使用。省略時はデフォルトのグループ）"
                                },
                                "user_id": {
                                    "type": "string",
                                    "description": "ユーザーID（targetがpersonalの場合に使用。省略時はデフォルトのユーザー）"
                                }
                            },
                            "required": ["message"]
                        }
                    }
                ]
            })
        
        elif method == "tools/call":
            # ツールを実行
            params = body.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "send_line_message":
                message = arguments.get("message")
                target = arguments.get("target", "group")
                group_id = arguments.get("group_id")
                user_id = arguments.get("user_id")
                
                if not message:
                    return JSONResponse({
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps({
                                    "success": False,
                                    "error": "message parameter is required"
                                })
                            }
                        ]
                    })
                
                # 送信先を決定
                if target == "personal":
                    target_id = user_id or PERSONAL_USER_ID
                    if not target_id:
                        return JSONResponse({
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps({
                                        "success": False,
                                        "error": "PERSONAL_USER_ID is not configured"
                                    })
                                }
                            ]
                        })
                else:
                    target_id = group_id or GROUP_ID
                
                result = send_line_message(message, target_id)
                
                return JSONResponse({
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False)
                        }
                    ]
                })
            
            else:
                return JSONResponse({
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({
                                "success": False,
                                "error": f"Unknown tool: {tool_name}"
                            })
                        }
                    ]
                })
        
        else:
            return JSONResponse({
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }, status_code=404)
    
    except Exception as e:
        logger.error(f"Error processing MCP request: {e}")
        return JSONResponse({
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }, status_code=500)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
