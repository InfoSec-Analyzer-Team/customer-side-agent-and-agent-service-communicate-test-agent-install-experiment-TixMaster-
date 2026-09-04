# Nginx Attack Log Collection Method

本資料夾只保留可作為正式資料來源的 Nginx access log。PowerShell Invoke-WebRequest 產生的 scripted attack-like batches 已判定不能作為正式 ML 訓練資料；PowerShell 只能用來輔助啟動工具、切批次與檢查檔案，不作為正式攻擊流量產生工具。

保留原則：

```text
1. request 必須真的打到本機 Nginx / TixMaster lab target
2. access log 必須由 Nginx 自己產生，不手寫偽造 log
3. 惡意資料優先使用專用工具或明確手動漏洞驗證流程產生
4. backend 必須有開，避免整批只打到 Nginx 而變成 502
```

## Current Formal Logs

| Log | Label | Stage | Tool / Method | Count | Notes |
|---|---|---:|---|---:|---|
| `collected/nginx01_batch_sqli_sqlmap_randomua_002.log` | BAHAYA | 2 | sqlmap (`parrotsec/sqlmap`, `--random-agent`) | 378 | SQLi tool traffic through Nginx/backend, 200 responses |
| `collected/nginx01_batch_xss_zap_fullscan_001.log` | BAHAYA | 3 | OWASP ZAP Docker full scan | 790 | XSS active scan traffic; ZAP also emits some SQLi/protocol probes |
| `collected/nginx01_batch_path_traversal_ffuf_002.log` | BAHAYA | 4 | ffuf | 33 | Path traversal payloads against the lab attachment sink |
| `collected/nginx01_batch_double_encoding_ffuf_002.log` | BAHAYA | 7 | ffuf | 34 | Double-encoded traversal payloads against the lab attachment sink |
| `collected/nginx01_batch_url_encoding_count_ffuf_001.log` | BAHAYA | 8 | ffuf | 36 | Single-layer and multi-layer URL-encoded attack payloads against `/api/events?keyword=` |
| `collected/nginx01_batch_special_chars_dense_ffuf_001.log` | BAHAYA | 9 | ffuf | 30 | Dense special-character attack payloads against `/api/events?keyword=` |
| `collected/nginx01_batch_scanner_ua_gobuster_005.log` | BAHAYA | 10 | gobuster | 33 | Scanner User-Agent and directory enumeration traffic against the lab target |
| `collected/nginx01_batch_abnormal_methods_ffuf_002.log` | BAHAYA | 11 | ffuf | 100 | PUT/DELETE/OPTIONS/PATCH/HEAD requests against common lab paths |
| `collected/nginx01_batch_abnormal_url_ffuf_001.log` | BAHAYA | 12 | ffuf | 30 | Deep paths, long paths, repeated parameters, traversal-like segments, and unusual delimiters |
| `collected/nginx01_batch_command_injection_commix_001.log` | BAHAYA | 5 | commix | 1666 | Command injection tool traffic against `/api/events?keyword=` |
| `LFI_method_record/access3_Local_file_inclusion_1.log` | BAHAYA | 6 | Browser/manual LFI payload | 22 | Manual requests against the real attachment sink |
| `LFI_method_record/access4_Local_file_inclusion_2_wfuzz.log` | BAHAYA | 6 | wfuzz | 881 | LFI/path traversal wordlist run against the real attachment sink |
| `LFI_method_record/access5_Local_file_inclusion_3_wfuzz.log` | BAHAYA | 6 | wfuzz | 71 | Additional LFI/path traversal wordlist run |

## Removed From Formal Dataset

以下批次已移除或不再列入 `stage_log_map.txt`：

```text
nginx01_batch_sqli_browserua_001
nginx01_batch_xss_browserua_001
nginx01_batch_path_traversal_encoded_001
nginx01_batch_dicurigai_diverse_probe_001
nginx01_batch_command_injection_browserua_001
nginx01_batch_sqlmap_sqli_001
nginx01_batch_xss_001
nginx01_batch_path_traversal_001
nginx01_batch_nikto_scan_001
nginx01_batch_dicurigai_probe_001
```

## Remaining Replacement Plan

All 12 stages currently have mapped log data. Future work should focus on collecting additional batches across different IP ranges, time windows, and tool/user-agent settings.

## Current Caveats

目前 SQLi、XSS、path traversal、double encoding、URL encoding count、special chars dense、scanner UA、abnormal methods、abnormal URL、command injection 已符合「工具真打 Nginx/backend」的要求，但仍有泛化風險需要後續批次補強：

