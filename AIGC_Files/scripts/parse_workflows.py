#!/usr/bin/env python3
"""
n8n Workflow Parser - 解析 AIGC_Files/workflows/ 下所有 JSON 工作流文件，
提取节点类型、连接关系、参数配置等元数据。
"""

import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

WORKFLOWS_DIR = Path(__file__).parent.parent / "workflows"
OUTPUT_DIR = Path(__file__).parent.parent / "analysis"


def parse_workflow(filepath: str) -> dict:
    """Parse a single n8n workflow JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    # Handle concatenated JSON objects (some files have multiple JSON blobs)
    # Try to parse as single JSON first
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Try to find the first valid JSON object
        decoder = json.JSONDecoder()
        data, _ = decoder.raw_decode(raw)

    return data


def extract_node_info(workflow: dict, filepath: str) -> dict:
    """Extract key information from a workflow."""
    nodes = workflow.get("nodes", [])
    connections = workflow.get("connections", {})

    node_types = []
    node_details = []
    trigger_nodes = []
    ai_nodes = []
    integration_nodes = []
    data_nodes = []
    control_nodes = []
    error_nodes = []

    for node in nodes:
        ntype = node.get("type", "")
        nname = node.get("name", "")
        nparams = node.get("parameters", {})
        nid = node.get("id", "")
        nposition = node.get("position", [0, 0])

        node_info = {
            "id": nid,
            "name": nname,
            "type": ntype,
            "typeVersion": node.get("typeVersion", 1),
            "position": nposition,
            "has_credentials": "credentials" in node,
        }
        node_types.append(ntype)
        node_details.append(node_info)

        # Classify node
        base_type = ntype.replace("n8n-nodes-base.", "")

        # Trigger nodes
        if any(
            t in base_type
            for t in [
                "Trigger",
                "Webhook",
                "webhook",
                "trigger",
                "manualTrigger",
                "scheduleTrigger",
                "formTrigger",
            ]
        ):
            trigger_nodes.append(node_info)

        # AI/LLM nodes
        if any(t in base_type.lower() for t in ["openai", "lmchat", "chainllm", "agent"]):
            ai_nodes.append(node_info)

        # Integration nodes (external services)
        if any(
            t in base_type
            for t in [
                "googleSheets",
                "google",
                "postgres",
                "telegram",
                "gmail",
                "slack",
                "jira",
                "airtable",
                "shopify",
                "woocommerce",
                "wordpress",
                "httpRequest",
                "bigquery",
            ]
        ):
            integration_nodes.append(node_info)

        # Data processing nodes
        if any(
            t in base_type
            for t in [
                "set",
                "merge",
                "splitInBatches",
                "splitOut",
                "aggregate",
                "limit",
                "convertToFile",
                "extractFromFile",
                "readBinaryFiles",
                "itemLists",
            ]
        ):
            data_nodes.append(node_info)

        # Control flow nodes
        if any(t in base_type for t in ["if", "switch", "filter", "wait", "noOp"]):
            control_nodes.append(node_info)

        # Error handling nodes
        if any(t in base_type for t in ["stopAndError", "errorTrigger"]):
            error_nodes.append(node_info)

    # Detect sticky notes content for experience patterns
    sticky_notes = []
    for node in nodes:
        if node.get("type") == "n8n-nodes-base.stickyNote":
            content = node.get("parameters", {}).get("content", "")
            sticky_notes.append(content)

    return {
        "filepath": str(filepath),
        "name": workflow.get("name", "Unnamed"),
        "id": workflow.get("id", ""),
        "tags": workflow.get("tags", []),
        "description": workflow.get("description", ""),
        "active": workflow.get("active", False),
        "node_count": len(nodes),
        "node_types": node_types,
        "node_type_counts": dict(Counter(node_types)),
        "node_details": node_details,
        "trigger_nodes": trigger_nodes,
        "ai_nodes": ai_nodes,
        "integration_nodes": integration_nodes,
        "data_nodes": data_nodes,
        "control_nodes": control_nodes,
        "error_nodes": error_nodes,
        "connection_count": len(connections),
        "sticky_notes": sticky_notes,
        "settings": workflow.get("settings", {}),
        "meta": workflow.get("meta", {}),
    }


def main():
    if not WORKFLOWS_DIR.exists():
        print(f"Error: Workflows directory not found: {WORKFLOWS_DIR}")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_workflows = []
    file_errors = []

    # Recursively find all JSON files
    json_files = list(WORKFLOWS_DIR.rglob("*.json"))
    print(f"Found {len(json_files)} JSON files")

    for filepath in sorted(json_files):
        try:
            wf = parse_workflow(str(filepath))
            info = extract_node_info(wf, str(filepath))
            all_workflows.append(info)
        except Exception as e:
            file_errors.append({"file": str(filepath), "error": str(e)})

    print(f"Successfully parsed: {len(all_workflows)} workflows")
    print(f"Errors: {len(file_errors)} files")

    # Collect statistics
    all_node_types = Counter()
    trigger_node_counts = Counter()
    ai_node_counts = Counter()
    integration_counts = Counter()
    error_handler_count = 0
    has_sticky_notes = 0
    active_count = 0

    for wf in all_workflows:
        all_node_types.update(wf["node_type_counts"])
        for n in wf["trigger_nodes"]:
            trigger_node_counts[n["type"]] += 1
        for n in wf["ai_nodes"]:
            ai_node_counts[n["type"]] += 1
        for n in wf["integration_nodes"]:
            integration_counts[n["type"]] += 1
        if wf["error_nodes"]:
            error_handler_count += 1
        if wf["sticky_notes"]:
            has_sticky_notes += 1
        if wf["active"]:
            active_count += 1

    stats = {
        "total_files": len(json_files),
        "total_parsed": len(all_workflows),
        "total_errors": len(file_errors),
        "active_workflows": active_count,
        "workflows_with_error_handling": error_handler_count,
        "workflows_with_sticky_notes": has_sticky_notes,
        "all_node_types": dict(all_node_types.most_common()),
        "trigger_node_types": dict(trigger_node_counts.most_common()),
        "ai_node_types": dict(ai_node_counts.most_common()),
        "integration_node_types": dict(integration_counts.most_common()),
    }

    # Save parsed data
    output_file = OUTPUT_DIR / "parsed_workflows.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_workflows, f, ensure_ascii=False, indent=2, default=str)

    stats_file = OUTPUT_DIR / "statistics.json"
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    if file_errors:
        errors_file = OUTPUT_DIR / "parse_errors.json"
        with open(errors_file, "w", encoding="utf-8") as f:
            json.dump(file_errors, f, ensure_ascii=False, indent=2)

    # Print summary
    print(f"\n=== PARSING SUMMARY ===")
    print(f"Total JSON files: {len(json_files)}")
    print(f"Successfully parsed: {len(all_workflows)}")
    print(f"Active workflows: {active_count}")
    print(f"With error handling: {error_handler_count}")
    print(f"With sticky notes: {has_sticky_notes}")
    print(f"\nTop 20 node types:")
    for ntype, count in all_node_types.most_common(20):
        print(f"  {ntype}: {count}")
    print(f"\nOutput saved to: {output_file}")
    print(f"Stats saved to: {stats_file}")
    print("Done!")


if __name__ == "__main__":
    main()
