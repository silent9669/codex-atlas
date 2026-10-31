(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const TYPE_COLORS = {
    decision: "#206f65",
    plan: "#206f65",
    source: "#2d6e84",
    api: "#9a6b24",
    ui: "#2d6e84",
    test: "#3e805c",
    document: "#6f7774",
    "runtime-check": "#a64449",
    commit: "#aab4b0",
  };
  const TYPE_LABELS = {
    decision: "Decision",
    plan: "Plan",
    source: "Source",
    api: "API",
    ui: "UI",
    test: "Test",
    document: "Document",
    "runtime-check": "Runtime",
  };
  const files = graph.nodes.filter(
    (n) => n.symbol === null && n.path && n.type !== "runtime-check",
  );
  const documentRecords =
    graph.workspace?.documents?.documents ||
    files
      .filter((n) => n.path.endsWith(".md"))
      .map((n) => ({ ...n, headings: [], signals: {} }));
  const documentByPath = new Map(documentRecords.map((d) => [d.path, d]));
  const routeNodes = graph.nodes.filter((n) => n.type === "api" && !/(^|\/)tests?\/|\.(?:test|spec)\.[^/]+$/.test(n.path));
  const nodeById = new Map(graph.nodes.map((n) => [n.id, n]));
  let currentView = "graph",
    selected = null,
    graphSearch = "",
    graphScope = "architecture",
    exactType = null,
    focused = false,
    transform = { x: 0, y: 0, k: 1 },
    graphNodes = [],
    graphEdges = [];
  const motionReduced = () =>
    matchMedia("(prefers-reduced-motion: reduce)").matches;
  const degree = new Map();
  graph.edges
    .filter((e) => e.type !== "contains" && e.type !== "changed_by")
    .forEach((e) => {
      degree.set(e.source, (degree.get(e.source) || 0) + 1);
      degree.set(e.target, (degree.get(e.target) || 0) + 1);
    });
  const iconPaths = {
    graph: "M4 18 10 6l8 12M10 6l8 3M4 18h14",
    files: "M4 5h7l2 2h7v12H4z",
    audit: "M5 5h14v14H5zM8 9h8M8 13h5",
    spark: "M12 3l1.6 5.4L19 10l-5.4 1.6L12 17l-1.6-5.4L5 10l5.4-1.6z",
    terminal: "M5 6l5 5-5 5M12 16h7",
    download: "M12 4v11m0 0 4-4m-4 4-4-4M5 20h14",
    inspect: "M5 4h14v16H5zM8 8h8M8 12h5",
  };
  function icon(name) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.classList.add("icon");
    svg.setAttribute("aria-hidden", "true");
    const p = document.createElementNS("http://www.w3.org/2000/svg", "path");
    p.setAttribute("d", iconPaths[name] || "");
    svg.append(p);
    return svg;
  }
  document
    .querySelectorAll("[data-icon]")
    .forEach((el) => el.replaceChildren(icon(el.dataset.icon)));
  const text = (el, value) => {
    el.textContent = value;
    return el;
  };
  const make = (tag, value, cls) => {
    const el = document.createElement(tag);
    if (value !== undefined) el.textContent = value;
    if (cls) el.className = cls;
    return el;
  };
  const button = (label, action, cls = "") => {
    const el = make("button", label, cls);
    el.type = "button";
    el.addEventListener("click", action);
    return el;
  };
  function fileName() {
    return graph.snapshot?.repository || graph.snapshot?.commit || "repository";
  }
  $("repo-name").textContent = fileName();
  $("repo-breadcrumb").textContent = fileName();
  $("repo-branch").textContent = graph.snapshot.commit
    ? graph.snapshot.commit.slice(0, 8)
    : "working tree";
  $("sidebar-snapshot").textContent =
    `${graph.snapshot.hash.slice(0, 12)} · local snapshot`;
  $("footer-snapshot").textContent =
    `Snapshot ${graph.snapshot.hash.slice(0, 12)} · ${graph.nodes.length} nodes · ${graph.edges.length} relationships`;
  function nodesForScope() {
    let list = (
      graphSearch
        ? graph.nodes.filter((n) => n.type !== "commit")
        : files.concat(routeNodes)
    ).filter(
      (n) =>
        !graphSearch ||
        [n.path, n.type, n.label, n.symbol]
          .join(" ")
          .toLowerCase()
          .includes(graphSearch.toLowerCase()),
    );
    if (graphScope === "documents")
      list = list.filter((n) =>
        ["decision", "plan", "document"].includes(n.type),
      );
    if (graphScope === "source")
      list = list.filter((n) => ["source", "api", "ui"].includes(n.type));
    if (graphScope === "test") list = list.filter((n) => n.type === "test");
    if (graphScope === "architecture")
      list = list.filter((n) =>
        ["decision", "plan", "source", "api", "ui", "test"].includes(n.type),
      );
    if (exactType) list = list.filter((n) => n.type === exactType);
    if (focused && selected) {
      const near = new Set([selected.id]);
      graph.edges
        .filter((e) => e.source === selected.id || e.target === selected.id)
        .forEach((e) => {
          near.add(e.source);
          near.add(e.target);
        });
      list = graph.nodes.filter((n) => near.has(n.id) && n.type !== "commit");
    }
    list.sort(
      (a, b) =>
        (degree.get(b.id) || 0) - (degree.get(a.id) || 0) ||
        a.path.localeCompare(b.path),
    );
    if (
      graphScope === "architecture" &&
      !graphSearch &&
      !focused &&
      !exactType
    ) {
      const narrow = document.querySelector(".canvas-wrap").clientWidth < 550;
      const groups = narrow
        ? [
            ["decision", 2],
            ["plan", 1],
            ["source", 4],
            ["ui", 1],
            ["api", 1],
            ["test", 3],
          ]
        : [
            ["decision", 3],
            ["plan", 3],
            ["source", 10],
            ["ui", 2],
            ["api", 2],
            ["test", 6],
          ];
      return groups.flatMap(([type, count]) =>
        list.filter((n) => n.type === type).slice(0, count),
      );
    }
    return list.slice(0, graphScope === "all" ? 48 : 28);
  }
  function setView(view) {
    currentView=view;
    document.querySelectorAll('.side-nav [data-view]').forEach(el=>el.setAttribute('aria-current',el.dataset.view===view?'page':'false'));
    document.querySelectorAll('[id^="view-"]').forEach(el=>{
      if(el.id==='view-graph'){el.hidden=false;return;}
      el.hidden=el.id!==`view-${view}`;
      if(!el.hidden){el.classList.add('tool-drawer');el.setAttribute('role','region');if(!el.querySelector('.drawer-close')){const close=button('Close ×',()=>setView('graph'),'drawer-close');el.prepend(close);}}
    });
    const titles={graph:'Repository map',documents:'Document organization',audit:'Audit & evidence',decision:'Decision studio'};
    text($("page-title"),"Repository map");
    if(view!=="graph")document.querySelector(`#view-${view} .drawer-close`)?.focus();
    if(view==='graph')renderGraph();if(view==='documents')renderDocuments();if(view==='audit')renderAudit();if(view==='decision')renderDecision();
  }
  document
    .querySelectorAll("[data-view]")
    .forEach((el) =>
      el.addEventListener("click", () => setView(el.dataset.view)),
    );
  document.querySelectorAll(".tabbar button").forEach((el) =>
    el.addEventListener("keydown", (e) => {
      if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
        e.preventDefault();
        const tabs = [...document.querySelectorAll(".tabbar button")];
        const i = tabs.indexOf(el);
        tabs[
          (i + (e.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length
        ].focus();
      }
    }),
  );
  const typeCounts = {};
  files
    .concat(routeNodes)
    .forEach((n) => (typeCounts[n.type] = (typeCounts[n.type] || 0) + 1));
  $("side-doc-count").textContent = documentRecords.length;
  $("side-audit-count").textContent = graph.diagnostics.length;
  const layerNav = $("layer-nav");
  [
    ["decision", "Decisions"],
    ["plan", "Plans"],
    ["source", "Source"],
    ["api", "API"],
    ["ui", "UI"],
    ["test", "Tests"],
  ].forEach(([type, label]) => {
    const b = button("", () => {
      $("graph-scope").value =
        type === "decision" || type === "plan"
          ? "documents"
          : type === "test"
            ? "test"
            : "source";
      graphScope = $("graph-scope").value;
      exactType = type;
      focused = false;
      setView("graph");
    });
    b.append(make("span", "", "type-dot"));
    b.firstChild.style.background = TYPE_COLORS[type];
    b.append(make("span", label));
    b.append(make("span", String(typeCounts[type] || 0), "count"));
    layerNav.append(b);
  });
  function graphData() {
    graphNodes = nodesForScope();
    const ids = new Set(graphNodes.map((n) => n.id));
    const pairSeen = new Set();
    graphEdges = graph.edges
      .filter((e) => {
        if (
          !ids.has(e.source) ||
          !ids.has(e.target) ||
          ![
            "depends_on",
            "references",
            "exposes",
            "tested_by",
            "verified_by",
          ].includes(e.type)
        )
          return false;
        const key = [e.source, e.target].sort().join("|");
        if (pairSeen.has(key)) return false;
        pairSeen.add(key);
        return true;
      })
      .slice(0, 80);
  }
  function renderGraph() {
    graphData();
    const svg = d3.select("#network");
    svg.selectAll("*").remove();
    const wrap = document.querySelector(".canvas-wrap");
    const width = wrap.clientWidth || 700,
      height = wrap.clientHeight || 445;
    const root = svg
      .append("g")
      .attr("class", "viewport")
      .attr(
        "transform",
        `translate(${transform.x},${transform.y}) scale(${transform.k})`,
      );
    graphNodes = graphNodes.map((n) => ({ ...n }));
    const byId = new Map(graphNodes.map((n) => [n.id, n]));
    const links = graphEdges
      .map((e) => ({
        source: byId.get(e.source),
        target: byId.get(e.target),
        type: e.type,
      }))
      .filter((e) => e.source && e.target);
    const columns = Math.max(2, Math.floor(width / 150));
    graphNodes.sort((a, b) => {
      const rank = { decision: 0, plan: 1, source: 2, ui: 3, api: 4, test: 5 };
      return (
        (rank[a.type] ?? 6) - (rank[b.type] ?? 6) ||
        a.path.localeCompare(b.path)
      );
    });
    const rows = Math.ceil(graphNodes.length / columns),
      gapX = width / columns,
      gapY = Math.min(66, (height - 50) / Math.max(rows, 1));
    graphNodes.forEach((n, i) => {
      const column = Math.floor(i / rows),
        row = i % rows;
      n.x = gapX * (column + 0.5);
      n.y = 25 + gapY * (row + 0.5);
    });
    const edge = root
      .append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("class", "graph-edge");
    const node = root
      .append("g")
      .selectAll("g")
      .data(graphNodes)
      .join("g")
      .attr(
        "class",
        (d) => `graph-node${selected?.id === d.id ? " is-selected" : ""}`,
      )
      .attr("tabindex", "0")
      .attr("role", "button")
      .attr(
        "aria-label",
        (d) =>
          `${TYPE_LABELS[d.type] || d.type} ${d.path}${d.symbol ? " " + d.symbol : ""}`,
      )
      .on("click", (_, d) => selectNode(d))
      .on("keydown", (event, d) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          selectNode(d);
        }
      });
    node
      .append("rect")
      .attr("x", -65)
      .attr("y", -22)
      .attr("width", 130)
      .attr("height", 44)
      .attr("rx", 6)
      .attr("stroke", (d) => TYPE_COLORS[d.type] || "#bdc9c5")
      .attr("stroke-opacity", 0.55);
    node
      .append("circle")
      .attr("cx", -55)
      .attr("cy", -10)
      .attr("r", 3)
      .attr("fill", (d) => TYPE_COLORS[d.type] || "#9aa6a2");
    node
      .append("text")
      .attr("x", -47)
      .attr("y", -7)
      .text((d) => TYPE_LABELS[d.type] || d.type)
      .attr("class", "graph-type");
    node
      .append("text")
      .attr("x", -55)
      .attr("y", 10)
      .text((d) => {
        const p = d.path || d.label;
        return p.length > 19 ? "…" + p.slice(-18) : p;
      });
    (() => {
      edge
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);
      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
    })();
    const zoom = d3
      .zoom()
      .scaleExtent([0.15, 2.4])
      .on("zoom", (event) => {
        transform = {
          x: event.transform.x,
          y: event.transform.y,
          k: event.transform.k,
        };
        root.attr("transform", event.transform);
      });
    svg
      .call(zoom)
      .call(
        zoom.transform,
        d3.zoomIdentity.translate(transform.x, transform.y).scale(transform.k),
      );
    $("zoom-in").onclick = () =>
      svg
        .transition()
        .duration(motionReduced() ? 0 : 180)
        .call(zoom.scaleBy, 1.2);
    $("zoom-out").onclick = () =>
      svg
        .transition()
        .duration(motionReduced() ? 0 : 180)
        .call(zoom.scaleBy, 0.83);
    $("zoom-fit").onclick = () => {
      if (!graphNodes.length) return;
      const xs = graphNodes.map((n) => n.x),
        ys = graphNodes.map((n) => n.y),
        minX = Math.min(...xs) - 65,
        maxX = Math.max(...xs) + 65,
        minY = Math.min(...ys) - 32,
        maxY = Math.max(...ys) + 32;
      const k = Math.min(width / (maxX - minX), height / (maxY - minY)) * 0.94;
      const fit = d3.zoomIdentity
        .translate(
          width / 2 - (k * (minX + maxX)) / 2,
          height / 2 - (k * (minY + maxY)) / 2,
        )
        .scale(k);
      svg
        .transition()
        .duration(motionReduced() ? 0 : 200)
        .call(zoom.transform, fit);
    };
    $("graph-total").textContent =
      `${graphNodes.length} nodes · ${links.length} edges${files.length > graphNodes.length ? " · bounded view" : ""}`;
    renderLegend();
    if (!selected && graphNodes.length)
      selected = nodeById.get(graphNodes[0].id);
    renderInspector();
    $("focus-node").disabled = !selected;
    $("focus-node").textContent = focused ? "All files" : "Focus";
    if (!transform.x && !transform.y && graphNodes.length)
      $("zoom-fit").onclick();
  }
  function renderLegend() {
    const legend = $("graph-legend");
    legend.replaceChildren();
    const types = [...new Set(graphNodes.map((n) => n.type))];
    types.forEach((type) => {
      const s = make("span");
      const dot = make("i", "");
      dot.className = "type-dot";
      dot.style.background = TYPE_COLORS[type] || "#9aa6a2";
      s.append(dot, make("span", TYPE_LABELS[type] || type));
      legend.append(s);
    });
  }
  function selectNode(node) {
    selected = node;
    renderInspector();
    $("focus-node").disabled = false;
    d3.selectAll(".graph-node").classed("is-selected", (d) => d.id === node.id);
  }
  function renderInspector() {
    const out = $("inspector");
    out.replaceChildren();
    if (!selected) {
      out.append(
        make(
          "div",
          "Select a node to inspect its evidence and connected surfaces.",
          "empty-state",
        ),
      );
      return;
    }
    const node = selected;
    const tag = make("span", TYPE_LABELS[node.type] || node.type, "tag");
    tag.style.borderColor = TYPE_COLORS[node.type] || "var(--border)";
    out.append(tag, make("h2", node.label || node.path));
    out.append(make("div", node.path || node.id, "path"));
    const facts = make("dl", "");
    facts.className = "facts";
    [
      ["Line", node.line || "—"],
      [
        "Hash",
        node.content_hash ? node.content_hash.slice(0, 12) : "unavailable",
      ],
      ["Confidence", "observed"],
    ].forEach(([k, v]) => {
      facts.append(make("dt", k), make("dd", v));
    });
    out.append(facts);
    const allRelations = graph.edges
      .filter((e) => e.source === node.id || e.target === node.id)
      .sort((a, b) => (a.type === "contains") - (b.type === "contains"));
    const relations = allRelations.slice(0, 15);
    out.append(make("h3", `Relationships (${allRelations.length})`));
    const ul = make("ul", "");
    ul.className = "relation-list";
    relations.forEach((e) => {
      const other = nodeById.get(e.source === node.id ? e.target : e.source);
      const li = make("li", "");
      const b = button(
        `${e.type} · ${other?.symbol || other?.path || e.target}`,
        () => other && selectNode(other),
        "flat",
      );
      li.append(
        b,
        make("p", `${e.origin} · ${e.confidence} · ${e.explanation}`),
      );
      ul.append(li);
    });
    out.append(ul);
    const actions = make("div", "");
    actions.className = "inspector-actions";
    actions.append(
      button("Prepare Codex context", () => {
        setView("decision");
        $("decision-task").value =
          `Explain the impact of changing ${node.path || node.id}`;
        renderDecision();
      }),
    );
    out.append(actions);
  }
  function renderDocuments() {
    const docs = documentRecords;
    const query = ($("document-search").value || "").toLowerCase();
    const type = $("document-type").value;
    const list = docs.filter(
      (n) =>
        (type === "all" || (n.labels?.kind || n.type) === type) &&
        ($("document-topic").value === "all" || n.labels?.topics?.includes($("document-topic").value)) &&
        ($("document-status").value === "all" || (n.labels?.status || "unclassified") === $("document-status").value) &&
        (!query || [n.path, n.label, ...(n.labels?.topics || [])].join(" ").toLowerCase().includes(query)),
    );
    $("document-count").textContent = `${list.length} documents`;
    const body = $("document-table");
    body.replaceChildren();
    if (!list.length) {
      body
        .append(make("tr"))
        .append(make("td", "No documents match this filter.", "empty-state"));
      return;
    }
    list.slice(0, 300).forEach((n) => {
      const tr = make("tr");
      const td = make("td", "");
      const b = button(
        n.headings?.[0]?.title || n.path.split("/").pop(),
        () => {
          selected = nodeById.get("file:" + n.path) || n;
          focused = true;
          setView("graph");
        },
        "flat",
      );
      td.append(b, make("div", n.path, "path"));
      tr.append(td, make("td", TYPE_LABELS[n.labels?.kind || n.type] || n.labels?.kind || n.type));
      const labels = make("td");
      const chips = make("div", undefined, "label-chips");
      (n.labels?.topics || ["general"]).forEach(topic => {
        const chip = button(topic, () => { $("document-topic").value = topic; renderDocuments(); }, "label-chip");
        chips.append(chip);
      });
      labels.append(chips, make("div", `${n.labels?.status || "unclassified"} · ${n.labels?.origin === "human-confirmed" ? "reviewed" : "auto"}${n.labels?.freshness === "stale" ? " · stale" : ""}`, "label-status"));
      if (graph.workspace?.connection) labels.append(button("Edit labels", () => editLabels(n), "flat small"));
      tr.append(labels);
      const signals = make("td", "");
      signals.className = "doc-extra";
      signals.append(
        make(
          "span",
          n.signals?.has_acceptance
            ? "Acceptance signal found"
            : n.type === "decision" || n.type === "plan"
              ? "No acceptance heading detected"
              : "No automated semantic claim",
          "signal",
        ),
      );
      tr.append(
        signals,
        make("td", String(n.headings?.length || 0), "num doc-extra"),
      );
      body.append(tr);
    });
  }
  function editLabels(doc) {
    const dialog = make("dialog", undefined, "label-editor");
    const form = make("form"); form.method = "dialog";
    form.append(make("h2", "Document labels"), make("p", doc.path, "path"));
    const inputs = {};
    [["kind", ["decision","plan","runbook","reference","overview","prompt","working-doc","document"]],
     ["status", ["unclassified","draft","approved","superseded","needs-review"]]].forEach(([key, options])=>{
      const label=make("label", key === "kind" ? "Type" : "Status"), select=make("select");
      options.forEach(value=>{const option=make("option", value);option.value=value;select.append(option)});
      select.value=doc.labels?.[key] || (key === "kind" ? doc.type : "unclassified");
      label.append(select);form.append(label);inputs[key]=select;
    });
    const label=make("label", "Topics (comma-separated)"), topics=make("input");
    topics.value=(doc.labels?.topics || ["general"]).join(", ");label.append(topics);form.append(label);
    const status=make("p", "", "small");status.setAttribute("role","status");form.append(status);
    const actions=make("div",undefined,"row"), cancel=button("Cancel",()=>dialog.close());
    const save=button("Save labels",async()=>{
      save.disabled=true;
      try {const response=await fetch("/api/labels",{method:"POST",headers:{"Content-Type":"application/json","X-Atlas-Token":graph.workspace.connection.token},body:JSON.stringify({path:doc.path,kind:inputs.kind.value,status:inputs.status.value,topics:topics.value.split(",").map(t=>t.trim()).filter(Boolean)})});
        const body=await response.json();if(!response.ok)throw new Error(body.error || "Labels could not be saved.");
        doc.labels=body.labels;initDocuments();renderDocuments();dialog.close();showToast("Document labels saved");
      }catch(error){status.textContent=error.message}finally{save.disabled=false}
    },"primary");actions.append(cancel,save);form.append(actions);dialog.append(form);document.body.append(dialog);
    dialog.addEventListener("close",()=>dialog.remove());dialog.showModal();
  }
  function renderAudit() {
    const runtime = graph.nodes.filter((n) => n.type === "runtime-check");
    const findings = graph.diagnostics
      .map((d) => ({ status: "needs-review", ...d }))
      .concat(
        runtime
          .filter((n) => n.freshness === "stale")
          .map((n) => ({
            status: "stale",
            kind: "verification",
            path: n.path,
            message: "Recorded evidence is stale for this snapshot.",
          })),
      );
    const counts = [
      ["Nodes", graph.nodes.length],
      ["Edges", graph.edges.length],
      ["Diagnostics", graph.diagnostics.length],
      ["Stale", findings.filter((f) => f.status === "stale").length],
    ];
    const sum = $("audit-summary");
    sum.replaceChildren();
    counts.forEach(([k, v]) => {
      const div = make("div");
      div.append(make("strong", String(v), "num"), make("span", k));
      sum.append(div);
    });
    const filter = $("audit-filter").value;
    const list = findings.filter(
      (f) => filter === "all" || f.status === filter,
    );
    const out = $("audit-findings");
    out.replaceChildren();
    if (!list.length) {
      out.append(make("div", "No findings for this filter.", "empty-state"));
      return;
    }
    list.slice(0, 200).forEach((f) => {
      const item = make("div");
      item.className = "audit-item";
      const tag = make(
        "span",
        f.status,
        "tag " + (f.status === "stale" ? "warn" : ""),
      );
      item.append(
        tag,
        make(
          "div",
          `${f.kind} · ${f.path || "repository"}${f.line ? ":" + f.line : ""}`,
          "path",
        ),
        make("p", f.message || "Needs source review."),
      );
      if(f.path){
        const candidate=nodeById.get("file:"+f.path);
        item.append(button(candidate ? "Locate in graph" : "Prepare investigation",()=>{
          if(candidate){selected=candidate;focused=true;transform={x:0,y:0,k:1};setView("graph");}
          else{setView("decision");$("decision-task").value=`Investigate ${f.kind} at ${f.path}: ${f.message || ""}`;renderDecision();}
        },"flat small"));
      }
      out.append(item);
    });
  }
  function routeTask(task) {
    const lower = task.toLowerCase();
    if (
      /security|auth|credential|permission|production|deploy|migration|delete|money|payment/.test(
        lower,
      ) ||
      files.length > 20000
    )
      return ["gpt-6-astra", "High-consequence or broad repository decision."];
    if (
      /cross-module|architecture|api|impact|decision|tradeoff|grounding|citation/.test(
        lower,
      ) ||
      files.length > 5000
    )
      return ["gpt-6.1-sol", "Cross-module reasoning with a balanced route."];
    return ["gpt-6-luna", "Focused decision with bounded context."];
  }
  let handoff = "",
    decisionCandidates = [];
  function candidates(task) {
    const terms = task.toLowerCase().match(/[\w/-]{3,}/g) || [];
    const pool = files
      .filter((n) => /\.(md|py|tsx?|jsx?|json|toml)$/.test(n.path))
      .filter((n) =>
        ["decision", "plan", "source", "api", "ui", "test"].includes(n.type),
      );
    const scored = pool
      .map((n) => ({
        n,
        score: terms.reduce(
          (sum, t) =>
            sum +
            ([
              n.path,
              n.label,
              ...(documentByPath.get(n.path)?.headings || []).map(
                (h) => h.title,
              ),
            ]
              .join(" ")
              .toLowerCase()
              .includes(t)
              ? 1
              : 0),
          0,
        ),
      }))
      .sort((a, b) => b.score - a.score || a.n.path.localeCompare(b.n.path));
    let relevant = scored.some((x) => x.score)
      ? scored.filter((x) => x.score)
      : scored;
    const picked = [];
    for (const type of ["decision", "plan", "source", "ui", "test"]) {
      const match = relevant.find((x) => x.n.type === type);
      if (match) picked.push(match.n);
    }
    for (const { n } of relevant)
      if (picked.length < 12 && !picked.includes(n)) picked.push(n);
    return picked;
  }
  function chosenAdvisor(task) {
    const override = $("advisor-model").value;
    return override === "auto"
      ? routeTask(task)
      : [
          override === "custom" ? $("advisor-custom").value.trim() : override,
          "Explicit advisor selection.",
        ];
  }
  function renderDecision() {
    const task = $("decision-task").value.trim();
    const [model, reason] = chosenAdvisor(task);
    $("route-reason").textContent =
      `Advisor route: ${model || "enter a model ID"} · ${reason}`;
    decisionCandidates = candidates(task);
    $("context-count").textContent =
      `${decisionCandidates.length} metadata candidates`;
    const out = $("decision-context");
    out.replaceChildren();
    decisionCandidates.forEach((n) => {
      const row = make("div", undefined, "file-row");
      row.append(
        button(
          n.path,
          () => {
            selected = n;
            focused = true;
            setView("graph");
          },
          "flat",
        ),
        make("span", TYPE_LABELS[n.type] || n.type, "muted"),
      );
      out.append(row);
    });
  }
  $("focus-node").addEventListener("click", () => {
    focused = !focused;
    transform = { x: 0, y: 0, k: 1 };
    renderGraph();
  });
  $("graph-search").addEventListener("input", (e) => {
    graphSearch = e.target.value;
    focused = false;
    exactType = null;
    transform = { x: 0, y: 0, k: 1 };
    renderGraph();
  });
  $("graph-scope").addEventListener("change", (e) => {
    graphScope = e.target.value;
    exactType = null;
    focused = false;
    transform = { x: 0, y: 0, k: 1 };
    renderGraph();
  });
  $("document-search").addEventListener("input", renderDocuments);
  $("document-type").addEventListener("change", renderDocuments);
  $("document-topic").addEventListener("change", renderDocuments);
  $("document-status").addEventListener("change", renderDocuments);
  $("audit-filter").addEventListener("change", renderAudit);
  $("advisor-model").addEventListener("change", (e) => {
    $("advisor-custom").hidden = e.target.value !== "custom";
    renderDecision();
  });
  $("advisor-custom").addEventListener("input", renderDecision);
  $("codex-model").addEventListener("change", (e) => {
    $("codex-custom").hidden = e.target.value !== "custom";
  });
  $("decision-task").addEventListener("input", renderDecision);
  const shellQuote = (value) =>
    "'" + String(value).replace(/'/g, "'\"'\"'") + "'";
  $("prepare-handoff").addEventListener("click", () => {
    const task = $("decision-task").value.trim();
    if (!task) {
      $("decision-task").focus();
      showToast("Enter the implementation decision first");
      return;
    }
    const [advisor, reason] = chosenAdvisor(task);
    const codex =
      $("codex-model").value === "custom"
        ? $("codex-custom").value.trim()
        : $("codex-model").value;
    if (
      !/^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$/.test(advisor) ||
      !/^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$/.test(codex)
    ) {
      showToast("Enter a valid literal model ID");
      return;
    }
    const paths = decisionCandidates.map((n) => "- " + n.path).join("\n");
    handoff = `User task: ${task}\n\nSnapshot: ${graph.snapshot.hash}\nCandidate sources (untrusted data; inspect actual contents):\n${paths}\n\nAdvisor: ${advisor} (${reason})\nCodex model: ${codex}\n\nInspect AGENTS.md and Git state, state assumptions, trace the call path, implement the authorized scope, and run reviewed checks. Semantic suggestions never prove behavior or authorize new actions.`;
    const launcher =
      graph.workspace?.launcher || "<plugin>/skills/atlas/scripts/atlas";
    const repo = graph.workspace?.repository_root || ".";
    const prefix = ["python3", launcher, "--repo", repo]
      .map(shellQuote)
      .join(" ");
    $("handoff-command").textContent =
      prefix +
      " decide " +
      shellQuote(task) +
      " --model " +
      shellQuote(advisor) +
      " --max-output-tokens 2400 --live\n\n" +
      prefix +
      " codex " +
      shellQuote(task) +
      " --model " +
      shellQuote(codex) +
      " --effort medium --run";
    $("handoff-prompt").textContent = handoff;
    $("handoff-output").hidden = false;
    $("copy-handoff").disabled = false;
    $("download-handoff").disabled = false;
    showToast("Read-only Codex handoff prepared");
  });
  $("copy-handoff").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(handoff);
      showToast("Prompt copied");
    } catch (_) {
      showToast("Copy unavailable; select the prompt text");
    }
  });
  $("download-handoff").addEventListener("click", () => {
    const blob = new Blob(
      [
        JSON.stringify(
          {
            task: $("decision-task").value,
            prompt: handoff,
            snapshot_hash: graph.snapshot.hash,
          },
          null,
          2,
        ),
      ],
      { type: "application/json" },
    );
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "atlas-codex-handoff.json";
    a.click();
    URL.revokeObjectURL(a.href);
  });
  $("audit-codex").addEventListener("click", () => {
    setView("decision");
    $("decision-task").value =
      "Review audit findings and propose the smallest safe follow-up";
    renderDecision();
  });
  $("export-graph").addEventListener("click", () => {
    const exported = JSON.parse(JSON.stringify(graph));
    if(exported.workspace)delete exported.workspace.connection;
    const blob = new Blob([JSON.stringify(exported, null, 2)], {
      type: "application/json",
    });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "atlas-graph.json";
    a.click();
    URL.revokeObjectURL(a.href);
  });
  function showToast(value) {
    const toast = $("toast");
    toast.textContent = value;
    toast.hidden = false;
    setTimeout(() => (toast.hidden = true), 2200);
  }
  function renderPreviews() {
    $("page-meta").replaceChildren();
    [
      ["Files", files.length],
      ["Relationships", graph.edges.length],
      ["Commit", graph.snapshot.commit?.slice(0, 8) || "uncommitted"],
    ].forEach(([label, value]) => {
      const span = make("span");
      span.append(
        make("b", String(value)),
        document.createTextNode(" " + label.toLowerCase()),
      );
      $("page-meta").append(span);
    });
    files
      .filter((n) => ["decision", "plan"].includes(n.type))
      .slice(0, 4)
      .forEach((n) => {
        const row = make("div", undefined, "file-row");
        row.append(
          button(
            n.path,
            () => {
              selectNode(n);
              setView("graph");
            },
            "flat",
          ),
          make("span", TYPE_LABELS[n.type], "muted"),
        );
        $("document-preview").append(row);
      });
    if (!$("document-preview").children.length)
      $("document-preview").append(
        make("p", "No decision or plan files indexed.", "muted small"),
      );
    graph.diagnostics.slice(0, 4).forEach((f) => {
      const row = make("div", undefined, "file-row");
      row.append(
        button(f.path || f.kind, () => setView("audit"), "flat"),
        make("span", f.kind, "muted"),
      );
      $("audit-preview").append(row);
    });
    if (!graph.diagnostics.length)
      $("audit-preview").append(
        make(
          "p",
          "No extraction gaps found. Semantic behavior remains unestablished.",
          "muted small",
        ),
      );
  }
  function initDocuments() {
    const previousType=$("document-type").value;
    const types = [...new Set(documentRecords.map((n) => n.labels?.kind || n.type))].sort();
    [ ["document-topic", [...new Set(documentRecords.flatMap(n => n.labels?.topics || []))]],
      ["document-status", [...new Set(documentRecords.map(n => n.labels?.status || "unclassified"))]] ].forEach(([id, values]) => {
      const control = $(id), previous = control.value;
      while(control.options.length > 1)control.remove(1);
      values.sort().forEach(value => {const option=make("option", value); option.value=value; control.append(option)});
      if([...control.options].some(o=>o.value===previous))control.value=previous;
    });
    while($("document-type").options.length>1)$("document-type").remove(1);
    types.forEach((t) => {
      const o = document.createElement("option");
      o.value = t;
      o.textContent = TYPE_LABELS[t] || t;
      $("document-type").append(o);
    });
    if(types.includes(previousType))$("document-type").value=previousType;
  }
  function renderRecentDecisions(){
  $("recent-decisions").replaceChildren();
  (graph.workspace?.decisions || []).slice(0, 3).forEach((record) => {
    const box = make("div", undefined, "decision-result");
    box.append(
      make("h3", record.task),
      make(
        "span",
        record.status + " · " + (record.freshness || "current"),
        "tag",
      ),
    );
    if (record.advisor) box.append(make("p", record.advisor.recommendation));
    else if (record.reason) box.append(make("p", record.reason));
    if(record.routing)box.append(make("p",`${record.routing.model} · ${record.origin || "inferred"}`));
    if(record.usage && typeof record.usage === "object")box.append(make("p",`${record.usage.input_tokens ?? "—"} input · ${record.usage.output_tokens ?? "—"} output tokens`,"small muted"));
    $("recent-decisions").append(box);
  });
  }
  renderRecentDecisions();
  initDocuments();
  renderGraph();
  renderDocuments();
  renderAudit();
  renderDecision();
  renderPreviews();

  const connection=graph.workspace?.connection;
  if(connection){
    $('chat-toggle').hidden=false;
    $('chat-toggle').addEventListener('click',()=>{$('chat-drawer').hidden=false;$('chat-input').focus()});
    $('chat-close').addEventListener('click',()=>{$('chat-drawer').hidden=true});
    $('chat-form').addEventListener('submit',async event=>{
      event.preventDefault();const input=$('chat-input');const message=input.value.trim();if(!message)return;
      input.value='';$('chat-messages').append(make('div',message,'chat-message user'));
      const wait=make('div','Atlas is reading the snapshot…','chat-message assistant');$('chat-messages').append(wait);
      $('chat-messages').scrollTop=$('chat-messages').scrollHeight;
      try{const response=await fetch(connection.endpoint,{method:'POST',headers:{'Content-Type':'application/json','X-Atlas-Token':connection.token},body:JSON.stringify({message})});
        const body=await response.json();wait.textContent=body.reply||body.error||'No response.';
        if(body.status)wait.prepend(make('div',body.status,'label-status'));
        if(body.execution?.finalize)wait.append(make('span',`Updated ${body.execution.finalize.documentation} and ${body.execution.finalize.memory}`,'chat-citation'));
        if(body.usage && typeof body.usage==='object')wait.append(make('span',`${body.usage.input_tokens ?? '—'} input · ${body.usage.output_tokens ?? '—'} output tokens`,'label-status'));
        if(body.execution?.usage && typeof body.execution.usage==='object')wait.append(make('span',`Codex: ${body.execution.usage.input_tokens ?? '—'} input · ${body.execution.usage.output_tokens ?? '—'} output tokens`,'label-status'));
        if(body.routing)wait.append(make('span',`Route: ${body.routing.model} · ${body.routing.effort||'medium'}`,'chat-citation'));
        (body.citations||[]).forEach(path=>wait.append(make('span',path,'chat-citation')));
        if(body.execution){const pre=make('pre',body.execution.command);wait.append(pre);}
      }catch(_){wait.textContent='The local Atlas server is unavailable. Use the CLI workflow.'}
      finally{$('chat-messages').scrollTop=$('chat-messages').scrollHeight}
    });
    setInterval(async()=>{if(document.hidden)return;try{const response=await fetch('/api/graph',{headers:{'X-Atlas-Token':connection.token}});if(!response.ok)return;const next=await response.json();if(next.snapshot.hash===graph.snapshot.hash && JSON.stringify(next.workspace.documents)===JSON.stringify(graph.workspace.documents) && JSON.stringify(next.workspace.decisions)===JSON.stringify(graph.workspace.decisions))return;
      Object.assign(graph,next);files.splice(0,files.length,...graph.nodes.filter(n=>n.symbol===null&&n.path&&n.type!=='runtime-check'));
      documentRecords.splice(0,documentRecords.length,...graph.workspace.documents.documents);documentByPath.clear();documentRecords.forEach(d=>documentByPath.set(d.path,d));
      initDocuments();nodeById.clear();graph.nodes.forEach(n=>nodeById.set(n.id,n));routeNodes.splice(0,routeNodes.length,...graph.nodes.filter(n=>n.type==='api'&&!/(^|\/)tests?\/|\.(?:test|spec)\.[^/]+$/.test(n.path)));
      degree.clear();graph.edges.filter(e=>e.type!=='contains'&&e.type!=='changed_by').forEach(e=>{degree.set(e.source,(degree.get(e.source)||0)+1);degree.set(e.target,(degree.get(e.target)||0)+1)});
      selected=selected?nodeById.get(selected.id)||null:null;
      $('side-doc-count').textContent=documentRecords.length;$('side-audit-count').textContent=graph.diagnostics.length;
      $('footer-snapshot').textContent=`Snapshot ${graph.snapshot.hash.slice(0,12)} · ${graph.nodes.length} nodes · ${graph.edges.length} relationships`;
      renderGraph();renderDocuments();renderAudit();renderDecision();renderRecentDecisions();$('document-preview').replaceChildren();$('audit-preview').replaceChildren();renderPreviews();showToast('Graph refreshed from repository changes');
    }catch(_){}},7000);
  }else{ $('chat-toggle').hidden=false;$('chat-toggle').textContent='Prepare Codex task';$('chat-toggle').addEventListener('click',()=>setView('decision')); }

  document.addEventListener("keydown", event => {
    if(event.key==="Escape") {setView("graph");$("chat-drawer").hidden=true;}
  });
  const resize = new ResizeObserver(() => {
    if (currentView === "graph") {transform={x:0,y:0,k:1};renderGraph();}
  });
  resize.observe(document.querySelector(".canvas-wrap"));
})();
