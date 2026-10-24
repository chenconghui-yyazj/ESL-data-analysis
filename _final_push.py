# -*- coding: utf-8 -*-
import subprocess, os
d = r"C:\Users\陈聪惠\Desktop\维界投影数据分析"
log = os.path.join(d, "_final_push.log")
def run(args, f):
    p = subprocess.run(args, cwd=d, capture_output=True, text=True, encoding="utf-8", errors="replace")
    f.write("$ " + " ".join(args) + "\n" + (p.stdout or "") + (("[ERR] " + p.stderr) if p.stderr else "") + "\n---\n")
    f.flush()
    return p.returncode
with open(log, "w", encoding="utf-8") as f:
    run(["git", "add", "-A"], f)
    rc = run(["git", "commit", "-m", "补全项目：requirements依赖、核心分析脚本、数据字典、数据来源清单、项目亮点、README更新"], f)
    run(["git", "push", "origin", "master"], f)
    rc2, out = run(["git", "ls-files"], f)
    n = len([l for l in out.splitlines() if l.strip()])
    f.write("TRACKED=" + str(n) + "\n")
    f.write("DONE\n")
print("commit_rc=", rc, "files=", n)
