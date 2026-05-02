document.addEventListener("DOMContentLoaded", function () {
  applySavedTheme();
  bindThemeToggle();
  bindSettingsControls();
  bindEvaluatorSettings();
  bindSidebarToggle();
  initIcons();
  initThreeBackground();

  const form = document.getElementById("studentForm");
  const overlay = document.getElementById("loadingOverlay");

  if (form && overlay) {
    form.addEventListener("submit", function () {
      overlay.classList.remove("hidden");
    });
  }

  const chartContainer = document.getElementById("performanceChart");
  const dashboardData = document.getElementById("dashboardData");
  const analyticsData = document.getElementById("analyticsData");

  if (chartContainer && dashboardData) {
    const chartTheme = getChartTheme();
    const attendance = parseFloat(dashboardData.dataset.attendance);
    const cpi = parseFloat(dashboardData.dataset.cpi);
    const assignments = parseFloat(dashboardData.dataset.assignments);
    const studyHours = parseFloat(dashboardData.dataset.study_hours);
    const backlogs = parseFloat(dashboardData.dataset.backlogs);
    const attendanceTarget = parseFloat(dashboardData.dataset.target_attendance || "75");
    const cpiTarget = parseFloat(dashboardData.dataset.target_cpi || "6");
    const assignmentsTarget = parseFloat(dashboardData.dataset.target_assignments || "80");
    const studyTarget = parseFloat(dashboardData.dataset.target_study_hours || "15");
    const performanceData = [attendance, cpi * 10, assignments, Math.min(studyHours * 4, 100), Math.min(backlogs * 20, 100)];
    const performanceLabels = ["Attendance", "CPI", "Assign.", "Study", "Backlogs"];

    new Chart(chartContainer, {
      type: "radar",
      data: {
        labels: performanceLabels,
        datasets: [
          {
            label: "Student Performance Profile",
            data: performanceData,
            backgroundColor: "rgba(108, 99, 255, 0.18)",
            borderColor: chartTheme.primaryStrong,
            pointBackgroundColor: chartTheme.primary,
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: {
          padding: 16,
        },
        scales: {
          r: {
            angleLines: { color: chartTheme.gridStrong },
            grid: { color: chartTheme.grid },
            pointLabels: { color: chartTheme.label, font: { size: 11, weight: "600" } },
            suggestedMin: 0,
            suggestedMax: 100,
            ticks: {
              backdropColor: chartTheme.tickBackdrop,
              color: chartTheme.muted,
              stepSize: 50,
              font: { size: 10 },
            },
          },
        },
        plugins: {
          legend: { display: false },
        },
      },
    });

    const riskCanvas = document.getElementById("riskChart");
    if (riskCanvas) {
      const riskScores = [
        Math.max(0, ((attendanceTarget - attendance) / Math.max(attendanceTarget - 40, 20)) * 100),
        Math.max(0, ((cpiTarget - cpi) / Math.max(cpiTarget - 3, 2)) * 100),
        Math.max(0, ((assignmentsTarget - assignments) / Math.max(assignmentsTarget - 30, 20)) * 100),
        Math.max(0, ((studyTarget - studyHours) / Math.max(studyTarget - 5, 5)) * 100),
        Math.min(backlogs * 25, 100),
      ];
      new Chart(riskCanvas, {
        type: "bar",
        data: {
          labels: ["Attend.", "CPI", "Assign.", "Study", "Backlogs"],
          datasets: [
            {
              label: "Risk indicator",
              data: riskScores,
              backgroundColor: [
                "rgba(214, 69, 69, 0.78)",
                "rgba(251, 191, 36, 0.78)",
                "rgba(52, 152, 219, 0.75)",
                "rgba(79, 179, 165, 0.78)",
                "rgba(193, 102, 69, 0.78)",
              ],
              borderColor: [
                "rgba(214, 69, 69, 1)",
                "rgba(251, 191, 36, 1)",
                "rgba(52, 152, 219, 1)",
                "rgba(79, 179, 165, 1)",
                "rgba(193, 102, 69, 1)",
              ],
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          layout: {
            padding: {
              top: 8,
              right: 8,
              bottom: 8,
              left: 4,
            },
          },
          scales: {
            x: {
              ticks: { color: chartTheme.text, maxRotation: 0, minRotation: 0, font: { size: 11 } },
              grid: { display: false },
            },
            y: {
              beginAtZero: true,
              max: 100,
              ticks: { color: chartTheme.text, stepSize: 50, font: { size: 11 } },
              grid: { color: chartTheme.grid },
            },
          },
          plugins: {
            legend: { display: false },
          },
        },
      });
    }
  }

  if (analyticsData) {
    const chartTheme = getChartTheme();
    const analytics = JSON.parse(analyticsData.textContent || "{}");
    const riskDistributionCanvas = document.getElementById("riskDistributionChart");
    const riskTrendCanvas = document.getElementById("riskTrendChart");
    const riskCounts = analytics.risk_counts || { Low: 0, Medium: 0, High: 0 };

    if (riskDistributionCanvas) {
      new Chart(riskDistributionCanvas, {
        type: "doughnut",
        data: {
          labels: ["Low", "Medium", "High"],
          datasets: [
            {
              data: [riskCounts.Low || 0, riskCounts.Medium || 0, riskCounts.High || 0],
              backgroundColor: ["#2ecc71", "#fbbf24", "#d64545"],
              borderColor: chartTheme.chartBorder,
              borderWidth: 4,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: "62%",
          plugins: {
            legend: {
              position: "bottom",
              labels: { color: chartTheme.label, boxWidth: 12, usePointStyle: true },
            },
          },
        },
      });
    }

    if (riskTrendCanvas) {
      new Chart(riskTrendCanvas, {
        type: "line",
        data: {
          labels: analytics.trend_labels || [],
          datasets: [
            {
              label: "Risk score",
              data: analytics.trend_scores || [],
              borderColor: chartTheme.primary,
              backgroundColor: chartTheme.area,
              pointBackgroundColor: chartTheme.accent,
              pointRadius: 4,
              tension: 0.35,
              fill: true,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              ticks: { color: chartTheme.muted, maxRotation: 0, autoSkip: true },
              grid: { display: false },
            },
            y: {
              min: 0,
              max: 100,
              ticks: { color: chartTheme.muted, stepSize: 25 },
              grid: { color: chartTheme.grid },
            },
          },
          plugins: {
            legend: { display: false },
          },
        },
      });
    }
  }
});

function initIcons() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

function getSavedTheme() {
  try {
    return localStorage.getItem("sns-theme") === "light" ? "light" : "dark";
  } catch (error) {
    return "dark";
  }
}

function applySavedTheme() {
  document.body.dataset.theme = getSavedTheme();
}

function setTheme(nextTheme) {
  const theme = nextTheme === "light" ? "light" : "dark";
  try {
    localStorage.setItem("sns-theme", theme);
  } catch (error) {
    // Theme still changes for the current page even if storage is unavailable.
  }
  document.body.dataset.theme = theme;
  syncThemeControls();
}

function bindThemeToggle() {
  const toggles = document.querySelectorAll("[data-theme-toggle]");
  if (!toggles.length) {
    return;
  }

  toggles.forEach(function (toggle) {
    toggle.addEventListener("click", function () {
      const nextTheme = document.body.dataset.theme === "light" ? "dark" : "light";
      setTheme(nextTheme);
    });
  });
  syncThemeControls();
}

function syncThemeControls() {
  const isLight = document.body.dataset.theme === "light";
  document.querySelectorAll("[data-theme-toggle]").forEach(function (toggle) {
    toggle.textContent = isLight ? "☾" : "☀";
    toggle.setAttribute("aria-label", isLight ? "Switch to dark theme" : "Switch to light theme");
    toggle.title = isLight ? "Dark theme" : "Light theme";
    toggle.setAttribute("aria-pressed", String(isLight));
  });

  document.querySelectorAll("[data-theme-choice]").forEach(function (choice) {
    const isActive = choice.dataset.themeChoice === document.body.dataset.theme;
    choice.classList.toggle("active", isActive);
    choice.setAttribute("aria-pressed", String(isActive));
  });
}

function bindSettingsControls() {
  document.querySelectorAll("[data-theme-choice]").forEach(function (choice) {
    choice.addEventListener("click", function () {
      setTheme(choice.dataset.themeChoice);
    });
  });

  document.querySelectorAll("[data-setting-toggle]").forEach(function (toggle) {
    const key = "sns-setting-" + toggle.dataset.settingToggle;
    try {
      toggle.checked = localStorage.getItem(key) === "true";
    } catch (error) {
      toggle.checked = false;
    }
    toggle.addEventListener("change", function () {
      try {
        localStorage.setItem(key, String(toggle.checked));
      } catch (error) {
        // Ignore storage failures; the checkbox still reflects this session.
      }
    });
  });
}

function bindEvaluatorSettings() {
  const lowInput = document.querySelector('input[name="risk_low_max"]');
  const mediumInput = document.querySelector('input[name="risk_medium_max"]');
  const highPreview = document.querySelector("[data-range-preview='high']");

  if (!lowInput || !mediumInput || !highPreview) {
    return;
  }

  const syncRanges = function () {
    const lowMax = Math.max(5, Math.min(80, Number(lowInput.value) || 29));
    const mediumMinimum = lowMax + 5;
    mediumInput.min = String(mediumMinimum);

    let mediumMax = Math.max(mediumMinimum, Math.min(95, Number(mediumInput.value) || 69));
    if (mediumMax <= lowMax) {
      mediumMax = mediumMinimum;
    }

    lowInput.value = String(lowMax);
    mediumInput.value = String(mediumMax);
    highPreview.textContent = `${mediumMax + 1}+`;
  };

  lowInput.addEventListener("input", syncRanges);
  mediumInput.addEventListener("input", syncRanges);
  syncRanges();
}

function bindSidebarToggle() {
  const toggle = document.querySelector("[data-sidebar-toggle]");
  if (!toggle) {
    return;
  }

  let isCollapsed = false;
  try {
    isCollapsed = localStorage.getItem("sns-sidebar-collapsed") === "true";
  } catch (error) {
    isCollapsed = false;
  }

  const applySidebarState = function (collapsed) {
    document.body.classList.toggle("sidebar-collapsed", collapsed);
    toggle.setAttribute("aria-expanded", String(!collapsed));
    toggle.setAttribute("aria-label", collapsed ? "Expand sidebar" : "Collapse sidebar");
    toggle.title = collapsed ? "Expand sidebar" : "Collapse sidebar";
    const icon = toggle.querySelector("i");
    if (icon) {
      icon.setAttribute("data-lucide", collapsed ? "panel-left-open" : "panel-left-close");
      initIcons();
    }
  };

  applySidebarState(isCollapsed);

  toggle.addEventListener("click", function () {
    const nextCollapsed = !document.body.classList.contains("sidebar-collapsed");
    applySidebarState(nextCollapsed);
    try {
      localStorage.setItem("sns-sidebar-collapsed", String(nextCollapsed));
    } catch (error) {
      // The visual state still changes for this session.
    }
  });
}

function getChartTheme() {
  const isLight = document.body.dataset.theme === "light";
  if (isLight) {
    return {
      text: "#172033",
      label: "#172033",
      muted: "#4d5b70",
      grid: "rgba(23,32,51,0.08)",
      gridStrong: "rgba(23,32,51,0.12)",
      tickBackdrop: "rgba(255,255,255,0.85)",
      primary: "#0f5d73",
      primaryStrong: "rgba(15,93,115,0.88)",
      accent: "#a84d2f",
      area: "rgba(15,93,115,0.12)",
      chartBorder: "#ffffff",
    };
  }

  return {
    text: "#f8fafc",
    label: "#d7e0f5",
    muted: "#b5c4e3",
    grid: "rgba(255,255,255,0.08)",
    gridStrong: "rgba(255,255,255,0.12)",
    tickBackdrop: "rgba(11,18,32,0.85)",
    primary: "#6c63ff",
    primaryStrong: "rgba(108,99,255,0.88)",
    accent: "#65d8d2",
    area: "rgba(108,99,255,0.14)",
    chartBorder: "#111827",
  };
}

function initThreeBackground() {
  const canvas = document.getElementById("bg3d");
  if (!canvas || !window.THREE) {
    return;
  }

  const threeTheme = getThreeTheme();
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(threeTheme.fogColor, threeTheme.fogDensity);

  const camera = new THREE.PerspectiveCamera(58, window.innerWidth / window.innerHeight, 0.1, 160);
  camera.position.set(0, 3.6, 27);

  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.7));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = threeTheme.exposure;

  const ambientLight = new THREE.AmbientLight(threeTheme.ambient, threeTheme.ambientIntensity);
  const keyLight = new THREE.PointLight(threeTheme.keyLight, 2.6, 82);
  keyLight.position.set(-12, 10, 16);
  const rimLight = new THREE.PointLight(threeTheme.rimLight, 2.1, 92);
  rimLight.position.set(13, -2, -2);
  const depthLight = new THREE.PointLight(threeTheme.depthLight, 1.9, 104);
  depthLight.position.set(0, 9, -30);
  scene.add(ambientLight, keyLight, rimLight, depthLight);

  const group = new THREE.Group();
  scene.add(group);

  const depthGroup = new THREE.Group();
  const floorGroup = new THREE.Group();
  group.add(depthGroup, floorGroup);

  const floorMaterial = new THREE.MeshStandardMaterial({
    color: threeTheme.floor,
    emissive: threeTheme.floorEmissive,
    emissiveIntensity: threeTheme.floorEmissiveIntensity,
    metalness: 0.72,
    roughness: 0.28,
    transparent: true,
    opacity: threeTheme.floorOpacity,
    side: THREE.DoubleSide,
  });
  const floorGeometry = new THREE.PlaneGeometry(84, 58, 1, 1);
  const floor = new THREE.Mesh(floorGeometry, floorMaterial);
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(0, -7.4, -10);
  floorGroup.add(floor);

  const gridMaterial = new THREE.LineBasicMaterial({
    color: threeTheme.grid,
    transparent: true,
    opacity: threeTheme.gridOpacity,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const gridLines = [];
  const gridLimit = 42;
  for (let index = -gridLimit; index <= gridLimit; index += 4) {
    const zLine = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(-gridLimit, -7.25, index - 10),
      new THREE.Vector3(gridLimit, -7.25, index - 10),
    ]);
    const xLine = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(index, -7.24, -50),
      new THREE.Vector3(index, -7.24, 20),
    ]);
    gridLines.push(new THREE.Line(zLine, gridMaterial), new THREE.Line(xLine, gridMaterial));
  }
  gridLines.forEach((line) => floorGroup.add(line));

  const tunnelMaterial = new THREE.LineBasicMaterial({
    color: threeTheme.tunnel,
    transparent: true,
    opacity: threeTheme.tunnelOpacity,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const tunnelFrames = [];
  for (let index = 0; index < 18; index += 1) {
    const size = 5.8 + index * 1.08;
    const geometry = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(-size, -size * 0.48, -index * 4 - 4),
      new THREE.Vector3(size, -size * 0.48, -index * 4 - 4),
      new THREE.Vector3(size * 1.18, size * 0.58, -index * 4 - 4),
      new THREE.Vector3(-size * 1.18, size * 0.58, -index * 4 - 4),
      new THREE.Vector3(-size, -size * 0.48, -index * 4 - 4),
    ]);
    const frame = new THREE.Line(geometry, tunnelMaterial);
    frame.rotation.z = index % 2 === 0 ? 0.05 : -0.04;
    tunnelFrames.push(frame);
    depthGroup.add(frame);
  }

  const layerMaterial = new THREE.MeshBasicMaterial({
    color: threeTheme.layer,
    transparent: true,
    opacity: threeTheme.layerOpacity,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide,
    depthWrite: false,
  });
  const layers = [];
  for (let index = 0; index < 16; index += 1) {
    const layer = new THREE.Mesh(new THREE.PlaneGeometry(8 + Math.random() * 12, 0.06), layerMaterial.clone());
    layer.position.set((Math.random() - 0.5) * 34, -5.6 + Math.random() * 11, -8 - index * 3.1);
    layer.rotation.set((Math.random() - 0.5) * 0.9, (Math.random() - 0.5) * 0.8, (Math.random() - 0.5) * 0.8);
    layer.material.opacity = threeTheme.layerOpacity * (0.48 + Math.random() * 0.7);
    layers.push(layer);
    depthGroup.add(layer);
  }

  const beamMaterials = threeTheme.beams.map((color) => new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity: threeTheme.beamOpacity,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide,
    depthWrite: false,
  }));
  const beams = [];
  const beamBlueprints = [
    { position: [-13, 2.8, -18], rotation: [0.35, -0.2, -0.35], scale: [19, 1, 1] },
    { position: [11.8, -1.2, -13], rotation: [-0.2, 0.18, 0.42], scale: [17, 1, 1] },
    { position: [0, 6.2, -28], rotation: [0.08, 0.02, -0.08], scale: [28, 1, 1] },
    { position: [-2.5, -4.8, -9], rotation: [-0.1, 0.28, 0.12], scale: [16, 1, 1] },
  ];
  beamBlueprints.forEach((blueprint, index) => {
    const beam = new THREE.Mesh(new THREE.PlaneGeometry(1, 0.09), beamMaterials[index % beamMaterials.length]);
    beam.position.fromArray(blueprint.position);
    beam.rotation.set(blueprint.rotation[0], blueprint.rotation[1], blueprint.rotation[2]);
    beam.scale.fromArray(blueprint.scale);
    beams.push(beam);
    depthGroup.add(beam);
  });

  const haloTexture = createGlowTexture();
  const halos = threeTheme.beams.map((color, index) => {
    const halo = new THREE.Sprite(new THREE.SpriteMaterial({
      map: haloTexture,
      color,
      transparent: true,
      opacity: threeTheme.haloOpacity,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    }));
    const x = [-9.5, 8.5, 0, 13][index] || 0;
    const y = [3.5, -2.8, 5.2, 2.4][index] || 0;
    const z = [-8, -10, -24, -30][index] || -16;
    halo.position.set(x, y, z);
    halo.scale.setScalar([9, 7, 12, 6][index] || 8);
    depthGroup.add(halo);
    return halo;
  });

  function resizeRenderer() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    const scale = window.innerWidth < 760 ? 0.74 : 1;
    group.scale.setScalar(scale);
    camera.position.z = window.innerWidth < 760 ? 31 : 27;
  }

  window.addEventListener("resize", resizeRenderer);
  resizeRenderer();

  let frame = 0;
  function animate() {
    frame += 0.01;
    group.rotation.y = Math.sin(frame * 0.16) * 0.075;
    group.rotation.x = Math.cos(frame * 0.13) * 0.026;
    camera.lookAt(Math.sin(frame * 0.18) * 1.4, 0.6 + Math.cos(frame * 0.12) * 0.5, -17);
    floorGroup.position.z = Math.sin(frame * 0.7) * 0.32;
    tunnelFrames.forEach((frameMesh, index) => {
      frameMesh.position.z = ((frame * 16 + index * 4) % 72) - 70;
      frameMesh.material.opacity = threeTheme.tunnelOpacity * (0.45 + (index / tunnelFrames.length) * 0.9);
    });
    layers.forEach((layer, index) => {
      layer.position.x += Math.sin(frame * 0.7 + index) * 0.004;
      layer.rotation.z += 0.0012 * (index % 2 === 0 ? 1 : -1);
    });
    beams.forEach((beam, index) => {
      beam.material.opacity = threeTheme.beamOpacity * (0.66 + Math.sin(frame * 1.8 + index) * 0.24);
      beam.position.z += Math.sin(frame * 0.9 + index) * 0.01;
    });
    halos.forEach((halo, index) => {
      halo.material.opacity = threeTheme.haloOpacity * (0.76 + Math.sin(frame * 1.35 + index) * 0.18);
      halo.scale.setScalar(([9, 7, 12, 6][index] || 8) + Math.sin(frame * 1.1 + index) * 0.28);
    });
    renderer.render(scene, camera);

    if (!reducedMotion) {
      requestAnimationFrame(animate);
    }
  }

  animate();
}

