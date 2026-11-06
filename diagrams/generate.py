#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 The Officina SDV Authors
# SPDX-License-Identifier: Apache-2.0
"""Generate the Officina SDV profile diagrams as light and dark SVG files.

Usage: python3 generate.py <output-directory>
"""
import sys
from pathlib import Path
from xml.sax.saxutils import escape

FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

PALETTES = {
    "light": dict(
        bg="#ffffff", panel="#f6f8fa", ink="#16202a", muted="#56636f", line="#cdd6dd",
        accent="#0d6a70",
        ofc="#0d6a70", ofc_t="#e2f1f1", score="#1f5ea6", score_t="#e5edf8",
        qnx="#b0242d", qnx_t="#fbeaeb", aos="#2d7a31", aos_t="#e6f2e6",
        xv="#6a3fb5", xv_t="#efe8fa", plain="#ffffff",
    ),
    "dark": dict(
        bg="#0d1117", panel="#161b22", ink="#e6edf3", muted="#8d96a0", line="#30363d",
        accent="#52b8bd",
        ofc="#52b8bd", ofc_t="#12302f", score="#74a9ea", score_t="#16293f",
        qnx="#f0737a", qnx_t="#3a1b1e", aos="#73c477", aos_t="#16301a",
        xv="#ad90ea", xv_t="#2a2140", plain="#0d1117",
    ),
}


def tw(text, size):
    """Rough text width for a proportional sans font."""
    return len(text) * size * 0.56


