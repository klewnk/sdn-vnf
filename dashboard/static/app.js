const cards = document.getElementById("cards");
const groupNav = document.getElementById("group-nav");
const scenarioContent = document.querySelector(".scenario-content");
const welcomeScreen = document.getElementById("welcome-screen");
const groupContent = document.getElementById("group-content");
const activeGroupLabel = document.getElementById("active-group-label");
const activeGroupTitle = document.getElementById("active-group-title");
const activeGroupDescription = document.getElementById("active-group-description");
const activeGroupInfo = document.getElementById("active-group-info");
const serviceStatus = document.getElementById("service-status");
const outputBox = document.getElementById("output-box");
const lastCommand = document.getElementById("last-command");
const apiStatus = document.getElementById("api-status");
const clearOutput = document.getElementById("clear-output");
const startLab = document.getElementById("start-lab");
const stopLab = document.getElementById("stop-lab");

let allTests = [];
let activeGroup = "";
let serviceStates = {};

const groupContainers = {
  DNS: ["vnf_dns"],
  IDS: ["vnf_ids"],
  Proxy: ["vnf_proxy"],
  WAF: ["vnf_waf"],
  "Load Balancer": ["vnf_lb", "lb_backend1", "lb_backend2"],
  "Edge Cache": ["vnf_cache", "cache_origin"],
  Firewall: ["vnf_firewall"],
  "FRR Router": ["vnf_frr"],
  NAT: ["vnf_nat"],
  "Traffic Control": ["vnf_tc"],
  "Monitoring / Tools": ["grafana", "prometheus", "dozzle", "cadvisor"],
};

const groupDescriptions = {
  "Lab Control": "Start, stop, and inspect Docker services for the lab.",
  DNS: "Name resolution tests through the DNS VNF.",
  Proxy: "Web filtering tests for blocked domains and file types.",
  IDS: "Alert demonstration after suspicious or blocked traffic.",
  WAF: "Application-layer protection against SQL injection and XSS.",
  "Load Balancer": "Traffic distribution across backend web servers.",
  "Edge Cache": "Content caching behavior with MISS and HIT responses.",
  Firewall: "Packet filtering policy and forwarding counters.",
  "FRR Router": "Routing table proof for the router VNF.",
  NAT: "Outbound VNF chain connectivity, MASQUERADE proof, and NAT table inspection.",
  "Traffic Control": "HTB QoS policy, HTTP priority classification proof, and class statistics.",
  "Monitoring / Tools": "Quick links to the lab monitoring and log web interfaces.",
};

const groupTitles = {
  "Lab Control": "Lab Control - Docker Services",
  Proxy: "Proxy VNF - Layer 7 Filtering",
  DNS: "DNS VNF - Name Resolution",
  IDS: "IDS VNF - Alert Detection",
  WAF: "WAF VNF - Web Attack Protection",
  "Load Balancer": "Load Balancer VNF - Least Active Connections",
  Firewall: "Firewall VNF - Default Deny Policy",
  "FRR Router": "FRR Router VNF - Inter-Subnet Routing",
  "Traffic Control": "Traffic Control VNF - QoS Configuration",
  "Monitoring / Tools": "Monitoring and Tool GUIs",
};