```text
- 單批 IP 幾乎都來自 Docker bridge，例如 172.17.0.1
- 單批時間集中在短時間內
- sqlmap/commix/wfuzz 這類工具批次仍可能有工具 UA 指紋
```

正式訓練前應使用多批次、不同時間、不同來源環境或不同工具設定補強 IP / time / UA diversity。

Stage 4 使用的 traversal-only payload 清單保存在 `collected/path_traversal_ffuf_payloads_002.txt`。
Stage 7 使用的 double-encoding payload 清單保存在 `collected/double_encoding_ffuf_payloads_001.txt`。
Stage 8 使用的 URL encoding payload 清單保存在 `collected/url_encoding_count_ffuf_payloads_001.txt`。
Stage 9 使用的 special-character payload 清單保存在 `collected/special_chars_dense_ffuf_payloads_001.txt`。
Stage 10 使用的 gobuster wordlist 保存在 `collected/scanner_ua_gobuster_wordlist_001.txt`。
Stage 11 使用的 abnormal-method path 清單保存在 `collected/abnormal_methods_ffuf_paths_001.txt`。
Stage 12 使用的 abnormal-URL payload 清單保存在 `collected/abnormal_url_ffuf_payloads_001.txt`。


## IP / UA Diversity Round 002

The following batches reuse the same lab endpoints and tool-generated payload lists, but collect another round with a different `X-Forwarded-For` range (`10.88.x.x`) and non-default User-Agent values where appropriate. These are not new stages; they are additional logs mapped to the same stage IDs to reduce IP and UA shortcut risk.

| Log | Stage | Tool | Count | Diversity change |
|---|---:|---|---:|---|
| `collected/nginx01_batch_path_traversal_ffuf_ipua_003.log` | 4 | ffuf | 33 | `10.88.4.31`, browser-like Chrome UA |
| `collected/nginx01_batch_double_encoding_ffuf_ipua_003.log` | 7 | ffuf | 34 | `10.88.7.31`, browser-like Firefox UA |
| `collected/nginx01_batch_url_encoding_count_ffuf_ipua_002.log` | 8 | ffuf | 36 | `10.88.8.31`, browser-like Edge UA |
| `collected/nginx01_batch_special_chars_dense_ffuf_ipua_002.log` | 9 | ffuf | 30 | `10.88.9.31`, browser-like Safari UA |
| `collected/nginx01_batch_scanner_ua_gobuster_ipua_002.log` | 10 | gobuster | 33 | `10.88.10.31`, alternate gobuster UA |
| `collected/nginx01_batch_abnormal_methods_ffuf_ipua_004.log` | 11 | ffuf | 100 | `10.88.11.32`, browser-like Chrome/Linux UA |
| `collected/nginx01_batch_abnormal_url_ffuf_ipua_003.log` | 12 | ffuf | 30 | `10.88.12.32`, browser-like mobile Safari UA, clean-IP URL set |

Time diversity is intentionally not faked in the log files. To address time shortcut risk, collect another round in a separate real time window and map the resulting logs to the same stage IDs.


## Night Round 003

The following batches were collected in a real night time window (Asia/Taipei, UTC+8) instead of synthetically editing timestamps. They add time diversity for stages that previously had fewer later-time samples, while also using a different `X-Forwarded-For` range (`10.99.x.x`) and non-default User-Agent settings.

| Log | Stage | Tool | Count | Diversity change |
|---|---:|---|---:|---|
| `collected/nginx01_batch_sqli_sqlmap_randomua_night_003.log` | 2 | sqlmap | 75 | night window, `10.99.2.31`, sqlmap `--random-agent` |
| `collected/nginx01_batch_xss_ffuf_browserua_night_002.log` | 3 | ffuf | 30 | night window, `10.99.3.31`, browser-like Chrome UA |
| `collected/nginx01_batch_command_injection_ffuf_browserua_night_002.log` | 5 | ffuf | 30 | night window, `10.99.5.32`, browser-like Chrome/Linux UA; complements commix baseline |

A second commix run was attempted for stage 5, but the Kali package installation did not reach the request phase in a reasonable time window. No formal log was kept from that failed attempt; the retained night round uses ffuf-generated command injection payload traffic.

## Labeling Rule

Nginx access.log 本身不包含 label。Label 應寫在對應 `.meta.txt`，或由 `stage_log_map.txt` 在轉 dataset 時補上。

```text
BAHAYA    = 明確攻擊 payload 或工具攻擊流量
DICURIGAI = 可疑探測、異常結構或掃描行為，但不一定是確認攻擊
AMAN      = 正常流量
```











