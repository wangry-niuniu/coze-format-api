from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Optional
import json
import re

app = FastAPI()

# 1. 定义前台接待员：告诉扣子我们要接收哪些参数
class FormatRequest(BaseModel):
    pure_content: Optional[str] = ""
    category: Optional[str] = "内部教辅资料"
    title_info: Optional[str] = "教辅排版引擎"
    theme_colors: Optional[str] = ""
    zjmk_ty: Optional[str] = ""
    zjmk_zs: Optional[str] = ""
    original_text: Optional[Any] = []  # 接收那个复杂的数组对象

# 2. 开通对外服务的接口地址
@app.post("/generate_html")
async def generate_html(req: FormatRequest):
    # =======================================================
    # 🚨 战区一：终极防护，提取与清洗 HTML 正文 (pure_content)
    # =======================================================
    content_area = req.pure_content
    
    if isinstance(content_area, str):
        # 1. 尝试解包（如果 Coze 把整个字典连带 debug_chunk_count 一起传过来了）
        try:
            parsed = json.loads(content_area)
            if isinstance(parsed, dict) and "pure_content" in parsed:
                content_area = parsed["pure_content"]
        except Exception:
            pass
        
        # 2. 暴力解除转义：让 class=\"xxx\" 完美还原成 class="xxx"
        content_area = str(content_area).replace('\\"', '"').replace('\\n', '')
        
        # 3. 终极过滤：如果它依然是一个带有 {" 前缀的残留废料
        if content_area.startswith('{"<'):
            content_area = re.sub(r'^\{"', '', content_area)
            content_area = re.sub(r'",\s*"debug_chunk_count".*?\}$', '', content_area, flags=re.DOTALL)

    # 提取常规的字符串参数
    doc_category = req.category
    doc_title = req.title_info
    theme_colors = req.theme_colors
    clean_zjmk_ty = req.zjmk_ty.strip()
    clean_zjmk_zs = req.zjmk_zs.strip()

    # =======================================================
    # 🚨 战区二：终极解包，提取生肉文本 (original_text)
    # =======================================================
    original_raw = req.original_text

    if isinstance(original_raw, str):
        try:
            original_raw = json.loads(original_raw)
        except Exception:
            pass

    if isinstance(original_raw, str):
        try:
            cleaned_str = original_raw.replace('\\n', '\n').replace('\\"', '"')
            original_raw = json.loads(cleaned_str)
        except Exception:
            pass

    extracted_text = ""
    if isinstance(original_raw, list):
        for item in original_raw:
            if isinstance(item, dict) and item.get("data"):
                extracted_text += str(item["data"]) + "\n"
            elif isinstance(item, str):
                extracted_text += item + "\n"
    elif isinstance(original_raw, dict) and original_raw.get("data"):
        extracted_text = str(original_raw["data"])
    else:
        extracted_text = str(original_raw)

    # =======================================================
    # 🚨 战区三：Markdown 符号大清洗（防漏字比对误报）
    # =======================================================
    if extracted_text:
        extracted_text = re.sub(r'(?m)^#+\s*', '', extracted_text)  # 去标题
        extracted_text = re.sub(r'\*+', '', extracted_text)         # 去加粗
        extracted_text = re.sub(r'(?m)^[-+]\s+', '', extracted_text)# 去列表
        extracted_text = re.sub(r'(?m)^>\s*', '', extracted_text)   # 去引用
        extracted_text = re.sub(r'[_＿]{2,}', '', extracted_text)   # 去下划线占位符

    final_style_content = clean_zjmk_ty + "\n\n" + clean_zjmk_zs
    safe_original_json = json.dumps(extracted_text.strip(), ensure_ascii=False).replace("</", "<\\/")

    # =======================================================
    # 🚨 战区四：终极引擎模板组装 (HTML/CSS/JS)
    # =======================================================
    html_template = "\ufeff" + """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>__DOC_TITLE__</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/color-thief/2.3.0/color-thief.umd.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/diff_match_patch/20121119/diff_match_patch.js"></script>

    <style id="dynamic-style">
        /* 基础打印与重置 */
        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; box-sizing: border-box; }
        
        :root {
            /* 默认主题 */
            --c-primary: #52A89E; --c-star: #2D7A71; --c-highlight: #D59A44;
            --c-mod-point: #9A7EB4; --c-mod-mnemonic: #E88796; --c-mod-practice: #48BB78;
            --c-border: #CBE3E0; --c-case-bg: #EAF5F4; --c-secondary: #F4FAFA;
            --f-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
            --f-size-base: 14px; --f-size-title: 18px; --line-height: 1.8;
            --letter-spacing: 0px; --radius-card: 6px;
        }
        __THEME_COLORS__

        body { background-color: #F8FAFC; font-family: var(--f-family, sans-serif); margin: 0; padding: 0; display: flex; gap: 30px; justify-content: center; overflow-x: hidden; color: #334155; }
        
        /* A4 纸张高级投影 */
        .a4-container { flex: 1; max-width: 210mm; display: flex; flex-direction: column; gap: 20px; align-items: center; padding-top: 30px; padding-bottom: 40px; transition: margin-right 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
        .a4-page { width: 210mm; min-height: 297mm; height: auto; overflow: visible; position: relative; padding: 18mm 15mm 30mm 15mm; page-break-after: always; background: #FFFFFF; box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08), 0 2px 6px rgba(0,0,0,0.03); border-radius: 2px; flex-shrink: 0; }
        
        .page-content table { width: 100%; border-collapse: collapse; table-layout: fixed; word-wrap: break-word; margin: 15px 0; font-size: 13px; }
        .page-content th, .page-content td { border: 1px solid var(--c-border); padding: 8px 12px; text-align: left; }
        .page-content th { background-color: var(--c-case-bg); color: var(--c-primary); font-weight: bold; }
        
        .page-content, .page-header, .page-footer { transition: all 0.2s ease; border-radius: 4px; }
        .page-content { display: flow-root; width: 100%; font-size: var(--f-size-base, 14px); line-height: var(--line-height, 1.8); letter-spacing: var(--letter-spacing, 0px); font-family: var(--f-family) !important; }
        
        /* 🚀 修复版页眉页脚 */
        .page-header { position: absolute; top: 12mm; left: 15mm; right: 15mm; display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 1.5px solid var(--c-border); padding-bottom: 6px; font-size: 10px; color: var(--c-star); font-weight: bold; }
        .page-footer { position: absolute; bottom: 10mm; left: 15mm; right: 15mm; display: flex; justify-content: space-between; align-items: center; font-size: 10px; color: var(--c-primary); opacity: 0.8; border-top: 1px dashed var(--c-border); padding-top: 6px; }
        .page-footer span { flex: 1; } .page-footer .f-left { text-align: left; } .page-footer .f-center { text-align: center; font-family: Arial, sans-serif; font-weight: bold; } .page-footer .f-right { text-align: right; }

        @media screen { 
            .page-content[contenteditable="true"]:hover, .page-header[contenteditable="true"]:hover, .page-footer[contenteditable="true"]:hover { box-shadow: 0 0 0 2px rgba(113, 176, 246, 0.3) inset; background-color: rgba(113, 176, 246, 0.02); cursor: text; } 
            .eraser-mode * { cursor: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="%23EF4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 20H7L3 16C2.5 15.5 2.5 14.5 3 14L13 4C13.5 3.5 14.5 3.5 15 4L20 9C20.5 9.5 20.5 10.5 20 11L11 20H20V20Z"/><line x1="18" y1="13" x2="11" y2="20"/></svg>') 0 20, crosshair !important; }
        }

        /* 🚀 现代悬浮控制面板 (Glassmorphism) */
        .control-panel { 
            width: 320px; background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
            padding: 24px; border-radius: 16px; box-shadow: 0 10px 40px rgba(0,0,0,0.08), inset 0 1px 0 rgba(255,255,255,0.6);
            border: 1px solid rgba(226, 232, 240, 0.8); height: fit-content; position: sticky; top: 30px; z-index: 1000; flex-shrink: 0; max-height: calc(100vh - 60px); overflow-y: auto; 
        }
        .control-panel::-webkit-scrollbar { width: 4px; } .control-panel::-webkit-scrollbar-thumb { background-color: #cbd5e1; border-radius: 4px; }
        
        .panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #e2e8f0; padding-bottom: 12px; }
        .panel-header h3 { margin: 0; font-size: 16px; color: #1e293b; font-weight: 800; display: flex; align-items: center; gap: 6px; }
        .reset-btn { font-size: 12px; padding: 4px 10px; cursor: pointer; border: 1px solid #e2e8f0; background: #f8fafc; border-radius: 20px; color: #64748b; font-weight: 600; transition: all 0.2s; }
        .reset-btn:hover { background: #f1f5f9; color: #0f172a; }

        /* 功能区块卡片化 */
        .tool-card { background: #ffffff; padding: 16px; border-radius: 12px; border: 1px solid #f1f5f9; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
        
        .ctrl-btn { width: 100%; padding: 12px; margin-bottom: 10px; border: 1px solid transparent; border-radius: 8px; cursor: pointer; transition: all 0.2s ease; font-size: 13px; font-weight: 700; display: flex; align-items: center; justify-content: center; gap: 8px; letter-spacing: 0.3px; }
        .ctrl-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        .ctrl-btn:active { transform: translateY(0); }
        
        .btn-color { background: #fefce8; color: #a16207; border-color: #fef08a; }
        .btn-brush { background: #f0fdf4; color: #15803d; border-color: #bbf7d0; }
        .btn-eraser { background: #fef2f2; color: #b91c1c; border-color: #fecaca; }
        .btn-inspector { background: #faf5ff; color: #6b21a8; border-color: #e9d5ff; }
        .btn-diff { background: #eff6ff; color: #1d4ed8; border-color: #bfdbfe; margin-bottom: 0; }
        .btn-export { background: var(--c-primary, #0f172a); color: #fff; box-shadow: 0 6px 16px color-mix(in srgb, var(--c-primary) 40%, transparent); margin-top: 10px; padding: 14px; font-size: 14px;}

        /* 色板样式回归 */
        .color-row { display:flex; justify-content:space-between; margin-bottom:8px; font-size:12px; align-items:center; border-bottom:1px dashed #e2e8f0; padding-bottom:6px; }
        .color-tool-btn { background:#f8fafc; border:1px solid #e2e8f0; border-radius:4px; cursor:pointer; font-size:11px; padding:3px 6px; display: flex; align-items: center; justify-content: center; color: #475569; font-weight: 600; transition: all 0.2s;}
        .color-tool-btn:hover { background:#e2e8f0; color: #0f172a;}

        .ctrl-group { margin-bottom: 16px; } 
        .ctrl-group label { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 8px; color: #64748b; font-weight: 600; }
        .ctrl-group label span { color: #0f172a; font-weight: 700; }
        .ctrl-group select { width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px; outline: none; background: #f8fafc; font-weight: 500; cursor: pointer; }
        
        input[type=range] { -webkit-appearance: none; width: 100%; background: transparent; }
        input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; height: 16px; width: 16px; border-radius: 50%; background: var(--c-primary); cursor: pointer; margin-top: -6px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
        input[type=range]::-webkit-slider-runnable-track { width: 100%; height: 4px; cursor: pointer; background: #e2e8f0; border-radius: 2px; }

        /* 寻色悬浮窗与 Notion级菜单 */
        #inspector-tooltip { 
            position: fixed; display: none; background: rgba(15, 23, 42, 0.9); backdrop-filter: blur(8px); 
            color: #f8fafc; padding: 14px 18px; border-radius: 12px; font-size: 12px; z-index: 99999; 
            pointer-events: none; line-height: 1.6; box-shadow: 0 10px 25px rgba(0,0,0,0.25); 
            max-width: 320px; word-break: break-all; border: 1px solid rgba(255,255,255,0.15); 
        }
        
        #notion-hover-menu {
            position: fixed; display: none; background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(8px);
            padding: 6px 12px; border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,0.2); z-index: 10000;
            gap: 12px; align-items: center; transition: opacity 0.2s; border: 1px solid rgba(255,255,255,0.15);
        }
        .hover-color-group { display: flex; gap: 6px; align-items: center; }
        .hover-color-btn { width: 18px; height: 18px; border-radius: 50%; cursor: pointer; border: 1px solid rgba(255,255,255,0.3); transition: transform 0.1s; }
        .hover-color-btn:hover { transform: scale(1.2); }
        .hover-label { color: #cbd5e1; font-size: 12px; font-weight: bold; margin-right: 4px; cursor: default;}
        .hover-divider { width: 1px; height: 16px; background: rgba(255,255,255,0.2); }

        /* Diff 侧边栏优化 */
        #diff-sidebar { position: fixed; right: -450px; top: 0; width: 400px; height: 100vh; background: rgba(255,255,255,0.98); backdrop-filter: blur(10px); box-shadow: -10px 0 30px rgba(0,0,0,0.1); z-index: 9999; transition: right 0.4s cubic-bezier(0.16, 1, 0.3, 1); display: flex; flex-direction: column; font-family: sans-serif; }
        #diff-sidebar.active { right: 0; }
        .diff-header { padding: 24px; border-bottom: 1px solid #eff6ff; display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #eff6ff, #ffffff); color: #1e3a8a; font-weight: 800; font-size: 16px; }
        .diff-content { flex: 1; overflow-y: auto; padding: 24px; font-size: 14px; line-height: 1.8; white-space: pre-wrap; color: #334155; }
        .diff-missing { background-color: #fee2e2; color: #b91c1c; font-weight: 800; padding: 2px 4px; border-radius: 4px; cursor: text; border-bottom: 2px solid #ef4444; }
        .diff-equal { color: #94a3b8; }

        @media print {
            @page { size: A4; margin: 0; }
            html, body { width: 210mm; margin: 0; padding: 0; background: #fff; }
            body { display: block; background: transparent; padding: 0; }
            .control-panel, #diff-sidebar, #notion-hover-menu { display: none !important; }
            .a4-container { display: block; overflow: visible; max-width: none; gap: 0; padding: 0; margin: 0; }
            .a4-page { margin: 0; padding: 18mm 15mm 30mm 15mm; box-shadow: none; border: none; width: 210mm; min-height: 297mm; height: auto; box-sizing: border-box; page-break-after: always; page-break-inside: auto; }
            .a4-page:last-child { page-break-after: auto; }
        }
        __FINAL_STYLE_CONTENT__
    </style>
</head>
<body>
    <div id="inspector-tooltip"></div>
    <div id="notion-hover-menu"></div>
    
    <div class="control-panel no-print">
        <div class="panel-header">
            <h3>⚙️ 工作台</h3>
            <button class="reset-btn" onclick="resetSettings()">↺ 恢复默认</button>
        </div>

        <div class="tool-card">
            <input type="file" id="color-image-upload" accept="image/*" style="display: none;">
            <button class="ctrl-btn btn-color" onclick="document.getElementById('color-image-upload').click()">
                🎨 传色卡·智能生成主题
            </button>
            <div id="extracted-colors-display" style="display:flex; gap:4px; height: 12px; border-radius: 12px; overflow: hidden; margin-bottom: 12px;"></div>

            <div style="display: flex; gap: 6px; margin-bottom: 10px;">
                <button class="ctrl-btn btn-brush" id="btn-format-painter" onclick="toggleFormatPainter()" style="flex: 1; padding: 10px 2px; font-size: 12px; margin: 0;">🪄 格式刷</button>
                <button class="ctrl-btn btn-eraser" id="btn-eraser" onclick="toggleEraser()" style="flex: 1; padding: 10px 2px; font-size: 12px; margin: 0;">🧹 橡皮擦</button>
                <button class="ctrl-btn btn-inspector" id="btn-inspector" onclick="toggleInspector()" style="flex: 1; padding: 10px 2px; font-size: 12px; margin: 0;">🔍 寻色器</button>
            </div>

            <button class="ctrl-btn btn-diff" onclick="toggleDiffSidebar()">👀 原文防漏字核对</button>
        </div>

        <div class="tool-card" id="color-panels-card">
            <div class="ctrl-group" id="group-base-colors" style="margin-bottom: 16px;"><label>🧊 基础色板</label><div id="panel-base-colors"></div></div>
            <div class="ctrl-group" id="group-comp-colors" style="margin-bottom: 0;"><label>🧩 组件专属色</label><div id="panel-comp-colors"></div></div>
        </div>

        <div class="tool-card">
            <div class="ctrl-group">
                <label>字体风格</label>
                <select id="sel-font">
                    <optgroup label="[现代UI风格]"><option value='"PingFang SC", "Microsoft YaHei", sans-serif'>现代黑体 (默认)</option><option value='"LXGW WenKai", "STKaiti", "KaiTi", serif'>手账文楷 (优雅)</option></optgroup>
                    <optgroup label="[传统公文风]"><option value='"KaiTi_GB2312", "KaiTi", serif'>标准楷体 (公文)</option><option value='"Source Han Serif SC", "STSong", "SimSun", serif'>标准宋体 (严肃)</option></optgroup>
                </select>
            </div>
            <div class="ctrl-group"><label>正文字号 <span id="val-f-size-base">14px</span></label><input type="range" id="sl-f-size-base" min="12" max="24" value="14"></div>
            <div class="ctrl-group"><label>标题字号 <span id="val-f-size-title">18px</span></label><input type="range" id="sl-f-size-title" min="14" max="36" value="18"></div>
            <div class="ctrl-group"><label>全局行距 <span id="val-line-height">1.8</span></label><input type="range" id="sl-line-height" min="1.2" max="3" step="0.1" value="1.8"></div>
            <div class="ctrl-group"><label>全局字距 <span id="val-letter-spacing">0px</span></label><input type="range" id="sl-letter-spacing" min="-1" max="10" step="0.5" value="0"></div>
            <div class="ctrl-group" style="margin-bottom: 0;"><label>卡片圆角 <span id="val-radius-card">6px</span></label><input type="range" id="sl-radius-card" min="0" max="30" value="6"></div>
        </div>

        <button class="ctrl-btn btn-export" onclick="recalculatePagination(); setTimeout(()=>window.print(), 500);">💾 导出 PDF 文件</button>
    </div>

    <div class="a4-container" id="main-a4-container"></div>

    <div id="diff-sidebar" class="no-print">
        <div class="diff-header">
            <span>🚨 防漏字智能报告</span>
            <button onclick="toggleDiffSidebar()" style="border:none; background:rgba(255,255,255,0.5); cursor:pointer; font-size:14px; color:#1e3a8a; font-weight:bold; padding: 4px 10px; border-radius: 20px;">关闭</button>
        </div>
        <div style="padding:15px 24px; background:#eff6ff; font-size:12px; color:#1e293b; border-bottom:1px solid #bfdbfe;">
            * <strong style="color:#b91c1c;">红底粗字</strong> 为大模型排版时漏掉的内容。请使用 [🪄 格式刷] 或悬浮菜单补齐。
        </div>
        <div class="diff-content" id="diff-content-area">正在为您极速比对，请稍候...</div>
    </div>

    <div id="source-data" style="display:none;">__CONTENT_AREA__</div>
    <script id="style-data" type="text/plain">__THEME_COLORS__</script>
    <script id="raw-source-data" type="application/json">__ORIGINAL_TEXT__</script>

    <script>
        const rootStyle = document.documentElement.style;
        const DOC_EN_TITLE = '__DOC_CATEGORY__'; const DOC_ZH_TITLE = '__DOC_TITLE__';
        function safeGetStorage(key) { try { return localStorage.getItem(key); } catch (e) { return null; } }
        function safeSetStorage(key, val) { try { localStorage.setItem(key, val); } catch (e) {} }
        let pageCount = 0; let dynamicMaxHeight = 850;
        function getSafeMaxHeight() { const tempPage = document.createElement('div'); tempPage.className = 'a4-page'; tempPage.style.visibility = 'hidden'; tempPage.style.position = 'absolute'; document.body.appendChild(tempPage); const rect = tempPage.getBoundingClientRect(); const realHeight = rect.height || 1122; document.body.removeChild(tempPage); return realHeight * 0.78; }
        window.resetSettings = function() { if(confirm('确定要清空所有自定义设置吗？')) { try { localStorage.clear(); } catch(e) {} location.reload(); } };
        function createNewPage() { pageCount++; const page = document.createElement('div'); page.className = 'a4-page'; page.innerHTML = '<div class="page-header" contenteditable="true" spellcheck="false"><span>' + DOC_EN_TITLE + '</span><span>' + DOC_ZH_TITLE + '</span></div><div class="page-content" contenteditable="true" spellcheck="false"></div><div class="page-footer" contenteditable="true" spellcheck="false"><span class="f-left">内部教研</span><span class="f-center">- ' + pageCount + ' -</span><span class="f-right">独家整理</span></div>'; document.getElementById('main-a4-container').appendChild(page); return page; }
        document.addEventListener('input', function(e) { if (e.target.classList.contains('page-header')) { const newHTML = e.target.innerHTML; document.querySelectorAll('.page-header').forEach(el => { if (el !== e.target) el.innerHTML = newHTML; }); } });
        function runPaginationEngine(nodes) { let currentPage = createNewPage(); let currentContent = currentPage.querySelector('.page-content'); let previousNode = null; let currentTitleLevel = ""; nodes.forEach(node => { const isTitleClass = node.className && node.className.includes('title-'); if (isTitleClass) { const titleText = node.innerText.trim(); if (titleText === currentTitleLevel) return; currentTitleLevel = titleText; } currentContent.appendChild(node); if (currentContent.offsetHeight > dynamicMaxHeight) { if (currentContent.children.length <= 1) { } else { currentContent.removeChild(node); let nodeToMoveWith = null; if (previousNode) { const isHeading = previousNode.tagName.match(/^H[1-6]$/i); const isPrevTitleClass = previousNode.className && previousNode.className.includes('title-'); if (isHeading || isPrevTitleClass) { nodeToMoveWith = previousNode; currentContent.removeChild(previousNode); } } currentPage = createNewPage(); currentContent = currentPage.querySelector('.page-content'); if (nodeToMoveWith) currentContent.appendChild(nodeToMoveWith); currentContent.appendChild(node); } } if (node.innerText && node.innerText.trim() !== "") { previousNode = node; } }); }
        window.recalculatePagination = function() { const allContents = document.querySelectorAll('.a4-page .page-content'); if (allContents.length === 0) return; const allNodes = []; allContents.forEach(content => { Array.from(content.children).forEach(child => { allNodes.push(child); }); }); document.querySelectorAll('.a4-page').forEach(page => page.remove()); pageCount = 0; dynamicMaxHeight = getSafeMaxHeight(); runPaginationEngine(allNodes); };
        
        function initLayoutControls() { ['f-size-base', 'f-size-title', 'line-height', 'letter-spacing', 'radius-card'].forEach(id => { const el = document.getElementById('sl-' + id); const valSpan = document.getElementById('val-' + id); if(el) { let saved = safeGetStorage('--' + id); if(saved) { let numOnly = saved.replace(/[^0-9.-]/g, ''); el.value = numOnly; if(valSpan) valSpan.innerText = numOnly + (id.includes('line') ? '' : 'px'); rootStyle.setProperty('--' + id, saved); } el.addEventListener('input', (e) => { let val = e.target.value; let suffix = id.includes('line') ? '' : 'px'; if(valSpan) valSpan.innerText = val + suffix; rootStyle.setProperty('--' + id, val + suffix); safeSetStorage('--' + id, val + suffix); }); } }); const fontSel = document.getElementById('sel-font'); if(fontSel) { let savedFont = safeGetStorage('--f-family'); if(savedFont) { fontSel.value = savedFont; rootStyle.setProperty('--f-family', savedFont); } fontSel.addEventListener('change', (e) => { rootStyle.setProperty('--f-family', e.target.value); safeSetStorage('--f-family', e.target.value); }); } }

        // 🎨 找回的：智能色板生成与局部高亮函数
        window.applyToText = function(varName, command) { const color = getComputedStyle(document.documentElement).getPropertyValue(varName).trim(); if (color) document.execCommand(command, false, color); };
        let globalExtractedVars = [];
        
        // 🚨 刷新色板UI
        function initDynamicColorPanel() { 
            const baseContainer = document.getElementById('panel-base-colors'); 
            const compContainer = document.getElementById('panel-comp-colors'); 
            if(!baseContainer || !compContainer) return; 
            
            const styleText = document.getElementById('style-data').textContent; 
            let varsMatch = styleText.match(/--[a-zA-Z0-9-]+/g) || []; 
            globalExtractedVars = [...new Set(varsMatch)]; 
            if(globalExtractedVars.length === 0) globalExtractedVars = ['--c-primary', '--c-star', '--c-highlight']; 
            
            const baseKeywords = ['primary', 'star', 'base', 'text', 'bg', 'background', 'border', 'main', 'highlight']; 
            baseContainer.innerHTML = ''; compContainer.innerHTML = ''; 
            
            globalExtractedVars.forEach(v => { 
                let currentVal = getComputedStyle(document.documentElement).getPropertyValue(v).trim() || '#cccccc'; 
                let saved = safeGetStorage(v); 
                if(saved) { currentVal = saved; rootStyle.setProperty(v, saved); } 
                if (currentVal && currentVal.startsWith('#')) { 
                    const cleanName = v.replace('--c-','').replace('--','').toLowerCase(); 
                    const isBase = baseKeywords.some(kw => cleanName.includes(kw)); 
                    const targetContainer = isBase ? baseContainer : compContainer; 
                    
                    let wrapper = document.createElement('div'); 
                    wrapper.className = 'color-row'; 
                    wrapper.innerHTML = '<span style="color:#475569; flex-grow:1; font-weight:600; font-size:12px;" title="' + v + '">' + cleanName + '</span><div style="display:flex; align-items:center; gap:4px;"><input type="color" value="' + currentVal + '" class="dyn-color-picker" data-var="' + v + '" style="width:24px;height:24px;padding:0;border:none;cursor:pointer; border-radius:6px; background:transparent;"><button class="color-tool-btn" title="给选中的字上色" onclick="applyToText(\'' + v + '\', \'foreColor\')">[字]</button><button class="color-tool-btn" title="给选中的字加高亮背景" onclick="applyToText(\'' + v + '\', \'backColor\')">[底]</button></div>'; 
                    
                    wrapper.querySelector('input').addEventListener('input', (e) => { 
                        rootStyle.setProperty(v, e.target.value); 
                        safeSetStorage(v, e.target.value);
                        buildHoverToolbar(); // 颜色改变时，同步刷新悬浮菜单
                    }); 
                    targetContainer.appendChild(wrapper); 
                } 
            }); 
            if(compContainer.children.length === 0) document.getElementById('group-comp-colors').style.display = 'none'; 
            if(baseContainer.children.length === 0) document.getElementById('group-base-colors').style.display = 'none';
            buildHoverToolbar(); // 构建悬浮菜单
        }

        // 🎨 真正的实体化数学混色逻辑
        document.getElementById('color-image-upload').addEventListener('change', function(e) {
            const file = e.target.files[0]; if (!file) return;
            const img = new Image(); const reader = new FileReader();
            reader.onload = function(e) { img.src = e.target.result; };
            img.onload = function() {
                try {
                    const colorThief = new ColorThief();
                    const palette = colorThief.getPalette(img, 5);
                    if(!palette || palette.length < 2) throw new Error("色卡颜色过少");
                    
                    const getLum = (rgb) => 0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2];
                    const rgbToHex = (r, g, b) => '#' + [r, g, b].map(x => Math.max(0, Math.min(255, Math.round(x))).toString(16).padStart(2, '0')).join('');
                    
                    // ✨ 数学混合公式
                    const mixWithWhite = (rgb, percent) => {
                        const w = 255; const p = percent / 100;
                        return rgbToHex(rgb[0]*p + w*(1-p), rgb[1]*p + w*(1-p), rgb[2]*p + w*(1-p));
                    };
                    
                    const sortedPalette = palette.map(rgb => ({ rgb, hex: rgbToHex(...rgb), lum: getLum(rgb) })).sort((a, b) => a.lum - b.lum);
                    
                    const starHex = sortedPalette[0].hex;
                    const dominantRGB = colorThief.getColor(img);
                    const primaryHex = rgbToHex(...dominantRGB);
                    const highlightHex = sortedPalette[sortedPalette.length - 1].hex !== primaryHex ? sortedPalette[sortedPalette.length - 1].hex : sortedPalette[sortedPalette.length - 2].hex;

                    rootStyle.setProperty('--c-primary', primaryHex); safeSetStorage('--c-primary', primaryHex);
                    rootStyle.setProperty('--c-star', starHex); safeSetStorage('--c-star', starHex);
                    rootStyle.setProperty('--c-highlight', highlightHex); safeSetStorage('--c-highlight', highlightHex);
                    
                    // 实体化写入
                    const realSecondaryHex = mixWithWhite(dominantRGB, 10);
                    const realCaseBgHex = mixWithWhite(dominantRGB, 4);
                    rootStyle.setProperty('--c-secondary', realSecondaryHex); safeSetStorage('--c-secondary', realSecondaryHex);
                    rootStyle.setProperty('--c-case-bg', realCaseBgHex); safeSetStorage('--c-case-bg', realCaseBgHex);
                    
                    document.body.style.backgroundColor = mixWithWhite(dominantRGB, 2);

                    const display = document.getElementById('extracted-colors-display');
                    display.innerHTML = `<div style="flex:1; background:${starHex};" title="标题深色"></div><div style="flex:1; background:${primaryHex};" title="主色"></div><div style="flex:1; background:${highlightHex};" title="强调色"></div>`;
                    
                    initDynamicColorPanel(); // 🚨 重建颜色控制台！
                    alert('🎉 魔法换色成功！所有色板已独立生成，悬浮菜单已同步更新！');
                } catch (err) { alert('提取颜色失败，请换一张色彩更丰富的图片重试！'); }
            }; reader.readAsDataURL(file);
        });

        // ==========================================
        // 🚀 王炸体验：Notion 级划词悬浮菜单
        // ==========================================
        window.clearSelectionColor = function() {
            const sel = window.getSelection(); if (sel.isCollapsed) return;
            document.execCommand('removeFormat', false, null);
            document.execCommand('backColor', false, 'transparent');
            const text = sel.toString();
            if (text.indexOf('\\n') === -1) { document.execCommand('insertText', false, text); }
        };

        function buildHoverToolbar() {
            const toolbar = document.getElementById('notion-hover-menu');
            if(!toolbar) return;
            toolbar.innerHTML = '';
            
            let textGrp = document.createElement('div'); textGrp.className = 'hover-color-group';
            textGrp.innerHTML = '<span class="hover-label">A</span>';
            let bgGrp = document.createElement('div'); bgGrp.className = 'hover-color-group';
            bgGrp.innerHTML = '<span class="hover-label" style="background:#475569;color:#fff;padding:0 4px;border-radius:2px;">A</span>';
            
            // 挑选最高频的几个核心色放入悬浮菜单
            const coreVars = ['--c-primary', '--c-star', '--c-highlight', '--c-mod-point', '--c-mod-practice'];
            
            coreVars.forEach(v => {
                let currentVal = getComputedStyle(document.documentElement).getPropertyValue(v).trim();
                if(currentVal && currentVal.startsWith('#')) {
                    // 字色按钮
                    let tb = document.createElement('div'); tb.className = 'hover-color-btn'; tb.style.background = currentVal;
                    tb.title = "字: " + v.replace('--c-','');
                    tb.onclick = () => { applyToText(v, 'foreColor'); };
                    
                    // 底色按钮
                    let bb = document.createElement('div'); bb.className = 'hover-color-btn'; bb.style.background = currentVal;
                    bb.title = "底: " + v.replace('--c-','');
                    bb.onclick = () => { applyToText(v, 'backColor'); };
                    
                    textGrp.appendChild(tb); bgGrp.appendChild(bb);
                }
            });
            
            let clearBtn = document.createElement('div'); clearBtn.className = 'hover-label';
            clearBtn.style.cursor = 'pointer'; clearBtn.style.marginLeft = '4px'; clearBtn.innerHTML = '🚫清空';
            clearBtn.title = "清除此处的特殊颜色";
            clearBtn.onclick = () => { clearSelectionColor(); };
            
            let divider = document.createElement('div'); divider.className = 'hover-divider';
            toolbar.appendChild(textGrp); toolbar.appendChild(divider);
            toolbar.appendChild(bgGrp); toolbar.appendChild(divider.cloneNode());
            toolbar.appendChild(clearBtn);
            
            // 阻止点击面板时失去焦点
            toolbar.addEventListener('mousedown', e => e.preventDefault());
        }

        document.addEventListener('mouseup', function(e) {
            if(isFormatPainterActive || isEraserActive || isInspectorActive) return;
            const sel = window.getSelection();
            const toolbar = document.getElementById('notion-hover-menu');
            if (!sel.isCollapsed && sel.rangeCount > 0 && sel.toString().trim() !== "") {
                let node = sel.anchorNode; let inPage = false;
                while(node && node !== document.body) {
                    if(node.classList && node.classList.contains('a4-page')) { inPage = true; break; }
                    node = node.parentNode;
                }
                if(inPage) {
                    const range = sel.getRangeAt(0); const rect = range.getBoundingClientRect();
                    toolbar.style.display = 'flex';
                    toolbar.style.top = (rect.top - 45) + 'px';
                    toolbar.style.left = (rect.left + (rect.width/2) - (toolbar.offsetWidth/2)) + 'px';
                } else { toolbar.style.display = 'none'; }
            }
        });
        
        // 点击其他地方隐藏悬浮菜单
        document.addEventListener('mousedown', function(e) {
            const toolbar = document.getElementById('notion-hover-menu');
            if (toolbar && !toolbar.contains(e.target) && e.target.id !== 'notion-hover-menu') {
                toolbar.style.display = 'none';
            }
        });
        document.addEventListener('scroll', () => { document.getElementById('notion-hover-menu').style.display = 'none'; }, true);

        // ==========================================
        // 🔍 寻色器、格式刷、橡皮擦 (互斥逻辑)
        // ==========================================
        let isFormatPainterActive = false; let pickedClass = null;
        let isEraserActive = false;
        let isInspectorActive = false;

        let colorVarMap = {};
        function refreshColorMap() {
            colorVarMap = {};
            const dummy = document.createElement('div'); dummy.style.display = 'none'; document.body.appendChild(dummy);
            globalExtractedVars.forEach(v => {
                dummy.style.color = `var(${v})`;
                let cColor = window.getComputedStyle(dummy).color;
                if (!colorVarMap[cColor]) colorVarMap[cColor] = [];
                colorVarMap[cColor].push(v.replace('--c-', ''));
                
                dummy.style.backgroundColor = `var(${v})`;
                let cBg = window.getComputedStyle(dummy).backgroundColor;
                if (!colorVarMap[cBg]) colorVarMap[cBg] = [];
                if (!colorVarMap[cBg].includes(v.replace('--c-', ''))) colorVarMap[cBg].push(v.replace('--c-', ''));
            });
            document.body.removeChild(dummy);
        }

        window.toggleInspector = function() {
            if (isFormatPainterActive) toggleFormatPainter();
            if (isEraserActive) toggleEraser();
            
            const btn = document.getElementById('btn-inspector'); const container = document.getElementById('main-a4-container');
            if (!isInspectorActive) {
                isInspectorActive = true; refreshColorMap(); 
                btn.innerText = '探测中(Esc)'; btn.style.background = '#e9d5ff'; btn.style.borderColor = '#d8b4fe'; btn.style.color = '#581c87'; 
                container.style.cursor = 'help'; 
                container.addEventListener('mousemove', handleInspectorMove, true);
                container.addEventListener('mouseleave', hideInspector, true);
            } else {
                isInspectorActive = false; 
                btn.innerText = '🔍 寻色器'; btn.style.background = ''; btn.style.borderColor = ''; btn.style.color = ''; 
                container.style.cursor = 'auto'; 
                container.removeEventListener('mousemove', handleInspectorMove, true);
                container.removeEventListener('mouseleave', hideInspector, true); hideInspector();
            }
        }
        function handleInspectorMove(e) {
            if (!isInspectorActive) return;
            const target = e.target;
            if (target.classList.contains('a4-container') || target.classList.contains('a4-page') || target.classList.contains('page-content')) { hideInspector(); return; }
            const tooltip = document.getElementById('inspector-tooltip');
            tooltip.style.display = 'block'; tooltip.style.left = (e.clientX + 15) + 'px'; tooltip.style.top = (e.clientY + 15) + 'px';
            
            let classList = Array.from(target.classList).join(', ') || '基础正文文本';
            let color = window.getComputedStyle(target).color;
            let bgColor = window.getComputedStyle(target).backgroundColor;
            
            let colorName = colorVarMap[color] ? colorVarMap[color].join(' / ') : '默认';
            let bgColorName = colorVarMap[bgColor] ? colorVarMap[bgColor].join(' / ') : (bgColor === 'rgba(0, 0, 0, 0)' ? '透明' : '默认');
            
            tooltip.innerHTML = `
                <div style="margin-bottom:6px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:6px;">
                    <span style="color:#93c5fd; font-weight:bold;">标签:</span> &lt;${target.tagName.toLowerCase()}&gt;<br>
                    <span style="color:#93c5fd; font-weight:bold;">类名:</span> ${classList}
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="color:#a7f3d0; font-weight:bold;">文字色:</span> 
                    <span style="display:inline-block;width:14px;height:14px;background:${color};border:1px solid rgba(255,255,255,0.3);border-radius:3px;"></span>
                    <span style="color:#f8fafc; font-size:11px; background:rgba(255,255,255,0.2); padding:1px 6px; border-radius:10px;">${colorName}</span>
                </div>
                <div style="display:flex; align-items:center; gap:8px; margin-top:4px;">
                    <span style="color:#a7f3d0; font-weight:bold;">背景色:</span> 
                    <span style="display:inline-block;width:14px;height:14px;background:${bgColor};border:1px solid rgba(255,255,255,0.3);border-radius:3px;"></span>
                    <span style="color:#f8fafc; font-size:11px; background:rgba(255,255,255,0.2); padding:1px 6px; border-radius:10px;">${bgColorName}</span>
                </div>
            `;
        }
        function hideInspector() { const tooltip = document.getElementById('inspector-tooltip'); if(tooltip) tooltip.style.display = 'none'; }

        // Format Painter 
        window.toggleFormatPainter = function() {
            if (isEraserActive) toggleEraser(); 
            if (isInspectorActive) toggleInspector();
            const btn = document.getElementById('btn-format-painter'); const container = document.getElementById('main-a4-container');
            if (!isFormatPainterActive) {
                isFormatPainterActive = true; pickedClass = null; 
                btn.innerText = '请点击吸取...'; btn.style.background = '#fef08a'; btn.style.borderColor = '#facc15'; btn.style.color = '#854d0e'; 
                container.style.cursor = 'crosshair'; container.addEventListener('click', handleFormatPainterClick, true);
            } else {
                isFormatPainterActive = false; pickedClass = null; 
                btn.innerText = '🪄 格式刷'; btn.style.background = ''; btn.style.borderColor = ''; btn.style.color = ''; 
                container.style.cursor = 'auto'; container.removeEventListener('click', handleFormatPainterClick, true);
            }
        }
        function handleFormatPainterClick(e) {
            if (!isFormatPainterActive) return; e.preventDefault(); e.stopPropagation();
            const target = e.target; const btn = document.getElementById('btn-format-painter');
            if (!pickedClass) {
                if (target.classList.length > 0 && !target.classList.contains('a4-page') && !target.classList.contains('page-content')) {
                    pickedClass = target.className; btn.innerText = '✅ 涂抹(Esc退出)'; btn.style.background = '#bbf7d0'; btn.style.color = '#166534';
                } else { alert('请点击特定组件(如标题、特殊词)进行吸取。'); } return;
            }
            if (pickedClass) {
                const isBlock = pickedClass.includes('title') || pickedClass.includes('block') || pickedClass.includes('panel');
                if (isBlock) {
                    let blockParent = target;
                    while(blockParent && blockParent.tagName !== 'DIV' && blockParent.tagName !== 'P' && !blockParent.classList.contains('page-content')) { blockParent = blockParent.parentElement; }
                    if (blockParent && !blockParent.classList.contains('page-content')) { blockParent.className = pickedClass; } else { target.className = pickedClass; }
                } else {
                    const selection = window.getSelection();
                    if (!selection.isCollapsed) {
                        const range = selection.getRangeAt(0); const span = document.createElement('span'); span.className = pickedClass; range.surroundContents(span); selection.removeAllRanges();
                    } else { target.className = pickedClass; }
                }
            }
        }

        // Eraser
        window.toggleEraser = function() {
            if (isFormatPainterActive) toggleFormatPainter();
            if (isInspectorActive) toggleInspector();
            const btn = document.getElementById('btn-eraser'); const container = document.getElementById('main-a4-container');
            if (!isEraserActive) {
                isEraserActive = true; 
                btn.innerText = '擦除中(Esc)'; btn.style.background = '#fca5a5'; btn.style.borderColor = '#f87171'; btn.style.color = '#7f1d1d'; 
                container.classList.add('eraser-mode'); container.addEventListener('click', handleEraserClick, true);
            } else {
                isEraserActive = false; 
                btn.innerText = '🧹 橡皮擦'; btn.style.background = ''; btn.style.borderColor = ''; btn.style.color = ''; 
                container.classList.remove('eraser-mode'); container.removeEventListener('click', handleEraserClick, true);
            }
        }
        function handleEraserClick(e) {
            if (!isEraserActive) return; e.preventDefault(); e.stopPropagation();
            const target = e.target;
            if (target.classList.contains('page-content') || target.classList.contains('a4-page')) return;
            if (target.tagName === 'DIV' || target.tagName === 'P' || target.tagName.match(/^H[1-6]$/i)) { target.className = 'text-block'; } 
            else if (target.tagName === 'SPAN') { const text = document.createTextNode(target.innerText); target.parentNode.replaceChild(text, target); }
        }

        document.addEventListener('keydown', function(e) { 
            if (e.key === 'Escape') {
                if (isFormatPainterActive) toggleFormatPainter(); 
                if (isEraserActive) toggleEraser();
                if (isInspectorActive) toggleInspector();
            }
        });

        // ==========================================
        // 👀 Diff 引擎
        // ==========================================
        let isDiffOpen = false;
        window.toggleDiffSidebar = function() {
            const sidebar = document.getElementById('diff-sidebar'); const container = document.getElementById('main-a4-container');
            isDiffOpen = !isDiffOpen;
            if (isDiffOpen) { sidebar.classList.add('active'); container.style.marginRight = "300px"; runDiffCheck(); } 
            else { sidebar.classList.remove('active'); container.style.marginRight = "0"; }
        }

        function runDiffCheck() {
            const contentArea = document.getElementById('diff-content-area');
            contentArea.innerHTML = '<div style="text-align:center; padding:40px;"><br><br>🔄 正在逐字比对防漏验证...</div>';

            setTimeout(() => {
                try {
                    const rawDataStr = document.getElementById('raw-source-data').textContent;
                    let originalText = "";
                    if (rawDataStr && rawDataStr.trim() !== "") { originalText = JSON.parse(rawDataStr); } 
                    else { contentArea.innerHTML = '<div style="color:#b91c1c; font-weight:bold; padding:20px;">⚠️ 未检测到大模型吐出的原始数据。</div>'; return; }

                    let currentText = "";
                    document.querySelectorAll('.a4-page .page-content').forEach(page => { currentText += page.innerText + "\\n"; });

                    const dmp = new diff_match_patch(); dmp.Diff_Timeout = 2; 
                    const diffs = dmp.diff_main(originalText, currentText);
                    dmp.diff_cleanupSemantic(diffs);

                    let html = ""; let missingCount = 0;
                    for (let i = 0; i < diffs.length; i++) {
                        const type = diffs[i][0]; const text = diffs[i][1];
                        if (type === -1) {
                            if (text.trim().length > 0) {
                                missingCount++;
                                html += '<span class="diff-missing" title="这是大模型排版时漏掉的词，请在左边纸上补回来">' + text + '</span>';
                            } else { html += text; }
                        } else if (type === 0) { html += '<span class="diff-equal">' + text + '</span>'; }
                    }

                    if (missingCount === 0) { contentArea.innerHTML = '<div style="color:#15803d; font-weight:800; padding:40px; text-align:center; font-size: 16px; border: 2px dashed #bbf7d0; border-radius: 8px; margin: 20px; background: #f0fdf4;">🎉 满分通关！<br><br><span style="font-size:13px; font-weight:normal;">大模型排版没有吞掉任何文字。</span></div>'; } 
                    else { contentArea.innerHTML = html; }
                } catch (e) { contentArea.innerHTML = '<div style="color:#b91c1c; font-weight:bold; padding:20px;">比对功能执行出错，可能是生肉数据格式异常。</div>'; }
            }, 300);
        }

        window.addEventListener('DOMContentLoaded', () => {
            try { initDynamicColorPanel(); } catch(e) {}
            try { initLayoutControls(); } catch(e) {}
            try {
                const source = document.getElementById('source-data'); if (!source) return;
                const initialNodes = Array.from(source.children);
                setTimeout(() => { dynamicMaxHeight = getSafeMaxHeight(); runPaginationEngine(initialNodes); }, 300); 
            } catch (err) {}
        });
    </script>
</body>
</html>"""

    final_html = (
        html_template.replace('__DOC_TITLE__', str(doc_title))
        .replace('__DOC_CATEGORY__', str(doc_category))
        .replace('__THEME_COLORS__', str(theme_colors))
        .replace('__FINAL_STYLE_CONTENT__', str(final_style_content))
        .replace('__CONTENT_AREA__', str(content_area))
        .replace('__ORIGINAL_TEXT__', str(safe_original_json))
    )

    return {"final_html": final_html}