const groupInfo = {
  "Lab Control": [
    "Green means the container is currently running.",
    "Red means the container is stopped or missing.",
    "Start/Stop affects Docker services; restart Mininet after recreating VNF containers.",
  ],
  Proxy: [
    "Blocked domains: .facebook.com, .youtube.com",
    "Blocked file types: .exe, .torrent, .bat, .mp4, .zip",
    "Blocked keywords: games, hack, casino, malware, phishing",
  ],
  DNS: [
    "Purpose: translate domain names into IP addresses.",
    "DNS VNF address used by Mininet hosts: 10.0.0.100.",
  ],
  IDS: [
    "Proxy monitor: alerts after repeated blocked proxy responses.",
    "DNS monitor: alerts on suspicious queries like phishing.test and malware.test.",
    "WAF monitor: alerts when the WAF blocks suspicious HTTP requests.",
    "Snort is running on eth1 and can use packet-based rules from local.rules.",
  ],
  WAF: [
    "Engine: OWASP ModSecurity CRS running in front of the web app.",
    "Blocks SQL injection: id=1' OR '1'='1.",
    "Blocks XSS: <script>alert(1)</script>.",
    "Blocks path traversal: ../../etc/passwd.",
  ],
  "Edge Cache": [
    "The cache stores HTTP responses/objects, such as HTML pages or files.",
    "First clean request for an object is a cache MISS.",
    "After the object is cached, repeated requests are cache HIT.",
  ],
  "Load Balancer": [
    "Algorithm: least_conn.",
    "New requests are sent to the backend server with the fewest active connections.",
    "Backends: lb_backend1 and lb_backend2.",
  ],
  Firewall: [
    "Default FORWARD policy: DROP.",
    "Allows established/related return traffic.",
    "Allows HTTP 80, HTTPS 443, and DNS 53 TCP/UDP.",
    "Allows ICMP with rate limit and logs other forwarded traffic.",
  ],
  "FRR Router": [
    "Routes traffic between 10.0.0.0/24 and 10.0.1.0/24.",
    "eth1 is connected to subnet 10.0.0.0/24.",
    "eth2 is connected to subnet 10.0.1.0/24.",
    "Default route points toward the Firewall VNF.",
  ],
  "Traffic Control": [
    "High-priority class 1:10: ICMP, HTTP, HTTPS, and DNS.",
    "Default class 1:20: traffic that does not match priority filters.",
    "This demo shows configured QoS classes and filters, not a full performance benchmark.",
  ],
  "Monitoring / Tools": [
    "Grafana: dashboards and visualization.",
    "Prometheus: metrics queries and targets.",
    "Dozzle: Docker container logs.",
    "cAdvisor: container resource metrics.",
  ],
};

const categoryOrder = {
  "Lab Control": ["Docker compose controls"],
  Proxy: ["Blocked examples", "Allowed examples"],
  DNS: ["Normal resolution"],
  IDS: ["Proxy alert detection", "DNS alert detection", "WAF alert detection"],
  WAF: ["Blocked examples", "Allowed examples"],
  "Load Balancer": ["Normal distribution", "Least connections use case"],
  "Edge Cache": ["Cache behavior"],
  Firewall: ["Policy inspection", "Allowed traffic tests", "Blocked traffic tests"],
  "FRR Router": ["Routing proof", "Inter-subnet test"],
  "Monitoring / Tools": ["Open web UIs"],
};

const categorySummaries = {
  IDS: {
    "Proxy alert detection": "Detect repeated proxy blocks",
    "DNS alert detection": "Detect suspicious DNS queries",
    "WAF alert detection": "Detect blocked HTTP requests",
  },
  Proxy: {
    "Blocked examples": "Run filtering tests for blocked traffic",
    "Allowed examples": "Run filtering tests for allowed traffic",
  },
  WAF: {
    "Blocked examples": "Demonstrate blocked attack patterns",
    "Allowed examples": "Demonstrate allowed normal requests",
  },
  Firewall: {
    "Policy inspection": "Inspect active firewall rules and counters",
    "Allowed traffic tests": "Prove allowed ports are forwarded",
    "Blocked traffic tests": "Prove blocked ports are dropped",
  },
};

const collapsibleGroups = new Set();

