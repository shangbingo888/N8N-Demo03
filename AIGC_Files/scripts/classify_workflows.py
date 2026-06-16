#!/usr/bin/env python3
"""
n8n Workflow Classifier - 基于节点类型和集成服务对工作流进行七大类别分类，
并提炼核心节点配置、参数逻辑和踩坑经验。
"""

import json
import re
from pathlib import Path
from collections import defaultdict

ANALYSIS_DIR = Path(__file__).parent.parent / "analysis"
OUTPUT_DIR = ANALYSIS_DIR / "classified"

# ============ 分类规则 ============

CATEGORIES = {
    "text-generation": {
        "label": "文本生成 (Text Generation)",
        "description": "使用 OpenAI/LLM 模型进行文本生成、对话、摘要、翻译等自然语言处理任务",
        "node_types": [
            "openAi",
            "@n8n/n8n-nodes-langchain.openAi",
            "lmChatOpenAi",
            "chainLlm",
            "openAiAssistant",
        ],
        "keywords": ["gpt", "chat", "assistant", "openai", "summarize", "translate"],
    },
    "image-processing": {
        "label": "图像处理 (Image Processing)",
        "description": "通过 ComfyUI/Stable Diffusion 等 API 进行 AI 图像生成与处理",
        "node_types": ["editImage"],
        "keywords": ["comfyui", "image", "stable diffusion", "dalle", "midjourney", "generate image"],
    },
    "data-processing": {
        "label": "数据处理 (Data Processing)",
        "description": "与 Google Sheets、PostgreSQL、BigQuery 等数据源集成，进行 ETL、导入导出、数据清洗等操作",
        "node_types": [
            "googleSheets",
            "googleSheetsTrigger",
            "postgres",
            "postgresTool",
            "googleBigQuery",
            "supabase",
            "readWriteFile",
            "readBinaryFiles",
            "convertToFile",
            "extractFromFile",
            "spreadsheetFile",
        ],
        "keywords": ["sheet", "database", "csv", "json", "export", "import", "data"],
    },
    "automation-triggers": {
        "label": "自动化触发 (Automation Triggers)",
        "description": "通过 Webhook、定时调度、Telegram Bot、表单提交等方式触发自动化流程",
        "node_types": [
            "webhook",
            "manualTrigger",
            "scheduleTrigger",
            "telegramTrigger",
            "formTrigger",
            "telegram",
            "respondToWebhook",
            "gmailTrigger",
            "googleDriveTrigger",
            "notionTrigger",
            "airtableTrigger",
            "twilioTrigger",
            "shopifyTrigger",
            "discord",
            "twilio",
            "slack",
        ],
        "keywords": ["webhook", "trigger", "schedule", "telegram", "bot", "automation"],
    },
    "conditional-loop": {
        "label": "条件分支与循环 (Conditional & Loop)",
        "description": "使用条件判断、分支选择、循环处理等控制流节点实现复杂业务逻辑",
        "node_types": [
            "if",
            "switch",
            "filter",
            "splitInBatches",
            "splitOut",
            "limit",
            "aggregate",
            "merge",
            "itemLists",
            "removeDuplicates",
        ],
        "keywords": ["if", "switch", "filter", "loop", "batch", "split", "aggregate"],
    },
    "error-handling": {
        "label": "错误处理与监控 (Error Handling & Monitoring)",
        "description": "包含错误捕获、异常处理、重试机制等保障工作流稳定性的配置",
        "node_types": ["stopAndError", "errorTrigger", "wait"],
        "keywords": ["error", "retry", "timeout", "failure", "monitor"],
    },
    "sub-workflow": {
        "label": "子工作流调用 (Sub-Workflow)",
        "description": "通过 Execute Workflow 节点实现模块化工作流组合与复用",
        "node_types": ["executeWorkflow", "executeWorkflowTrigger"],
        "keywords": ["execute", "sub", "module", "reuse"],
    },
}


def load_parsed_workflows():
    """Load parsed workflow data."""
    with open(ANALYSIS_DIR / "parsed_workflows.json", "r", encoding="utf-8") as f:
        return json.load(f)


