對照規格 §3.1 的 12 個 stage,可以這樣對應:

| Log                                | 筆數  | 對應 stage                          |
|------------------------------------|-------|-------------------------------------|
| nginx01_batch_sqlmap_sqli_001.log  | 378   | stage 2 SQLi                        |
| nginx01_batch_xss_001.log          | 250   | stage 3 XSS                         |
| nginx01_batch_path_traversal_001.log | 120 | stage 4 路徑遍歷                     |
| nginx01_batch_nikto_scan_001.log   | 15843 | stage 1 敏感路徑 (最接近，但 nikto 涵蓋範圍更廣) |
| nginx01_batch_dicurigai_probe_001.log | 100 | 不對應單一 stage (故意混合，見下)    |