function createGlowTexture() {
  const size = 128;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const context = canvas.getContext("2d");
  const gradient = context.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  gradient.addColorStop(0, "rgba(255,255,255,0.95)");
  gradient.addColorStop(0.22, "rgba(255,255,255,0.38)");
  gradient.addColorStop(0.58, "rgba(255,255,255,0.12)");
  gradient.addColorStop(1, "rgba(255,255,255,0)");
  context.fillStyle = gradient;
  context.fillRect(0, 0, size, size);
  return new THREE.CanvasTexture(canvas);
}

function getThreeTheme() {
  if (document.body.dataset.theme === "light") {
    return {
      fogColor: 0xf7fafc,
      fogDensity: 0.021,
      exposure: 1,
      ambient: 0xf7fafc,
      ambientIntensity: 0.95,
      keyLight: 0x0f5d73,
      rimLight: 0xa84d2f,
      depthLight: 0x7c3aed,
      floor: 0xdbeafe,
      floorEmissive: 0x0f5d73,
      floorEmissiveIntensity: 0.06,
      floorOpacity: 0.28,
      grid: 0x0f5d73,
      gridOpacity: 0.2,
      tunnel: 0xa84d2f,
      tunnelOpacity: 0.22,
      layer: 0x0f5d73,
      layerOpacity: 0.16,
      beams: [0x0f5d73, 0xa84d2f, 0x7c3aed, 0x2e8f72],
      beamOpacity: 0.14,
      haloOpacity: 0.14,
    };
  }

  return {
    fogColor: 0x060815,
    fogDensity: 0.016,
    exposure: 1.24,
    ambient: 0x26345c,
    ambientIntensity: 0.72,
    keyLight: 0x00e5ff,
    rimLight: 0xff2bd6,
    depthLight: 0x7c3cff,
    floor: 0x050a16,
    floorEmissive: 0x00e5ff,
    floorEmissiveIntensity: 0.16,
    floorOpacity: 0.62,
    grid: 0x00e5ff,
    gridOpacity: 0.36,
    tunnel: 0xff2bd6,
    tunnelOpacity: 0.34,
    layer: 0x39ff88,
    layerOpacity: 0.22,
    beams: [0x00e5ff, 0xff2bd6, 0x7c3cff, 0x39ff88],
    beamOpacity: 0.18,
    haloOpacity: 0.2,
  };
}
