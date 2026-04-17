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
    # =======================================================
    # 🚨 战区一：数据清洗与防错 (pure_content)
    # =======================================================
    content_area = req.pure_content
    if isinstance(content_area, str):
        try:
            parsed = json.loads(content_area)
            if isinstance(parsed, dict) and "pure_content" in parsed:
                content_area = parsed["pure_content"]
        except Exception: pass
        content_area = str(content_area).replace('\\"', '"').replace('\\n', '')
        if content_area.startswith('{"<'):
            content_area = re.sub(r'^\{"', '', content_area)
            content_area = re.sub(r'",\s*"debug_chunk_count".*?\}$', '', content_area, flags=re.DOTALL)

    doc_category = req.category or "2026 教研内参"
    doc_title = req.title_info or "排版报告"
    theme_colors = req.theme_colors
    clean_zjmk_ty = (req.zjmk_ty or "").strip()
    clean_zjmk_zs = (req.zjmk_zs or "").strip()

    # =======================================================
    # 🚨 战区二：比对文本预处理 (original_text)
    # =======================================================
    original_raw = req.original_text
    if isinstance(original_raw, str):
        try: original_raw = json.loads(original_raw)
        except Exception: pass
    if isinstance(original_raw, str):
        try:
            cleaned_str = original_raw.replace('\\n', '\n').replace('\\"', '"')
            original_raw = json.loads(cleaned_str)
        except Exception: pass

    extracted_text = ""
    if isinstance(original_raw, list):
        for item in original_raw:
            if isinstance(item, dict) and item.get("data"): extracted_text += str(item["data"]) + "\n"
            elif isinstance(item, str): extracted_text += item + "\n"
    elif isinstance(original_raw, dict) and original_raw.get("data"): extracted_text = str(original_raw["data"])
    else: extracted_text = str(original_raw)

    if extracted_text:
        extracted_text = re.sub(r'(?m)^#+\s*', '', extracted_text)
        extracted_text = re.sub(r'\*+', '', extracted_text)
        extracted_text = re.sub(r'(?m)^[-+]\s+', '', extracted_text)
        extracted_text = re.sub(r'(?m)^>\s*', '', extracted_text)
        extracted_text = re.sub(r'[_＿]{2,}', '', extracted_text)

    final_style_content = clean_zjmk_ty + "\n\n" + clean_zjmk_zs
    safe_original_json = json.dumps(extracted_text.strip(), ensure_ascii=False).replace("</", "<\\/")

    # =======================================================
    # 🚨 战区三：终极引擎代码生成 (包含页眉记忆修复)
    # =======================================================
    html_template = "\ufeff" + """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>__DOC_TITLE__</title>
    <link href="https://fonts.googleapis.com/css2?family=LXGW+WenKai+Screen&family=Noto+Serif+SC:wght@600;900&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/color-thief/2.3.0/color-thief.umd.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/diff_match_patch/20121119/diff_match_patch.js"></script>

    <style id="dynamic-style">
        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; box-sizing: border-box; }
        :root {
            --c-primary: #52A89E; --c-star: #2D7A71; --c-highlight: #D59A44; --c-accent: #E07A5F;
            --c-mod-point: #9A7EB4; --c-mod-mnemonic: #E88796; --c-mod-practice: #48BB78;
            --c-border: #CBE3E0; --c-case-bg: #EAF5F4; --c-secondary: #F4FAFA;
            --f-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
            --f-size-base: 14px; --f-size-title: 18px; --line-height: 1.8;
            --letter-spacing: 0px; --radius-card: 6px; --watermark-opacity: 0.05;
        }
        __THEME_COLORS__

        /* 🚨 大标题绝对居中 */
        .page-content .title-primary, .page-content h1 { display: block !important; text-align: center !important; width: 100% !important; margin: 30px 0 !important; }
        .page-content .panel-summary { display: block !important; margin: 30px auto 20px !important; }
        
        /* 🚨 两端对齐，杜绝最后一行拉伸 */
        .text-block, .script-line {
            margin-bottom: 8px;
            text-align: justify !important; 
            text-justify: inter-ideograph !important; 
            text-align-last: left !important;
            word-break: break-word;
            break-inside: avoid;
        }

        body { background-color: #F1F5F9; font-family: var(--f-family, sans-serif); margin: 0; padding: 0; display: flex; gap: 30px; justify-content: center; color: #334155; }
        
        .a4-container { flex: 1; max-width: 210mm; display: flex; flex-direction: column; gap: 20px; align-items: center; padding-top: 30px; padding-bottom: 40px; transition: margin-right 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
        .a4-page { width: 210mm; min-height: 297mm; position: relative; padding: 18mm 15mm 30mm 15mm; page-break-after: always; background: #FFFFFF; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08); overflow: hidden; flex-shrink: 0; }
        
        .watermark-container { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0; display: flex; align-items: center; justify-content: center; }
        .watermark-text { font-size: 80px; font-weight: 900; color: #000; opacity: var(--watermark-opacity); transform: rotate(-45deg); white-space: nowrap; font-family: sans-serif; text-transform: uppercase; letter-spacing: 10px; }

        .page-header { position: absolute; top: 12mm; left: 15mm; right: 15mm; display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 1.2px solid #cbd5e1; padding-bottom: 6px; font-size: 10px; color: #64748b; font-weight: bold; z-index: 10; }
        .page-footer { position: absolute; bottom: 10mm; left: 15mm; right: 15mm; display: grid; grid-template-columns: 1fr 1fr 1fr; align-items: center; font-size: 10px; color: #94a3b8; border-top: 1px dashed #cbd5e1; padding-top: 6px; z-index: 10; }
        .page-footer .f-left { text-align: left; outline: none; }
        .page-footer .f-center { text-align: center; font-family: Arial, sans-serif; font-weight: bold; pointer-events: none; user-select: none; }
        .page-footer .f-right { text-align: right; outline: none; }

        .page-content { position: relative; z-index: 5; display: flow-root; width: 100%; font-size: var(--f-size-base, 14px); line-height: var(--line-height, 1.8); letter-spacing: var(--letter-spacing, 0px); font-family: var(--f-family) !important; min-height: 50px; }
        
        .page-content table { width: 100%; border-collapse: collapse; table-layout: fixed; word-wrap: break-word; margin: 15px 0; font-size: 13px; }
        .page-content th, .page-content td { border: 1px solid var(--c-border); padding: 8px 12px; text-align: left; }
        .page-content th { background-color: var(--c-case-bg); color: var(--c-primary); font-weight: bold; }

        [contenteditable="true"]:hover { background-color: rgba(113, 176, 246, 0.03); cursor: text; }
        .eraser-mode * { cursor: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="%23EF4444" stroke-width="2"><path d="M20 20H7L3 16C2.5 15.5 2.5 14.5 3 14L13 4C13.5 3.5 14.5 3.5 15 4L20 9C20.5 9.5 20.5 10.5 20 11L11 20H20V20Z"/><line x1="18" y1="13" x2="11" y2="20"/></svg>') 0 20, crosshair !important; }

        .control-panel { width: 340px; background: rgba(255, 255, 255, 0.88); backdrop-filter: blur(15px); padding: 24px; border-radius: 20px; box-shadow: 0 15px 50px rgba(0,0,0,0.1), inset 0 1px 0 rgba(255,255,255,0.8); border: 1px solid rgba(226, 232, 240, 0.8); height: fit-content; position: sticky; top: 30px; z-index: 1000; flex-shrink: 0; max-height: 95vh; overflow-y: auto; }
        .control-panel::-webkit-scrollbar { width: 4px; } .control-panel::-webkit-scrollbar-thumb { background-color: #cbd5e1; border-radius: 4px; }
        
        .panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
        .panel-header h3 { margin: 0; font-size: 16px; color: #1e293b; font-weight: 800; display: flex; align-items: center; gap: 6px; }
        .tool-card { background: #fff; padding: 18px; border-radius: 14px; border: 1px solid #f1f5f9; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.02); }
        .ctrl-btn { width: 100%; padding: 12px; margin-bottom: 8px; border: 1px solid transparent; border-radius: 10px; cursor: pointer; transition: 0.2s; font-size: 13px; font-weight: 700; display: flex; align-items: center; justify-content: center; gap: 8px; }
        .ctrl-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        .btn-main { background: var(--c-primary); color: #fff; border: none; padding: 14px; margin-top: 10px; }

        .color-row { display:flex; justify-content:space-between; margin-bottom:10px; align-items:center; }
        .color-tool-btn { background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; cursor:pointer; width:28px; height:28px; display:flex; align-items:center; justify-content:center; transition:0.2s; color:#475569;}
        .color-tool-btn:hover { background:#e2e8f0; color:#0f172a;}

        .preset-badge { width: 22px; height: 22px; border-radius: 50%; cursor: pointer; border: 2px solid #fff; box-shadow: 0 2px 5px rgba(0,0,0,0.15); transition: 0.2s; }
        .preset-badge:hover { transform: scale(1.2); }

        .ctrl-group { margin-bottom: 10px; } 
        .ctrl-group label { display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 4px; color: #94a3b8; font-weight: 600; }
        .ctrl-group label span { color: #0f172a; font-weight: 700; }
        .ctrl-group select { width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px; outline: none; background: #f8fafc; cursor: pointer; }
        input[type=range] { -webkit-appearance: none; width: 100%; background: transparent; }
        input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; height: 16px; width: 16px; border-radius: 50%; background: var(--c-primary); cursor: pointer; margin-top: -6px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
        input[type=range]::-webkit-slider-runnable-track { width: 100%; height: 4px; cursor: pointer; background: #e2e8f0; border-radius: 2px; }

        #inspector-tooltip { position: fixed; display: none; background: rgba(15, 23, 42, 0.9); backdrop-filter: blur(8px); color: #f8fafc; padding: 14px 18px; border-radius: 12px; font-size: 12px; z-index: 99999; pointer-events: none; line-height: 1.6; box-shadow: 0 10px 25px rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.15); }
        #notion-hover-menu { position: fixed; display: none; background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(8px); padding: 8px 14px; border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); z-index: 10000; align-items: center; gap: 10px; border: 1px solid rgba(255,255,255,0.1); flex-direction: column; align-items: flex-start;}
        .hover-color-btn { width: 22px; height: 22px; border-radius: 50%; cursor: pointer; border: 1.5px solid rgba(255,255,255,0.2); transition: transform 0.1s; }
        .hover-color-btn:hover { transform: scale(1.2); }

        #diff-sidebar { position: fixed; right: -450px; top: 0; width: 400px; height: 100vh; background: #fff; box-shadow: -10px 0 40px rgba(0,0,0,0.1); z-index: 9999; transition: right 0.4s cubic-bezier(0.16, 1, 0.3, 1); display: flex; flex-direction: column; }
        .diff-missing { background:#fee2e2; color:#b91c1c; font-weight:800; padding:2px 4px; border-radius:4px; cursor:pointer; border-bottom:2px solid #ef4444; }
        
        /* 🚨 终极核弹级修复：彻底打破打印机的 Flexbox 灾难 */
        @media print { 
            .control-panel, #diff-sidebar, #notion-hover-menu { display: none !important; } 
            body { display: block !important; background: #fff !important; margin: 0 !important; padding: 0 !important; }
            .a4-container { display: block !important; padding: 0 !important; margin: 0 !important; max-width: none !important; }
            .a4-page { box-shadow: none !important; margin: 0 !important; page-break-after: always !important; }
            @page { size: A4 portrait; margin: 0; }
        }
        __FINAL_STYLE_CONTENT__
    </style>
</head>
<body onpaste="handlePaste(event)">
    <div id="inspector-tooltip"></div>
    <div id="notion-hover-menu"></div>
    
    <div class="control-panel no-print">
        <div class="panel-header">
            <h3>⚙️ 排版工作室</h3>
            <button onclick="resetSettings()" style="font-size:11px; color:#94a3b8; border:none; background:none; cursor:pointer; font-weight:bold;">↺ 恢复默认</button>
        </div>

        <div class="tool-card">
            <input type="file" id="color-image-upload" accept="image/*" style="display: none;">
            <button class="ctrl-btn" style="background:#fefce8; color:#a16207; border-color:#fef08a;" onclick="document.getElementById('color-image-upload').click()">🎨 点击上传 / 粘贴图片换色</button>
            <div id="extracted-colors-display" style="display:flex; gap:4px; height: 12px; border-radius: 12px; overflow: hidden; margin-top: 10px;"></div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:12px;">
                <div id="theme-presets" style="display:flex; gap:6px;"></div>
                <button onclick="saveCurrentTheme()" style="font-size:11px; background:#f1f5f9; border:1px solid #e2e8f0; border-radius:6px; cursor:pointer; padding:4px 8px; color:#475569; font-weight:bold;">⭐ 收藏主题</button>
            </div>
        </div>

        <div class="tool-card">
            <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:6px;">
                <button class="ctrl-btn" id="btn-format-painter" onclick="toggleFormatPainter()" style="background:#f0fdf4; color:#15803d; padding:10px 0; font-size:12px;">🪄 格式刷</button>
                <button class="ctrl-btn" id="btn-eraser" onclick="toggleEraser()" style="background:#fef2f2; color:#b91c1c; padding:10px 0; font-size:12px;">🧹 橡皮擦</button>
                <button class="ctrl-btn" id="btn-inspector" onclick="toggleInspector()" style="background:#faf5ff; color:#6b21a8; padding:10px 0; font-size:12px;">🔍 寻色器</button>
            </div>
            <button class="ctrl-btn" style="background:#eff6ff; color:#1d4ed8; margin-top:8px;" onclick="toggleDiffSidebar()">👀 原文防漏字核对</button>
        </div>

        <div class="tool-card" id="color-panels-card">
            <div class="ctrl-group" id="group-base-colors" style="margin-bottom: 16px;"><label style="font-weight:700; color:#64748b; margin-bottom:8px; display:block;">🧊 基础四色板</label><div id="panel-base-colors"></div></div>
            <div class="ctrl-group" id="group-comp-colors" style="margin-bottom: 0;"><label style="font-weight:700; color:#64748b; margin-bottom:8px; display:block;">🧩 组件专属色</label><div id="panel-comp-colors"></div></div>
        </div>

        <div class="tool-card">
            <div style="margin-bottom:12px;">
                <label style="font-size:12px; font-weight:700; color:#64748b;">☁️ 字体风格库</label>
                <select id="sel-font" style="margin-top:5px;">
                    <optgroup label="✨ 云端甄选 (需联网)">
                        <option value="'LXGW WenKai Screen', sans-serif">霞鹜文楷 (手账风)</option>
                        <option value="'Noto Serif SC', serif">思源宋体 (印刷风)</option>
                    </optgroup>
                    <optgroup label="💻 系统内置">
                        <option value="'PingFang SC', 'Microsoft YaHei', sans-serif">现代黑体 (默认)</option>
                        <option value="'STKaiti', 'KaiTi', serif">标准楷体 (公文)</option>
                    </optgroup>
                </select>
            </div>
            
            <div style="margin-bottom:16px;">
                <label style="font-size:12px; font-weight:700; color:#64748b;">🔏 版权与水印</label>
                <input type="text" id="in-watermark" placeholder="输入您的品牌水印..." oninput="updateWatermark()" style="width:100%; padding:8px; border-radius:6px; border:1px solid #e2e8f0; margin-top:5px; font-size:13px; background:#f8fafc; outline:none;">
                <div style="display:flex; justify-content:space-between; margin-top:8px; font-size:11px; color:#94a3b8; align-items:center;">
                    <span>透明度</span><input type="range" id="sl-watermark-opacity" min="0" max="0.3" step="0.01" value="0.05" oninput="updateWatermark()" style="width:70%;">
                </div>
            </div>
            
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                <div class="ctrl-group"><label>正文字号 <span id="val-f-size-base">14px</span></label><input type="range" id="sl-f-size-base" min="12" max="24" value="14"></div>
                <div class="ctrl-group"><label>标题字号 <span id="val-f-size-title">18px</span></label><input type="range" id="sl-f-size-title" min="14" max="36" value="18"></div>
                <div class="ctrl-group"><label>全局行距 <span id="val-line-height">1.8</span></label><input type="range" id="sl-line-height" min="1.2" max="3" step="0.1" value="1.8"></div>
                <div class="ctrl-group"><label>全局字距 <span id="val-letter-spacing">0px</span></label><input type="range" id="sl-letter-spacing" min="-1" max="10" step="0.5" value="0"></div>
                <div class="ctrl-group" style="grid-column: span 2; margin-bottom: 0;"><label>卡片圆角 <span id="val-radius-card">6px</span></label><input type="range" id="sl-radius-card" min="0" max="30" value="6"></div>
            </div>
        </div>

        <div style="display:flex; gap:6px; margin-bottom:10px;">
            <button class="ctrl-btn" style="flex:1; background:#f8fafc; color:#475569; border:1px solid #e2e8f0; margin:0; padding:10px 0; font-size:12px;" onclick="recalculatePagination()" title="增删内容后，重新计算 A4 换页">🔄 重新分页</button>
            <button class="ctrl-btn" style="flex:1; background:#f8fafc; color:#475569; border:1px solid #e2e8f0; margin:0; padding:10px 0; font-size:12px;" onclick="restoreOriginal()" title="放弃修改，彻底还原回最初大模型的排版">⏪ 还原原文</button>
            <button class="ctrl-btn" style="flex:1; background:#fff1f2; color:#be123c; border:1px solid #fecdd3; margin:0; padding:10px 0; font-size:12px;" onclick="clearManualStyles()" title="仅清除用悬浮菜单涂抹的颜色、高亮和批注，保留文字">🧹 清除手改</button>
        </div>

        <button class="ctrl-btn btn-main" style="margin-top:0;" onclick="recalculatePagination(); setTimeout(()=>window.print(), 500);">💾 导出最终 PDF</button>
    </div>

    <div class="a4-container" id="main-a4-container"></div>

    <div id="diff-sidebar" class="no-print">
        <div style="padding:24px; border-bottom:1px solid #f1f5f9; display:flex; justify-content:space-between; align-items:center; background:#eff6ff;">
            <span style="font-weight:900; color:#1e3a8a;">🚨 防漏字验证报告</span>
            <button onclick="toggleDiffSidebar()" style="border:none; background:rgba(255,255,255,0.5); padding:5px 12px; border-radius:20px; cursor:pointer; color:#1e3a8a; font-weight:bold;">关闭</button>
        </div>
        <div style="padding:15px 24px; background:#f8fafc; font-size:12px; border-bottom:1px solid #e2e8f0; color:#475569;">
            * 点击红色词块即可 <strong style="color:#b91c1c;">一键复制</strong>，随后在左侧粘贴补回。
        </div>
        <div id="diff-content-area" style="flex:1; overflow-y:auto; padding:24px; font-size:14px; line-height:1.8;"></div>
    </div>

    <div id="source-data" style="display:none;">__CONTENT_AREA__</div>
    <script id="style-data" type="text/plain">__THEME_COLORS__</script>
    <script id="raw-source-data" type="application/json">__ORIGINAL_TEXT__</script>

    <script>
        const root = document.documentElement.style;
        // 🚨 终极防丢失状态机：实时保存你打过的字
        let headerFooterState = {
            'h-left': '__DOC_CATEGORY__',
            'h-right': '__DOC_TITLE__',
            'f-left': '内部教研',
            'f-right': '独家整理'
        };
        let pageCount = 0; let dynH = 930;

        function getSafeH() { 
            try {
                let t = document.createElement('div');
                t.style.height = '248mm'; 
                t.style.position = 'absolute';
                t.style.visibility = 'hidden';
                document.body.appendChild(t);
                let h = t.getBoundingClientRect().height;
                document.body.removeChild(t);
                return h > 100 ? h : 930;
            } catch(e) { return 930; }
        }
        
        function safeGetStorage(k) { try { return localStorage.getItem(k); } catch(e){ return null;} }
        function safeSetStorage(k,v) { try { localStorage.setItem(k,v); } catch(e){} }
        window.resetSettings = function() { if(confirm('确定清空所有本地配置吗？')) { try{ localStorage.clear(); }catch(e){} location.reload(); } };

        document.addEventListener('input', e => {
            if (e.target.classList.contains('sync-text')) {
                const key = e.target.dataset.key; const val = e.target.innerHTML;
                headerFooterState[key] = val; // 🚨 每次打字，实时存入记忆芯片
                document.querySelectorAll(`.sync-text[data-key="${key}"]`).forEach(el => { if(el !== e.target) el.innerHTML = val; });
            }
        });

        function createNewPage() {
            pageCount++;
            const p = document.createElement('div'); p.className = 'a4-page';
            // 🚨 造纸时，从记忆芯片里读取你最新的修改！
            p.innerHTML = `
                <div class="watermark-container"><div class="watermark-text"></div></div>
                <div class="page-header">
                    <span class="sync-text" data-key="h-left" contenteditable="true">${headerFooterState['h-left']}</span>
                    <span class="sync-text" data-key="h-right" contenteditable="true">${headerFooterState['h-right']}</span>
                </div>
                <div class="page-content" contenteditable="true" spellcheck="false"></div>
                <div class="page-footer">
                    <span class="f-left sync-text" data-key="f-left" contenteditable="true">${headerFooterState['f-left']}</span>
                    <span class="f-center">- ${pageCount} -</span>
                    <span class="f-right sync-text" data-key="f-right" contenteditable="true">${headerFooterState['f-right']}</span>
                </div>`;
            document.getElementById('main-a4-container').appendChild(p);
            updateWatermark();
            return p;
        }

        window.clearManualStyles = function() {
            if(confirm('🧹 确定要清除所有手动涂抹的颜色、高亮和批注吗？\\n（只会清除手改的样式，不会删除文字。若想彻底还原大模型排版，请点击【还原原文】）')) {
                document.querySelectorAll('.page-content *').forEach(el => {
                    el.style.color = ''; 
                    el.style.background = ''; 
                    el.style.backgroundColor = '';
                    el.style.textDecoration = ''; 
                    el.style.textEmphasis = ''; 
                    el.style.webkitTextEmphasis = '';
                });
                document.querySelectorAll('.page-content font').forEach(el => {
                    el.removeAttribute('color');
                    el.removeAttribute('size');
                    el.removeAttribute('face');
                });
            }
        };

        window.restoreOriginal = function() {
            if(confirm('⏪ 确定要放弃所有手动修改，还原回最初排版状态吗？')) {
                document.querySelectorAll('.a4-page').forEach(p => p.remove());
                pageCount = 0; dynH = getSafeH();
                const src = document.getElementById('source-data');
                src.innerHTML = window.__ORIGINAL_HTML_BACKUP__;
                const nodes = Array.from(src.childNodes).map(n => n.cloneNode(true));
                runPaginationEngine(nodes);
            }
        };

        function mix(rgb, p) { 
            const w=255; const f=p/100; 
            const r=(v)=>Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2,'0');
            return '#' + r(rgb[0]*f + w*(1-f)) + r(rgb[1]*f + w*(1-f)) + r(rgb[2]*f + w*(1-f));
        }
        
        function rgbToHex(str) {
            let m = str.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
            if(m) return "#" + ("0"+parseInt(m[1]).toString(16)).slice(-2) + ("0"+parseInt(m[2]).toString(16)).slice(-2) + ("0"+parseInt(m[3]).toString(16)).slice(-2);
            return str;
        }

        function processImage(img) {
            try {
                const ct = new ColorThief();
                const rawPalette = ct.getPalette(img, 20);
                const domRGB = ct.getColor(img);
                
                const dist = (c1, c2) => Math.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2);
                let uniquePalette = [];
                for (let c of rawPalette) {
                    let isUnique = true;
                    for (let u of uniquePalette) { if (dist(c, u) < 45) { isUnique = false; break; } }
                    const lum = 0.299*c[0] + 0.587*c[1] + 0.114*c[2];
                    if (isUnique && lum > 15 && lum < 245) uniquePalette.push(c);
                }
                if (uniquePalette.length < 4) uniquePalette = rawPalette;

                uniquePalette.sort((a,b) => (0.299*a[0]+0.587*a[1]+0.114*a[2]) - (0.299*b[0]+0.587*b[1]+0.114*b[2]));
                const hexGen = (r,g,b) => '#' + [r,g,b].map(x=>Math.max(0,Math.min(255,Math.round(x))).toString(16).padStart(2,'0')).join('');
                
                const starHex = hexGen(...uniquePalette[0]);
                const primaryHex = hexGen(...domRGB);
                const highlightHex = hexGen(...uniquePalette[uniquePalette.length - 1]);
                
                let accentHex = primaryHex;
                for(let i=1; i<uniquePalette.length; i++) {
                    let temp = hexGen(...uniquePalette[i]);
                    if(temp !== starHex && temp !== primaryHex && temp !== highlightHex) { accentHex = temp; break; }
                }
                
                root.setProperty('--c-primary', primaryHex); safeSetStorage('--c-primary', primaryHex);
                root.setProperty('--c-star', starHex); safeSetStorage('--c-star', starHex);
                root.setProperty('--c-highlight', highlightHex); safeSetStorage('--c-highlight', highlightHex);
                root.setProperty('--c-accent', accentHex); safeSetStorage('--c-accent', accentHex);
                
                root.setProperty('--c-secondary', mix(domRGB, 10)); root.setProperty('--c-case-bg', mix(domRGB, 4));
                document.body.style.backgroundColor = mix(domRGB, 2);
                
                const display = document.getElementById('extracted-colors-display');
                display.innerHTML = `<div style="flex:1; background:${starHex};" title="深色"></div><div style="flex:1; background:${primaryHex};" title="主色"></div><div style="flex:1; background:${accentHex};" title="点缀色"></div><div style="flex:1; background:${highlightHex};" title="强调色"></div>`;

                initDynamicColorPanel();
                alert('🎉 魔法引擎升级！已成功剥离色卡中的独特色彩。');
            } catch(e) { alert('提取颜色失败，请换一张色彩丰富的图片重试！'); }
        }

        window.handlePaste = function(e) {
            if(e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) return; 
            const items = (e.clipboardData || e.originalEvent.clipboardData).items;
            for (let i=0; i<items.length; i++) {
                if (items[i].type.indexOf("image") !== -1) {
                    const blob = items[i].getAsFile(); const reader = new FileReader();
                    reader.onload = (event) => { const img = new Image(); img.onload = ()=>processImage(img); img.src = event.target.result; };
                    reader.readAsDataURL(blob); e.preventDefault(); break;
                }
            }
        }

        document.getElementById('color-image-upload').onchange = (e) => {
            const file = e.target.files[0]; if(!file) return;
            const reader = new FileReader();
            reader.onload = (ev) => { const img = new Image(); img.onload = ()=>processImage(img); img.src = ev.target.result; };
            reader.readAsDataURL(file);
        };

        window.saveCurrentTheme = function() {
            const colors = {};
            globalExtractedVars.forEach(v => colors[v] = rgbToHex(getComputedStyle(document.documentElement).getPropertyValue(v).trim()));
            let list = JSON.parse(localStorage.getItem('my_themes') || '[]');
            list.push(colors);
            localStorage.setItem('my_themes', JSON.stringify(list.slice(-5))); 
            renderThemePresets();
        }

        function renderThemePresets() {
            const container = document.getElementById('theme-presets'); container.innerHTML = '';
            let list = JSON.parse(localStorage.getItem('my_themes') || '[]');
            list.forEach((theme, index) => {
                const b = document.createElement('div'); b.className = 'preset-badge'; b.style.background = theme['--c-primary'];
                
                b.title = "左键：切换至此主题\\n右键：取消收藏该主题";
                
                b.onclick = () => { Object.keys(theme).forEach(k => root.setProperty(k, theme[k])); initDynamicColorPanel(); };
                
                b.oncontextmenu = (e) => {
                    e.preventDefault(); 
                    if(confirm('🗑️ 确定要取消收藏这个主题色彩吗？')) {
                        list.splice(index, 1); 
                        localStorage.setItem('my_themes', JSON.stringify(list)); 
                        renderThemePresets(); 
                    }
                };
                
                container.appendChild(b);
            });
        }

        window.applyToText = function(varName, command) { const color = rgbToHex(getComputedStyle(document.documentElement).getPropertyValue(varName).trim()); if (color) document.execCommand(command, false, color); };
        
        window.applyStyleSpan = function(color, type) {
            const sel = window.getSelection(); if (sel.isCollapsed) return;
            const range = sel.getRangeAt(0); const span = document.createElement('span');
            
            if (type === 'marker') {
                span.style.background = `linear-gradient(transparent 60%, ${color}80 40%)`;
                span.style.padding = '0 2px'; span.style.borderRadius = '3px';
            } else if (type === 'wavy') {
                span.style.textDecoration = `underline wavy ${color}`;
                span.style.textUnderlineOffset = '4px'; span.style.textDecorationThickness = '1.5px';
            } else if (type === 'dot') {
                span.style.textEmphasis = `filled circle ${color}`;
                span.style.webkitTextEmphasis = `filled circle ${color}`;
            }
            
            try { span.appendChild(range.extractContents()); range.insertNode(span); } 
            catch(e) { document.execCommand('backColor', false, color+'40'); } 
            sel.removeAllRanges();
        };

        window.clearSelectionColor = function() {
            const sel = window.getSelection(); if (sel.isCollapsed) return;
            document.execCommand('removeFormat', false, null); document.execCommand('backColor', false, 'transparent');
            const text = sel.toString(); if (text.indexOf('\\n') === -1) { document.execCommand('insertText', false, text); }
        };

        function buildHoverToolbar() {
            const menu = document.getElementById('notion-hover-menu');
            if(!menu) return; menu.innerHTML = '';
            
            const title = document.createElement('div'); title.style.cssText = "color:#94a3b8; font-size:10px; font-weight:bold; letter-spacing:1px; margin-bottom:6px;"; title.innerText = "文字 / 马克笔";
            menu.appendChild(title);

            const rowText = document.createElement('div'); rowText.style.cssText = "display:flex; gap:8px; align-items:center; margin-bottom:8px;";
            const rowBg = document.createElement('div'); rowBg.style.cssText = "display:flex; gap:8px; align-items:center;";
            
            const coreVars = ['--c-primary', '--c-star', '--c-highlight', '--c-accent', '--c-mod-point'];
            
            coreVars.forEach(v => {
                let c = rgbToHex(getComputedStyle(document.documentElement).getPropertyValue(v).trim());
                if(c.startsWith('#')) {
                    let tb = document.createElement('div'); tb.className='hover-color-btn'; tb.style.background = c;
                    tb.title = "字色: " + v.replace('--c-','');
                    tb.onmousedown = (e) => { e.preventDefault(); applyToText(v, 'foreColor'); };
                    rowText.appendChild(tb);
                    
                    let bb = document.createElement('div'); bb.className='hover-color-btn'; 
                    bb.style.background = `linear-gradient(transparent 50%, ${c} 50%)`;
                    bb.style.borderRadius = "4px"; 
                    bb.title = "马克笔: " + v.replace('--c-','');
                    bb.onmousedown = (e) => { e.preventDefault(); applyStyleSpan(c, 'marker'); }; 
                    rowBg.appendChild(bb);
                }
            });
            
            const divider = document.createElement('div'); divider.style.cssText = "width:1px; height:16px; background:rgba(255,255,255,0.2); margin: 0 4px;";
            rowBg.appendChild(divider);
            
            const accentColor = rgbToHex(getComputedStyle(document.documentElement).getPropertyValue('--c-accent').trim());
            
            const btnWavy = document.createElement('div'); btnWavy.innerHTML = '〰️'; btnWavy.style.cssText = "cursor:pointer; font-size:12px; filter:grayscale(100%); transition:0.2s;";
            btnWavy.title = "添加波浪线"; btnWavy.onmousedown = (e) => { e.preventDefault(); applyStyleSpan(accentColor, 'wavy'); };
            btnWavy.onmouseover = ()=>btnWavy.style.filter='none'; btnWavy.onmouseout = ()=>btnWavy.style.filter='grayscale(100%)';
            
            const btnDot = document.createElement('div'); btnDot.innerHTML = '••'; btnDot.style.cssText = "cursor:pointer; font-size:12px; filter:grayscale(100%); font-weight:900; letter-spacing:-2px; transition:0.2s;";
            btnDot.title = "添加着重号"; btnDot.onmousedown = (e) => { e.preventDefault(); applyStyleSpan(accentColor, 'dot'); };
            btnDot.onmouseover = ()=>btnDot.style.filter='none'; btnDot.onmouseout = ()=>btnDot.style.filter='grayscale(100%)';

            rowBg.appendChild(btnWavy); rowBg.appendChild(btnDot);

            const clearBtn = document.createElement('div'); clearBtn.innerHTML = '🚫'; clearBtn.style.cssText = "cursor:pointer; font-size:14px; margin-left:6px; border-left:1px solid rgba(255,255,255,0.2); padding-left:8px;";
            clearBtn.title = "清除样式"; clearBtn.onmousedown = (e) => { e.preventDefault(); clearSelectionColor(); };
            rowText.appendChild(clearBtn);
            
            menu.appendChild(rowText); menu.appendChild(rowBg);
            menu.addEventListener('mousedown', e => e.preventDefault());
        }

        document.addEventListener('mouseup', () => {
            if(isFormatPainterActive || isEraserActive || isInspectorActive) return;
            const sel = window.getSelection(); const menu = document.getElementById('notion-hover-menu');
            if(!sel.isCollapsed && sel.toString().trim()) {
                let node = sel.anchorNode; let inPage = false;
                while(node && node !== document.body) { if(node.classList && node.classList.contains('a4-page')) { inPage = true; break; } node = node.parentNode; }
                if(inPage) {
                    const r = sel.getRangeAt(0).getBoundingClientRect();
                    menu.style.display = 'flex'; 
                    menu.style.top = (r.top - 75) + 'px';
                    menu.style.left = (r.left + r.width/2 - menu.offsetWidth/2) + 'px';
                }
            } else { menu.style.display = 'none'; }
        });
        document.addEventListener('mousedown', (e) => { const m = document.getElementById('notion-hover-menu'); if (m && !m.contains(e.target)) m.style.display = 'none'; });
        document.addEventListener('scroll', () => { document.getElementById('notion-hover-menu').style.display = 'none'; }, true);

        window.updateWatermark = function() {
            const txt = document.getElementById('in-watermark').value;
            const op = document.getElementById('sl-watermark-opacity').value;
            root.setProperty('--watermark-opacity', op);
            document.querySelectorAll('.watermark-text').forEach(el => el.innerText = txt);
        }

        let globalExtractedVars = [];
        function initDynamicColorPanel() {
            const base = document.getElementById('panel-base-colors'); const comp = document.getElementById('panel-comp-colors');
            if(!base || !comp) return;
            const styleText = document.getElementById('style-data').textContent;
            let varsMatch = styleText.match(/--c-[a-zA-Z0-9-]+/g) || [];
            globalExtractedVars = [...new Set(varsMatch)];
            if(globalExtractedVars.length===0) globalExtractedVars = ['--c-primary', '--c-star', '--c-highlight', '--c-accent'];
            
            base.innerHTML = ''; comp.innerHTML = '';
            globalExtractedVars.forEach(v => {
                let current = rgbToHex(getComputedStyle(document.documentElement).getPropertyValue(v).trim() || '#cccccc');
                let saved = safeGetStorage(v); if(saved) { current = rgbToHex(saved); root.setProperty(v, saved); }
                if (current.startsWith('#')) {
                    const cleanName = v.replace('--c-','');
                    const row = document.createElement('div'); row.className = 'color-row';
                    row.innerHTML = `
                        <span style="font-size:12px; color:#475569; font-weight:600;">${cleanName}</span>
                        <div style="display:flex; gap:4px; align-items:center;">
                            <input type="color" value="${current}" oninput="root.setProperty('${v}', this.value); safeSetStorage('${v}', this.value); buildHoverToolbar();" style="width:24px; height:24px; border:none; background:none; cursor:pointer; padding:0;">
                            <button class="color-tool-btn" title="文字上色" onclick="applyToText('${v}', 'foreColor')"><span style="font-family:serif; font-weight:bold; font-size:14px;">A</span></button>
                            <button class="color-tool-btn" title="马克笔半高亮" onclick="applyStyleSpan('${current}', 'marker')"><div style="width:12px; height:12px; background:linear-gradient(transparent 50%, currentColor 50%); border-radius:2px;"></div></button>
                        </div>`;
                    if(['primary', 'star', 'highlight', 'accent', 'main'].some(k => v.includes(k))) base.appendChild(row); else comp.appendChild(row);
                }
            });
            buildHoverToolbar();
        }

        function initLayoutControls() { 
            ['f-size-base', 'f-size-title', 'line-height', 'letter-spacing', 'radius-card'].forEach(id => { 
                const el = document.getElementById('sl-' + id); const valSpan = document.getElementById('val-' + id); 
                if(el) { 
                    let saved = safeGetStorage('--' + id); 
                    if(saved) { let num = saved.replace(/[^0-9.-]/g, ''); el.value = num; if(valSpan) valSpan.innerText = num; root.setProperty('--' + id, saved); } 
                    el.addEventListener('input', (e) => { let v = e.target.value; let s = id.includes('line') ? '' : 'px'; if(valSpan) valSpan.innerText = v; root.setProperty('--' + id, v + s); safeSetStorage('--' + id, v + s); }); 
                } 
            }); 
            const fontSel = document.getElementById('sel-font'); 
            if(fontSel) { 
                let savedFont = safeGetStorage('--f-family'); if(savedFont) { fontSel.value = savedFont; root.setProperty('--f-family', savedFont); } 
                fontSel.addEventListener('change', (e) => { root.setProperty('--f-family', e.target.value); safeSetStorage('--f-family', e.target.value); }); 
            } 
        }

        function runPaginationEngine(nodes) {
            let page = createNewPage(); let content = page.querySelector('.page-content');
            let currentTitleLevel = ""; let previousNode = null;
            nodes.forEach(node => {
                if (node.nodeType === 1) {
                    const isTitleClass = node.className && typeof node.className === 'string' && node.className.includes('title-');
                    if (isTitleClass) { const titleText = node.innerText.trim(); if (titleText === currentTitleLevel) return; currentTitleLevel = titleText; }
                }
                content.appendChild(node);
                if (content.offsetHeight > dynH) {
                    if (content.childNodes.length > 1) {
                        content.removeChild(node);
                        let nodeToMoveWith = null;
                        if (previousNode && previousNode.nodeType === 1) {
                            const isHeading = previousNode.tagName && previousNode.tagName.match(/^H[1-6]$/i);
                            const isPrevTitleClass = previousNode.className && typeof previousNode.className === 'string' && previousNode.className.includes('title-');
                            if (isHeading || isPrevTitleClass) { nodeToMoveWith = previousNode; content.removeChild(previousNode); }
                        }
                        page = createNewPage(); content = page.querySelector('.page-content');
                        if (nodeToMoveWith) content.appendChild(nodeToMoveWith);
                        content.appendChild(node);
                    }
                }
                if (node.textContent && node.textContent.trim() !== "") previousNode = node;
            });
        }

        window.recalculatePagination = function() { 
            const allContents = document.querySelectorAll('.a4-page .page-content'); if (allContents.length === 0) return; 
            const allNodes = []; 
            allContents.forEach(content => { Array.from(content.childNodes).forEach(child => allNodes.push(child)); }); 
            document.querySelectorAll('.a4-page').forEach(page => page.remove()); 
            pageCount = 0; 
            dynH = getSafeH();
            runPaginationEngine(allNodes); 
        };

        let isFormatPainterActive = false; let pickedClass = null; let isEraserActive = false; let isInspectorActive = false; let colorVarMap = {};
        
        function refreshColorMap() {
            colorVarMap = {}; const dummy = document.createElement('div'); dummy.style.display = 'none'; document.body.appendChild(dummy);
            globalExtractedVars.forEach(v => {
                dummy.style.color = `var(${v})`; let cColor = window.getComputedStyle(dummy).color;
                if (!colorVarMap[cColor]) colorVarMap[cColor] = []; colorVarMap[cColor].push(v.replace('--c-', ''));
                dummy.style.backgroundColor = `var(${v})`; let cBg = window.getComputedStyle(dummy).backgroundColor;
                if (!colorVarMap[cBg]) colorVarMap[cBg] = []; if (!colorVarMap[cBg].includes(v.replace('--c-', ''))) colorVarMap[cBg].push(v.replace('--c-', ''));
            });
            document.body.removeChild(dummy);
        }

        window.toggleInspector = function() {
            isFormatPainterActive = false; isEraserActive = false; const btn = document.getElementById('btn-inspector'); const container = document.getElementById('main-a4-container');
            isInspectorActive = !isInspectorActive;
            if (isInspectorActive) { btn.innerText = '探测中(Esc)'; btn.style.background = '#e9d5ff'; btn.style.color = '#581c87'; container.style.cursor = 'help'; refreshColorMap(); container.addEventListener('mousemove', handleInsp, true); } 
            else { btn.innerText = '🔍 寻色器'; btn.style.background = ''; btn.style.color = ''; container.style.cursor = 'auto'; container.removeEventListener('mousemove', handleInsp, true); document.getElementById('inspector-tooltip').style.display='none'; }
        }
        function handleInsp(e) {
            const t = e.target; if(t.classList.contains('page-content') || t.classList.contains('a4-page')) { document.getElementById('inspector-tooltip').style.display='none'; return; }
            const tt = document.getElementById('inspector-tooltip'); tt.style.display = 'block'; tt.style.left = (e.clientX+15)+'px'; tt.style.top = (e.clientY+15)+'px';
            let c = window.getComputedStyle(t).color; let bg = window.getComputedStyle(t).backgroundColor;
            let cN = colorVarMap[c] ? colorVarMap[c].join(' / ') : '默认'; let bgN = colorVarMap[bg] ? colorVarMap[bg].join(' / ') : (bg === 'rgba(0, 0, 0, 0)' ? '透明' : '默认');
            tt.innerHTML = `标签: &lt;${t.tagName.toLowerCase()}&gt;<br>类名: ${Array.from(t.classList).join(', ') || '正文'}<br><br>字色: <span style="display:inline-block;width:10px;height:10px;background:${c};"></span> ${cN}<br>背景: <span style="display:inline-block;width:10px;height:10px;background:${bg};"></span> ${bgN}`;
        }

        window.toggleFormatPainter = function() {
            isInspectorActive = false; isEraserActive = false; isFormatPainterActive = !isFormatPainterActive; pickedClass = null;
            const btn = document.getElementById('btn-format-painter'); btn.innerText = isFormatPainterActive ? '点击吸取...' : '🪄 格式刷'; btn.style.background = isFormatPainterActive ? '#fef08a' : ''; btn.style.color = isFormatPainterActive ? '#854d0e' : '';
        }

        window.toggleEraser = function() {
            isFormatPainterActive = false; isInspectorActive = false; isEraserActive = !isEraserActive;
            const btn = document.getElementById('btn-eraser'); btn.innerText = isEraserActive ? '擦除中(Esc)' : '🧹 橡皮擦'; btn.style.background = isEraserActive ? '#fca5a5' : ''; btn.style.color = isEraserActive ? '#7f1d1d' : '';
        }

        document.addEventListener('click', e => {
            if(isFormatPainterActive) {
                e.preventDefault(); e.stopPropagation();
                if(!pickedClass) { if(e.target.classList.length>0 && !e.target.classList.contains('page-content')) { pickedClass = e.target.className; document.getElementById('btn-format-painter').innerText = '✅ 涂抹中(Esc)'; document.getElementById('btn-format-painter').style.background = '#bbf7d0'; } }
                else { const isBlock = pickedClass.includes('title') || pickedClass.includes('block'); if(isBlock) { let p = e.target; while(p && p.tagName!=='DIV' && p.tagName!=='P' && !p.classList.contains('page-content')) p=p.parentElement; if(p && !p.classList.contains('page-content')) p.className=pickedClass; else e.target.className=pickedClass; } else { const sel = window.getSelection(); if(!sel.isCollapsed) { const r = sel.getRangeAt(0); const s = document.createElement('span'); s.className=pickedClass; r.surroundContents(s); sel.removeAllRanges(); } else e.target.className=pickedClass; } }
            }
            if(isEraserActive) {
                e.preventDefault(); e.stopPropagation(); const t = e.target; if(t.classList.contains('page-content') || t.classList.contains('a4-page')) return;
                if(t.tagName === 'DIV' || t.tagName === 'P' || t.tagName.match(/^H[1-6]$/i)) { t.className = 'text-block'; t.style.cssText = ''; } 
                else if(t.tagName === 'SPAN') { if(t.style.color || t.style.background || t.style.textDecoration || t.style.textEmphasis) { const text = document.createTextNode(t.innerText); t.parentNode.replaceChild(text, t); } else { const text = document.createTextNode(t.innerText); t.parentNode.replaceChild(text, t); } }
            }
        }, true);
        document.addEventListener('keydown', (e) => { if(e.key==='Escape') { if(isEraserActive)toggleEraser(); if(isFormatPainterActive)toggleFormatPainter(); if(isInspectorActive)toggleInspector(); } });

        window.copyTxt = function(encoded, el) { navigator.clipboard.writeText(decodeURIComponent(encoded)).then(() => { const old = el.innerHTML; el.innerHTML = '✅ 已复制'; el.style.background='#bbf7d0'; el.style.color='#166534'; setTimeout(() => { el.innerHTML = old; el.style.background=''; el.style.color=''; }, 1500); }); };
        
        let isDiffOpen = false;
        window.toggleDiffSidebar = function() {
            const s = document.getElementById('diff-sidebar'); const isOpen = s.style.right === '0px';
            s.style.right = isOpen ? '-450px' : '0px'; document.getElementById('main-a4-container').style.marginRight = isOpen ? '0' : '300px';
            if(!isOpen) {
                const area = document.getElementById('diff-content-area'); area.innerHTML = '<div style="text-align:center; padding:40px;">🔄 比对中...</div>';
                setTimeout(() => {
                    try {
                        const raw = JSON.parse(document.getElementById('raw-source-data').textContent);
                        let cur = ""; document.querySelectorAll('.page-content').forEach(p => cur += p.innerText + "\\n");
                        const dmp = new diff_match_patch(); dmp.Diff_Timeout = 2; const diffs = dmp.diff_main(raw, cur); dmp.diff_cleanupSemantic(diffs);
                        let h = ""; let missingCount = 0;
                        diffs.forEach(d => {
                            if(d[0]===-1) { if(d[1].trim().length>0) { missingCount++; h += `<span class="diff-missing" title="点击复制" onclick="copyTxt('${encodeURIComponent(d[1])}', this)">${d[1]}</span>`; } else h+=d[1]; }
                            else if(d[0]===0) h += `<span style="color:#94a3b8">${d[1]}</span>`;
                        });
                        area.innerHTML = missingCount===0 ? '<div style="color:#15803d; font-weight:800; padding:40px; text-align:center; border:2px dashed #bbf7d0; border-radius:8px; margin:20px; background:#f0fdf4;">🎉 完美通关！无漏字。</div>' : h;
                    } catch(e) { area.innerHTML = '<div style="color:#b91c1c;">⚠️ 比对失败，数据异常。</div>'; }
                }, 300);
            }
        }

        window.addEventListener('DOMContentLoaded', () => {
            renderThemePresets();
            try {
                initLayoutControls(); initDynamicColorPanel();
                const src = document.getElementById('source-data');
                window.__ORIGINAL_HTML_BACKUP__ = src.innerHTML; 
                const nodes = Array.from(src.children).map(n => n.cloneNode(true));
                setTimeout(() => { dynH = getSafeH(); runPaginationEngine(nodes); }, 300);
            } catch(e){}
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
