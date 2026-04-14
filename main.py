from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Optional
import json
import re

app = FastAPI()

class FormatRequest(BaseModel):
    pure_content: Optional[str] = ""
    category: Optional[str] = "内部教辅资料"
    title_info: Optional[str] = "教辅排版引擎"
    theme_colors: Optional[str] = ""
    zjmk_ty: Optional[str] = ""
    zjmk_zs: Optional[str] = ""
    original_text: Optional[Any] = []

@app.post("/generate_html")
async def generate_html(req: FormatRequest):
    # 1. 安全获取基础参数
    doc_category = req.category or "内部教辅资料"
    doc_title = req.title_info or "教辅排版引擎"
    theme_colors = req.theme_colors or ""
    clean_zjmk_ty = (req.zjmk_ty or "").strip()
    clean_zjmk_zs = (req.zjmk_zs or "").strip()

    # =======================================================
    # 🛡️ 第一战区：处理 pure_content（防 Coze 变态打包）
    # =======================================================
    content_area = req.pure_content

    if isinstance(content_area, str) and content_area.strip():
        # 尝试解包：如果是一整个 JSON 字典被打包成了字符串
        try:
            parsed = json.loads(content_area)
            if isinstance(parsed, dict) and "pure_content" in parsed:
                content_area = parsed["pure_content"]
            elif isinstance(parsed, dict) and "htmlCode" in parsed: # 预防传错字段
                 content_area = parsed["htmlCode"]
        except Exception:
            pass

        content_str = str(content_area)
        
        # 暴力洗澡：不管有多少层反斜杠转义的引号，全洗掉
        content_str = re.sub(r'\\+"', '"', content_str)
        # 把被转义的换行符还原（不要直接删掉，可能会让标签连在一起）
        content_str = content_str.replace('\\n', '\n')

        # 终极物理开膛手（性能优化版）：寻找第一个 < 到 最后一个 > 之间的所有内容
        # 使用贪婪匹配，忽略首尾可能因为强制转换 JSON 带来的 {" 或 "} 等垃圾字符
        match = re.search(r'(<[\s\S]+>)', content_str)
        if match:
            content_area = match.group(1)
        else:
             content_area = content_str # 如果连标签都找不到，原样兜底

    else:
        content_area = str(content_area) # 极度异常情况兜底

    # =======================================================
    # 🛡️ 第二战区：处理 original_text（防嵌套解析死锁）
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
    # 🛡️ 第三战区：Markdown 符号大清洗（防 Diff 误报）
    # =======================================================
    if extracted_text:
        extracted_text = re.sub(r'(?m)^#+\s*', '', extracted_text)
        extracted_text = re.sub(r'\*+', '', extracted_text)
        extracted_text = re.sub(r'(?m)^[-+]\s+', '', extracted_text)
        extracted_text = re.sub(r'(?m)^>\s*', '', extracted_text)

    # =======================================================
    # 🛡️ 第四战区：组装与安全输出
    # =======================================================
    final_style_content = clean_zjmk_ty + "\n\n" + clean_zjmk_zs

    # 安全序列化，防网页 JS 崩溃
    safe_original_json = json.dumps(extracted_text.strip(), ensure_ascii=False).replace("</", "<\\/")

    # 满血版 HTML 模板
    # 满血版与高级 UI 版 HTML 模板
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
            /* 默认主题，如果未上传色卡则使用此套 */
            --c-primary: #52A89E; --c-star: #2D7A71; --c-highlight: #D59A44;
            --c-mod-point: #9A7EB4; --c-mod-mnemonic: #E88796; --c-mod-practice: #48BB78;
            --c-border: #CBE3E0; --c-case-bg: rgba(82, 168, 158, 0.05);
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
        
        /* 按钮高级配色 */
        .btn-color { background: #fefce8; color: #a16207; border-color: #fef08a; }
        .btn-brush { background: #f0fdf4; color: #15803d; border-color: #bbf7d0; }
        .btn-eraser { background: #fef2f2; color: #b91c1c; border-color: #fecaca; }
        .btn-diff { background: #eff6ff; color: #1d4ed8; border-color: #bfdbfe; margin-bottom: 0; }
        .btn-export { background: var(--c-primary, #0f172a); color: #fff; box-shadow: 0 6px 16px color-mix(in srgb, var(--c-primary) 40%, transparent); margin-top: 10px; padding: 14px; font-size: 14px;}

        .ctrl-group { margin-bottom: 16px; } 
        .ctrl-group label { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 8px; color: #64748b; font-weight: 600; }
        .ctrl-group label span { color: #0f172a; font-weight: 700; }
        .ctrl-group select { width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px; outline: none; background: #f8fafc; font-weight: 500; cursor: pointer; }
        
        input[type=range] { -webkit-appearance: none; width: 100%; background: transparent; }
        input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; height: 16px; width: 16px; border-radius: 50%; background: var(--c-primary); cursor: pointer; margin-top: -6px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
        input[type=range]::-webkit-slider-runnable-track { width: 100%; height: 4px; cursor: pointer; background: #e2e8f0; border-radius: 2px; }

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

            <div style="display: flex; gap: 8px;">
                <button class="ctrl-btn btn-brush" id="btn-format-painter" onclick="toggleFormatPainter()" style="flex: 1;">🪄 格式刷</button>
                <button class="ctrl-btn btn-eraser" id="btn-eraser" onclick="toggleEraser()" style="flex: 1;">🧹 橡皮擦</button>
            </div>

            <button class="ctrl-btn btn-diff" onclick="toggleDiffSidebar()">👀 原文防漏字核对</button>
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
            * <strong style="color:#b91c1c;">红底粗字</strong> 为大模型排版时漏掉的内容。请点击上方 [🪄 格式刷] 或 [🧹 橡皮擦] 在左侧手工修补。
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

        // 🎨 降维打击：智能色卡推算逻辑
        document.getElementById('color-image-upload').addEventListener('change', function(e) {
            const file = e.target.files[0]; if (!file) return;
            const img = new Image(); const reader = new FileReader();
            reader.onload = function(e) { img.src = e.target.result; };
            img.onload = function() {
                try {
                    const colorThief = new ColorThief();
                    // 贪婪提取 5 种颜色建立色库
                    const palette = colorThief.getPalette(img, 5);
                    if(!palette || palette.length < 2) throw new Error("色卡颜色过少");
                    
                    // 计算亮度公式
                    const getLum = (rgb) => 0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2];
                    const rgbToHex = (r, g, b) => '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('');
                    
                    // 对提取到的颜色按亮度排序 (从暗到亮)
                    const sortedPalette = palette.map(rgb => ({ rgb, hex: rgbToHex(...rgb), lum: getLum(rgb) })).sort((a, b) => a.lum - b.lum);
                    
                    // 1. 标题/深色字体 (Star)：取最暗的颜色，确保高对比度
                    const starHex = sortedPalette[0].hex;
                    
                    // 2. 主题色 (Primary)：取中间亮度或 ColorThief 认为最主导的颜色
                    const dominantRGB = colorThief.getColor(img);
                    const primaryHex = rgbToHex(...dominantRGB);
                    
                    // 3. 强调色 (Highlight)：取除了最暗色之外，最鲜艳（反差大）的颜色。简化处理：取亮色系中最亮眼的
                    const highlightHex = sortedPalette[sortedPalette.length - 1].hex !== primaryHex ? sortedPalette[sortedPalette.length - 1].hex : sortedPalette[sortedPalette.length - 2].hex;

                    // 写入核心三原色
                    rootStyle.setProperty('--c-primary', primaryHex); safeSetStorage('--c-primary', primaryHex);
                    rootStyle.setProperty('--c-star', starHex); safeSetStorage('--c-star', starHex);
                    rootStyle.setProperty('--c-highlight', highlightHex); safeSetStorage('--c-highlight', highlightHex);
                    
                    // 🌟 魔法步骤：背景色/辅色全部通过 CSS color-mix 自动由主色推算！(混入90%及95%的白色)
                    // 注意：这需要在用户的样式表里支持 color-mix，绝大多数现代浏览器已支持。
                    const autoSecondary = `color-mix(in srgb, ${primaryHex} 10%, white)`;
                    const autoBg = `color-mix(in srgb, ${primaryHex} 4%, white)`;
                    rootStyle.setProperty('--c-secondary', autoSecondary); safeSetStorage('--c-secondary', autoSecondary);
                    rootStyle.setProperty('--c-case-bg', autoBg); safeSetStorage('--c-case-bg', autoBg);
                    // 全局大背景微调
                    document.body.style.backgroundColor = `color-mix(in srgb, ${primaryHex} 2%, #F8FAFC)`;

                    // UI 展示
                    const display = document.getElementById('extracted-colors-display');
                    display.innerHTML = `<div style="flex:1; background:${starHex};" title="标题深色"></div><div style="flex:1; background:${primaryHex};" title="主色"></div><div style="flex:1; background:${highlightHex};" title="强调色"></div>`;
                    
                    alert('🎉 魔法换色成功！基于您的色卡，系统已自动推算出标题色、主色、强调色，并生成了绝佳的配套浅色背景！');
                } catch (err) { alert('提取颜色失败，请换一张色彩更分明的图片重试！'); }
            }; reader.readAsDataURL(file);
        });

        let isFormatPainterActive = false; let pickedClass = null;
        let isEraserActive = false;

        // 🪄 格式刷逻辑
        window.toggleFormatPainter = function() {
            if (isEraserActive) toggleEraser(); // 互斥
            const btn = document.getElementById('btn-format-painter'); const container = document.getElementById('main-a4-container');
            if (!isFormatPainterActive) {
                isFormatPainterActive = true; pickedClass = null; btn.innerText = '请点击吸取样式...'; btn.style.background = '#fef08a'; btn.style.borderColor = '#facc15'; btn.style.color = '#854d0e'; container.style.cursor = 'crosshair'; container.addEventListener('click', handleFormatPainterClick, true);
            } else {
                isFormatPainterActive = false; pickedClass = null; btn.innerText = '🪄 格式刷'; btn.style.background = ''; btn.style.borderColor = ''; btn.style.color = ''; container.style.cursor = 'auto'; container.removeEventListener('click', handleFormatPainterClick, true);
            }
        }
        function handleFormatPainterClick(e) {
            if (!isFormatPainterActive) return; e.preventDefault(); e.stopPropagation();
            const target = e.target; const btn = document.getElementById('btn-format-painter');
            if (!pickedClass) {
                if (target.classList.length > 0 && !target.classList.contains('a4-page') && !target.classList.contains('page-content')) {
                    pickedClass = target.className; btn.innerText = '✅ 已吸取，点击涂刷 (Esc退出)'; btn.style.background = '#bbf7d0'; btn.style.color = '#166534';
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

        // 🧹 橡皮擦逻辑
        window.toggleEraser = function() {
            if (isFormatPainterActive) toggleFormatPainter(); // 互斥
            const btn = document.getElementById('btn-eraser'); const container = document.getElementById('main-a4-container');
            if (!isEraserActive) {
                isEraserActive = true; btn.innerText = '点击文字清除样式 (Esc退出)'; btn.style.background = '#fca5a5'; btn.style.borderColor = '#f87171'; btn.style.color = '#7f1d1d'; container.classList.add('eraser-mode'); container.addEventListener('click', handleEraserClick, true);
            } else {
                isEraserActive = false; btn.innerText = '🧹 橡皮擦'; btn.style.background = ''; btn.style.borderColor = ''; btn.style.color = ''; container.classList.remove('eraser-mode'); container.removeEventListener('click', handleEraserClick, true);
            }
        }
        function handleEraserClick(e) {
            if (!isEraserActive) return; e.preventDefault(); e.stopPropagation();
            const target = e.target;
            if (target.classList.contains('page-content') || target.classList.contains('a4-page')) return;
            
            // 如果是块级元素，重置为普通正文
            if (target.tagName === 'DIV' || target.tagName === 'P' || target.tagName.match(/^H[1-6]$/i)) {
                target.className = 'text-block';
            } 
            // 如果是行内 span 元素，直接剥离（保留文字内容）
            else if (target.tagName === 'SPAN') {
                const text = document.createTextNode(target.innerText);
                target.parentNode.replaceChild(text, target);
            }
        }

        document.addEventListener('keydown', function(e) { 
            if (e.key === 'Escape') {
                if (isFormatPainterActive) toggleFormatPainter(); 
                if (isEraserActive) toggleEraser();
            }
        });

        // 👀 Diff 侧边栏
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
                    if (rawDataStr && rawDataStr.trim() !== "") {
                        originalText = JSON.parse(rawDataStr);
                    } else {
                        contentArea.innerHTML = '<div style="color:#b91c1c; font-weight:bold; padding:20px;">⚠️ 未检测到大模型吐出的原始数据。</div>'; return;
                    }

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