class Svg:
    def __init__(self, w, h, title, desc, p):
        self.w, self.h, self.p = w, h, p
        self.out = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-labelledby="t d">',
            f'<title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>',
            "<defs>"
            f'<marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{p["ink"]}"/></marker>'
            f'<marker id="b" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{p["accent"]}"/></marker>'
            "</defs>",
            f'<rect x="0" y="0" width="{w}" height="{h}" rx="8" fill="{p["bg"]}"/>',
        ]

    def rect(self, x, y, w, h, kind="plain", rx=5, width=1.5, fill=None, dash=False):
        p = self.p
        stroke = p["line"] if kind in ("plain", "panel") else p[kind]
        if fill is None:
            fill = p["panel"] if kind == "panel" else (p["plain"] if kind == "plain" else p[kind + "_t"])
        d = ' stroke-dasharray="6 4"' if dash else ""
        self.out.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{width}"{d}/>'
        )

    def frame(self, x, y, w, h, kind):
        self.rect(x, y, w, h, kind, rx=7, width=2, fill="none")

    def text(self, x, y, s, size=13, weight=400, color="ink", mono=False, anchor="start"):
        fam = MONO if mono else FONT
        self.out.append(
            f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" font-weight="{weight}" '
            f'fill="{self.p[color]}" text-anchor="{anchor}">{escape(s)}</text>'
        )

    def line(self, d, accent=False, start=False, width=1.6):
        c = self.p["accent"] if accent else self.p["ink"]
        m = "b" if accent else "a"
        s = f' marker-start="url(#{m})"' if start else ""
        self.out.append(
            f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{width}" marker-end="url(#{m})"{s}/>'
        )

    def render(self):
        return "\n".join(self.out + ["</svg>"]) + "\n"


# ---------------------------------------------------------------- platform layers
LAYERS = [
    ("Entry", "One front door per person", [
        ("plain", "GitHub pull request", "one required check per rung"),
        ("plain", "officina CLI", "submit, logs, scenarios, evidence"),
        ("ofc", "officina-lobby", "web portal, one page per mod"),
        ("ofc", "Live run view", "cluster, IVI and world side by side, live verdict"),
    ]),
    ("Core", "Receives, authorises, queues, runs, records", [
        ("ofc", "officina-relay", "GitHub ⇄ cluster, outbound only, merge queue"),
        ("ofc", "officina-switchboard", "API, identity, roles, speculative gating"),
        ("ofc", "Argo Events + Workflows", "the only job engine"),
        ("ofc", "Kueue", "quotas, licence-aware admission"),
        ("ofc", "officina-patchbay", "turns mods on and off"),
        ("ofc", "officina-ledger", "write-once evidence, attestations"),
        ("ofc", "officina-mirror · stash", "mirrors, remote cache and execution"),
        ("ofc", "officina-radar", "metrics, logs, traces, dashboards"),
        ("ofc", "officina-deck", "browser workspaces, devcontainers"),
    ]),
    ("Mods", "What the factory can do, one plug-in per stack", [
        ("score", "officina-forge", "S-CORE build, integration, release"),
        ("qnx", "officina-forge-qnx", "QNX images, hypervisor configs"),
        ("aos", "officina-forge-aaos", "Android Automotive build, CTS/VTS"),
        ("ofc", "officina-shells", "virtual ECUs: KubeVirt, Cuttlefish, QEMU"),
        ("xv", "Simulation", "X-Verse, CARLA, scenario runners"),
        ("xv", "officina-jack-in", "Zenoh + SIL Kit, joins virtual and bench"),
        ("ofc", "officina-bench", "bench leasing, flashing, fault injection"),
        ("qnx", "officina-showroom", "the reference cockpit sample"),
    ]),
    ("Infrastructure", "On-premises, open APIs only", [
        ("plain", "Kubernetes", "RKE2 or any conformant cluster"),
        ("plain", "Cilium + Gateway API", "network and ingress"),
        ("plain", "Rook-Ceph", "S3 with object lock"),
        ("plain", "Harbor", "signed images"),
        ("plain", "OpenBao + ESO", "secrets and PKI"),
        ("plain", "Keycloak", "identity, OIDC"),
        ("plain", "KubeVirt", "VMs as pods"),
        ("plain", "Node pools", "build · shells · sim · rt-hil"),
    ]),
    ("Targets", "Where the software under test runs", [
        ("aos", "Cuttlefish", "Android Automotive, multi-VM"),
        ("qnx", "QNX in QEMU", "virtual ECU"),
        ("qnx", "QNX Hypervisor in QEMU/KVM", "host + guests, virtual"),
        ("xv", "X-Verse + CARLA", "the simulated world"),
        ("qnx", "Bench boards", "physical ECUs on a leased bench"),
    ]),
]
ARROWS = [
    "every job goes through the switchboard",
    "the workflow comes from a mod's template",
    "runs on",
    "starts and controls",
]
LEGEND = [("ofc", "Officina core"), ("score", "S-CORE"), ("qnx", "QNX"),
          ("aos", "Android Automotive"), ("xv", "X-Verse / simulation"), ("plain", "Open-source infrastructure")]


def layers(p):
    W, LBL, PAD, CH, GAP = 1000, 180, 14, 46, 8
    area = W - 2 * 20 - LBL - 2 * PAD
    # lay out first to know the height
    plans, y = [], 64
    for name, sub, chips in LAYERS:
        rows, row, x = [], [], 0
        for kind, t, s in chips:
            w = max(tw(t, 13) * 1.0 + (14 if t == "officina CLI" else 0), tw(s, 11.5) * 0.84) + 24
            if row and x + w > area:
                rows.append(row)
                row, x = [], 0
            row.append((kind, t, s, w))
            x += w + GAP
        rows.append(row)
        h = max(len(rows) * (CH + GAP) - GAP + 2 * PAD, 74)
        plans.append((name, sub, rows, y, h))
        y += h + 34
    H = y - 34 + 20
    g = Svg(W, H, "Officina SDV platform layers",
            "Entry, core, mods, infrastructure and targets, from top to bottom.", p)
    lx = 20
    for kind, label in LEGEND:
        g.rect(lx, 22, 14, 14, kind, rx=3, width=2)
        g.text(lx + 20, 34, label, 12, color="muted")
        lx += tw(label, 12) + 46
    for i, (name, sub, rows, y, h) in enumerate(plans):
        g.rect(20, y, W - 40, h, "panel", rx=6, width=1.2)
        g.text(36, y + 28, name, 15, 700)
        g.text(36, y + 46, sub if len(sub) < 26 else sub[:sub.rfind(" ", 0, 26)], 11.5, color="muted")
        if len(sub) >= 26:
            g.text(36, y + 61, sub[sub.rfind(" ", 0, 26) + 1:], 11.5, color="muted")
        g.out.append(f'<path d="M{20 + LBL},{y} V{y + h}" stroke="{p["line"]}" stroke-width="1.2"/>')
        cy = y + PAD
        for row in rows:
            cx = 20 + LBL + PAD
            for kind, t, s, w in row:
                g.rect(cx, cy, w, CH, kind, rx=4)
                g.text(cx + 11, cy + 19, t, 13, 600, mono=(t == "officina CLI"))
                g.text(cx + 11, cy + 36, s, 11.5, color="muted")
                cx += w + GAP
            cy += CH + GAP
        if i < len(ARROWS):
            ay = y + h
            g.line(f"M500,{ay + 4} V{ay + 30}")
            g.text(512, ay + 22, ARROWS[i], 11.5, color="muted")
    return g.render()


# ---------------------------------------------------------------- pull request flow
RUNGS = [
    ("R0", "Build and unit", ["Build pods: S-CORE, QNX", "and Android unit tests"], "every push", "minutes"),
    ("R1", "One virtual ECU", ["QNX in QEMU, or one Android", "VM fed by recorded signals"], "every pull request", "10–20 min"),
    ("R2", "Software in the loop", ["X-Verse + virtual ECUs", "+ Cuttlefish"], "safety-path changes", "15–30 min"),
    ("R3", "Mixed criticality", ["Multi-VM targets; hypervisor", "guests forced to fail"], "safety changes, nightly", "20–40 min"),
    ("R4", "Hardware in the loop", ["Bench board + virtual", "targets on the bench network"], "merge candidates, release", "30–60 min"),
]


def pr_flow(p):
    W, H = 1000, 520
    g = Svg(W, H, "What a pull request goes through",
            "A pull request goes through the relay and the switchboard to Argo, runs on rungs R0 to R4, "
            "and every result goes to the write-once ledger before the required check is set.", p)
    top = [("plain", "Pull request", "on GitHub"), ("ofc", "officina-relay", "outbound only"),
           ("ofc", "officina-switchboard", "identity + role check"), ("ofc", "Argo + Kueue", "workflow, quotas, licences")]
    bw, gap = 214, 36
    x = (W - (4 * bw + 3 * gap)) / 2
    for i, (k, t, s) in enumerate(top):
        g.rect(x, 24, bw, 56, k)
        g.text(x + bw / 2, 48, t, 14, 600, anchor="middle")
        g.text(x + bw / 2, 66, s, 11.5, color="muted", anchor="middle")
        if i < 3:
            g.line(f"M{x + bw + 2},52 H{x + bw + gap - 2}")
        last_cx = x + bw / 2
        x += bw + gap
    rw, rg = 184, 12
    rx0 = (W - (5 * rw + 4 * rg)) / 2
    g.out.append(f'<path d="M{last_cx},80 V108 H{rx0 + rw / 2} " fill="none" stroke="{p["ink"]}" stroke-width="1.6"/>')
    g.out.append(f'<path d="M{last_cx},108 H{rx0 + 4 * (rw + rg) + rw / 2}" fill="none" stroke="{p["ink"]}" stroke-width="1.6"/>')
    g.text(W / 2 - 90, 100, "a scenario names a rung, not a machine: the same test runs on a laptop, in the lab or on a bench", 11.5, color="muted", anchor="middle")
    for i, (r, name, target, when, t) in enumerate(RUNGS):
        x = rx0 + i * (rw + rg)
        g.line(f"M{x + rw / 2},108 V128")
        kind = "qnx" if r == "R4" else ("xv" if r == "R2" else "ofc")
        g.rect(x, 130, rw, 180, kind)
        g.text(x + 12, 160, r, 22, 700, color=kind)
        g.text(x + 12, 184, name, 13.5, 600)
        g.text(x + 12, 210, target[0], 11.5, color="muted")
        g.text(x + 12, 226, target[1], 11.5, color="muted")
        g.out.append(f'<path d="M{x + 12},244 H{x + rw - 12}" stroke="{p["line"]}" stroke-width="1"/>')
        g.text(x + 12, 266, when, 12, 600)
        g.text(x + 12, 286, t, 12, color="muted", mono=True)
        g.line(f"M{x + rw / 2},312 V350")
        g.rect(rx0, 352, 5 * rw + 4 * rg, 60, "ofc", rx=6, width=2)
    g.text(W / 2, 377, "officina-ledger · write-once evidence", 14, 600, anchor="middle")
    g.text(W / 2, 398, "requirement → scenario → rung and virtual-ECU level → result → artefact digests, "
           "with an attestation per step", 11.5, color="muted", anchor="middle")
    bw2 = 300
    bx1, bx2 = W / 2 - bw2 - 30, W / 2 + 30
    g.line(f"M{W / 2},414 V440 H{bx1 + bw2 / 2} V452")
    g.line(f"M{W / 2},440 H{bx2 + bw2 / 2} V452")
    g.rect(bx1, 454, bw2, 50, "plain")
    g.text(bx1 + bw2 / 2, 476, "Required check on the pull request", 13, 600, anchor="middle")
    g.text(bx1 + bw2 / 2, 493, "red blocks the merge", 11.5, color="muted", anchor="middle")
    g.rect(bx2, 454, bw2, 50, "plain")
    g.text(bx2 + bw2 / 2, 476, "Merge queue", 13, 600, anchor="middle")
    g.text(bx2 + bw2 / 2, 493, "only what passed gets in", 11.5, color="muted", anchor="middle")
    return g.render()


# ---------------------------------------------------------------- reference cockpit
def cockpit(p):
    g = Svg(1000, 620, "officina-showroom reference cockpit",
            "X-Verse feeds the Android Automotive cluster over gRPC and the radar ECU on QNX over SOME/IP. "
            "The freshness gateway on QNX returns the warning level, or radar unavailable, to the cluster.", p)
    # X-Verse
    g.frame(20, 30, 290, 562, "xv")
    g.text(36, 56, "X-Verse", 15, 700)
    g.text(36, 74, "the simulated world", 11.5, color="muted")
    boxes = [("xv", "CARLA", "physics, sensors, traffic"), ("xv", "Zenoh bus", "vehicle signals"),
             ("xv", "Zenoh ⇄ SOME/IP bridge", "talks to the ECUs"), ("score", "S-CORE cruise control + VCU", "virtual ECUs")]
    for i, (k, t, s) in enumerate(boxes):
        y = 92 + i * 76
        g.rect(40, y, 250, 56, k, rx=4)
        g.text(56, y + 24, t)
        g.text(56, y + 42, s, 11.5, color="muted")
        if i < 3:
            g.line(f"M165,{y + 56} V{y + 74}")
    # Cuttlefish
    g.frame(400, 30, 580, 220, "aos")
    g.text(416, 56, "Cuttlefish · AOSP Display Safety", 15, 700)
    g.text(416, 74, "virtual Android Automotive, two VMs", 11.5, color="muted")
    g.rect(416, 88, 330, 146, "aos", rx=4)
    g.text(430, 110, "Cluster VM · safety monitor", weight=600)
    for x, w, t in [(430, 90, "publisher"), (534, 96, "subscriber"), (644, 92, "cluster UI")]:
        g.rect(x, 124, w, 44, "plain", rx=3)
        g.text(x + w / 2, 150, t, 11.5, mono=True, anchor="middle")
    g.line("M520,146 H532")
    g.line("M630,146 H642")
    g.text(430, 196, "shows placeholders when the heartbeat stops", 11.5, color="muted")
    g.text(430, 214, "or the data goes stale", 11.5, color="muted")
    g.rect(792, 88, 172, 146, "aos", rx=4)
    g.text(806, 110, "Infotainment VM", weight=600)
    g.text(806, 132, "DriverUI and apps", 11.5, color="muted")
    g.text(806, 150, "a hang here never", 11.5, color="muted")
    g.text(806, 166, "freezes the cluster", 11.5, color="muted")
    g.line("M750,200 H788", start=True)
    g.text(806, 206, "heartbeat + gRPC", 11.5, color="muted")
    # QNX
    g.frame(400, 292, 580, 300, "qnx")
    g.text(416, 318, "QNX target · bench board or QEMU", 15, 700)
    g.text(416, 336, "QNX SDP 8.0 with your own licence", 11.5, color="muted")
    g.rect(416, 350, 370, 174, "qnx", rx=4)
    g.text(430, 372, "QNX Hypervisor host", weight=600)
    g.rect(430, 386, 342, 36, "score", rx=3)
    g.text(444, 409, "S-CORE Launch Manager + Health Monitor")
    g.rect(430, 440, 150, 70, "plain", rx=3)
    g.text(444, 466, "radar fusion ECU", 12, mono=True)
    g.text(444, 486, "computes the level", 11.5, color="muted")
    g.rect(604, 440, 168, 70, "plain", rx=3)
    g.text(616, 466, "freshness gateway", 12, mono=True)
    g.text(616, 486, "marks stale radar data", 11.5, color="muted")
    g.line("M580,475 H602")
    g.rect(800, 350, 164, 174, "qnx", rx=4)
    g.text(814, 372, "Rich guest", weight=600)
    g.text(814, 394, "non-safety domain", 11.5, color="muted")
    g.text(814, 412, "watchdog to the host", 11.5, color="muted")
    g.text(814, 446, "if it hangs, the host", 11.5, color="muted")
    g.text(814, 464, "keeps the safety", 11.5, color="muted")
    g.text(814, 482, "functions running", 11.5, color="muted")
    # buses
    g.line("M290,208 H360 V146 H428")
    g.text(318, 138, "gRPC feed", 11.5, color="muted")
    g.line("M290,284 H372 V466 H428")
    g.text(316, 276, "SOME/IP", 11.5, mono=True, color="muted")
    g.text(378, 458, "distance", 11.5, color="muted")
    g.line("M688,512 V552 H340 V300 H292", accent=True, width=2)
    g.text(430, 576, "level 0–3, or “radar unavailable” when the data is stale", 12, 600, color="accent")
    return g.render()


# ---------------------------------------------------------------- deployment profiles
PROFILES = [
    ("Laptop", "first validation", ["kind: 1 control plane + 2 workers", "local build cache", "one bench board on the desk",
                                    "proves function, not availability"]),
    ("Small lab", "3 servers", ["RKE2 on 3 nodes, etcd quorum", "Ceph 3× replication, object lock",
                                "shared, labelled node pools", "bench PC as an rt-hil worker"]),
    ("Data centre", "production cluster", ["dedicated build, RBE, sim pools", "Buildbarn on Ceph",
                                           "Kueue cohorts per tenant", "backups to a second site"]),
    ("Fleet", "many sites", ["central ledger and registry", "bench sites as peers", "supplier sites with own installs",
                             "air-gapped sites via signed bundles"]),
]


def profiles(p):
    W, H = 1000, 300
    g = Svg(W, H, "Deployment profiles",
            "One code base, four profiles: laptop, small lab, data centre and fleet.", p)
    cw, gap = 226, 18
    for i, (name, tag, items) in enumerate(PROFILES):
        x = 20 + i * (cw + gap)
        g.rect(x, 24, cw, 210, "plain", rx=6)
        g.out.append(f'<rect x="{x}" y="24" width="{cw}" height="5" rx="2" fill="{p["ofc"]}" '
                     f'fill-opacity="{0.35 + 0.2 * i:.2f}"/>')
        g.text(x + 16, 54, tag.upper(), 11, color="muted", mono=True)
        g.text(x + 16, 80, name, 17, 700)
        for j, it in enumerate(items):
            g.text(x + 16, 112 + j * 28, "• " + it, 12)
        if i < 3:
            g.line(f"M{x + cw + 2},129 H{x + cw + gap - 2}")
    g.line(f"M40,262 H{W - 40}", accent=True, width=2)
    g.text(W / 2, 286, "same scripts, same tests, same scenarios: a site is a profile, capacity is nodes, benches and sites",
           12, color="muted", anchor="middle")
    return g.render()


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    head = "<!-- SPDX-FileCopyrightText: 2026 The Officina SDV Authors -->\n" \
           "<!-- SPDX-License-Identifier: Apache-2.0 -->\n"
    for name, fn in [("platform-layers", layers), ("pull-request-flow", pr_flow),
                     ("reference-cockpit", cockpit), ("deployment-profiles", profiles)]:
        for theme, pal in PALETTES.items():
            suffix = "" if theme == "light" else "-dark"
            (out / f"{name}{suffix}.svg").write_text(head + fn(pal), encoding="utf-8")


if __name__ == "__main__":
    main()
