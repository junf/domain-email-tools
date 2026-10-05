# domain-email-tools

[English](README.md)

Kindle 本『独自ドメインのメール、設定したのに、なぜ届かない？ — SPF・DKIM・DMARC を、測って直す』（Jun F.）の付属スクリプトです。

## headers.py — 原文から、判定に要る行だけを抜き出す

保存したメールの原文（`.eml`）から、送信ドメイン認証の判定に要る行だけを抜き出して並べます。

- `From:` と `Return-Path:` のアドレス
- DKIM 署名の `d=`（署名したドメイン）と `s=`（セレクタ）
- `Received:` の行数
- 受信側の `Authentication-Results:` のうち、spf・dkim・dmarc の結果と、それぞれが見たドメイン

ドメインが揃っているか（アラインメント）の判定はしません。並べて見せるだけです。揃っているかの答えは、受信側が書いた `dmarc=` の結果を見てください（本書 第2章 2.2）。

### 要るもの

Python 3 だけです。標準ライブラリだけで動くので、追加のインストールはありません。

### 使い方

```
python3 headers.py message.eml
```

出力の例:

```
From:            info@example.com
Return-Path:     bounce@em.example.com
DKIM-Signature:  d=example.com s=s1
DKIM-Signature:  d=svc.example s=k1
Received:        3

Authentication-Results (mx.google.com)
  dkim  pass  header.i=@example.com header.s=s1
  dkim  pass  header.i=@svc.example header.s=k1
  spf   pass  smtp.mailfrom=bounce@em.example.com
  dmarc pass  header.from=example.com
```

読み方は本書の付録D で説明しています。

### 確かめた環境

- Ubuntu 24.04（Python 3.12.3）
- Windows 11 の WSL（Ubuntu 26.04・Python 3.14.4）
- macOS 26.7.1（Command Line Tools の Python 3.9.6）

## ライセンス

MIT（[LICENSE](LICENSE)）