## POST Method Diversity Round 004

The following batches were collected after review feedback that most attack logs were GET-only. They are real tool-generated requests through Nginx, not hand-written logs. Because the current Nginx parser expects the standard `combined` log format and does not record request bodies, these batches use POST requests while keeping the attack payload in the query string. This preserves both the HTTP method and the payload in `access.log` without changing the parser contract.

| Log | Stage | Tool | Count | Method | Notes |
|---|---:|---|---:|---|---|
| `collected/nginx01_batch_sqli_sqlmap_postquery_night_005.log` | 2 | sqlmap | 147 | POST | POST `/api/users/login` with SQLi probes; sqlmap `--random-agent`, `10.99.2.42` |
| `collected/nginx01_batch_xss_ffuf_postquery_night_004.log` | 3 | ffuf | 30 | POST | XSS payloads against `/api/events?keyword=FUZZ`, browser-like UA, `10.99.3.41` |
| `collected/nginx01_batch_path_traversal_ffuf_postquery_night_004.log` | 4 | ffuf | 33 | POST | traversal payloads against attachment path, `10.99.4.41` |
| `collected/nginx01_batch_command_injection_ffuf_postquery_night_004.log` | 5 | ffuf | 30 | POST | command injection payloads against `/api/events?keyword=FUZZ`, `10.99.5.41` |
| `collected/nginx01_batch_double_encoding_ffuf_postquery_night_004.log` | 7 | ffuf | 34 | POST | double-encoded payloads, `10.99.7.41` |
| `collected/nginx01_batch_url_encoding_count_ffuf_postquery_night_004.log` | 8 | ffuf | 36 | POST | URL-encoding-heavy payloads, `10.99.8.41` |
| `collected/nginx01_batch_special_chars_dense_ffuf_postquery_night_004.log` | 9 | ffuf | 30 | POST | special-character-dense payloads, `10.99.9.41` |
| `collected/nginx01_batch_abnormal_url_ffuf_post_night_004.log` | 12 | ffuf | 30 | POST | abnormal URL paths using POST, `10.99.12.41` |

Validation result for this round: all eight new files are parseable Nginx combined logs (`bad_format=0`) and each file is 100% POST. This does not eliminate every method shortcut by itself, but it removes the previous GET-only shape for the major attack stages while keeping log format compatible with the existing ML pipeline.

## Nikto Stage 1補強

PR feedback noted that stage 1 should combine the manual sensitive-path probe with a Nikto scanner batch. A controlled Nikto run was collected against the local Nginx/TixMaster lab target with a 45-second cap:

```text
collection: Nikto v2.6.1 real scan through local Nginx with a 45-second cap
formal mapped log: collected/nginx01_batch_nikto_scan_xff_clean_003.log
stage: 1
label: DICURIGAI
tool: nikto
count: 4479
source IP: 10.99.1.41 via X-Forwarded-For
```

The formal mapped file is a parser-compatible subset of the real Nginx access log. It excludes malformed/pre-header rejection lines and lines where Nginx could not apply the X-Forwarded-For source IP. This keeps the dataset compatible with the current Nginx combined-log parser while preserving real tool-generated traffic.

Caveat: Nikto still has a strong scanner User-Agent fingerprint. It is included because stage 1 explicitly covers sensitive-path/scanner probing, but it should not be treated as solving UA diversity by itself.



## Parser-Compatible Clean Subsets

Some real tool/browser traffic can produce malformed or pre-header request lines that are valid Nginx observations but not accepted by the current combined-log parser. To keep the formal ML dataset parser-compatible, clean subset files were created without editing the original source logs.

| Formal mapped log | Source log | Removed | Reason |
|---|---|---:|---|
| `logs/access1_Aman_clean.log` | `logs/access1_Aman.log` | 1 | malformed/non-combined line |
| `collected/nginx01_batch_xss_zap_fullscan_clean_001.log` | `collected/nginx01_batch_xss_zap_fullscan_001.log` | 3 | ZAP TLS/pre-header probe lines such as `"\x16"` |
| `LFI_method_record/access4_Local_file_inclusion_2_wfuzz_clean.log` | `LFI_method_record/access4_Local_file_inclusion_2_wfuzz.log` | 1 | malformed/non-combined line |

The original raw logs are preserved for auditability. `stage_log_map.txt` points to the clean files so dataset conversion and diversity checks do not fail on malformed lines.

## Morning Round 005

