"""Dependency-free drafts from recorded facts; all HTML content is escaped."""
from html import escape

from .store import WorkflowError, read_json


def facts(profile):
    basic = profile.get("basic", {})
    headline = profile.get("headline", "")
    if isinstance(headline, dict):
        headline = headline.get("one_liner", "")
    sections = [(basic.get("name") or "待补姓名", [headline] if headline else ["待补职业定位"])]
    for item in profile.get("education", []):
        sections.append(("教育背景", [" · ".join(str(item.get(k, "")) for k in ("school", "major", "level", "start", "end") if item.get(k))]))
    for item in profile.get("experiences", []):
        lines = [item.get("situation", ""), item.get("task", "")]
        lines += item.get("actions", []) + item.get("results", [])
        sections.append((item.get("title") or "待补经历名称", [str(v) for v in lines if v] or ["待补行动与结果证据"]))
    skills = profile.get("skills", [])
    if isinstance(skills, dict):
        skills = [v for values in skills.values() if isinstance(values, list) for v in values]
    if skills:
        sections.append(("技能", ["、".join(map(str, skills))]))
    return sections


def markdown(profile):
    return "\n\n".join("## " + title + "\n\n" + "\n".join("- " + line for line in lines) for title, lines in facts(profile)) + "\n"


def deck(profile):
    slides = "".join('<section class="slide" aria-label="' + escape(title, quote=True) + '"><h1>' + escape(title) + '</h1>' + "".join("<p>" + escape(line) + "</p>" for line in lines) + "</section>" for title, lines in facts(profile))
    return '''<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>自我介绍 · CareerFlow</title><style>
*{box-sizing:border-box}body{margin:0;background:#f7f8fc;color:#18243a;font:clamp(18px,2.2vw,28px)/1.7 system-ui,sans-serif}
main{max-width:1100px;margin:auto}.slide{padding:8vh 7vw;min-height:90vh;overflow-wrap:anywhere}h1{line-height:1.25;color:#2548a5}p{max-width:900px}
nav{position:sticky;bottom:0;background:#fff;padding:12px;text-align:center;border-top:1px solid #ddd}button{font:inherit;padding:4px 18px;margin:0 8px;border:1px solid #9caac8;border-radius:8px;background:white}
@media print{nav{display:none}.slide{break-after:page;min-height:0}}
</style><main>''' + slides + '''</main><nav aria-label="翻页"><button id="prev">上一页</button><span id="counter" aria-live="polite"></span><button id="next">下一页</button></nav>
<script>
const slides=[...document.querySelectorAll('.slide')];let index=0;
function show(n){index=Math.max(0,Math.min(slides.length-1,n));slides.forEach((s,i)=>s.hidden=i!==index);document.getElementById('counter').textContent=`${index+1} / ${slides.length}`;document.getElementById('prev').disabled=index===0;document.getElementById('next').disabled=index===slides.length-1;}
document.getElementById('prev').onclick=()=>show(index-1);document.getElementById('next').onclick=()=>show(index+1);
document.addEventListener('keydown',e=>{if(['ArrowRight','PageDown',' '].includes(e.key)){e.preventDefault();show(index+1)}if(['ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();show(index-1)}});
addEventListener('beforeprint',()=>slides.forEach(s=>s.hidden=false));addEventListener('afterprint',()=>show(index));show(0);
</script></html>'''


def render(ws, kind, output):
    from pathlib import Path
    profile = read_json(ws.root / "profile.json")
    path = Path(output).expanduser().resolve()
    if path.exists():
        raise WorkflowError("Render target exists; choose a new version path")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(markdown(profile) if kind == "resume" else deck(profile))
    return {"path": str(path), "kind": kind, "state": "draft", "note": "仅按档案排版，未进行 JD 匹配、内容润色或演讲计时。"}
