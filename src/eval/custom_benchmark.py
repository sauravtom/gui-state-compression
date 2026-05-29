from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from src.utils.dom_parser import extract_elements, extract_visible_text, parse_html
from src.utils.screenshot import create_placeholder_screenshot
from src.utils.types import GUIAction, GUIObservation, TaskSpec


TASK_TYPES = [
    "form_filling",
    "web_search",
    "file_navigation",
    "settings_change",
    "checkout_flow",
    "email_flow",
    "dashboard_filtering",
    "document_editing",
]


def _accessibility_from_dom(dom: Dict) -> Dict:
    children = []
    for element in extract_elements(dom):
        tag = element.get("tag")
        role = element.get("role")
        if not role:
            if tag == "button":
                role = "button"
            elif tag == "a":
                role = "link"
            elif tag in {"input", "textarea"}:
                role = "textbox"
            else:
                role = "text"
        children.append(
            {
                "role": role,
                "name": element.get("label"),
                "value": element.get("value"),
                "focused": False,
                "children": [],
            }
        )
    return {"role": "window", "name": "Synthetic browser", "children": children}


def _obs(
    task_id: str,
    step_id: int,
    url: str,
    html: str,
    screenshot_dir: Path,
    focused: str | None = None,
) -> GUIObservation:
    dom = parse_html(html)
    text = "\n".join(extract_visible_text(dom))
    screenshot_path = create_placeholder_screenshot(
        screenshot_dir / f"{task_id}_step_{step_id:02d}.png",
        f"{task_id} step {step_id}: {text[:180]}",
    )
    return GUIObservation(
        step_id=step_id,
        screenshot_path=screenshot_path,
        dom_tree=dom,
        accessibility_tree=_accessibility_from_dom(dom),
        ocr_text=text,
        url=url,
        active_window="Synthetic Browser",
        focused_element=focused,
        timestamp=f"2026-05-29T00:00:{step_id:02d}Z",
    )


def _task(
    task_id: str,
    task_type: str,
    instruction: str,
    success_condition: str,
    html_steps: List[str],
    actions: List[GUIAction],
    screenshot_dir: Path,
    difficulty: float,
    visual_dependency: float,
) -> TaskSpec:
    base_url = f"http://localhost:3000/{task_type}/{task_id}"
    observations = [
        _obs(task_id, step, f"{base_url}?step={step}", html, screenshot_dir)
        for step, html in enumerate(html_steps)
    ]
    return TaskSpec(
        task_id=task_id,
        task_type=task_type,
        instruction=instruction,
        start_url=base_url,
        success_condition=success_condition,
        trajectory=observations,
        ideal_actions=actions,
        metadata={"difficulty": difficulty, "visual_dependency": visual_dependency},
    )


def _form_task(variant: int, screenshot_dir: Path) -> TaskSpec:
    name = ["Mira Chen", "Ravi Patel", "Ada Lovelace", "Nora West", "Sam Rivera"][variant]
    html = [
        "<main><h1>Contact form</h1><label>Name<input name='name'></label><label>Email<input name='email'></label><button>Continue</button></main>",
        f"<main><h1>Contact form</h1><label>Name<input name='name' value='{name}'></label><label>Email<input name='email'></label><button>Continue</button></main>",
        f"<main><h1>Contact form</h1><label>Name<input name='name' value='{name}'></label><label>Email<input name='email' value='{name.split()[0].lower()}@example.com'></label><button>Submit</button></main>",
        "<main><h1>Submission complete</h1><p>Reference saved.</p><button>Finish</button></main>",
    ]
    return _task(
        f"form_{variant + 1:03d}",
        "form_filling",
        f"Fill the form for {name} using their example email and submit it.",
        "DOM contains Submission complete",
        html,
        [
            GUIAction("type", "Name", name),
            GUIAction("type", "Email", f"{name.split()[0].lower()}@example.com"),
            GUIAction("click", "Submit"),
            GUIAction("finish", "Submission complete"),
        ],
        screenshot_dir,
        0.35 + 0.03 * variant,
        0.35,
    )


