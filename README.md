# domain-email-tools

[日本語](README.ja.md)

Companion scripts for the Kindle book *独自ドメインのメール、設定したのに、なぜ届かない？ — SPF・DKIM・DMARC を、測って直す* (Jun F.; Japanese).

## headers.py — show only the header lines that matter

Reads a saved message (`.eml`) and prints only the lines you need to check email authentication:

- the `From:` and `Return-Path:` addresses
- `d=` (signing domain) and `s=` (selector) of each DKIM signature
- the number of `Received:` lines
- the spf / dkim / dmarc results in the receiver's `Authentication-Results:`, with the domain each one checked

It does **not** decide whether the domains are aligned. It only lines them up. For the answer, read the `dmarc=` result written by the receiver.

### Requirements

Python 3 only. It uses the standard library, so there is nothing to install.

### Usage

```
python3 headers.py message.eml
```

Example output:

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

The topmost `Authentication-Results:` is the one written by the last server that received the message. Microsoft services do not write a server name there, so the name in parentheses is omitted.

### Tested on

- Ubuntu 24.04 (Python 3.12.3)
- Windows 11, WSL with Ubuntu 26.04 (Python 3.14.4)

## License

MIT ([LICENSE](LICENSE))