These batches were collected in a real morning time window (Asia/Taipei, UTC+8) on 2026-09-02. The purpose is to add time/IP/UA diversity without editing timestamps. Because the current ZeroTier IP configured in `docker-compose.nginx.yml` was not present on the host, this round used a temporary localhost Nginx container (`127.0.0.1:8080`) without changing the compose file.

| Log | Stage | Tool | Count | Method shape | Diversity change |
|---|---:|---|---:|---|---|
| `collected/nginx01_batch_sqli_sqlmap_randomua_morning_005.log` | 2 | sqlmap | 75 | GET | morning window, `10.120.2.51`, sqlmap `--random-agent` |
| `collected/nginx01_batch_xss_ffuf_browserua_morning_005.log` | 3 | ffuf | 30 | GET | morning window, `10.120.3.51`, browser-like Chrome UA |
| `collected/nginx01_batch_path_traversal_ffuf_morning_005.log` | 4 | ffuf | 33 | GET | morning window, `10.120.4.51`, browser-like Safari UA |
| `collected/nginx01_batch_command_injection_ffuf_browserua_morning_005.log` | 5 | ffuf | 30 | GET | morning window, `10.120.5.51`, browser-like Chrome/Linux UA |
| `collected/nginx01_batch_double_encoding_ffuf_morning_005.log` | 7 | ffuf | 34 | GET | morning window, `10.120.7.51`, browser-like Firefox UA |
| `collected/nginx01_batch_url_encoding_count_ffuf_morning_005.log` | 8 | ffuf | 36 | GET | morning window, `10.120.8.51`, browser-like Edge UA |
| `collected/nginx01_batch_special_chars_dense_ffuf_morning_005.log` | 9 | ffuf | 30 | GET | morning window, `10.120.9.51`, browser-like iPad Safari UA |
| `collected/nginx01_batch_scanner_ua_gobuster_morning_008.log` | 10 | gobuster | 33 | GET | morning window, `10.120.10.54`, alternate gobuster UA; wildcard length excluded |
| `collected/nginx01_batch_abnormal_methods_ffuf_morning_006.log` | 11 | ffuf | 100 | PUT/DELETE/OPTIONS/PATCH/HEAD | morning window, `10.120.11.52`, browser-like Chrome UA |
| `collected/nginx01_batch_abnormal_url_ffuf_morning_005.log` | 12 | ffuf | 30 | GET | morning window, `10.120.12.51`, browser-like Android Firefox UA |

Validation result for this round: all ten files are parseable Nginx combined logs (`bad_format=0`), use the new `10.120.x.x` lab source range, and were collected during the real morning window. This round is for time/IP/UA diversity; POST method diversity is covered by the POST Method Diversity Round 004.

## Afternoon Local-IP Round 006

These batches were collected in a real afternoon time window (Asia/Taipei, UTC+8) on 2026-09-02. The Nginx container was bound to the current host Wi-Fi IP `192.168.0.112:8080`, and the attack tools targeted `http://192.168.0.112:8080` instead of the previous ZeroTier IP. `X-Forwarded-For` was also set to `192.168.0.112`, so the Nginx combined access log records the current host IP for this lab collection round.

| Log | Stage | Tool | Count | Source IP | Notes |
|---|---:|---|---:|---|---|
| `collected/nginx01_batch_sqli_sqlmap_randomua_afternoon_localip_006.log` | 2 | sqlmap | 75 | `192.168.0.112` | real sqlmap traffic, random-agent |
| `collected/nginx01_batch_xss_ffuf_afternoon_localip_006.log` | 3 | ffuf | 30 | `192.168.0.112` | XSS payload traffic, browser-like UA |
| `collected/nginx01_batch_path_traversal_ffuf_afternoon_localip_006.log` | 4 | ffuf | 33 | `192.168.0.112` | traversal payload traffic against attachment sink |
| `collected/nginx01_batch_command_injection_ffuf_afternoon_localip_006.log` | 5 | ffuf | 30 | `192.168.0.112` | command injection payload traffic |
| `collected/nginx01_batch_double_encoding_ffuf_afternoon_localip_006.log` | 7 | ffuf | 34 | `192.168.0.112` | double-encoded payload traffic |
| `collected/nginx01_batch_url_encoding_count_ffuf_afternoon_localip_006.log` | 8 | ffuf | 36 | `192.168.0.112` | URL-encoding-heavy payload traffic |
| `collected/nginx01_batch_special_chars_dense_ffuf_afternoon_localip_006.log` | 9 | ffuf | 30 | `192.168.0.112` | special-character-dense payload traffic |
| `collected/nginx01_batch_scanner_ua_gobuster_afternoon_localip_006.log` | 10 | gobuster | 33 | `192.168.0.112` | scanner UA traffic; wildcard response length excluded |
| `collected/nginx01_batch_abnormal_methods_ffuf_afternoon_localip_006.log` | 11 | ffuf | 100 | `192.168.0.112` | PUT/DELETE/OPTIONS/PATCH/HEAD method traffic |
| `collected/nginx01_batch_abnormal_url_ffuf_afternoon_localip_006.log` | 12 | ffuf | 30 | `192.168.0.112` | abnormal URL structure traffic |