const groupIcons = {
  DNS: '<svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="8" stroke="currentColor" stroke-width="2"/><path d="M4 12h16M12 4a12 12 0 0 1 0 16M12 4a12 12 0 0 0 0 16" stroke="currentColor" stroke-width="1.8"/></svg>',
  IDS: '<svg viewBox="0 0 24 24" fill="none"><path d="M12 3l7 3v6c0 4.2-2.8 7.8-7 9-4.2-1.2-7-4.8-7-9V6l7-3z" stroke="currentColor" stroke-width="2"/></svg>',
  Proxy: '<svg viewBox="0 0 24 24" fill="none"><rect x="4" y="6" width="16" height="12" rx="2" stroke="currentColor" stroke-width="2"/><path d="M8 10h8M8 14h5" stroke="currentColor" stroke-width="2"/></svg>',
  WAF: '<svg viewBox="0 0 24 24" fill="none"><path d="M12 3l8 4v6c0 4-3.5 7.4-8 8-4.5-.6-8-4-8-8V7l8-4z" stroke="currentColor" stroke-width="2"/><path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2"/></svg>',
  "Load Balancer": '<svg viewBox="0 0 24 24" fill="none"><path d="M6 7h12M6 12h12M6 17h12" stroke="currentColor" stroke-width="2"/><circle cx="18" cy="7" r="2" fill="currentColor"/><circle cx="18" cy="12" r="2" fill="currentColor"/><circle cx="18" cy="17" r="2" fill="currentColor"/></svg>',
  "Edge Cache": '<svg viewBox="0 0 24 24" fill="none"><rect x="5" y="5" width="14" height="14" rx="2" stroke="currentColor" stroke-width="2"/><path d="M8 9h8M8 13h8M8 17h5" stroke="currentColor" stroke-width="2"/></svg>',
  Firewall: '<svg viewBox="0 0 24 24" fill="none"><path d="M12 3l7 3v6c0 4.2-2.8 7.8-7 9-4.2-1.2-7-4.8-7-9V6l7-3z" stroke="currentColor" stroke-width="2"/><path d="M12 8v8M8 12h8" stroke="currentColor" stroke-width="2"/></svg>',
  "FRR Router": '<svg viewBox="0 0 24 24" fill="none"><rect x="4" y="8" width="16" height="9" rx="2" stroke="currentColor" stroke-width="2"/><path d="M8 12h8" stroke="currentColor" stroke-width="2"/></svg>',
  NAT: '<svg viewBox="0 0 24 24" fill="none"><path d="M7 7h10v10H7z" stroke="currentColor" stroke-width="2"/><path d="M10 12h4M12 10v4" stroke="currentColor" stroke-width="2"/></svg>',
  "Traffic Control": '<svg viewBox="0 0 24 24" fill="none"><path d="M4 14h4l2-8 4 16 2-6h4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  "Monitoring / Tools": '<svg viewBox="0 0 24 24" fill="none"><path d="M4 18V6M8 18V10M12 18V13M16 18V8M20 18V4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
};

const ANSI_CLASSES = {
  1: "ansi-bold",
  31: "ansi-red",
  32: "ansi-green",
  33: "ansi-yellow",
  34: "ansi-blue",
  36: "ansi-cyan",
};

function escapeHtml(text) {
  return text.replace(/[&<>]/g, (char) => `&${{ "&": "amp", "<": "lt", ">": "gt" }[char]};`);
}