def _web_search_task(variant: int, screenshot_dir: Path) -> TaskSpec:
    query = ["keyframe compression", "semantic GUI diff", "browser agent benchmark", "delta encoding UI", "computer use latency"][variant]
    html = [
        "<main><h1>Search</h1><input role='searchbox' name='q' placeholder='Search'><button>Search</button></main>",
        f"<main><h1>Search</h1><input role='searchbox' name='q' value='{query}'><button>Search</button></main>",
        "<main><h1>Loading results</h1><p>Please wait.</p></main>",
        f"<main><h1>Results</h1><a href='/r1'>Guide to {query}</a><a href='/r2'>Other result</a></main>",
        f"<main><h1>Guide to {query}</h1><p>Relevant result opened.</p><button>Finish</button></main>",
    ]
    return _task(
        f"search_{variant + 1:03d}",
        "web_search",
        f"Search for '{query}' and open the most relevant guide result.",
        "URL contains /r1",
        html,
        [
            GUIAction("type", "Search", query),
            GUIAction("click", "Search"),
            GUIAction("wait", "Loading results"),
            GUIAction("click", f"Guide to {query}"),
            GUIAction("finish", "Relevant result opened"),
        ],
        screenshot_dir,
        0.42 + 0.04 * variant,
        0.55,
    )


def _file_task(variant: int, screenshot_dir: Path) -> TaskSpec:
    folder = ["Reports", "Invoices", "Designs", "Research", "Contracts"][variant]
    file_name = ["Q2 Summary.pdf", "May Invoice.pdf", "Logo Draft.png", "Notes.md", "Vendor Agreement.docx"][variant]
    html = [
        f"<main><h1>Files</h1><button>{folder}</button><button>Archive</button></main>",
        f"<main><h1>{folder}</h1><button>{file_name}</button><button>Back</button></main>",
        f"<main><h1>{file_name}</h1><p>Preview is open.</p><button>Finish</button></main>",
    ]
    return _task(
        f"files_{variant + 1:03d}",
        "file_navigation",
        f"Open {file_name} inside the {folder} folder.",
        "Preview is open",
        html,
        [GUIAction("click", folder), GUIAction("click", file_name), GUIAction("finish", "Preview is open")],
        screenshot_dir,
        0.3 + 0.04 * variant,
        0.6,
    )


def _settings_task(variant: int, screenshot_dir: Path) -> TaskSpec:
    setting = ["Dark mode", "Email alerts", "Two factor auth", "Compact layout", "Weekly digest"][variant]
    html = [
        f"<main><h1>Settings</h1><label>{setting}<input type='checkbox' value='off'></label><button>Save</button></main>",
        f"<main><h1>Settings</h1><label>{setting}<input type='checkbox' value='on'></label><button>Save</button></main>",
        f"<main><h1>Settings saved</h1><p>{setting} is enabled.</p><button>Finish</button></main>",
    ]
    return _task(
        f"settings_{variant + 1:03d}",
        "settings_change",
        f"Enable {setting} and save settings.",
        f"{setting} is enabled",
        html,
        [GUIAction("click", setting), GUIAction("click", "Save"), GUIAction("finish", "Settings saved")],
        screenshot_dir,
        0.32 + 0.025 * variant,
        0.45,
    )


def _checkout_task(variant: int, screenshot_dir: Path) -> TaskSpec:
    item = ["Notebook", "Headphones", "Desk lamp", "USB hub", "Backpack"][variant]
    coupon = ["PAPER10", "AGENT15", "DELTA20", "TOKEN5", "LATENCY8"][variant]
    old_total = 42 + variant * 8
    new_total = old_total - 5
    html = [
        f"<main><h1>Cart</h1><p>{item}</p><p>Total ${old_total}.00</p><input name='coupon' placeholder='Coupon'><button>Apply coupon</button></main>",
        f"<main><h1>Cart</h1><p>{item}</p><p>Total ${old_total}.00</p><input name='coupon' value='{coupon}'><button>Apply coupon</button></main>",
        "<main><h1>Applying coupon</h1><p>Please wait.</p></main>",
        f"<main><h1>Checkout</h1><p>{item}</p><p>Total ${new_total}.00</p><button>Pay Now</button></main>",
        "<main><h1>Payment complete</h1><p>Receipt sent.</p><button>Finish</button></main>",
    ]
    return _task(
        f"checkout_{variant + 1:03d}",
        "checkout_flow",
        f"Apply coupon {coupon} to the {item} cart and pay.",
        "Payment complete",
        html,
        [
            GUIAction("type", "Coupon", coupon),
            GUIAction("click", "Apply coupon"),
            GUIAction("wait", "Applying coupon"),
            GUIAction("click", "Pay Now"),
            GUIAction("finish", "Payment complete"),
        ],
        screenshot_dir,
        0.48 + 0.04 * variant,
        0.65,
    )


