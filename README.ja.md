# domain-email-tools

[English](README.md)

Kindle 本『独自ドメインのメール、設定したのに、なぜ届かない？ — SPF・DKIM・DMARC を、確かめて直す』（Jun F.）の付属スクリプトです。

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

読み方は本書の付録F で説明しています。

### 確かめた環境

- Ubuntu 24.04（Python 3.12.3）
- Windows 11 の WSL（Ubuntu 26.04・Python 3.14.4）
- macOS 26.7.1（Command Line Tools の Python 3.9.6）

## spf-count.py — SPF が DNS を引く回数を数える

SPF の評価で DNS を引けるのは10回までです（RFC 7208 4.6.4）。`include:` は取り込んだ先で引いた回数も合算されるので、3つでも超えることがあります。このスクリプトは `include:` と `redirect=` の先まで辿り、DNS を引く項目（`include` `a` `mx` `ptr` `exists` `redirect`）を数えます。

空の結果（レコードが無い）の回数（2回以内が推奨）と、`include:` の先に SPF が無い・2つあるといった壊れ方も出します。

### 要るもの

Python 3 と `dig` コマンド。Windows では WSL で動かしてください（本書 付録D）。

### 使い方

```
python3 spf-count.py example.com
```

出力の例:

```
example.com
 1 mx
 2 include:_spf.example.net
    _spf.example.net
     3 include:_spf2.example.net
        _spf2.example.net
 4 include:mail.svc.example
    mail.svc.example
     5 exists:%{i}._spf.svc.example
       (macro: not followed)

DNS lookups:   5 / 10
Empty answers: 0 / 2
Within the limit
```

DNS に設定する前の値を数えたいときは、2つ目の引数に、設定する予定の値を渡します。出力の1行目に `(record not in DNS yet)` と出ます。`include:` の先は、DNS を引いて辿ります。

```
python3 spf-count.py example.com "v=spf1 include:_spf.example.net mx ~all"
```

数えるのは最も多くなる場合の回数です。受信側は一致した項目で評価を止めますが、どの送信元から来ても上限に収まっている必要があります。マクロ（`%{i}` など）を含む項目は1回と数え、その先は辿りません。

読み方は本書の付録G で説明しています。

### 確かめた環境

- Ubuntu 24.04（Python 3.12.3）

## dkim-check.py — DKIM の署名を検証する（DNS に入れる前でも）

保存したメール（`.eml`）の DKIM の署名を検証します。公開鍵を引数で渡せるので、**DNS に設定する前に**鍵が正しいかを確かめられます。鍵を渡さなければ、`dig` で DNS から引いて検証します。

署名ごとに、次のことを出します。

- 本文のハッシュ（`bh=`）と署名（`b=`）の結果を分けて。本文が変わったのか、鍵かヘッダが違うのかを見分けられます
- 鍵の長さ
- 陰性対照: PASS したら、わざと別の鍵でも検証し、失敗することを確かめます

### 要るもの

Python 3、dkimpy、`dig`（DNS を引くとき）。Ubuntu・Debian では `sudo apt install python3-dkim`。それ以外では、仮想環境に dkimpy を入れてください（本書 付録H）。

### 使い方

```
python3 dkim-check.py message.eml "<p= の値>"
python3 dkim-check.py message.eml
```

出力の例:

```
Signature 1
  d=example.com  s=s1  c=relaxed/simple
  key: the one you gave
  key length: 2048 bit
  body hash (bh=): OK
  signature (b=):  OK
  result: PASS
  wrong key: NG  (rejected, as expected)
```

読み方は本書の第5章 5.3・5.4 で説明しています。

### 確かめた環境

- Ubuntu 24.04（Python 3.12.3）、dkimpy 1.1.6 と 1.1.8

## ライセンス

MIT（[LICENSE](LICENSE)）
