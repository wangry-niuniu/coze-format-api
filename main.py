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
    # 提取常规的字符串参数
    content_area = req.pure_content
    doc_category = req.category
    doc_title = req.title_info
    theme_colors = req.theme_colors
    clean_zjmk_ty = req.zjmk_ty.strip()
    clean_zjmk_zs = req.zjmk_zs.strip()

    original_raw = req.original_text

    # 🚨 终极解包逻辑：应对 Coze 的各种字符串花样
    if isinstance(original_raw, str):
        try:
            # 第一层：尝试标准的 JSON 解析
            original_raw = json.loads(original_raw)
        except Exception:
            pass

    # 如果解开一层之后发现里面居然还是一个字符串（嵌套转义的情况）
    if isinstance(original_raw, str):
        try:
            # 第二层：针对极其顽固的二次转义 JSON 进行清理和再解析
            cleaned_str = original_raw.replace('\\n', '\n').replace('\\"', '"')
            original_raw = json.loads(cleaned_str)
        except Exception:
            pass

    extracted_text = ""

    # 🎯 照抄你成功的 Array Object 拆包逻辑！
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
    # 🚨 新增：Markdown 符号大清洗（对齐大模型的输出）
    # =======================================================
    if extracted_text:
        # 1. 剔除行首的标题符号 (如 ### , #### )
        extracted_text = re.sub(r'(?m)^#+\s*', '', extracted_text)
        # 2. 剔除加粗和斜体符号 (如 **文字** 变成 文字)
        extracted_text = re.sub(r'\*+', '', extracted_text)
        # 3. 剔除无序列表符号 (如 - 或 + 开头)
        extracted_text = re.sub(r'(?m)^[-+]\s+', '', extracted_text)
        # 4. 剔除引用符号 (如 > )
        extracted_text = re.sub(r'(?m)^>\s*', '', extracted_text)
    # =======================================================

    final_style_content = clean_zjmk_ty + "\n\n" + clean_zjmk_zs

    # 安全序列化，防网页 JS 崩溃
    safe_original_json = json.dumps(extracted_text.strip(), ensure_ascii=False).replace("</", "<\\/")

    # 满血版 HTML 模板
    html_template = "\ufeff" + """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>__DOC_TITLE__</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/color-thief/2.3.0/color-thief.umd.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/diff_match_patch/20121119/diff_match_patch.js"></script>

    <style id="dynamic-style">
        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
        :root {
            --c-primary: #52A89E; --c-star: #2D7A71; --c-highlight: #D59A44;
            --c-mod-point: #9A7EB4; --c-mod-mnemonic: #E88796; --c-mod-practice: #48BB78;
            --c-border: #CBE3E0; --c-case-bg: rgba(82, 168, 158, 0.05);
            --f-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
            --f-size-base: 14px; --f-size-title: 18px; --line-height: 1.8;
            --letter-spacing: 0px; --radius-card: 6px;
        }
        __THEME_COLORS__

        body { background-color: #F4F6F8; font-family: var(--f-family, sans-serif); margin: 0; padding: 0; display: flex; gap: 24px; justify-content: center; overflow-x: hidden; }
        .a4-container { flex: 1; max-width: 210mm; display: flex; flex-direction: column; gap: 20px; align-items: center; padding-top: 20px; transition: margin-right 0.3s ease; }
        .a4-page { width: 210mm; min-height: 297mm; height: auto; overflow: visible; position: relative; padding: 18mm 15mm 30mm 15mm; page-break-after: always; box-sizing: border-box; background: #FFFFFF; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06); flex-shrink: 0; }
        .page-content table { width: 100%; border-collapse: collapse; table-layout: fixed; word-wrap: break-word; margin: 15px 0; font-size: 13px; }
        .page-content th, .page-content td { border: 1px solid var(--c-border); padding: 8px 12px; text-align: left; }
        .page-content th { background-color: var(--c-case-bg); color: var(--c-primary); font-weight: bold; }
        [contenteditable="true"]:focus { outline: 1px dashed var(--c-primary); outline-offset: 2px; }
        .page-content, .page-header, .page-footer { transition: all 0.2s ease; border-radius: 4px; }
        .page-content { display: flow-root; width: 100%; font-size: var(--f-size-base, 14px); line-height: var(--line-height, 1.8); letter-spacing: var(--letter-spacing, 0px); font-family: var(--f-family) !important; }
        @media screen { .page-content[contenteditable="true"]:hover, .page-header[contenteditable="true"]:hover, .page-footer[contenteditable="true"]:hover { box-shadow: 0 0 0 2px rgba(113, 176, 246, 0.3) inset; background-color: rgba(113, 176, 246, 0.02); cursor: text; } }
        .action-tag { display: inline-block; margin: 0 2px; vertical-align: baseline; font-weight: bold; }
        .action-tag.phase { color: var(--c-primary); border: 1px dashed var(--c-primary); padding: 2px 14px; border-radius: 12px; font-size: 14px; }
        .highlight-line { color: var(--c-highlight); font-weight: bold; text-decoration: underline; text-underline-offset: 2px; text-decoration-thickness: 1.5px; padding: 0 2px; }
        .action-tag.student { color: var(--c-mod-point); font-weight: bold; text-decoration: underline; text-underline-offset: 2px; text-decoration-thickness: 1.5px; padding: 0 2px; }
        .action-tag.emotion { color: var(--c-mod-mnemonic); background-color: rgba(232, 135, 150, 0.12); padding: 0px 4px; border-radius: 6px; }
        .action-tag.action { color: var(--c-mod-practice); background-color: rgba(72, 187, 120, 0.12); padding: 0px 4px; border-radius: 6px; }
        .board-box { margin: 30px auto 20px; padding: 20px; border: 2px dashed var(--c-border); background: var(--c-case-bg); position: relative; border-radius: var(--radius-card); width: 85%; text-align: left; break-inside: avoid; }
        .board-box::before { content: "板书设计"; position: absolute; top: -12px; left: 20px; background: #fff; padding: 0 10px; font-size: 12px; color: var(--c-primary); font-weight: bold; border-radius: 4px; border: 1px solid var(--c-border); }
        .blank-fill { display: inline-block; min-width: 50px; width: auto; border-bottom: 1px solid var(--c-star, #333); margin: 0 5px; white-space: nowrap; text-align: center; }
        .notice-card::after, .card-container::after { content: "内部核心资料，严禁外传"; display: block; text-align: right; font-size: 10px; font-weight: normal; color: rgba(0, 0, 0, 0.06); margin-top: 15px; pointer-events: none; }
        .page-header { position: absolute; top: 12mm; left: 15mm; right: 15mm; display: flex; justify-content: space-between; border-bottom: 1px solid #eee; padding-bottom: 5px; font-size: 10px; color: #999; font-weight: bold; }
        .page-footer { position: absolute; bottom: 12mm; left: 15mm; right: 15mm; display: flex; justify-content: space-between; align-items: center; font-size: 9px; color: #ccc; }
        .page-footer span { flex: 1; } .page-footer .f-left { text-align: left; } .page-footer .f-center { text-align: center; font-family: Arial, sans-serif; font-weight: bold; } .page-footer .f-right { text-align: right; }

        .control-panel { width: 300px; background: #fff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); height: fit-content; position: sticky; top: 20px; z-index: 1000; flex-shrink: 0; max-height: 90vh; overflow-y: auto; }
        .control-panel::-webkit-scrollbar { width: 6px; } .control-panel::-webkit-scrollbar-thumb { background-color: #cbd5e1; border-radius: 4px; }
        .control-panel h3 { margin-top: 0; border-bottom: 1px solid #eee; padding-bottom: 10px; font-size: 16px; color: #333; display: flex; justify-content: space-between; align-items: center; }
        .ctrl-group { margin-bottom: 15px; } .ctrl-group label { display: block; font-size: 13px; margin-bottom: 5px; color: #475569; font-weight: bold; }
        .ctrl-group select { width: 100%; padding: 6px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 13px; outline: none; }
        .color-row { display:flex; justify-content:space-between; margin-bottom:8px; font-size:12px; align-items:center; border-bottom:1px dashed #e2e8f0; padding-bottom:4px; }
        .color-tool-btn { background:none; border:1px solid #cbd5e1; border-radius:4px; cursor:pointer; font-size:12px; margin-left:4px; padding:2px 4px; display: flex; align-items: center; justify-content: center; }
        .color-tool-btn:hover { background:#f1f5f9; }
        .ctrl-btn { width: 100%; padding: 10px; margin-bottom: 8px; border: 1px solid #cbd5e1; background: #f8fafc; border-radius: 6px; cursor: pointer; transition: 0.2s; font-size: 13px; color: #334155; }
        .ctrl-btn:hover { background: #e2e8f0; transform: translateY(-1px); }
        .ctrl-btn.primary { background: var(--c-primary); color: #fff; border: none; font-weight: bold; font-size: 14px; margin-top: 10px; box-shadow: 0 4px 12px rgba(82, 168, 158, 0.4); }
        .page-content img { max-width: 100%; height: auto; display: block; margin: 10px auto; border-radius: var(--radius-card); }
        #inspector-tooltip { position: fixed; display: none; background: rgba(0,0,0,0.85); color: #fff; padding: 10px 15px; border-radius: 8px; font-size: 12px; z-index: 99999; pointer-events: none; line-height: 1.5; box-shadow: 0 4px 12px rgba(0,0,0,0.2); max-width: 300px; word-break: break-all; }

        #diff-sidebar { position: fixed; right: -450px; top: 0; width: 400px; height: 100vh; background: #fff; box-shadow: -4px 0 25px rgba(0,0,0,0.15); z-index: 9999; transition: right 0.3s cubic-bezier(0.4, 0, 0.2, 1); display: flex; flex-direction: column; font-family: sans-serif; }
        #diff-sidebar.active { right: 0; }
        .diff-header { padding: 20px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; background: #fef2f2; color: #991b1b; font-weight: bold; font-size: 16px; }
        .diff-content { flex: 1; overflow-y: auto; padding: 20px; font-size: 14px; line-height: 1.8; white-space: pre-wrap; color: #475569; }
        .diff-missing { background-color: #fee2e2; color: #b91c1c; font-weight: 800; padding: 2px 4px; border-radius: 4px; cursor: text; border-bottom: 2px solid #ef4444; }
        .diff-equal { color: #94a3b8; }

        @media print {
            @page { size: A4; margin: 0; }
            html, body { width: 210mm; margin: 0; padding: 0; background: #fff; }
            body { display: block; background: transparent; padding: 0; }
            .control-panel, #diff-sidebar { display: none !important; }
            .a4-container { display: block; overflow: visible; max-width: none; gap: 0; padding: 0; margin: 0; }
            .a4-page { margin: 0; padding: 18mm 15mm 30mm 15mm; box-shadow: none; border: none; width: 210mm; min-height: 297mm; height: auto; box-sizing: border-box; page-break-after: always; page-break-inside: auto; }
            .a4-page:last-child { page-break-after: auto; }
        }
        __FINAL_STYLE_CONTENT__
    </style>
</head>
<body>
    <div id="inspector-tooltip"></div>
    <div class="control-panel no-print">
        <h3><span>[工作台]</span><button onclick="resetSettings()" style="font-size: 11px; padding: 4px 8px; cursor: pointer; border: 1px solid #ddd; background: #fafafa; border-radius: 4px; color: #666;">[重置]</button></h3>

        <div style="background: #f8fafc; padding: 10px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 15px;">
            <input type="file" id="color-image-upload" accept="image/*" style="display: none;">
            <button class="ctrl-btn" onclick="document.getElementById('color-image-upload').click()" style="background: #fef3c7; color: #92400e; border-color: #fde68a; font-weight: bold; margin-bottom: 8px;">
                [上传色卡智能换色]
            </button>
            <div id="extracted-colors-display" style="display:flex; gap:5px; height: 15px; border-radius: 4px; overflow: hidden; margin-bottom: 8px;"></div>

            <button class="ctrl-btn" id="btn-format-painter" onclick="toggleFormatPainter()" style="background: #ecfdf5; color: #166534; border-color: #a7f3d0; font-weight: bold;">
                [开启语义格式刷]
            </button>

            <button class="ctrl-btn" onclick="toggleDiffSidebar()" style="background: #fef2f2; color: #991b1b; border-color: #fca5a5; font-weight: bold; margin-bottom: 0;">
                [防吞字漏字校验]
            </button>
        </div>

        <div class="ctrl-group" id="group-base-colors"><label>[基础色板]</label><div id="panel-base-colors"></div></div>
        <div class="ctrl-group" id="group-comp-colors"><label>[组件专属色]</label><div id="panel-comp-colors"></div></div>
        <hr style="border: 0; border-top: 1px dashed #cbd5e1; margin: 15px 0;">
        <div class="ctrl-group">
            <label>[字体选择]</label>
            <select id="sel-font">
                <optgroup label="[现代UI风格]"><option value='"PingFang SC", "Microsoft YaHei", sans-serif'>系统黑体</option><option value='"LXGW WenKai", "STKaiti", "KaiTi", serif'>手账文楷</option></optgroup>
                <optgroup label="[传统公文风]"><option value='"KaiTi_GB2312", "KaiTi", serif'>标准楷体</option><option value='"Source Han Serif SC", "STSong", "SimSun", serif'>标准宋体</option></optgroup>
            </select>
        </div>
        <div class="ctrl-group"><label>[正文字号] (<span id="val-f-size-base">14</span>px)</label><input type="range" id="sl-f-size-base" min="12" max="24" value="14" style="width:100%;"></div>
        <div class="ctrl-group"><label>[标题字号] (<span id="val-f-size-title">18</span>px)</label><input type="range" id="sl-f-size-title" min="14" max="36" value="18" style="width:100%;"></div>
        <div class="ctrl-group"><label>[行间距] (<span id="val-line-height">1.8</span>)</label><input type="range" id="sl-line-height" min="1.2" max="3" step="0.1" value="1.8" style="width:100%;"></div>
        <div class="ctrl-group"><label>[字间距] (<span id="val-letter-spacing">0</span>px)</label><input type="range" id="sl-letter-spacing" min="-1" max="10" step="0.5" value="0" style="width:100%;"></div>
        <div class="ctrl-group"><label>[圆角] (<span id="val-radius-card">6</span>px)</label><input type="range" id="sl-radius-card" min="0" max="30" value="6" style="width:100%;"></div>
        <hr style="border: 0; border-top: 1px dashed #cbd5e1; margin: 15px 0;">
        <button class="ctrl-btn" onclick="clearSelectionColor()" style="border-color: #fca5a5; color: #dc2626; background: #fff;">[擦除选中格式]</button>
        <button class="ctrl-btn" onclick="recalculatePagination()" style="background: var(--c-primary); color: white; border: none; font-weight: bold; box-shadow: 0 2px 6px rgba(0,0,0,0.1);">[重新排版防断裂]</button>
        <button class="ctrl-btn primary" onclick="window.print()">[导出 PDF 文件]</button>
    </div>

    <div class="a4-container" id="main-a4-container"></div>

    <div id="diff-sidebar" class="no-print">
        <div class="diff-header">
            <span>原文防漏字比对报告</span>
            <button onclick="toggleDiffSidebar()" style="border:none;background:none;cursor:pointer;font-size:16px;color:#991b1b;font-weight:bold;">[关闭]</button>
        </div>
        <div style="padding:10px 20px; background:#f8fafc; font-size:12px; color:#475569; border-bottom:1px solid #e2e8f0;">
            * <strong style="color:#b91c1c;">红色高亮字</strong> 为大模型排版时漏掉的内容。请复制后直接粘贴到左侧 A4 纸对应位置，并使用[格式刷]修补。
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
        window.resetSettings = function() { if(confirm('确定要恢复到默认状态吗？')) { try { localStorage.clear(); } catch(e) {} location.reload(); } };
        function createNewPage() { pageCount++; const page = document.createElement('div'); page.className = 'a4-page'; page.innerHTML = '<div class="page-header" contenteditable="true" spellcheck="false"><span>' + DOC_EN_TITLE + '</span><span>' + DOC_ZH_TITLE + '</span></div><div class="page-content" contenteditable="true" spellcheck="false"></div><div class="page-footer" contenteditable="true" spellcheck="false"><span class="f-left">内部教研</span><span class="f-center">- ' + pageCount + ' -</span><span class="f-right">独家整理</span></div>'; document.getElementById('main-a4-container').appendChild(page); return page; }
        document.addEventListener('input', function(e) { if (e.target.classList.contains('page-header')) { const newHTML = e.target.innerHTML; document.querySelectorAll('.page-header').forEach(el => { if (el !== e.target) el.innerHTML = newHTML; }); } });
        function runPaginationEngine(nodes) { let currentPage = createNewPage(); let currentContent = currentPage.querySelector('.page-content'); let previousNode = null; let currentTitleLevel = ""; nodes.forEach(node => { const isTitleClass = node.className && node.className.includes('title-'); if (isTitleClass) { const titleText = node.innerText.trim(); if (titleText === currentTitleLevel) return; currentTitleLevel = titleText; } currentContent.appendChild(node); if (currentContent.offsetHeight > dynamicMaxHeight) { if (currentContent.children.length <= 1) { } else { currentContent.removeChild(node); let nodeToMoveWith = null; if (previousNode) { const isHeading = previousNode.tagName.match(/^H[1-6]$/i); const isPrevTitleClass = previousNode.className && previousNode.className.includes('title-'); if (isHeading || isPrevTitleClass) { nodeToMoveWith = previousNode; currentContent.removeChild(previousNode); } } currentPage = createNewPage(); currentContent = currentPage.querySelector('.page-content'); if (nodeToMoveWith) currentContent.appendChild(nodeToMoveWith); currentContent.appendChild(node); } } if (node.innerText && node.innerText.trim() !== "") { previousNode = node; } }); }
        window.recalculatePagination = function() { const allContents = document.querySelectorAll('.a4-page .page-content'); if (allContents.length === 0) return; const allNodes = []; allContents.forEach(content => { Array.from(content.children).forEach(child => { allNodes.push(child); }); }); document.querySelectorAll('.a4-page').forEach(page => page.remove()); pageCount = 0; dynamicMaxHeight = getSafeMaxHeight(); runPaginationEngine(allNodes); };
        window.clearSelectionColor = function() { const sel = window.getSelection(); if (sel.isCollapsed) return; document.execCommand('removeFormat', false, null); document.execCommand('backColor', false, 'transparent'); const text = sel.toString(); if (text.indexOf('\\n') === -1) { document.execCommand('insertText', false, text); } };
        window.applyToText = function(varName, command) { const color = getComputedStyle(document.documentElement).getPropertyValue(varName).trim(); if (color) document.execCommand(command, false, color); };
        let globalExtractedVars = [];
        function initDynamicColorPanel() { const baseContainer = document.getElementById('panel-base-colors'); const compContainer = document.getElementById('panel-comp-colors'); if(!baseContainer || !compContainer) return; const styleText = document.getElementById('style-data').textContent; let varsMatch = styleText.match(/--[a-zA-Z0-9-]+/g) || []; globalExtractedVars = [...new Set(varsMatch)]; if(globalExtractedVars.length === 0) globalExtractedVars = ['--c-primary', '--c-star', '--c-highlight']; const baseKeywords = ['primary', 'star', 'base', 'text', 'bg', 'background', 'border', 'main']; baseContainer.innerHTML = ''; compContainer.innerHTML = ''; globalExtractedVars.forEach(v => { let currentVal = getComputedStyle(document.documentElement).getPropertyValue(v).trim() || '#cccccc'; let saved = safeGetStorage(v); if(saved) { currentVal = saved; rootStyle.setProperty(v, saved); } if (currentVal && currentVal.startsWith('#')) { const cleanName = v.replace('--c-','').replace('--','').toLowerCase(); const isBase = baseKeywords.some(kw => cleanName.includes(kw)); const targetContainer = isBase ? baseContainer : compContainer; let wrapper = document.createElement('div'); wrapper.className = 'color-row'; wrapper.innerHTML = '<span style="color:#475569; flex-grow:1; font-weight:500;" title="' + v + '">' + cleanName + '</span><div style="display:flex; align-items:center;"><input type="color" value="' + currentVal + '" class="dyn-color-picker" data-var="' + v + '" style="width:22px;height:22px;padding:0;border:none;cursor:pointer; border-radius:4px;"><button class="color-tool-btn" title="文字" onclick="applyToText(\\'' + v + '\\', \\'foreColor\\')">[字]</button><button class="color-tool-btn" title="背景" onclick="applyToText(\\'' + v + '\\', \\'backColor\\')">[底]</button></div>'; wrapper.querySelector('input').addEventListener('input', (e) => { rootStyle.setProperty(v, e.target.value); safeSetStorage(v, e.target.value); }); targetContainer.appendChild(wrapper); } }); if(compContainer.children.length === 0) document.getElementById('group-comp-colors').style.display = 'none'; }
        function initLayoutControls() { ['f-size-base', 'f-size-title', 'line-height', 'letter-spacing', 'radius-card'].forEach(id => { const el = document.getElementById('sl-' + id); const valSpan = document.getElementById('val-' + id); if(el) { let saved = safeGetStorage('--' + id); if(saved) { let numOnly = saved.replace(/[^0-9.-]/g, ''); el.value = numOnly; if(valSpan) valSpan.innerText = numOnly; rootStyle.setProperty('--' + id, saved); } el.addEventListener('input', (e) => { let val = e.target.value; let suffix = id.includes('line') ? '' : 'px'; if(valSpan) valSpan.innerText = val; rootStyle.setProperty('--' + id, val + suffix); safeSetStorage('--' + id, val + suffix); }); } }); const fontSel = document.getElementById('sel-font'); if(fontSel) { let savedFont = safeGetStorage('--f-family'); if(savedFont) { fontSel.value = savedFont; rootStyle.setProperty('--f-family', savedFont); } fontSel.addEventListener('change', (e) => { rootStyle.setProperty('--f-family', e.target.value); safeSetStorage('--f-family', e.target.value); }); } }

        document.getElementById('color-image-upload').addEventListener('change', function(e) {
            const file = e.target.files[0]; if (!file) return;
            const img = new Image(); const reader = new FileReader();
            reader.onload = function(e) { img.src = e.target.result; };
            img.onload = function() {
                try {
                    const colorThief = new ColorThief();
                    const primaryRGB = colorThief.getColor(img);
                    const paletteRGB = colorThief.getPalette(img, 4);
                    const rgbToHex = (r, g, b) => '#' + [r, g, b].map(x => { const hex = x.toString(16); return hex.length === 1 ? '0' + hex : hex; }).join('');
                    const primaryHex = rgbToHex(primaryRGB[0], primaryRGB[1], primaryRGB[2]);
                    const secondaryHex = paletteRGB[1] ? rgbToHex(paletteRGB[1][0], paletteRGB[1][1], paletteRGB[1][2]) : primaryHex;
                    const highlightHex = paletteRGB[2] ? rgbToHex(paletteRGB[2][0], paletteRGB[2][1], paletteRGB[2][2]) : primaryHex;
                    const lightBgHex = rgbToHex(Math.floor(primaryRGB[0] + (255 - primaryRGB[0]) * 0.95), Math.floor(primaryRGB[1] + (255 - primaryRGB[1]) * 0.95), Math.floor(primaryRGB[2] + (255 - primaryRGB[2]) * 0.95));
                    rootStyle.setProperty('--c-primary', primaryHex); safeSetStorage('--c-primary', primaryHex);
                    rootStyle.setProperty('--c-star', primaryHex); safeSetStorage('--c-star', primaryHex);
                    rootStyle.setProperty('--c-highlight', highlightHex); safeSetStorage('--c-highlight', highlightHex);
                    rootStyle.setProperty('--c-secondary', secondaryHex); safeSetStorage('--c-secondary', secondaryHex);
                    rootStyle.setProperty('--c-bg-main', lightBgHex); safeSetStorage('--c-bg-main', lightBgHex);
                    rootStyle.setProperty('--c-case-bg', lightBgHex); safeSetStorage('--c-case-bg', lightBgHex);
                    const display = document.getElementById('extracted-colors-display');
                    display.innerHTML = `<div style="flex:1; background:${primaryHex};" title="主色"></div><div style="flex:1; background:${secondaryHex};" title="辅助色"></div><div style="flex:1; background:${highlightHex};" title="强调色"></div><div style="flex:1; background:${lightBgHex};" title="浅背景色"></div>`;
                    initDynamicColorPanel(); alert('提取成功！已为您一键更换主题色。');
                } catch (err) { alert('提取颜色失败，请重试！'); }
            }; reader.readAsDataURL(file);
        });

        let isFormatPainterActive = false; let pickedClass = null;
        window.toggleFormatPainter = function() {
            const btn = document.getElementById('btn-format-painter'); const container = document.getElementById('main-a4-container');
            if (!isFormatPainterActive) {
                isFormatPainterActive = true; pickedClass = null; btn.innerText = '请点击要[吸取]的组件'; btn.style.background = '#fef08a'; btn.style.borderColor = '#facc15'; container.style.cursor = 'crosshair'; container.addEventListener('click', handleFormatPainterClick, true);
            } else {
                isFormatPainterActive = false; pickedClass = null; btn.innerText = '[开启语义格式刷]'; btn.style.background = '#ecfdf5'; btn.style.borderColor = '#a7f3d0'; container.style.cursor = 'auto'; container.removeEventListener('click', handleFormatPainterClick, true);
            }
        }
        function handleFormatPainterClick(e) {
            if (!isFormatPainterActive) return; e.preventDefault(); e.stopPropagation();
            const target = e.target; const btn = document.getElementById('btn-format-painter');
            if (!pickedClass) {
                if (target.classList.length > 0 && !target.classList.contains('a4-page') && !target.classList.contains('page-content')) {
                    pickedClass = target.className; btn.innerText = '已吸取！请点击涂刷 (Esc退出)'; btn.style.background = '#86efac';
                } else { alert('请点击特定组件进行吸取。'); } return;
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
        document.addEventListener('keydown', function(e) { if (e.key === 'Escape' && isFormatPainterActive) toggleFormatPainter(); });

        let isDiffOpen = false;
        window.toggleDiffSidebar = function() {
            const sidebar = document.getElementById('diff-sidebar');
            const container = document.getElementById('main-a4-container');
            isDiffOpen = !isDiffOpen;
            if (isDiffOpen) {
                sidebar.classList.add('active');
                container.style.marginRight = "300px";
                runDiffCheck();
            } else {
                sidebar.classList.remove('active');
                container.style.marginRight = "0";
            }
        }

        function runDiffCheck() {
            const contentArea = document.getElementById('diff-content-area');
            contentArea.innerHTML = '<div style="text-align:center; padding:30px;"><br><br>正在极速比对，请稍候...</div>';

            setTimeout(() => {
                try {
                    const rawDataStr = document.getElementById('raw-source-data').textContent;
                    let originalText = "";
                    if (rawDataStr && rawDataStr.trim() !== "__ORIGINAL_TEXT__") {
                        originalText = JSON.parse(rawDataStr);
                    } else {
                        contentArea.innerHTML = '<div style="color:#b91c1c;">未检测到原始数据！请确保传入了 original_text。</div>';
                        return;
                    }

                    let currentText = "";
                    document.querySelectorAll('.a4-page .page-content').forEach(page => {
                        currentText += page.innerText + "\\n";
                    });

                    const dmp = new diff_match_patch();
                    dmp.Diff_Timeout = 2; 
                    const diffs = dmp.diff_main(originalText, currentText);
                    dmp.diff_cleanupSemantic(diffs);

                    let html = "";
                    let missingCount = 0;
                    for (let i = 0; i < diffs.length; i++) {
                        const type = diffs[i][0];
                        const text = diffs[i][1];

                        if (type === -1) {
                            if (text.trim().length > 0) {
                                missingCount++;
                                html += '<span class="diff-missing" title="请复制此段补回A4纸">' + text + '</span>';
                            } else {
                                html += text;
                            }
                        } else if (type === 0) {
                            html += '<span class="diff-equal">' + text + '</span>';
                        }
                    }

                    if (missingCount === 0) {
                        contentArea.innerHTML = '<div style="color:#166534; font-weight:bold; padding:30px; text-align:center; font-size: 16px;">🎉 完美！大模型没有漏掉任何内容。</div>';
                    } else {
                        contentArea.innerHTML = html;
                    }
                } catch (e) {
                    contentArea.innerHTML = '<div style="color:#b91c1c; font-weight:bold;">比对出错。可能是数据格式异常。</div>';
                }
            }, 150);
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