function ansiToHtml(text) {
  const cleaned = text.replace(/\u001b\[[0-9;]*[A-HJKfhlsu]/g, "");
  const sgr = /\u001b\[([0-9;]*)m/g;
  let html = "";
  let cursor = 0;
  let openSpans = 0;
  let match;

  while ((match = sgr.exec(cleaned)) !== null) {
    html += escapeHtml(cleaned.slice(cursor, match.index));
    cursor = sgr.lastIndex;

    const codes = match[1].split(";").filter(Boolean);
    if (!codes.length || codes.includes("0")) {
      html += "</span>".repeat(openSpans);
      openSpans = 0;
      continue;
    }

    const classes = codes.map((code) => ANSI_CLASSES[code]).filter(Boolean);
    if (classes.length) {
      html += `<span class="${classes.join(" ")}">`;
      openSpans += 1;
    }
  }

  html += escapeHtml(cleaned.slice(cursor));
  return html + "</span>".repeat(openSpans);
}

function setOutput(text, isError = false, mode = "result") {
  outputBox.classList.toggle("error", isError);
  outputBox.classList.remove("output-idle", "output-waiting");

  if (mode === "idle") {
    outputBox.classList.add("output-idle");
    outputBox.innerHTML = `
      <div class="output-placeholder">
        <div class="output-placeholder-icon" aria-hidden="true">&gt;_</div>
        <p class="output-placeholder-title">No test executed yet</p>
        <p class="output-placeholder-text">Select a VNF and run a demo to see the results here.</p>
      </div>`;
    return;
  }

  if (mode === "waiting") {
    outputBox.classList.add("output-waiting");
    outputBox.innerHTML = `
      <div class="output-placeholder">
        <div class="output-placeholder-icon waiting" aria-hidden="true">...</div>
        <p class="output-placeholder-title">Waiting for test execution</p>
        <p class="output-placeholder-text">Choose a demo scenario and press Run demo.</p>
      </div>`;
    return;
  }

  outputBox.innerHTML = ansiToHtml(text || "(no output)");
}

function setOutputIdle() {
  lastCommand.textContent = "No test executed yet";
  setOutput("", false, "idle");
}

function setOutputWaiting(groupName) {
  lastCommand.textContent = groupName ? `${groupName} — waiting for demo` : "Waiting for test execution...";
  setOutput("", false, "waiting");
}

const labStatusCopy = {
  checking: {
    label: "Checking...",
    detail: "Loading service status...",
    dotClass: "",
  },
  stopped: {
    label: "Stopped",
    detail: "All services are stopped",
    dotClass: "stopped",
  },
  running: {
    label: "Running",
    detail: "All VNF services are running",
    dotClass: "ok",
  },
  partial: {
    label: "Partial",
    detail: "Some VNF services are unavailable",
    dotClass: "warn",
  },
};

function computeLabStatus() {
  const containerValues = Object.values(serviceStates);
  if (!containerValues.length) {
    return "checking";
  }

  const runningCount = containerValues.filter(Boolean).length;
  const totalCount = containerValues.length;

  if (runningCount === 0) {
    return "stopped";
  }
  if (runningCount === totalCount) {
    return "running";
  }
  return "partial";
}

function updateLabStatusBar() {
  const labCard = document.getElementById("status-lab-card");
  const readyLabel = document.getElementById("status-ready-label");
  const readyText = document.getElementById("status-ready-text");
  const containersText = document.getElementById("status-containers-text");
  const monitoringText = document.getElementById("status-monitoring-text");
  const readyIcon = document.getElementById("status-ready-icon");
  const containerValues = Object.values(serviceStates);
  const hasStatus = containerValues.length > 0;
  const runningCount = containerValues.filter(Boolean).length;
  const totalCount = containerValues.length;
  const monitoringNames = ["grafana", "prometheus", "dozzle", "cadvisor"];
  const monitoringUp = monitoringNames.every((name) => serviceStates[name]);
  const labState = computeLabStatus();
  const status = labStatusCopy[labState];

  if (labCard) {
    labCard.dataset.state = labState;
  }

  if (readyLabel) {
    readyLabel.textContent = status.label;
  }

  if (readyText) {
    readyText.textContent = status.detail;
  }

  if (readyIcon) {
    readyIcon.classList.remove("ok", "warn", "stopped", "ready");
    if (status.dotClass) {
      readyIcon.classList.add(status.dotClass);
    }
  }

  if (containersText) {
    containersText.textContent = hasStatus
      ? `${runningCount}/${totalCount} VNF services running`
      : "Checking services...";
  }

  if (monitoringText) {
    monitoringText.textContent = hasStatus
      ? monitoringUp
        ? "Grafana + Prometheus + Dozzle"
        : "Some monitoring tools are down"
      : "Grafana + Prometheus";
  }
}

function setViewState(mode) {
  const showHome = mode === "home";
  if (scenarioContent) {
    scenarioContent.dataset.view = showHome ? "home" : "vnf";
  }
  welcomeScreen.hidden = !showHome;
  groupContent.hidden = showHome;
}

function showWelcomeScreen() {
  activeGroup = "";
  setViewState("home");
  renderGroupNav(visibleGroups(allTests));
  setOutputIdle();
  updateLabStatusBar();
}

function showGroupContent(group) {
  activeGroup = group;
  setViewState("vnf");
  setOutputWaiting(group);
  updateLabStatusBar();
}

function formatResult(result) {
  const parts = [
    result.stdout || "(empty)",
  ];

  if (result.stderr) {
    parts.push("", "Details:", result.stderr);
  }

  if (result.exitCode !== 0) {
    parts.unshift(`Scenario finished with exit code ${result.exitCode}.`);
  }

  return parts.join("\n");
}

function refreshServiceStatusAfterLabChange() {
  loadServiceStatus();
  window.setTimeout(loadServiceStatus, 2000);
  window.setTimeout(loadServiceStatus, 5000);
}

async function loadServiceStatus() {
  const showPanel = activeGroup === "Lab Control";
  serviceStatus.hidden = !showPanel;
  serviceStatus.innerHTML = "";
  if (showPanel) {
    serviceStatus.textContent = "Loading container status...";
  }

  try {
    const response = await fetch("/api/status");
    const payload = await response.json();
    serviceStates = {};
    for (const container of payload.containers || []) {
      serviceStates[container.name] = container.running;
    }
    if (allTests.length) {
      renderGroupNav(visibleGroups(allTests));
    }
    updateLabStatusBar();

    if (!showPanel) {
      return;
    }

    serviceStatus.innerHTML = "";

    for (const container of payload.containers || []) {
      const item = document.createElement("span");
      item.className = `service-pill ${container.running ? "running" : "stopped"}`;
      item.textContent = `${container.running ? "UP" : "DOWN"} ${container.name}`;
      serviceStatus.appendChild(item);
    }

    if (payload.error) {
      const error = document.createElement("p");
      error.className = "status-error";
      error.textContent = payload.error;
      serviceStatus.appendChild(error);
    }
  } catch (error) {
    if (showPanel) {
      serviceStatus.textContent = error.message;
    }
    updateLabStatusBar();
  }
}

async function runTest(test, button) {
  if (test.url) {
    lastCommand.textContent = test.title;
    setOutput(`Opening ${test.title}:\n${test.url}`);
    window.open(test.url, "_blank", "noopener,noreferrer");
    return;
  }

  const originalText = button.textContent;
  button.disabled = true;
  button.textContent = "Running...";
  lastCommand.textContent = test.title;
  setOutput(`Running ${test.title}...`);

  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: test.id }),
    });
    const result = await response.json();
    if (!response.ok) {
      setOutput(result.error || "Command failed", true);
      return;
    }
    setOutput(formatResult(result), result.exitCode !== 0);
    if (test.id === "lab-start" || test.id === "lab-stop") {
      refreshServiceStatusAfterLabChange();
    } else if (activeGroup === "Lab Control") {
      loadServiceStatus();
    }
  } catch (error) {
    setOutput(error.message, true);
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
}