def classify_workflow(wf):
    """Classify a single workflow into one or more categories based on its node types."""
    node_type_names = set()
    for nt in wf["node_types"]:
        # Extract base type name
        base = nt.replace("n8n-nodes-base.", "").replace("n8n-nodes-mcp.", "")
        node_type_names.add(base)
        node_type_names.add(nt)

    name_lower = wf["name"].lower()
    description_lower = wf.get("description", "").lower()
    tags = [t.lower() for t in wf.get("tags", [])]

    text_content = f"{name_lower} {description_lower} {' '.join(tags)}"

    # Score each category
    scores = {}
    for cat_name, cat_info in CATEGORIES.items():
        score = 0

        # Check node types
        for ntype in cat_info["node_types"]:
            if ntype in node_type_names:
                score += 5
            # Partial match for subtypes
            for ntn in node_type_names:
                if ntype in ntn or ntn in ntype:
                    score += 3

        # Check keywords
        for kw in cat_info["keywords"]:
            if kw.lower() in text_content:
                score += 2

        scores[cat_name] = score

    # Determine primary and secondary categories
    primary = max(scores, key=scores.get)
    primary_score = scores[primary]

    if primary_score == 0:
        primary = "automation-triggers"  # Default fallback

    # Secondary categories (score > 0 and not primary)
    secondary = [k for k, v in scores.items() if v > 0 and k != primary]
    secondary.sort(key=lambda k: scores[k], reverse=True)
    secondary = secondary[:3]  # Top 3 secondary

    return {
        "primary": primary,
        "primary_label": CATEGORIES[primary]["label"],
        "secondary": secondary,
        "scores": scores,
    }


def extract_openai_config(workflow):
    """Extract OpenAI node configuration patterns."""
    configs = []
    for node in workflow.get("node_details", []):
        if "openAi" in node["type"].lower() or "langchain" in node["type"].lower():
            # Get the actual node data from the original file
            configs.append(
                {
                    "node_name": node["name"],
                    "node_type": node["type"],
                }
            )
    return configs


def extract_sticky_experience(workflow):
    """Extract experience patterns from sticky notes."""
    experiences = []
    for note in workflow.get("sticky_notes", []):
        if not note:
            continue
        # Extract actionable tips from sticky notes
        if "tips" in note.lower() or "note" in note.lower() or "important" in note.lower():
            experiences.append(note[:500])
        elif len(note) > 50:
            experiences.append(note[:500])
    return experiences


def extract_trigger_patterns(workflow):
    """Extract trigger node configurations."""
    triggers = []
    for node in workflow.get("trigger_nodes", []):
        triggers.append(
            {
                "name": node["name"],
                "type": node["type"].replace("n8n-nodes-base.", ""),
            }
        )
    return triggers


def extract_error_handling(workflow):
    """Extract error handling patterns."""
    errors = []
    for node in workflow.get("error_nodes", []):
        errors.append(
            {
                "name": node["name"],
                "type": node["type"].replace("n8n-nodes-base.", ""),
            }
        )
    return errors


def main():
    workflows = load_parsed_workflows()
    print(f"Loaded {len(workflows)} parsed workflows")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Classify all workflows
    classified = defaultdict(list)
    for wf in workflows:
        cls = classify_workflow(wf)
        wf["classification"] = cls
        classified[cls["primary"]].append(wf)

    # Print classification summary
    summary = {}
    for cat_name, cat_info in CATEGORIES.items():
        wfs = classified[cat_name]
        summary[cat_name] = {
            "label": cat_info["label"],
            "description": cat_info["description"],
            "count": len(wfs),
            "workflows": [
                {
                    "name": w["name"],
                    "filepath": w["filepath"],
                    "node_count": w["node_count"],
                    "secondary": w["classification"]["secondary"],
                }
                for w in wfs
            ],
        }

    # Save classification results
    summary_file = OUTPUT_DIR / "classification_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # Save detailed classified data for each category
    for cat_name, wfs in classified.items():
        # Enrich with patterns
        enriched = []
        for wf in wfs[:15]:  # Limit to top 15 per category to control size
            enriched.append(
                {
                    "name": wf["name"],
                    "filepath": wf["filepath"],
                    "tags": wf["tags"],
                    "description": wf["description"],
                    "node_count": wf["node_count"],
                    "active": wf["active"],
                    "classification": wf["classification"],
                    "trigger_nodes": wf["trigger_nodes"],
                    "ai_nodes": wf["ai_nodes"],
                    "integration_nodes": wf["integration_nodes"],
                    "data_nodes": wf["data_nodes"],
                    "control_nodes": wf["control_nodes"],
                    "error_nodes": wf["error_nodes"],
                    "sticky_notes_count": len(wf["sticky_notes"]),
                    "sticky_experiences": extract_sticky_experience(wf),
                    "trigger_patterns": extract_trigger_patterns(wf),
                    "error_handling": extract_error_handling(wf),
                    "settings": wf["settings"],
                }
            )

        cat_file = OUTPUT_DIR / f"{cat_name}_detailed.json"
        with open(cat_file, "w", encoding="utf-8") as f:
            json.dump(enriched, f, ensure_ascii=False, indent=2)

    # Print summary
    print(f"\n=== CLASSIFICATION SUMMARY ===")
    total = sum(v["count"] for v in summary.values())
    for cat_name, data in summary.items():
        pct = data["count"] / total * 100 if total > 0 else 0
        print(f"{data['label']}: {data['count']} workflows ({pct:.1f}%)")

    print(f"\nTotal: {total} workflows")
    print(f"Results saved to: {OUTPUT_DIR}")
    print("Done!")


if __name__ == "__main__":
    main()