Validation result: all ten afternoon local-IP files are parser-compatible (`bad_format=0`), and every line records source IP `192.168.0.112`. This round improves real time-window coverage and aligns collection with the current host IP, but it is still a local lab setup rather than true multi-machine source diversity.

## Stage 10 UA/Referrer/Method Diversity Round 007

Diagnosis found that all prior stage 10 batches collapsed on 4 of 5 support features once merged: `os_type`, `is_bot`, and `referrer_type` were completely collapsed (`collapsed=True`, single value), and `request_method` was always `GET`. Root cause (`dataset_health/feature_engineering.py`'s `parse_os()`): gobuster's default UA string (`gobuster/x.y`) contains none of the `windows`/`android`/`iphone`/`ipad`/`linux`/`mac`/`bot`/`crawler`/`spider` keywords the classifier checks, so it always fell into `os_type=7 (other)`; `is_bot` is derived from `os_type==6` so it was always 0; gobuster sends no `Referer` by default; gobuster `dir` mode is GET-only. Stage 10 has no `DEFINING_FLAG`/`DEFINING_PREDICATE` in `config.py`, so there is no "must look like a scanner" constraint being violated by varying these — the fix is to keep hitting the same kind of sensitive/enumeration paths with a real tool, but control UA/Referer/Method so real requests land in the categories that were missing.

`collected/nginx01_batch_scanner_ua_diversity_007.log` (384 lines) was collected with `feroxbuster` run from a Kali VM against the host Nginx (bridged network, `NGINX_BIND_HOST=0.0.0.0` in `.env`, target `http://192.168.194.86:8080/`), against the same 8-word sensitive-path wordlist used for other stage 10 batches. 12 runs: a UA sweep (win/android/ios/linux/mac/bot/other, no Referer) and a Referer sweep (UA fixed to the win string; local/ip/search/social/external), each run using `-m GET,HEAD,OPTIONS` so every run also contributes method diversity. See `.meta.txt` for the exact UA/Referer strings used per run.

Standalone validation: `Diversity_stage=0.5000` on the new file alone (`n=384`). Merged with the existing stage 10 batches (`n=516`, clears `MIN_SAMPLES=200`, no longer provisional): `Diversity_stage` rose from **0.017 to 0.5603**. `os_type`/`is_bot`/`referrer_type` are no longer `collapsed=True`; `request_method` coverage is `0.38` (GET/HEAD/OPTIONS present; DELETE/PATCH/POST/PUT/TRACE intentionally left to stage 11, which already covers abnormal methods).

Caveat carried forward: all 384 lines record source IP `172.20.0.1` (the VM's own docker-bridge address) — this round fixes UA/Referer/Method collapse but does not add new IP diversity for stage 10.

## Night Sample-Count Top-Up Round 007

These batches were collected in a real night time window (Asia/Taipei, UTC+8) on 2026-09-04 to move the previously provisional low-count stages past the 200-sample threshold. The traffic was generated by ffuf running from a local Kali Docker image against the Nginx/backend target at `http://192.168.0.112:8080`; PowerShell only handled batch capture.

| Log | Stage | Tool | Count | Source IP | Notes |
|---|---:|---|---:|---|---|
| `collected/nginx01_batch_double_encoding_ffuf_night_007.log` | 7 | ffuf | 34 | `10.140.7.71` | Double-encoding payloads against the attachment sink |
| `collected/nginx01_batch_url_encoding_count_ffuf_night_007.log` | 8 | ffuf | 36 | `10.140.8.71` | URL-encoding-heavy payloads against `/api/events?keyword=` |
| `collected/nginx01_batch_abnormal_url_ffuf_night_clean_007.log` | 12 | ffuf | 55 | `10.140.12.71` | Clean subset from a 60-request abnormal URL run; 5 Nginx pre-header `400 "-" "-"` lines were excluded from the formal stage map |

Validation result: all three mapped files are parser-compatible (`bad_format=0`). The updated mapped sample counts are stage 7 = 204, stage 8 = 216, and stage 12 = 205.
