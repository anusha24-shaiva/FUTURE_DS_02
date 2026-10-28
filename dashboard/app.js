// RetainPulse Executive Customer Retention & Churn Intelligence Engine
// Logic, Visualizations, Simulator & Watchlist Controller

document.addEventListener('DOMContentLoaded', () => {
  let appData = null;
  let chartInstances = {};
  let currentWatchlistPage = 1;
  const rowsPerPage = 12;
  let filteredCustomers = [];

  // 1. Data Loader with Graceful Fallback
  async function initData() {
    if (window.ANALYTICS_DATA) {
      appData = window.ANALYTICS_DATA;
    } else {
      try {
        const res = await fetch('analytics_data.json');
        appData = await res.json();
      } catch (err) {
        console.error("Failed to load analytics JSON", err);
        return;
      }
    }

    renderKPIRibbon();
    renderCohortMatrix();
    initCharts();
    initSimulator();
    initWatchlist();
    setupEventListeners();
  }

  // 2. Render Executive KPI Ribbon
  function renderKPIRibbon() {
    if (!appData) return;
    const s = appData.summary;

    document.getElementById('kpiChurnRate').textContent = `${s.churnRate}%`;
    document.getElementById('kpiRetentionRate').textContent = `${s.retentionRate}%`;
    document.getElementById('kpiRetainedMRR').textContent = `$${(s.retainedMRR / 1000).toFixed(1)}K`;
    document.getElementById('kpiChurnedARR').textContent = `$${((s.churnedMRR * 12) / 1000000).toFixed(2)}M`;
    document.getElementById('kpiAtRiskCount').textContent = `${s.highRiskActiveCount || 104} Accounts`;
    const navBadge = document.getElementById('navWatchlistBadge');
    if (navBadge) navBadge.textContent = `${s.highRiskActiveCount || 104}`;
  }

  // 3. Render Triangular Cohort Retention Matrix
  function renderCohortMatrix() {
    if (!appData || !appData.cohorts) return;
    const tbody = document.getElementById('cohortMatrixBody');
    tbody.innerHTML = '';

    appData.cohorts.forEach(cohort => {
      const tr = document.createElement('tr');

      // Month Label
      const tdMonth = document.createElement('td');
      tdMonth.className = 'cohort-month-label';
      tdMonth.textContent = cohort.CohortMonth;
      tr.appendChild(tdMonth);

      // Cohort Size
      const tdSize = document.createElement('td');
      tdSize.className = 'cohort-size-label';
      tdSize.textContent = cohort.CohortSize.toLocaleString();
      tr.appendChild(tdSize);

      // Month 0 to 12 Retention %
      for (let m = 0; m <= 12; m++) {
        const td = document.createElement('td');
        const val = cohort[`M_${m}`];

        if (val !== undefined && val !== null && val !== '') {
          const numVal = parseFloat(val);
          td.textContent = `${numVal.toFixed(1)}%`;
          td.className = 'cell-active';

          // Dynamic Color Scaling
          const bgGrad = getRetentionColor(numVal);
          td.style.background = bgGrad;
          td.style.color = '#ffffff';
          td.style.textShadow = '0 1px 3px rgba(0, 0, 0, 0.6)';

          td.title = `${cohort.CohortMonth} Cohort | Month ${m}: ${numVal.toFixed(1)}% retained (${Math.round((numVal / 100) * cohort.CohortSize)} active)`;
        } else {
          td.textContent = '—';
          td.style.color = 'var(--text-muted)';
          td.style.background = 'rgba(255, 255, 255, 0.02)';
        }
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    });
  }

  // Helper: Retention Color Interpolator with Rich Luminous Gradients
  function getRetentionColor(pct) {
    if (pct >= 88) {
      return 'linear-gradient(135deg, rgba(5, 150, 105, 0.90), rgba(16, 185, 129, 0.96))';
    } else if (pct >= 72) {
      return 'linear-gradient(135deg, rgba(8, 145, 178, 0.88), rgba(6, 182, 212, 0.96))';
    } else if (pct >= 58) {
      return 'linear-gradient(135deg, rgba(99, 102, 241, 0.85), rgba(139, 92, 246, 0.94))';
    } else if (pct >= 45) {
      return 'linear-gradient(135deg, rgba(217, 119, 6, 0.88), rgba(245, 158, 11, 0.96))';
    } else {
      return 'linear-gradient(135deg, rgba(190, 18, 60, 0.90), rgba(244, 63, 94, 0.96))';
    }
  }

  // 4. Initialize Interactive Charts (Chart.js)
  function initCharts() {
    if (typeof Chart === 'undefined' || !appData) return;

    const isDark = document.body.classList.contains('theme-dark');
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)';
    const textColor = isDark ? '#94a3b8' : '#475569';

    Chart.defaults.color = textColor;
    Chart.defaults.font.family = "'Outfit', 'Plus Jakarta Sans', sans-serif";

    // Chart 1: Survival Curve with Neon Gradient Line & Area Fill
    const ctxSurvival = document.getElementById('survivalChart');
    if (ctxSurvival && appData.survival) {
      const ctxS = ctxSurvival.getContext('2d');
      const lineGrad = ctxS.createLinearGradient(0, 0, 700, 0);
      lineGrad.addColorStop(0, '#06b6d4');
      lineGrad.addColorStop(0.5, '#6366f1');
      lineGrad.addColorStop(1, '#ec4899');

      const fillGrad = ctxS.createLinearGradient(0, 0, 0, 320);
      fillGrad.addColorStop(0, 'rgba(6, 182, 212, 0.45)');
      fillGrad.addColorStop(0.6, 'rgba(99, 102, 241, 0.15)');
      fillGrad.addColorStop(1, 'rgba(15, 23, 42, 0.0)');

      const labels = appData.survival.map(d => `Month ${d.TenureMonth}`);
      const dataSurvival = appData.survival.map(d => d.SurvivalProbability);

      chartInstances.survival = new Chart(ctxSurvival, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [{
            label: 'Survival Probability (%)',
            data: dataSurvival,
            borderColor: lineGrad,
            backgroundColor: fillGrad,
            borderWidth: 3.5,
            fill: true,
            tension: 0.38,
            pointBackgroundColor: '#06b6d4',
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2,
            pointRadius: 4.5,
            pointHoverRadius: 7
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: ctx => `Survival Probability: ${ctx.parsed.y}%`
              }
            }
          },
          scales: {
            x: { grid: { color: gridColor } },
            y: {
              min: 0,
              max: 100,
              grid: { color: gridColor },
              ticks: { callback: v => `${v}%` }
            }
          }
        }
      });
    }

    // Chart 2: Hazard Rate with Dynamic Cliff Gradients
    const ctxHazard = document.getElementById('hazardChart');
    if (ctxHazard && appData.survival) {
      const ctxH = ctxHazard.getContext('2d');
      const gradCliff = ctxH.createLinearGradient(0, 0, 0, 300);
      gradCliff.addColorStop(0, '#f43f5e');
      gradCliff.addColorStop(1, '#be123c');

      const gradWarn = ctxH.createLinearGradient(0, 0, 0, 300);
      gradWarn.addColorStop(0, '#fbbf24');
      gradWarn.addColorStop(1, '#d97706');

      const gradNormal = ctxH.createLinearGradient(0, 0, 0, 300);
      gradNormal.addColorStop(0, '#38bdf8');
      gradNormal.addColorStop(1, '#4f46e5');

      const labels = appData.survival.map(d => `M${d.TenureMonth}`);
      const dataHazard = appData.survival.map(d => d.HazardRate);

      chartInstances.hazard = new Chart(ctxHazard, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Monthly Churn Hazard (%)',
            data: dataHazard,
            backgroundColor: dataHazard.map(v => v > 8 ? gradCliff : (v > 4 ? gradWarn : gradNormal)),
            borderRadius: 7
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: ctx => `Hazard Rate: ${ctx.parsed.y}%`
              }
            }
          },
          scales: {
            x: { grid: { display: false } },
            y: {
              grid: { color: gridColor },
              ticks: { callback: v => `${v}%` }
            }
          }
        }
      });
    }

    // Chart 3: Retention Drivers with Indigo-to-Cyan Gradient
    const ctxDrivers = document.getElementById('driversChart');
    if (ctxDrivers && appData.drivers) {
      const ctxD = ctxDrivers.getContext('2d');
      const gradDrivers = ctxD.createLinearGradient(0, 0, 600, 0);
      gradDrivers.addColorStop(0, '#6366f1');
      gradDrivers.addColorStop(0.6, '#06b6d4');
      gradDrivers.addColorStop(1, '#10b981');

      const driversSorted = [...appData.drivers].reverse();
      chartInstances.drivers = new Chart(ctxDrivers, {
        type: 'bar',
        data: {
          labels: driversSorted.map(d => d.FeatureLabel),
          datasets: [{
            label: 'Importance Weight (%)',
            data: driversSorted.map(d => d.ImportancePct),
            backgroundColor: gradDrivers,
            borderRadius: 7
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: {
              grid: { color: gridColor },
              ticks: { callback: v => `${v}%` }
            },
            y: { grid: { display: false } }
          }
        }
      });
    }

    // Chart 4: Pareto Churn Reasons with Sunset Gradients
    const ctxPareto = document.getElementById('paretoChart');
    if (ctxPareto && appData.reasons) {
      const reasonsSorted = [...appData.reasons].reverse();
      chartInstances.pareto = new Chart(ctxPareto, {
        type: 'bar',
        data: {
          labels: reasonsSorted.map(d => d.ChurnReason),
          datasets: [{
            label: 'Lost Accounts',
            data: reasonsSorted.map(d => d.Count),
            backgroundColor: ['#f43f5e', '#fb7185', '#f97316', '#fbbf24', '#a855f7', '#06b6d4'].reverse(),
            borderRadius: 7
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { color: gridColor } },
            y: { grid: { display: false } }
          }
        }
      });
    }

    // Small Segment Charts
    // Contract
    const ctxContract = document.getElementById('contractChart');
    if (ctxContract && appData.segments?.byContract) {
      chartInstances.contract = new Chart(ctxContract, {
        type: 'bar',
        data: {
          labels: appData.segments.byContract.map(d => d.ContractType),
          datasets: [{
            data: appData.segments.byContract.map(d => d.ChurnRatePct),
            backgroundColor: ['#10b981', '#f43f5e'],
            borderRadius: 8
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            y: { max: 70, ticks: { callback: v => `${v}%` }, grid: { color: gridColor } },
            x: { grid: { display: false } }
          }
        }
      });
    }

    // Plan
    const ctxPlan = document.getElementById('planChart');
    if (ctxPlan && appData.segments?.byPlan) {
      chartInstances.plan = new Chart(ctxPlan, {
        type: 'bar',
        data: {
          labels: appData.segments.byPlan.map(d => d.PlanTier),
          datasets: [{
            data: appData.segments.byPlan.map(d => d.ChurnRatePct),
            backgroundColor: ['#06b6d4', '#6366f1', '#a855f7'],
            borderRadius: 8
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            y: { max: 60, ticks: { callback: v => `${v}%` }, grid: { color: gridColor } },
            x: { grid: { display: false } }
          }
        }
      });
    }

    // Onboarding
    const ctxOnboarding = document.getElementById('onboardingChart');
    if (ctxOnboarding && appData.segments?.byOnboarding) {
      chartInstances.onboarding = new Chart(ctxOnboarding, {
        type: 'bar',
        data: {
          labels: ['Completed', 'Incomplete'],
          datasets: [{
            data: appData.segments.byOnboarding.map(d => d.ChurnRatePct),
            backgroundColor: ['#10b981', '#f43f5e'],
            borderRadius: 8
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            y: { max: 80, ticks: { callback: v => `${v}%` }, grid: { color: gridColor } },
            x: { grid: { display: false } }
          }
        }
      });
    }
  }

  // 5. Interactive What-If Churn Simulator & ROI Calculator
  function initSimulator() {
    const sOnboard = document.getElementById('sliderOnboard');
    const sAnnual = document.getElementById('sliderAnnual');
    const sSupport = document.getElementById('sliderSupport');
    const sDunning = document.getElementById('sliderDunning');
    const resetBtn = document.getElementById('resetSimulatorBtn');

    function calculateImpact() {
      const vOnboard = parseInt(sOnboard.value, 10);
      const vAnnual = parseInt(sAnnual.value, 10);
      const vSupport = parseInt(sSupport.value, 10);
      const vDunning = parseInt(sDunning.value, 10);

      document.getElementById('valOnboard').textContent = `+${vOnboard}%`;
      document.getElementById('valAnnual').textContent = `+${vAnnual}%`;
      document.getElementById('valSupport').textContent = `-${vSupport} hrs`;
      document.getElementById('valDunning').textContent = `${vDunning}% Recovery`;

      // Base metrics
      const baseChurn = 38.7;
      const totalCust = 5000;
      const avgMRR = 89.93;

      // Sensitivity weights:
      // +10% onboarding -> ~1.6% churn reduction
      // +10% annual -> ~2.2% churn reduction
      // -10hr support -> ~1.2% churn reduction
      // Dunning -> up to 0.9% churn reduction
      const deltaOnboard = (vOnboard / 10) * 1.6;
      const deltaAnnual = (vAnnual / 10) * 2.2;
      const deltaSupport = (vSupport / 10) * 1.2;
      const deltaDunning = (vDunning / 100) * 0.9;

      const totalReduction = Math.min(18.0, deltaOnboard + deltaAnnual + deltaSupport + deltaDunning);
      const newChurn = Math.max(12.0, baseChurn - totalReduction);
      const savedAccounts = Math.round((totalReduction / 100) * totalCust);
      const savedMRR = savedAccounts * avgMRR;
      const savedARR = savedMRR * 12;

      // Lifetime extension
      const oldLifetime = 1.0 / (baseChurn / 100);
      const newLifetime = 1.0 / (newChurn / 100);
      const deltaMonths = Math.max(0.2, (newLifetime - oldLifetime) * 0.4);

      // DOM Updates
      document.getElementById('chipSimEffect').textContent = `Target: -${totalReduction.toFixed(1)}% Churn`;
      document.getElementById('simArrSaved').textContent = `$${Math.round(savedARR).toLocaleString()}`;
      document.getElementById('simNewChurn').textContent = `${newChurn.toFixed(1)}%`;
      document.getElementById('simAccountsSaved').textContent = `${savedAccounts.toLocaleString()} Accounts`;
      document.getElementById('simLifetimeExt').textContent = `+${deltaMonths.toFixed(1)} Months`;

      // 3-Year Table
      const y1 = savedARR;
      const y2 = savedARR * 2.1;
      const y3 = savedARR * 3.31;
      const cacSaved1 = savedAccounts * 600;

      document.getElementById('simY1ARR').textContent = `$${Math.round(y1).toLocaleString()}`;
      document.getElementById('simY1Cash').textContent = `$${Math.round(y1).toLocaleString()}`;
      document.getElementById('simY1CAC').textContent = `$${Math.round(cacSaved1).toLocaleString()}`;

      document.getElementById('simY2ARR').textContent = `$${Math.round(y2).toLocaleString()}`;
      document.getElementById('simY2Cash').textContent = `$${Math.round(y1 + y2).toLocaleString()}`;
      document.getElementById('simY2CAC').textContent = `$${Math.round(cacSaved1 * 2.1).toLocaleString()}`;

      document.getElementById('simY3ARR').textContent = `$${Math.round(y3).toLocaleString()}`;
      document.getElementById('simY3Cash').textContent = `$${Math.round(y1 + y2 + y3).toLocaleString()}`;
      document.getElementById('simY3CAC').textContent = `$${Math.round(cacSaved1 * 3.31).toLocaleString()}`;
    }

    [sOnboard, sAnnual, sSupport, sDunning].forEach(slider => {
      slider.addEventListener('input', calculateImpact);
    });

    resetBtn.addEventListener('click', () => {
      sOnboard.value = 15;
      sAnnual.value = 20;
      sSupport.value = 12;
      sDunning.value = 75;
      calculateImpact();
    });

    calculateImpact();
  }

  // 6. Watchlist & Account Explorer
  function initWatchlist() {
    if (!appData || !appData.sampleCustomers) return;
    filteredCustomers = [...appData.sampleCustomers];

    const searchInput = document.getElementById('custSearchInput');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');

    searchInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase().trim();
      filteredCustomers = appData.sampleCustomers.filter(c => 
        c.CustomerName.toLowerCase().includes(q) || c.CustomerID.toLowerCase().includes(q)
      );
      currentWatchlistPage = 1;
      renderWatchlistTable();
    });

    prevBtn.addEventListener('click', () => {
      if (currentWatchlistPage > 1) {
        currentWatchlistPage--;
        renderWatchlistTable();
      }
    });

    nextBtn.addEventListener('click', () => {
      const maxPages = Math.ceil(filteredCustomers.length / rowsPerPage);
      if (currentWatchlistPage < maxPages) {
        currentWatchlistPage++;
        renderWatchlistTable();
      }
    });

    renderWatchlistTable();
  }

  function renderWatchlistTable() {
    const tbody = document.getElementById('customerTableBody');
    const info = document.getElementById('paginationInfo');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');

    tbody.innerHTML = '';
    const total = filteredCustomers.length;
    const maxPages = Math.max(1, Math.ceil(total / rowsPerPage));
    const startIdx = (currentWatchlistPage - 1) * rowsPerPage;
    const endIdx = Math.min(total, startIdx + rowsPerPage);

    const slice = filteredCustomers.slice(startIdx, endIdx);

    slice.forEach(c => {
      const tr = document.createElement('tr');

      const isHighRisk = c.ChurnRiskScore >= 70;
      const isMedRisk = c.ChurnRiskScore >= 40 && c.ChurnRiskScore < 70;
      const riskClass = isHighRisk ? 'risk-high' : (isMedRisk ? 'risk-med' : 'risk-low');
      const playbook = isHighRisk 
        ? '🚨 Executive CSM Intervention' 
        : (c.ContractType === 'Month-to-Month' ? '🎁 Offer Annual Upgrade Discount' : '📘 Feature Adoption Nurture');

      tr.innerHTML = `
        <td style="font-family:'JetBrains Mono', monospace; font-weight:600;">${c.CustomerID}</td>
        <td><strong>${c.CustomerName}</strong></td>
        <td>${c.PlanTier}</td>
        <td>${c.ContractType}</td>
        <td>${c.OnboardingCompleted === 'Yes' ? '<span class="highlight-pos">Completed</span>' : '<span class="highlight-neg">Incomplete</span>'}</td>
        <td><strong>${c.FeatureAdoptionScore}</strong> / 100</td>
        <td><strong>$${c.MonthlyRecurringRevenue.toFixed(2)}</strong></td>
        <td>${c.TenureMonths} mos</td>
        <td><span class="risk-badge ${riskClass}">${c.ChurnRiskScore}%</span></td>
        <td>${c.ChurnStatus === 1 ? '<span class="risk-badge risk-high">Churned</span>' : '<span class="risk-badge risk-low">Active</span>'}</td>
        <td style="font-size:0.78rem;">${playbook}</td>
      `;
      tbody.appendChild(tr);
    });

    info.textContent = `Showing ${total === 0 ? 0 : startIdx + 1} to ${endIdx} of ${total} accounts`;
    prevBtn.disabled = currentWatchlistPage <= 1;
    nextBtn.disabled = currentWatchlistPage >= maxPages;
  }

  // 7. General Event Listeners (Tabs, Theme, Export, Filters)
  function setupEventListeners() {
    // Tab switching
    const tabTitles = {
      'tab-cohorts': 'Cohort Decay Matrix',
      'tab-survival': 'Customer Lifetime & Survival Analysis',
      'tab-drivers': 'Retention Drivers & Pareto Churn Analysis',
      'tab-simulator': 'What-If Retention & ARR ROI Simulator',
      'tab-watchlist': 'High-Risk Customer Early Warning Watchlist',
      'tab-playbook': 'Executive Retention & Churn Reduction Playbook'
    };

    const tabBtns = document.querySelectorAll('.tab-btn');
    const pageTitleDisplay = document.getElementById('pageTitleDisplay');

    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        tabBtns.forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        btn.classList.add('active');
        const targetId = btn.getAttribute('data-tab');
        const targetPane = document.getElementById(targetId);
        if (targetPane) {
          targetPane.classList.add('active');
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        if (pageTitleDisplay && tabTitles[targetId]) {
          pageTitleDisplay.textContent = tabTitles[targetId];
        }

        // Resize charts when revealed
        Object.values(chartInstances).forEach(inst => {
          if (inst && typeof inst.resize === 'function') inst.resize();
        });
      });
    });

    // Theme Toggle
    const themeBtn = document.getElementById('themeToggleBtn');
    themeBtn.addEventListener('click', () => {
      document.body.classList.toggle('theme-light');
      document.body.classList.toggle('theme-dark');
      // Re-init charts with adapted theme colors
      Object.values(chartInstances).forEach(inst => inst.destroy());
      chartInstances = {};
      initCharts();
    });

    // Export CSV
    const exportBtn = document.getElementById('exportCsvBtn');
    exportBtn.addEventListener('click', () => {
      if (!appData || !appData.sampleCustomers) return;
      let csvContent = "data:text/csv;charset=utf-8,";
      csvContent += "CustomerID,CustomerName,PlanTier,ContractType,OnboardingCompleted,FeatureAdoptionScore,MonthlyRecurringRevenue,TenureMonths,ChurnRiskScore,RiskTier,ChurnStatus\n";

      appData.sampleCustomers.forEach(c => {
        csvContent += `"${c.CustomerID}","${c.CustomerName}","${c.PlanTier}","${c.ContractType}","${c.OnboardingCompleted}",${c.FeatureAdoptionScore},${c.MonthlyRecurringRevenue},${c.TenureMonths},${c.ChurnRiskScore},"${c.RiskTier}",${c.ChurnStatus}\n`;
      });

      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", "saas_at_risk_customers_watchlist.csv");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    });

    // Filters (Plan & Contract)
    const planFilter = document.getElementById('planFilter');
    const contractFilter = document.getElementById('contractFilter');

    function applyFilters() {
      const p = planFilter.value;
      const c = contractFilter.value;

      if (!appData || !appData.sampleCustomers) return;

      filteredCustomers = appData.sampleCustomers.filter(item => {
        const matchesPlan = (p === 'All' || item.PlanTier === p);
        const matchesContract = (c === 'All' || item.ContractType === c);
        return matchesPlan && matchesContract;
      });

      currentWatchlistPage = 1;
      renderWatchlistTable();
    }

    planFilter.addEventListener('change', applyFilters);
    contractFilter.addEventListener('change', applyFilters);
  }

  // Run initialization
  initData();
});
