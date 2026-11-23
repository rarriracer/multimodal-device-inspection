"""Generate wholly fictional text fixtures and original SVG illustrations."""
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    conditions = [
        ("Das Display hat deutliche Kratzer.", "yes"), ("Das Display ist gesprungen.", "yes"),
        ("Ein Riss zieht sich über das Display.", "yes"), ("Auf dem Display sind Kratzer sichtbar.", "yes"),
        ("Das Display ist ohne Kratzer.", "no"), ("Keine Risse oder Kratzer am Display.", "no"),
        ("Display ohne Beschädigungen.", "no"), ("Das Display ist unbeschädigt.", "no"),
        ("Zum Displayzustand gibt es keine Angabe.", "unknown"), ("Der Zustand des Displays ist nicht beschrieben.", "unknown"),
        ("Speicher und Farbe stehen im Titel.", "unknown"), ("Weitere Informationen auf Anfrage.", "unknown")]
    cables = [("Ladekabel dabei.", "yes"), ("Kabel liegt bei.", "yes"),
              ("Ohne Ladekabel.", "no"), ("Das Kabel fehlt.", "no"),
              ("Zum Kabel keine Angabe.", "unknown"), ("Lieferumfang nicht beschrieben.", "unknown")]
    locks = [("iCloud wurde abgemeldet.", "no"), ("Apple-ID wurde entfernt.", "no"),
             ("iCloud-Sperre aktiv.", "yes"), ("Apple-ID ist noch verknüpft.", "yes"),
             ("Kontostatus nicht angegeben.", "unknown"), ("Zur Aktivierung keine Information.", "unknown")]
    rows = []
    for i, (condition, cable, lock) in enumerate(itertools.product(conditions, cables, locks)):
        # Hold out whole combination families. All fixtures remain templated/synthetic.
        part = "test" if (i % 17 == 0 or i % 19 == 0) else "train"
        rows.append({"id": f"synthetic-{i:04}", "split": part,
                     "text": " ".join([condition[0], cable[0], lock[0]]),
                     "labels": {"screen_damage": condition[1], "cable_included": cable[1], "account_lock": lock[1]}})
    (ROOT / "examples/text_training.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2)+"\n")
    cases = [
        {"id":"surface-review", "title":"A closer look at the display", "tag":"Possible conflict", "device":"Phone · 128 GB · Graphite",
         "text":"Das Display ist ohne Kratzer. Ladekabel dabei. iCloud wurde abgemeldet.",
         "note":"The description denies scratches. The illustrated finding shows how a reviewer would investigate a possible conflict.",
         "variant":"scratch", "findings":[{"label":"Device", "kind":"device", "box":[25,8,43,82]}, {"label":"Possible scratch · illustrative", "kind":"damage", "box":[39,38,17,18]}]},
        {"id":"accessory-check", "title":"What is actually included?", "tag":"Accessory review", "device":"Phone · 256 GB · Blue",
         "text":"Zum Displayzustand gibt es keine Angabe. Ladekabel dabei. Apple-ID wurde entfernt.",
         "note":"Visible accessories can support a seller claim. An accessory outside the frame remains unverified.",
         "variant":"cable", "findings":[{"label":"Device", "kind":"device", "box":[25,8,43,82]},{"label":"Cable · illustrative", "kind":"accessory", "box":[71,39,22,38]}]},
        {"id":"honest-uncertainty", "title":"Leave uncertainty visible", "tag":"Needs more evidence", "device":"Phone · 128 GB · Silver",
         "text":"Weitere Informationen auf Anfrage. Lieferumfang nicht beschrieben. Kontostatus nicht angegeben.",
         "note":"An incomplete description and limited views do not establish that the device is undamaged or unlocked.",
         "variant":"plain", "findings":[{"label":"Device", "kind":"device", "box":[25,8,43,82]}]},
        {"id":"stated-damage", "title":"A disclosed display defect", "tag":"Stated damage", "device":"Phone · 64 GB · Graphite",
         "text":"Das Display ist gesprungen. Ohne Ladekabel. iCloud wurde abgemeldet.",
         "note":"Keep the seller's statement and any visual finding as separate evidence sources. Severity still requires review.",
         "variant":"crack", "findings":[{"label":"Device", "kind":"device", "box":[25,8,43,82]},{"label":"Crack · illustrative", "kind":"damage", "box":[32,26,29,39]}]},
        {"id":"multiple-devices", "title":"Two devices, one description", "tag":"Identity review", "device":"Two phones · mixed views",
         "text":"Speicher und Farbe stehen im Titel. Kabel liegt bei. Zur Aktivierung keine Information.",
         "note":"Evidence must belong to a specific device. A single listing-level label cannot safely describe two phones.",
         "variant":"multiple", "findings":[{"label":"Device A · illustrative", "kind":"device", "box":[12,16,35,69]},{"label":"Device B · illustrative", "kind":"accessory", "box":[53,16,35,69]}]},
        {"id":"restricted-device", "title":"Read the account status", "tag":"Text warning", "device":"Phone · 128 GB · Graphite",
         "text":"Display ohne Beschädigungen. Das Kabel fehlt. iCloud-Sperre aktiv.",
         "note":"A visually intact device can still have a disclosed account restriction. Physical inspection and text claims answer different questions.",
         "variant":"plain", "findings":[{"label":"Device", "kind":"device", "box":[25,8,43,82]}]}
    ]
    for case in cases:
        case["image"] = f"/examples/images/{case['id']}.svg"
        case["visual_source"] = "authored_illustration_not_model_output"
        (ROOT / "examples/images" / f"{case['id']}.svg").write_text(illustration(case["variant"]))
    (ROOT / "examples/cases.json").write_text(json.dumps(cases,ensure_ascii=False,indent=2)+"\n")
    print(f"Created {len(rows)} synthetic text fixtures and {len(cases)} original illustrations.")


def illustration(variant):
    def phone(x,y,scale=1):
        detail = ''
        if variant == "scratch":
            detail = '<path d="M225 215l59 31m-53-36 46 22m-39-10 33 25" stroke="#bbc8ca" stroke-width="1.4" opacity=".8"/>'
        if variant == "crack":
            detail = '<path d="m200 130 20 53-8 26 25 18-3 57 33 39m-47-140 35 12 14-8m-57 22-30 17m55-9 30-38m-33 95-30 22" fill="none" stroke="#dbe4e3" stroke-width="1.3"/>'
        return f'''<g transform="translate({x} {y}) scale({scale})">
          <rect x="155" y="39" width="214" height="443" rx="41" fill="#152325" opacity=".13" filter="url(#blur)"/>
          <rect x="147" y="28" width="214" height="443" rx="41" fill="url(#metal)" stroke="#758184" stroke-width="1.4"/>
          <rect x="152" y="33" width="204" height="433" rx="37" fill="#111719"/>
          <rect x="160" y="42" width="188" height="415" rx="29" fill="url(#screen)"/>
          <path d="M177 55h150L177 423z" fill="#fff" opacity=".035"/>
          <rect x="216" y="51" width="76" height="21" rx="11" fill="#0b1113"/>
          <circle cx="280" cy="61" r="3" fill="#20363f"/>
          <rect x="145" y="112" width="3" height="29" rx="1" fill="#778285"/>
          <rect x="145" y="151" width="3" height="43" rx="1" fill="#778285"/>
          <rect x="360" y="141" width="3" height="55" rx="1" fill="#778285"/>
          <rect x="219" y="444" width="70" height="4" rx="2" fill="#65777a"/>{detail}</g>'''
    cable = '''<g fill="none" stroke="#b6c4bd" stroke-width="7" stroke-linecap="round"><path d="M445 222c83-28 71 113 18 91-51-20-19-71 10-44 36 34-10 71-33 61"/><path d="m445 222-8-15m3 123-12 13"/></g><rect x="430" y="187" width="15" height="24" rx="4" fill="#f8faf5" stroke="#b6c4bd"/><rect x="419" y="339" width="16" height="25" rx="4" fill="#f8faf5" stroke="#b6c4bd"/>'''
    devices = phone(-76,26,.81)+phone(177,26,.81) if variant == "multiple" else phone(0,0)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="560" height="520" viewBox="0 0 560 520">
      <defs><linearGradient id="metal"><stop stop-color="#b4bec0"/><stop offset=".15" stop-color="#727e82"/><stop offset=".65" stop-color="#b7c0bf"/><stop offset="1" stop-color="#6a777c"/></linearGradient><linearGradient id="screen" x2=".8" y2="1"><stop stop-color="#35494b"/><stop offset=".5" stop-color="#1b2d32"/><stop offset="1" stop-color="#101b22"/></linearGradient><filter id="blur" x="-30%" y="-30%" width="180%" height="180%"><feGaussianBlur stdDeviation="13"/></filter></defs>
      <rect width="560" height="520" fill="#e8eeea"/><path d="M0 392 560 120v400H0z" fill="#e1e9e3"/>
      <g opacity=".22" stroke="#becbc2"><path d="M0 130h560M0 260h560M0 390h560M140 0v520M280 0v520M420 0v520"/></g>
      {devices}{cable if variant == 'cable' else ''}
      <text x="24" y="496" font-family="monospace" font-size="10" fill="#718378" letter-spacing="1.7">ORIGINAL DEMO ILLUSTRATION / NO MARKETPLACE PHOTO</text>
    </svg>'''


if __name__ == "__main__":
    main()