def _email_task(variant: int, screenshot_dir: Path) -> TaskSpec:
    recipient = ["pi@example.com", "reviewer@example.com", "team@example.com", "advisor@example.com", "ops@example.com"][variant]
    subject = ["Draft ready", "Benchmark update", "Figures attached", "Meeting notes", "Launch checklist"][variant]
    html = [
        "<main><h1>Inbox</h1><button>Compose</button><p>No urgent messages.</p></main>",
        "<main><h1>Compose</h1><input name='to' placeholder='To'><input name='subject' placeholder='Subject'><textarea name='body'></textarea><button>Send</button></main>",
        f"<main><h1>Compose</h1><input name='to' value='{recipient}'><input name='subject'><textarea></textarea><button>Send</button></main>",
        f"<main><h1>Compose</h1><input name='to' value='{recipient}'><input name='subject' value='{subject}'><textarea>Sent from benchmark.</textarea><button>Send</button></main>",
        "<main><h1>Sent</h1><p>Message delivered.</p><button>Finish</button></main>",
    ]
    return _task(
        f"email_{variant + 1:03d}",
        "email_flow",
        f"Compose an email to {recipient} with subject '{subject}' and send it.",
        "Message delivered",
        html,
        [
            GUIAction("click", "Compose"),
            GUIAction("type", "To", recipient),
            GUIAction("type", "Subject", subject),
            GUIAction("click", "Send"),
            GUIAction("finish", "Message delivered"),
        ],
        screenshot_dir,
        0.5 + 0.035 * variant,
        0.4,
    )


def _dashboard_task(variant: int, screenshot_dir: Path) -> TaskSpec:
    region = ["North", "South", "East", "West", "Central"][variant]
    html = [
        "<main><h1>Revenue dashboard</h1><select name='region'><option>All</option><option>North</option><option>South</option><option>East</option><option>West</option><option>Central</option></select><button>Apply</button></main>",
        f"<main><h1>Revenue dashboard</h1><select name='region' value='{region}'><option>{region}</option></select><button>Apply</button></main>",
        f"<main><h1>Revenue dashboard</h1><p>Filtered region: {region}</p><button>Export CSV</button></main>",
        f"<main><h1>Export ready</h1><p>{region} revenue.csv generated.</p><button>Finish</button></main>",
    ]
    return _task(
        f"dashboard_{variant + 1:03d}",
        "dashboard_filtering",
        f"Filter the revenue dashboard to {region} and export the CSV.",
        "Export ready",
        html,
        [
            GUIAction("click", "Region", region),
            GUIAction("click", "Apply"),
            GUIAction("click", "Export CSV"),
            GUIAction("finish", "Export ready"),
        ],
        screenshot_dir,
        0.45 + 0.03 * variant,
        0.7,
    )


def _document_task(variant: int, screenshot_dir: Path) -> TaskSpec:
    phrase = ["add limitations", "cite WebArena", "tighten abstract", "insert ablation table", "mark future work"][variant]
    html = [
        "<main><h1>Document editor</h1><textarea name='doc'>Workshop paper draft.</textarea><button>Save</button></main>",
        f"<main><h1>Document editor</h1><textarea name='doc'>Workshop paper draft. TODO: {phrase}.</textarea><button>Save</button></main>",
        "<main><h1>Saving document</h1><p>Please wait.</p></main>",
        f"<main><h1>Document saved</h1><p>Revision includes {phrase}.</p><button>Finish</button></main>",
    ]
    return _task(
        f"doc_{variant + 1:03d}",
        "document_editing",
        f"Edit the document to {phrase} and save it.",
        "Document saved",
        html,
        [
            GUIAction("type", "Document", phrase),
            GUIAction("click", "Save"),
            GUIAction("wait", "Saving document"),
            GUIAction("finish", "Document saved"),
        ],
        screenshot_dir,
        0.52 + 0.04 * variant,
        0.5,
    )


BUILDERS = {
    "form_filling": _form_task,
    "web_search": _web_search_task,
    "file_navigation": _file_task,
    "settings_change": _settings_task,
    "checkout_flow": _checkout_task,
    "email_flow": _email_task,
    "dashboard_filtering": _dashboard_task,
    "document_editing": _document_task,
}


def load_custom_benchmark(output_root: str | Path, tasks_per_type: int = 5) -> List[TaskSpec]:
    if tasks_per_type < 1 or tasks_per_type > 5:
        raise ValueError("tasks_per_type must be between 1 and 5")
    screenshot_dir = Path(output_root) / "logs" / "screenshots"
    tasks: List[TaskSpec] = []
    for task_type in TASK_TYPES:
        builder = BUILDERS[task_type]
        for variant in range(tasks_per_type):
            tasks.append(builder(variant, screenshot_dir))
    return tasks
