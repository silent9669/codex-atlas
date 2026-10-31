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
  const baseViews = ["workspace", "documents", "graph", "runs", "memory", "audit"];
  let currentView = "workspace",
    baseView = "workspace",
    selected = null,
    readerPath = documentByPath.has("README.md") ? "README.md" : documentRecords[0]?.path,
    selectedCategory = null,
    chatDocument = null,
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
    overview: "M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z",
    organize: "M3 7h18M6 3v4M18 3v4M5 11h5v9H5zM14 11h5v9h-5z",
    chat: "M21 11a8 8 0 0 1-8 8H7l-5 3 2-6a8 8 0 0 1-1-5 9 9 0 0 1 18 0zM7 10h10M7 14h6",
    edit: "m15 4 5 5M4 20l5-1L21 7l-5-5L4 14z",
    memory: "M7 3h10v18H7zM3 7h4M17 7h4M3 12h4M17 12h4M3 17h4M17 17h4M10 7h4M10 12h4M10 17h4",
    graph: "M5 5h4v4H5zM15 15h4v4h-4zM3 17h4v4H3zM7 9v4H5v4M9 7h8v8",
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
        ["decision", "plan", "document", "source", "api", "ui", "test"].includes(n.type),
      );
    if (selectedCategory) list = list.filter(n => (documentByPath.get(n.path)?.labels?.category || 'Documents') === selectedCategory);
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
      return [
        list.filter(n => documentByPath.has(n.path)).slice(0, 5),
        list.filter(n => ["source", "ui", "api"].includes(n.type)).slice(0, 5),
        list.filter(n => n.type === "test").slice(0, 4),
      ].flat();
    }
    if (focused && selected) return [selected,...list.filter(n=>n.id!==selected.id)].slice(0,14);
    return list.slice(0, graphScope === "all" ? 48 : 28);
  }
  let drawerTrigger = null;
  function syncDrawerAccess() {
    const overlay = currentView !== baseView && innerWidth < 1200;
    baseViews.forEach(id => $('view-'+id).inert = overlay);
    document.querySelector('.sidebar').inert = overlay && innerWidth <= 850;
    document.querySelector('.topbar').inert = overlay && innerWidth <= 850;
    document.querySelector('.page-head').inert = overlay && innerWidth <= 850;
    if(innerWidth<=850 && document.querySelector('.shell').classList.contains('library-open')) $('view-documents').inert=true;
  }
  function restoreDrawerFocus() {
    if (drawerTrigger?.isConnected && !drawerTrigger.closest('[hidden]')) drawerTrigger.focus();
    else $('chat-toggle').focus();
  }
  function setView(view) {
    const previousBase = baseView;
    if (baseViews.includes(view)) baseView = view;
    else if (currentView === baseView) drawerTrigger = document.activeElement;
    currentView = view;
    if(baseViews.includes(view))history.replaceState(null,'','#'+view);
    if(view!=='documents'){document.querySelector('.shell').classList.remove('library-open');$('library-toggle').setAttribute('aria-expanded','false');}
    const drawer = view !== baseView;
    document.querySelector('.sheet').classList.toggle('has-drawer', drawer);
    $('page-title').textContent = {workspace:fileName(),documents:'Documents',graph:'Graph',runs:'Runs',memory:'Memory',audit:'Audit'}[baseView];
    $('page-title').removeAttribute('title');
    document.querySelector('.page-head').hidden = baseView === 'workspace';
    $('library-browser').hidden = baseView !== 'documents';
    document.querySelector('.sidebar').hidden = baseView !== 'documents';
    document.querySelector('.sheet').classList.toggle('wide-view',baseView !== 'documents');
    $('library-toggle').hidden = baseView !== 'documents';
    $('export-graph').hidden = ['documents','workspace'].includes(baseView);
    const chatLabel = baseView === 'documents' ? 'Ask document' : 'Assistant';
    $('chat-toggle').querySelector('.chat-label').textContent = chatLabel;
    $('chat-toggle').setAttribute('aria-label',chatLabel);
    $('chat-toggle').title=chatLabel;
    document.querySelectorAll('.side-nav [data-view]').forEach(el => el.setAttribute('aria-current', el.dataset.view === (view === 'audit' ? view : baseView) ? 'page' : 'false'));
    const titles = {audit: 'Audit', inspector: 'Selected file'};
    document.querySelectorAll('[id^="view-"]').forEach(el => {
      const id = el.id.slice(5);
      if (baseViews.includes(id)) { el.hidden = id !== baseView; return; }
      el.hidden = id !== view;
      el.classList.add('tool-drawer');
      if (!el.querySelector('.drawer-head')) {
        const head = make('div', undefined, 'drawer-head');
        head.append(make('h2', titles[id]), button('×', () => {setView(baseView); restoreDrawerFocus();}, 'drawer-close flat'));
        head.lastChild.setAttribute('aria-label', 'Close ' + titles[id]);
        el.prepend(head);
      }
    });
    $('chat-drawer').hidden = view !== 'chat';
    syncDrawerAccess();
    if (view === 'chat') $('chat-input').focus();
    else if (drawer) document.querySelector(`#view-${view} .drawer-close`)?.focus();
    if (baseView === 'workspace' && (previousBase !== 'workspace' || !$('workspace-overview').childElementCount)) renderWorkspace();
    if (baseView === 'graph') renderGraph();
    if (baseView === 'documents') {renderDocuments();renderReader();}
    if (['runs','memory'].includes(baseView)) renderJournal();
    if (view === 'audit') renderAudit();
  }
  document.querySelectorAll('[data-view]').forEach(el => el.addEventListener('click', () => {
    if (el.dataset.view === 'graph') {selectedCategory = null; graphScope = 'architecture'; $('graph-scope').value = graphScope; focused = false; transform = {x:0,y:0,k:1}; renderCategories(); renderGraph();}
    setView(el.dataset.view);
  }));
  function graphData() {
    graphNodes = nodesForScope();
    const ids = new Set(graphNodes.map((n) => n.id));
    const pairSeen = new Set();
    const relationship = $('graph-relationship').value;
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
        if(relationship !== 'all' && e.type !== relationship)return false;
        const key = [e.source, e.target,e.type].join("|");
        if (pairSeen.has(key)) return false;
        pairSeen.add(key);
        return true;
      })
      .slice(0, 80);
    if (relationship !== 'all') {
      const connected=new Set(graphEdges.flatMap(e=>[e.source,e.target]));
      graphNodes=graphNodes.filter(n=>connected.has(n.id));
    }
  }
  let presentationChosen = false;
  $('graph-presentation').value = innerWidth < 1000 ? 'list' : 'graph';
  $('graph-presentation').addEventListener('change',()=>{presentationChosen=true;renderGraph();});
  function renderGraphList() {
    const out=$('graph-list');out.replaceChildren();
    out.append(make('p', `${graphNodes.length} files · ${graphEdges.length} relationships · bounded view`, 'list-count muted small'));
    const visibleDegree=new Map();graphEdges.forEach(e=>{visibleDegree.set(e.source,(visibleDegree.get(e.source)||0)+1);visibleDegree.set(e.target,(visibleDegree.get(e.target)||0)+1)});
    for(const [name,nodes] of d3.group(graphNodes,n=>documentByPath.has(n.path)?'Documents':n.type==='test'?'Verification':'Implementation')) {
      const section=make('section');section.append(make('h2',name));
      nodes.forEach(n=>{
        const item=button('',()=>selectNode(n),'graph-list-item');
        const identity=make('span');identity.append(make('strong',n.symbol || n.path.split('/').pop()),make('span',n.path,'path'));
        item.append(identity,make('span',String(visibleDegree.get(n.id)||0)+' links','small muted'));section.append(item);
      });out.append(section);
    }
    if(!graphNodes.length)out.append(make('p','No files match this view.','empty-state'));
    const list=$('graph-presentation').value==='list';
    out.hidden=!list;document.querySelector('.canvas-wrap').hidden=list;$('graph-legend').hidden=list;
  }
  function renderGraph() {
    graphData();
    renderGraphList();
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
        type: e.type, explanation: e.explanation,
      }))
      .filter((e) => e.source && e.target);
    const groupFor = n => graphScope === 'documents'
      ? (documentByPath.get(n.path)?.labels?.category || 'Documents')
      : documentByPath.has(n.path) ? 'Documents' : n.type === 'test' || n.type === 'runtime-check' ? 'Verification' : 'Implementation';
    const grouped = d3.group(graphNodes, groupFor);
    const groups = [...grouped].sort((a,b) => {
      const order = ['Documents','Implementation','Verification'];
      return graphScope === 'documents' ? a[0].localeCompare(b[0]) : order.indexOf(a[0]) - order.indexOf(b[0]);
    });
    const columns = Math.min(3, groups.length || 1), laneWidth = 248, laneGap = 32;
    let offsetY = 24;
    const frames = [];
    for (let row = 0; row < groups.length; row += columns) {
      const batch = groups.slice(row, row + columns);
      const tallest = Math.max(...batch.map(([,nodes]) => nodes.length)) * 68 + 66;
      batch.forEach(([name, nodes], col) => {
        const x = 24 + col * (laneWidth + laneGap);
        frames.push({name, count:nodes.length, x, y:offsetY, width:laneWidth, height:tallest});
        nodes.sort((a,b) => a.path.localeCompare(b.path)).forEach((n,i) => {n.x=x+laneWidth/2; n.y=offsetY+76+i*68;});
      });
      offsetY += tallest + laneGap;
    }
    const frame = root.append('g').selectAll('g').data(frames).join('g').attr('class','graph-group');
    frame.append('rect').attr('x',d=>d.x).attr('y',d=>d.y).attr('width',d=>d.width).attr('height',d=>d.height).attr('rx',10);
    frame.append('text').attr('x',d=>d.x+16).attr('y',d=>d.y+27).text(d=>d.name.length>27?d.name.slice(0,26)+'…':d.name);
    frame.append('title').text(d=>d.name);
    frame.append('text').attr('class','group-count').attr('text-anchor','end').attr('x',d=>d.x+d.width-16).attr('y',d=>d.y+27).text(d=>d.count);
    svg.append('defs').append('marker').attr('id','edge-arrow').attr('viewBox','0 -5 10 10').attr('refX',10).attr('refY',0).attr('markerWidth',6).attr('markerHeight',6).attr('orient','auto').append('path').attr('d','M0,-5L10,0L0,5').attr('fill','#829b93');
    const edge = root.append('g').selectAll('path').data(links).join('path')
      .attr('class','graph-edge').attr('marker-end','url(#edge-arrow)').attr('d', d => {
        const direction=d.target.x>=d.source.x?1:-1;
        const sx=d.source.x+direction*103, tx=d.target.x-direction*103;
        if(d.source.x===d.target.x) return `M${sx},${d.source.y} C${sx+24},${d.source.y} ${tx+230},${d.target.y} ${sx},${d.target.y}`;
        return `M${sx},${d.source.y} C${(sx+tx)/2},${d.source.y} ${(sx+tx)/2},${d.target.y} ${tx},${d.target.y}`;
      });
    edge.append('title').text(d=>`${d.source.path} → ${d.target.path}: ${d.type}. ${d.explanation || ''}`);
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
      .attr("x", -104)
      .attr("y", -22)
      .attr("width", 208)
      .attr("height", 48)
      .attr("rx", 6)
      .attr("stroke", (d) => TYPE_COLORS[d.type] || "#bdc9c5")
      .attr("stroke-opacity", 0.55);
    node
      .append("circle")
      .attr("cx", -90)
      .attr("cy", -10)
      .attr("r", 3)
      .attr("fill", (d) => TYPE_COLORS[d.type] || "#9aa6a2");
    node
      .append("text")
      .attr("x", -80)
      .attr("y", -7)
      .text((d) => documentByPath.get(d.path)?.labels?.kind || TYPE_LABELS[d.type] || d.type)
      .attr("class", "graph-type");
    node
      .append("text")
      .attr("x", -90)
      .attr("y", 10)
      .text((d) => {
        const p = d.symbol || d.path.split("/").pop() || d.label;
        return p.length > 28 ? p.slice(0,25) + "…" : p;
      });
    node.append('title').text(d => d.path + (d.symbol ? ' · ' + d.symbol : ''));
    const emphasize = active => {
      const near = active ? new Set([active.id,...links.filter(e=>e.source.id===active.id||e.target.id===active.id).flatMap(e=>[e.source.id,e.target.id])]) : null;
      node.classed('is-muted',d=>near && !near.has(d.id));
      edge.classed('is-muted',d=>active && d.source.id!==active.id && d.target.id!==active.id)
        .classed('is-highlighted',d=>active && (d.source.id===active.id || d.target.id===active.id));
    };
    node.on('mouseenter',(_,d)=>emphasize(d)).on('mouseleave',()=>emphasize(null))
      .on('focus',(_,d)=>emphasize(d)).on('blur',()=>emphasize(null));
    node.attr("transform", d => `translate(${d.x},${d.y})`);
    if (!graphNodes.length) svg.append('text').attr('x',24).attr('y',48).attr('class','graph-empty').text('No files match this view.');
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
        .interrupt()
        .transition()
        .duration(motionReduced() ? 0 : 180)
        .call(zoom.scaleBy, 1.2);
    $("zoom-out").onclick = () =>
      svg
        .interrupt()
        .transition()
        .duration(motionReduced() ? 0 : 180)
        .call(zoom.scaleBy, 0.83);
    $("zoom-fit").onclick = () => {
      if (!graphNodes.length) return;
      const minX = Math.min(...frames.map(f=>f.x)) - 8,
        maxX = Math.max(...frames.map(f=>f.x+f.width)) + 8,
        minY = 8,
        maxY = Math.max(...frames.map(f=>f.y+f.height)) + 48;
      const k = Math.min(1.25, width / (maxX - minX), height / (maxY - minY)) * 0.96;
      const fit = d3.zoomIdentity
        .translate(
          width / 2 - (k * (minX + maxX)) / 2,
          height / 2 - (k * (minY + maxY)) / 2,
        )
        .scale(k);
      svg
        .interrupt()
        .call(zoom.transform, fit);
    };
    $("graph-total").textContent =
      `${graphNodes.length} nodes · ${links.length} edges${files.length > graphNodes.length ? " · bounded view" : ""}`;
    renderLegend();
    d3.selectAll('.graph-edge').classed('is-active',d=>selected && (d.source.id===selected.id || d.target.id===selected.id));
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
    if (documentByPath.has(node.path) && baseView !== 'graph') {openDocument(node.path);return;}
    renderInspector();
    setView("inspector");
    $("focus-node").disabled = false;
    d3.selectAll(".graph-node").classed("is-selected", (d) => d.id === node.id);
    d3.selectAll(".graph-edge").classed("is-active", d => d.source.id === node.id || d.target.id === node.id);

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
    out.append(tag, make("h3", node.symbol || node.path?.split("/").pop() || node.label));
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
    const doc = documentByPath.get(node.path);
    if (doc) {
      const actions = make('div', undefined, 'inspector-actions');
      actions.append(button('Read document', () => openDocument(doc.path)), button('Ask about this document', () => openChat(doc.path)), button('Audit this document', () => useCommand('audit', doc.path)));
      if (graph.workspace?.connection) actions.append(button('Edit labels', () => editLabels(doc)));
      out.append(actions);
      const content = make('div', undefined, 'document-content');
      const pre = markdown(doc.excerpt || doc.headings.map(h => h.title).join('\n'),doc.path);
      content.append(pre);
      if (doc.excerpt_truncated) content.append(make('p','Preview truncated at 16,000 characters.','muted small'));
      out.append(content);
    }
    const details = make('details', undefined, 'source-details');
    details.append(make('summary','Source details'), facts);
    out.append(details);
    const allRelations = graph.edges
      .filter((e) => e.source === node.id || e.target === node.id)
      .filter(e => !["contains", "changed_by"].includes(e.type));
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
      button("Ask about impact", () => {
        useCommand('ask', doc?.path || null);
        $('chat-input').value = `Explain the impact of changing ${node.path || node.id}`;
      }),
    );
    out.append(actions);
  }
  const collapsedCategories = new Set(documentRecords.filter(d=>d.path!==readerPath).map(d=>d.labels?.category || 'Documents'));
  collapsedCategories.delete(documentByPath.get(readerPath)?.labels?.category || 'Documents');
  function renderDocuments() {
    const docs = documentRecords;
    const query = ($("document-search").value || "").toLowerCase();
    const type = $("document-type").value;
    const list = docs.filter(
      (n) =>
        (type === "all" || (n.labels?.kind || n.type) === type) &&
        (!selectedCategory || (n.labels?.category || 'Documents') === selectedCategory) &&
        ($("document-topic").value === "all" || n.labels?.topics?.includes($("document-topic").value)) &&
        ($("document-status").value === "all" || (n.labels?.status || "unclassified") === $("document-status").value) &&
        (!query || [n.path, n.label, ...(n.labels?.topics || [])].join(" ").toLowerCase().includes(query)),
    );
    $("document-count").textContent = `${list.length} document${list.length === 1 ? '' : 's'}`;
    $('document-category-heading').replaceChildren();
    if (selectedCategory) $('document-category-heading').append(make('strong',selectedCategory), button('All categories',()=>{selectedCategory=null;renderCategories();renderDocuments();renderGraph();},'flat small'));
    const body = $("document-table");
    body.replaceChildren();
    if (!list.length) body.append(make('p','No documents match.','empty-state'));
    for (const [category, notes] of [...d3.group(list, n => n.labels?.category || 'Documents')].sort((a,b)=>a[0].localeCompare(b[0]))) {
      const group = make('details', undefined, 'note-group'); group.open = Boolean(query || selectedCategory) || !collapsedCategories.has(category);
      group.addEventListener('toggle',()=>{if(!group.isConnected)return;if(!query && !selectedCategory){if(group.open)collapsedCategories.delete(category);else collapsedCategories.add(category);}updateLibraryExpand();});
      const heading=make('summary');heading.append(make('span',category),make('span',String(notes.length),'category-count'));group.append(heading);
      notes.forEach(n => {
        const item = button('', () => openDocument(n.path), 'note-button');
        item.setAttribute('aria-current', String(readerPath === n.path));
        item.title = n.path;
        item.append(icon('inspect'), make('span', n.headings?.[0]?.title || n.path.split('/').pop()));
        group.append(item);
      }); body.append(group);
    }
    updateLibraryExpand();
  }
  function updateLibraryExpand() {
    const hasClosed=[...document.querySelectorAll('.note-group')].some(group=>!group.open);
    $('library-expand').textContent=hasClosed?'Expand all':'Collapse all';
  }
  $('library-expand').addEventListener('click',()=>{
    const groups=[...document.querySelectorAll('.note-group')];
    const expand=groups.some(group=>!group.open);
    groups.forEach(group=>group.open=expand);
    if(expand)collapsedCategories.clear();
    else documentRecords.forEach(doc=>collapsedCategories.add(doc.labels?.category || 'Documents'));
    updateLibraryExpand();
  });
  function openDocument(path) {
    readerPath = path;
    collapsedCategories.delete(documentByPath.get(path)?.labels?.category || 'Documents');
    selected = nodeById.get('file:' + path) || documentByPath.get(path);
    const chatOpen = currentView === 'chat';
    setView('documents');
    $('view-documents').scrollTop=0;
    document.querySelector('.shell').classList.remove('library-open');
    $('library-toggle').setAttribute('aria-expanded','false');
    syncDrawerAccess();
    if (chatOpen) openChat(path);
    else $('document-reader').focus();
  }
  function inlineMarkdown(parent, value, path) {
    const pattern = /(`[^`]+`|\*\*[^*]+\*\*|!?\[[^\]]+\]\([^)]+\))/g;
    let cursor = 0;
    for (const match of value.matchAll(pattern)) {
      parent.append(document.createTextNode(value.slice(cursor,match.index)));
      const token=match[0];
      if (token.startsWith('`')) parent.append(make('code',token.slice(1,-1)));
      else if (token.startsWith('**')) parent.append(make('strong',token.slice(2,-2)));
      else {
        const link=/^!?\[([^\]]+)\]\(([^)]+)\)$/.exec(token);
        const label=link[1], href=link[2];
        const localHref=graph.workspace?.repository_root && href.startsWith(graph.workspace.repository_root+'/') ? href.slice(graph.workspace.repository_root.length+1).replace(/:\d+(?:-\d+)?$/,'') : href;
        const source=nodeById.get('file:'+localHref);
        if(source && !token.startsWith('!')){parent.append(button(label,()=>selectNode(source),'inline-link'));cursor=match.index+token.length;continue;}
        let target;
        try { target = decodeURIComponent(new URL(href, 'https://atlas.local/'+path).pathname.slice(1)); } catch (_) {}
        if (!token.startsWith('!') && !/^[a-z]+:/i.test(href) && documentByPath.has(target)) parent.append(button(label,()=>openDocument(target),'inline-link'));
        else if (!token.startsWith('!') && /^https?:\/\//i.test(href)) {const a=make('a',label);a.href=href;a.target='_blank';a.rel='noopener noreferrer';parent.append(a);}
        else parent.append(document.createTextNode(label));
      }
      cursor=match.index+token.length;
    }
    parent.append(document.createTextNode(value.slice(cursor)));
  }
  function markdown(value, path) {
    const out=make('div',undefined,'markdown');const lines=value.split('\n');
    let paragraph=[], list=null;
    const flush=()=>{if(paragraph.length){const p=make('p');inlineMarkdown(p,paragraph.join(' '),path);out.append(p);paragraph=[];}list=null;};
    for(let i=0;i<lines.length;i++) {
      const line=lines[i];
      if (/^\s*```/.test(line)) {flush();const code=[];while(++i<lines.length && !/^\s*```/.test(lines[i]))code.push(lines[i]);const pre=make('pre');pre.append(make('code',code.join('\n')));out.append(pre);}
      else if (/^#{1,6} /.test(line)) {flush();const depth=line.match(/^#+/)[0].length;const h=make('h'+Math.min(6,depth+1));inlineMarkdown(h,line.slice(depth+1),path);out.append(h);}
      else if (/^\s*([-*+] |\d+\. )/.test(line)) {if(paragraph.length)flush();const tag=/^\s*\d/.test(line)?'ol':'ul';if(!list || list.tagName.toLowerCase()!==tag){list=make(tag);out.append(list);}const li=make('li');inlineMarkdown(li,line.replace(/^\s*(?:[-*+]|\d+\.) /,''),path);list.append(li);}
      else if (line.includes('|') && /^\s*\|?\s*:?-{3}/.test(lines[i+1]||'')) {flush();const wrap=make('div',undefined,'markdown-table');const table=make('table');const row=(text,tag)=>{const tr=make('tr');text.trim().replace(/^\||\|$/g,'').split('|').forEach(cell=>{const td=make(tag);inlineMarkdown(td,cell.trim(),path);tr.append(td);});return tr;};const head=make('thead');head.append(row(line,'th'));table.append(head);i++;const body=make('tbody');while(i+1<lines.length && lines[i+1].includes('|'))body.append(row(lines[++i],'td'));table.append(body);wrap.append(table);out.append(wrap);}
      else if (/^> ?/.test(line)) {flush();const quote=make('blockquote');inlineMarkdown(quote,line.replace(/^> ?/,''),path);out.append(quote);}
      else if (!line.trim()) flush();
      else if (/^\s*---+\s*$/.test(line)) {flush();out.append(make('hr'));}
      else paragraph.push(line);
    }flush();return out;
  }
  $('document-outline').addEventListener('toggle',()=>{
    if($('document-outline').open && $('document-outline').closest('.reader-toolbar')) {
      const details=document.querySelector('.reader-details');if(details)details.open=false;
    }
  });
  document.addEventListener('click',event=>{
    if(event.target.closest('.reader-toolbar'))return;
    const details=document.querySelector('.reader-details');if(details)details.open=false;
    if($('document-outline').closest('.reader-toolbar'))$('document-outline').open=false;
  });
  function placeOutline() {
    const outline=$('document-outline'),wide=innerWidth>=1400 && currentView===baseView;
    const target=wide?$('view-documents'):document.querySelector('.reader-toolbar');
    if(target)target.append(outline);
    outline.open=wide;
  }
  function renderReader() {
    const out=$('document-reader');
    $('view-documents').append($('document-outline'));
    out.replaceChildren();out.tabIndex=-1;
    const doc=documentByPath.get(readerPath);
    if(!doc){$('document-outline').hidden=true;out.append(make('p','No documents in this repository.','empty-state'));return;}
    if(baseView==='documents') { $('page-title').textContent=doc.path; $('page-title').title=doc.path; }
    const header=make('header',undefined,'reader-head');
    header.append(make('h2',doc.headings?.[0]?.title || doc.path.split('/').pop()));
    const toolbar=make('div',undefined,'reader-toolbar');
    const metadata=make('details',undefined,'reader-details');
    metadata.append(make('summary','Details'));
    metadata.addEventListener('toggle',()=>{if(metadata.open && $('document-outline').parentElement===toolbar)$('document-outline').open=false;});
    const info=make('div',undefined,'reader-details-body');
    const labels=make('dl',undefined,'reader-labels');
    [['Category',doc.labels?.category || 'Uncategorized'],['Type',doc.labels?.kind || doc.type],['Status',doc.labels?.status || 'unclassified'],['Topics',(doc.labels?.topics || []).join(', ') || 'None']].forEach(([key,value])=>labels.append(make('dt',key),make('dd',value)));
    info.append(labels);
    const actions=make('div',undefined,'reader-actions');
    actions.append(button('Audit document',()=>useCommand('audit',doc.path),'flat'));
    if(graph.workspace?.connection)actions.append(button('Edit labels',()=>editLabels(doc),'flat'));
    info.append(actions);metadata.append(info);
    toolbar.append(button('Connections',()=>{selected=nodeById.get('file:'+doc.path);focused=true;transform={x:0,y:0,k:1};setView('graph');},'flat'),metadata);
    header.append(toolbar);out.append(header);
    const content=markdown((doc.excerpt || '').replace(/^# [^\n]+\n/,''),doc.path);
    out.append(content);
    const outline=$('document-outline'),nav=outline.querySelector('nav');nav.replaceChildren();
    const headings=[...content.querySelectorAll('h2,h3,h4')];
    outline.hidden=!headings.length;
    placeOutline();
    headings.forEach((heading,index)=>{
      heading.id='document-section-'+index;heading.tabIndex=-1;
      const jump=button(heading.textContent,()=>{
        if(innerWidth<1400 || currentView!==baseView)outline.open=false;
        const panel=$('view-documents');
        panel.scrollTo({top:heading.getBoundingClientRect().top-panel.getBoundingClientRect().top+panel.scrollTop-24,behavior:motionReduced()?'instant':'smooth'});
        heading.focus({preventScroll:true});
      },'outline-link');
      jump.classList.toggle('subheading',heading.tagName==='H4');nav.append(jump);
    });
    if(doc.excerpt_truncated)out.append(make('p','Preview truncated at 16,000 characters.','muted small'));
    const links=graph.edges.filter(e=>(e.source==='file:'+doc.path||e.target==='file:'+doc.path)&&!['contains','changed_by'].includes(e.type));
    if(links.length){const section=make('section',undefined,'reader-connections');section.append(make('h2','Connections'));links.slice(0,20).forEach(edge=>{const other=nodeById.get(edge.source==='file:'+doc.path?edge.target:edge.source);if(!other)return;const row=make('div');row.append(button(other.path+(other.symbol?' · '+other.symbol:''),()=>selectNode(other),'flat'),make('p',edge.type+' · '+edge.explanation,'muted small'));section.append(row);});out.append(section);}
  }
  function openGraphFor(path) {
    selectedCategory=null;graphScope='architecture';$('graph-scope').value=graphScope;
    graphSearch='';$('graph-search').value='';exactType=null;$('graph-relationship').value='all';
    selected=path?nodeById.get('file:'+path):null;focused=Boolean(selected);transform={x:0,y:0,k:1};setView('graph');
  }
  function openLibrary() {
    selectedCategory=null;renderCategories();$('document-search').value='';
    ['type','topic','status'].forEach(key=>$('document-'+key).value='all');
    setView('documents');if(innerWidth<=850)$('library-toggle').click();
  }
  function renderWorkspace() {
    const out=$('workspace-overview');out.replaceChildren();
    const findings=auditFindings(), pending=documentRecords.filter(d=>d.labels?.origin!=='human-confirmed' && (d.labels?.category_origin!=='model-inferred'||d.labels?.category_freshness==='stale'));
    const head=make('div',undefined,'workspace-heading');
    head.append(make('h1','Overview'),make('span',graph.snapshot.commit?.slice(0,8)||'Working tree','path'));out.append(head);
    const actions=make('div',undefined,'workspace-actions');
    [['Organize docs','organize','organize'],['Audit code & docs','audit','audit'],['Write docs','edit','docs'],['Save memory','memory','memory']].forEach(([label,glyph,action])=>{
      const control=button('',()=>useCommand(action,null),action==='organize'?'primary':'');control.append(icon(glyph),make('span',label));actions.append(control);
    });out.append(actions);
    const grid=make('div',undefined,'workspace-grid');out.append(grid);
    const section=(title,action,label,cls='')=>{const box=make('section',undefined,'workspace-section '+cls),header=make('div',undefined,'workspace-section-head');header.append(make('h2',title));if(action)header.append(button(label,action,'flat'));box.append(header);grid.append(box);return box;};
    const docs=section('Document library',openLibrary,'Browse all','workspace-library');
    docs.querySelector('h2').append(make('span',' '+documentRecords.length,'section-count'));
    if(pending.length)docs.append(make('p',`${pending.length} to organize`,'muted small'));
    const categories=make('div',undefined,'workspace-categories');
    const groups=[...d3.group(documentRecords,d=>d.labels?.category||'Documents')].sort((a,b)=>b[1].length-a[1].length);
    for(const [category,notes] of groups.slice(0,8)) {
      const row=button('',()=>{selectedCategory=category;renderCategories();$('document-search').value='';['type','topic','status'].forEach(key=>$('document-'+key).value='all');openDocument(notes[0].path);},'category-row');
      row.append(icon('files'),make('span',category),make('span',String(notes.length),'category-total'));categories.append(row);
    }docs.append(categories);if(groups.length>4)docs.append(button(`All ${groups.length} categories`,openLibrary,'flat all-categories'));if(!documentRecords.length)docs.append(make('p','No Markdown documents indexed.','empty-state'));
    const review=section('Review queue',()=>setView('audit'),'All findings','workspace-review');
    review.querySelector('h2').append(make('span',' '+findings.length,'section-count'));
    const ranked=[...findings].sort((a,b)=>(b.status==='stale')-(a.status==='stale') || Number(documentByPath.has(b.path))-Number(documentByPath.has(a.path)));
    ranked.slice(0,3).forEach(f=>{
      const row=make('div',undefined,'review-row');
      const path=documentByPath.has(f.path)?button(f.path,()=>openDocument(f.path),'flat path review-path'):make('span',f.path||'Repository','path review-path');
      path.title=f.path||'Repository';
      row.append(make('p',f.kind==='acceptance'?'Acceptance criteria not detected':f.message),make('span',f.status==='stale'?'Stale':'Needs review','tag '+(f.status==='stale'?'warn':'')),path);
      row.append(button('Investigate',()=>{useCommand('audit',documentByPath.has(f.path)?f.path:null);$('chat-input').value=`Investigate ${f.kind} at ${f.path||'repository'}: ${f.message}`;},'flat review-action'));review.append(row);
    });if(!ranked.length)review.append(make('p','No findings in this snapshot.','empty-state'));
    const map=section('Explore connections',()=>openGraphFor(null),'Open graph','workspace-map');
    const connected=documentRecords.map(d=>({doc:d,count:graph.edges.filter(e=>(e.source==='file:'+d.path||e.target==='file:'+d.path)&&!['contains','changed_by'].includes(e.type)).length})).sort((a,b)=>b.count-a.count).slice(0,4);
    connected.forEach(({doc,count})=>{const row=button('',()=>openGraphFor(doc.path),'connection-row');row.append(icon('graph'),make('span',doc.path),make('span',`${count} links`,'small muted'));map.append(row);});
    if(!connected.length)map.append(make('p','Index documents to explore their connections.','empty-state'));
    const activity=section('Latest run',()=>setView('runs'),'Run history','workspace-activity');
    const run=(graph.workspace?.runs||[])[0];
    if(run){activity.append(make('span',run.status==='not-run'?'Preview':run.status||'Recorded','tag'),make('p',run.task,'latest-task'));activity.append(make('p',run.model||run.route?.model||'Model not recorded','muted small'));}
    else activity.append(make('p','No execution runs yet.','empty-state'));
    const memories=graph.workspace?.memories||[],current=memories.filter(m=>m.freshness==='current').length;
    activity.append(button(`${current} current memory record${current===1?'':'s'}`,()=>setView('memory'),'flat memory-link'));

  }
  function renderJournal() {
    const query=$('memory-search').value.toLowerCase();
    for(const [id, records] of [['run-list',graph.workspace?.runs||[]],['memory-list',(graph.workspace?.memories||[]).filter(m=>JSON.stringify(m).toLowerCase().includes(query))]]) {
      const out=$(id);out.replaceChildren();
      if(!records.length)out.append(make('p',id==='run-list'?'No runs yet.':'No matching project memory.','empty-state'));
      records.forEach(record=>{
        const article=make('article',undefined,'journal-entry');
        const title=record.task.length>120?record.task.slice(0,117)+'…':record.task;
        article.append(make('span',record.freshness || record.status,'tag'),make('h2',title),make('p',record.recorded_at?new Date(record.recorded_at).toLocaleString():'','muted small'));
        if(record.task.length>120){const details=make('details');details.append(make('summary','Full request'),make('p',record.task));article.append(details);}
        if(id==='run-list')article.append(make('p',`${record.router || 'Router'} → ${record.model || record.route?.model || 'Pending'} → ${record.completion ? 'Memory saved' : 'No memory written'}`,'run-stages'));
        (record.summary || record.impact || []).forEach(line=>{const p=make('p');inlineMarkdown(p,line,'README.md');article.append(p);});
        if(record.reason)article.append(make('p',record.reason));
        const checks=record.checks||[];
        if(checks.length){const details=make('details');details.append(make('summary',`Reported checks (${checks.length})`));const ul=make('ul');checks.forEach(check=>ul.append(make('li',check)));details.append(ul);article.append(details);}
        const path=record.document || record.completion?.documentation;
        if(path)article.append(button('Open work record',()=>documentByPath.has(path)?openDocument(path):showToast('Refresh the graph to load this record.'),'flat'));
        out.append(article);
      });
    }
  }
  $('memory-search').addEventListener('input',renderJournal);
  $('library-toggle').addEventListener('click',()=>{const open=document.querySelector('.shell').classList.toggle('library-open');$('library-toggle').setAttribute('aria-expanded',String(open));syncDrawerAccess();if(open)$('document-search').focus();});
  function editLabels(doc) {
    const dialog = make("dialog", undefined, "label-editor");dialog.setAttribute('aria-label','Document labels');
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
    const categoryLabel=make('label','Category'), category=make('input');
    category.value=doc.labels?.category || doc.type;category.maxLength=48;categoryLabel.append(category);form.append(categoryLabel);
    const status=make("p", "", "small");status.setAttribute("role","status");form.append(status);
    const actions=make("div",undefined,"row"), cancel=button("Cancel",()=>dialog.close());
    const save=button("Save labels",async()=>{
      save.disabled=true;
      try {const response=await fetch("/api/labels",{method:"POST",headers:{"Content-Type":"application/json","X-Atlas-Token":graph.workspace.connection.token},body:JSON.stringify({path:doc.path,category:category.value.trim(),kind:inputs.kind.value,status:inputs.status.value,topics:topics.value.split(",").map(t=>t.trim()).filter(Boolean)})});
        const body=await response.json();if(!response.ok)throw new Error(body.error || "Labels could not be saved.");
        doc.labels=body.labels;initDocuments();renderCategories();renderDocuments();renderGraph();renderReader();dialog.close();showToast("Document labels saved");
      }catch(error){status.textContent=error.message}finally{save.disabled=false}
    },"primary");actions.append(cancel,save);form.append(actions);dialog.append(form);document.body.append(dialog);
    dialog.addEventListener("close",()=>dialog.remove());dialog.showModal();
  }
  function auditFindings() {
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
    documentRecords.forEach(doc => {
      if (doc.labels?.freshness === 'stale' || doc.labels?.category_freshness === 'stale') findings.push({status:'stale',kind:'document-labels',path:doc.path,message:'Document changed since its labels were assigned. Review or organize it again.'});
      if (['decision','plan'].includes(doc.labels?.kind || doc.type) && !doc.signals?.has_acceptance) findings.push({status:'needs-review',kind:'acceptance',path:doc.path,message:'No acceptance criteria detected. Check whether the intended behavior can be verified.'});
    });
    return findings;
  }
  function renderAudit() {
    const findings=auditFindings();
    $('side-audit-count').textContent=findings.length;
    const counts = [
      ["Needs review", findings.filter(f => f.status === 'needs-review').length],
      ["Stale evidence", findings.filter(f => f.status === 'stale').length],
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
          else{useCommand('audit');$('chat-input').value=`Investigate ${f.kind} at ${f.path}: ${f.message || ''}`;}
        },"flat small"));
      }
      out.append(item);
    });
  }
  $('graph-relationship').addEventListener('change',()=>{transform={x:0,y:0,k:1};renderGraph();});
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
  $("audit-codex").addEventListener('click', () => useCommand('audit'));
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
  }
  function renderCategories() {
    const groups=d3.rollup(documentRecords, ds=>ds.length, d=>d.labels?.category || 'Documents');
    const control=$('document-category');control.replaceChildren(make('option','All categories'));control.firstChild.value='all';
    [...groups.keys()].sort().forEach(name=>{const option=make('option',name);option.value=name;control.append(option)});
    control.value=selectedCategory || 'all';
  }
  function openChat(path=null) {
    chatDocument=path;
    if (!$('chat-mode').disabled) {$('chat-mode').value='ask';updateComposer();}
    const context=$('chat-context');context.replaceChildren();context.hidden=!path;
    if(path)context.append(make('span',path),button('×',()=>openChat(null),'flat'));
    context.querySelector('button')?.setAttribute('aria-label','Remove document context');
    setView('chat');
  }
  const skillEntries = [
    ['atlas-organize','Organize documents','organize'],['atlas-audit','Audit code & docs','audit'],
    ['atlas-docs','Write docs','docs'],['atlas-memory','Save project memory','memory'],['atlas-graph','Explore graph','graph']
  ];
  skillEntries.forEach(([name])=>{
    const row=make('div',undefined,'cli-skill-row'), code=make('code','$'+name);
    row.append(code,button('Copy',async()=>{try{await navigator.clipboard.writeText('$'+name);showToast('Copied $'+name);}catch(_){showToast('Select and copy the command shown.');}},'flat'));
    row.lastChild.setAttribute('aria-label','Copy $'+name);$('cli-skill-list').append(row);
  });
  const modes = {
    ask: ['Ask about this project…', 'Ask', 'Read-only'],
    task: ['Describe the change to implement…', 'Run & edit files', 'Updates docs & memory after checks'],
    docs: ['Describe the documentation to write…', 'Run & edit files', 'Updates project documentation'],
    audit: ['What should Codex audit?', 'Run audit', 'Read-only'],
    organize: ['Optional scope', 'Organize', 'Changes category labels only'],
    memory: ['Optional scope', 'Save memory', 'Requires a verified implementation'],
  };
  function updateComposer() {
    const [placeholder, label, scope] = modes[$('chat-mode').value];
    $('chat-input').placeholder = placeholder;
    $('chat-input').hidden = ['organize', 'memory'].includes($('chat-mode').value);
    $('chat-form').querySelector('[type=submit]').textContent = label;
    $('chat-state').textContent = graph.workspace?.connection ? scope : 'Offline export';
  }
  function useCommand(action, path=chatDocument) {
    $('command-dialog').close();
    openChat(path);
    $('chat-mode').value = action;
    $('chat-input').value = path && action === 'docs' ? `Update ${path} against its implementation` : '';
    updateComposer();
    ($('chat-input').hidden ? $('chat-mode') : $('chat-input')).focus();
  }
  $('chat-mode').addEventListener('change', updateComposer);
  document.querySelectorAll('[data-command]').forEach(el=>el.addEventListener('click',()=>useCommand(el.dataset.command)));
  $('command-graph').addEventListener('click',()=>{$('command-dialog').close();openGraphFor(null);});
  $('command-open').addEventListener('click',()=>$('command-dialog').showModal());
  $('command-close').addEventListener('click',()=>$('command-dialog').close());
  $('document-organize').addEventListener('click',()=>useCommand('organize'));
  $('document-category').addEventListener('change',()=>{selectedCategory=$('document-category').value==='all'?null:$('document-category').value;graphScope='documents';$('graph-scope').value='documents';focused=false;exactType=null;transform={x:0,y:0,k:1};renderCategories();renderDocuments();renderGraph();});
  document.querySelector('.sheet').append($('chat-drawer'));
  function initDocuments() {
    $('side-doc-count').textContent=documentRecords.length;
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
  renderCategories();
  renderGraph();
  renderDocuments();
  renderAudit();
  renderPreviews();

  setView(baseViews.includes(location.hash.slice(1))?location.hash.slice(1):'workspace');
  addEventListener('hashchange',()=>{const view=location.hash.slice(1);if(baseViews.includes(view))setView(view);});
  updateComposer();
  const connection=graph.workspace?.connection;
  if(connection){
    $('chat-toggle').hidden=false;
    $('chat-toggle').addEventListener('click',()=>openChat(baseView==='documents'?readerPath:chatDocument));
    $('chat-close').addEventListener('click',()=>{setView(baseView);$('chat-toggle').focus()});
    $('chat-form').addEventListener('submit',async event=>{
      event.preventDefault();const input=$('chat-input');const mode=$('chat-mode').value;
      const entered=input.value.trim();
      if(!entered && !['organize','memory','audit'].includes(mode)) {input.focus();return;}
      const task=entered || (chatDocument ? 'Review '+chatDocument : 'Review this project');
      const scoped=chatDocument && mode !== 'ask' ? task+' — focus on '+chatDocument : task;
      const literal=entered.startsWith('/codex-atlas');
      const message=literal || mode==='ask' ? entered : `/codex-atlas ${mode==='task'?'':mode+' '}TASK=${JSON.stringify(scoped)} RUN=true${['task','docs'].includes(mode)?' ALLOW_EDITS=true':''}`;
      const submit=$('chat-form').querySelector('button[type=submit]');submit.disabled=true;input.disabled=true;$('chat-mode').disabled=true;$('chat-form').setAttribute('aria-busy','true');$('chat-state').textContent='Working…';
      input.value='';$('chat-messages').append(make('div',literal ? entered : `${$('chat-mode').selectedOptions[0].textContent}${entered ? ': '+entered : ''}`,'chat-message user'));
      const wait=make('div',mode==='ask'?'Reading project context…':'Running in Codex…','chat-message assistant');$('chat-messages').append(wait);
      $('chat-messages').scrollTop=$('chat-messages').scrollHeight;
      const activityTimer=setInterval(async()=>{try{const response=await fetch('/api/activity',{headers:{'X-Atlas-Token':connection.token}});if(!response.ok)return;const activity=await response.json();const labels={reading:'Reading sources',deciding:'Choosing execution model',executing:'Executing in Codex',remembering:'Writing docs and memory',organizing:'Organizing documents'};if(labels[activity.stage])wait.textContent=labels[activity.stage]+(activity.model?' · '+activity.model:'')+'…';}catch(_){}},1500);
      try{const response=await fetch(connection.endpoint,{method:'POST',headers:{'Content-Type':'application/json','X-Atlas-Token':connection.token},body:JSON.stringify({message,document:chatDocument})});
        const body=await response.json();wait.replaceChildren(markdown(body.reply||body.error||'No response.','README.md'));
        if(body.status)wait.prepend(make('div',body.status==='routed'?(body.execution?.result || body.status):body.status,'label-status'));
        if(body.execution?.finalize)wait.append(make('span',`${['current','stale'].includes(body.status)?'Previously recorded in':'Recorded in'} ${body.execution.finalize.documentation} and ${body.execution.finalize.memory}`,'chat-citation'));
        if(body.usage && typeof body.usage==='object')wait.append(make('span',`${body.usage.input_tokens ?? '—'} input · ${body.usage.output_tokens ?? '—'} output tokens`,'label-status'));
        if(body.execution?.usage && typeof body.execution.usage==='object')wait.append(make('span',`Codex: ${body.execution.usage.input_tokens ?? '—'} input · ${body.execution.usage.output_tokens ?? '—'} output tokens`,'label-status'));
        if(body.routing)wait.append(make('span',`Route: ${body.routing.model} · ${body.routing.effort||'medium'}`,'chat-citation'));
        if(body.citations?.length){const details=make('details');details.append(make('summary',`Sources (${body.citations.length})`));body.citations.forEach(path=>details.append(button(path,()=>{const node=nodeById.get('file:'+path);if(node)selectNode(node);},'flat chat-citation')));wait.append(details);}
        if(body.execution?.command){const details=make('details');details.append(make('summary','Execution command'),make('pre',body.execution.command));wait.append(details);}
      }catch(_){wait.textContent='The local Atlas server is unavailable. Use the CLI workflow.'}
      finally{clearInterval(activityTimer);submit.disabled=false;input.disabled=false;$('chat-mode').disabled=false;$('chat-form').removeAttribute('aria-busy');updateComposer();$('chat-messages').scrollTop=$('chat-messages').scrollHeight;input.focus()}
    });
    setInterval(async()=>{if(document.hidden)return;try{const response=await fetch('/api/graph',{headers:{'X-Atlas-Token':connection.token}});if(!response.ok)return;const next=await response.json();if(next.snapshot.hash===graph.snapshot.hash && JSON.stringify(next.workspace.documents)===JSON.stringify(graph.workspace.documents) && JSON.stringify(next.workspace.decisions)===JSON.stringify(graph.workspace.decisions) && JSON.stringify(next.workspace.runs)===JSON.stringify(graph.workspace.runs) && JSON.stringify(next.workspace.memories)===JSON.stringify(graph.workspace.memories))return;
      Object.assign(graph,next);files.splice(0,files.length,...graph.nodes.filter(n=>n.symbol===null&&n.path&&n.type!=='runtime-check'));
      documentRecords.splice(0,documentRecords.length,...graph.workspace.documents.documents);documentByPath.clear();documentRecords.forEach(d=>documentByPath.set(d.path,d));
      initDocuments();renderCategories();nodeById.clear();graph.nodes.forEach(n=>nodeById.set(n.id,n));routeNodes.splice(0,routeNodes.length,...graph.nodes.filter(n=>n.type==='api'&&!/(^|\/)tests?\/|\.(?:test|spec)\.[^/]+$/.test(n.path)));
      degree.clear();graph.edges.filter(e=>e.type!=='contains'&&e.type!=='changed_by').forEach(e=>{degree.set(e.source,(degree.get(e.source)||0)+1);degree.set(e.target,(degree.get(e.target)||0)+1)});
      selected=selected?nodeById.get(selected.id)||null:null;
      $('side-doc-count').textContent=documentRecords.length;$('side-audit-count').textContent=graph.diagnostics.length;
      $('sidebar-snapshot').textContent=graph.snapshot.hash.slice(0,12)+' · local snapshot';
      $('footer-snapshot').textContent=`Snapshot ${graph.snapshot.hash.slice(0,12)} · ${graph.nodes.length} nodes · ${graph.edges.length} relationships`;
      renderGraph();renderDocuments();renderAudit();renderReader();renderJournal();renderRecentDecisions();renderPreviews();renderWorkspace();showToast('Graph refreshed from repository changes');
    }catch(_){}},7000);
  }else{
    $('chat-toggle').addEventListener('click',()=>openChat(baseView==='documents'?readerPath:chatDocument));
    $('chat-close').addEventListener('click',()=>setView(baseView));
    $('chat-state').textContent='Offline export';
    $('chat-form').addEventListener('submit',event=>{event.preventDefault();showToast('Start the local Atlas server to use chat and commands.');});
  }

  document.addEventListener("keydown", event => {
    if(event.key==='k' && (event.metaKey || event.ctrlKey)){event.preventDefault();$('command-dialog').showModal();}
    if(event.key==="Escape" && !document.querySelector('dialog[open]')) {document.querySelector('.shell').classList.remove('library-open');$('library-toggle').setAttribute('aria-expanded','false');setView(baseView);restoreDrawerFocus();}
  });
  addEventListener('resize',()=>{
    if(baseView==='documents')placeOutline();
    syncDrawerAccess();
    if(!presentationChosen)$('graph-presentation').value=innerWidth<1000?'list':'graph';
    transform={x:0,y:0,k:1};renderGraph();
  });
  const resize = new ResizeObserver(() => {
    syncDrawerAccess();
    if(!presentationChosen)$('graph-presentation').value=innerWidth<1000?'list':'graph';
    transform={x:0,y:0,k:1};renderGraph();
  });
  resize.observe(document.querySelector(".canvas-wrap"));
})();