function uniqueGroups(tests) {
  return [...new Set(tests.map((test) => test.group))];
}

function visibleGroups(tests) {
  return uniqueGroups(tests).filter((group) => group !== "Lab Control");
}

const groupStatusTitles = {
  running: "All related containers are running",
  stopped: "Related containers are stopped",
  partial: "Some related containers are unavailable",
};

function groupStatus(group) {
  const containers = groupContainers[group];
  if (!containers || !Object.keys(serviceStates).length) {
    return null;
  }

  const runningCount = containers.filter((name) => serviceStates[name] === true).length;

  if (runningCount === 0) {
    return "stopped";
  }
  if (runningCount === containers.length) {
    return "running";
  }
  return "partial";
}

function renderGroupNav(groups) {
  groupNav.innerHTML = "";
  for (const group of groups) {
    const button = document.createElement("button");
    button.className = "group-button";
    button.classList.toggle("active", group === activeGroup);

    const label = document.createElement("span");
    label.className = "group-button-label";
    label.textContent = group;

    if (groupIcons[group]) {
      const icon = document.createElement("span");
      icon.className = "group-nav-icon";
      icon.innerHTML = groupIcons[group];
      button.appendChild(icon);
    }

    button.appendChild(label);

    const status = groupStatus(group);
    if (status !== null) {
      const dot = document.createElement("span");
      dot.className = `nav-dot ${status}`;
      dot.title = groupStatusTitles[status];
      button.appendChild(dot);
    }

    button.addEventListener("click", () => {
      showGroupContent(group);
      renderGroupNav(groups);
      renderTests(allTests);
      loadServiceStatus();
    });
    groupNav.appendChild(button);
  }
}

function categorySummary(group, category, testsInCategory) {
  const configured = categorySummaries[group]?.[category];
  if (configured) {
    return configured;
  }
  if (testsInCategory.length === 1) {
    return testsInCategory[0].description;
  }
  return `${testsInCategory.length} demo scenarios`;
}

function renderTests(tests) {
  if (!activeGroup) {
    return;
  }

  const visibleTests = tests.filter((test) => test.group === activeGroup);
  const discoveredCategories = [...new Set(visibleTests.map((test) => test.category || "Demo commands"))];
  const preferredOrder = categoryOrder[activeGroup] || [];
  const categories = [
    ...preferredOrder.filter((category) => discoveredCategories.includes(category)),
    ...discoveredCategories.filter((category) => !preferredOrder.includes(category)),
  ];

  activeGroupLabel.textContent = activeGroup || "Select VNF";
  activeGroupTitle.textContent = groupTitles[activeGroup] || `${activeGroup || "VNF"} Demo Scenarios`;
  activeGroupDescription.textContent =
    groupDescriptions[activeGroup] || "Run one presentation scenario and review the output.";
  activeGroupInfo.innerHTML = "";
  for (const item of groupInfo[activeGroup] || []) {
    const li = document.createElement("li");
    li.textContent = item;
    activeGroupInfo.appendChild(li);
  }
  loadServiceStatus();

  const orderedTests = [];
  for (const category of categories) {
    orderedTests.push(
      ...visibleTests.filter((item) => (item.category || "Demo commands") === category),
    );
  }

  cards.innerHTML = "";
  cards.className = "cards";

  for (const test of orderedTests) {
    const card = document.createElement("article");
    card.className = "card";

    const title = document.createElement("h3");
    title.textContent = test.title;

    const description = document.createElement("p");
    description.className = "description";
    description.textContent = test.description;

    const commands = document.createElement("pre");
    commands.className = "commands";
    commands.textContent = test.commands.join("\n");

    const button = document.createElement("button");
    button.textContent = test.url ? "Open GUI" : "Run demo";
    button.addEventListener("click", () => runTest(test, button));

    card.append(title, description, commands, button);
    cards.appendChild(card);
  }
}

async function loadTests() {
  try {
    const response = await fetch("/api/tests");
    const tests = await response.json();
    allTests = tests;
    showWelcomeScreen();
    loadServiceStatus();
    apiStatus.textContent = "Dashboard ready";
  } catch (error) {
    apiStatus.textContent = "Backend unavailable";
    setOutput(error.message, true);
  }
}

clearOutput.addEventListener("click", () => {
  if (activeGroup) {
    setOutputWaiting(activeGroup);
    return;
  }
  setOutputIdle();
});

startLab.addEventListener("click", () => {
  const test = allTests.find((item) => item.id === "lab-start");
  if (test) {
    runTest(test, startLab);
  }
});

stopLab.addEventListener("click", () => {
  const test = allTests.find((item) => item.id === "lab-stop");
  if (test) {
    runTest(test, stopLab);
  }
});

loadTests();
