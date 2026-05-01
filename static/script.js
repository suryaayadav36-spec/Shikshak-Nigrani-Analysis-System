document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("studentForm");
  const overlay = document.getElementById("loadingOverlay");

  if (form && overlay) {
    form.addEventListener("submit", function () {
      overlay.classList.remove("hidden");
    });
  }

  const chartContainer = document.getElementById("performanceChart");
  const dashboardData = document.getElementById("dashboardData");

  if (chartContainer && dashboardData) {
    const attendance = parseFloat(dashboardData.dataset.attendance);
    const marks = parseFloat(dashboardData.dataset.marks);
    const assignments = parseFloat(dashboardData.dataset.assignments);
    const studyHours = parseFloat(dashboardData.dataset.study_hours);
    const backlogs = parseFloat(dashboardData.dataset.backlogs);
    const performanceData = [attendance, marks, assignments, studyHours, backlogs * 15];
    const performanceLabels = ["Attendance", "Marks", "Assignments", "Study Hours", "Backlogs x15"];

    new Chart(chartContainer, {
      type: "radar",
      data: {
        labels: performanceLabels,
        datasets: [
          {
            label: "Student Performance Profile",
            data: performanceData,
            backgroundColor: "rgba(108, 99, 255, 0.18)",
            borderColor: "rgba(108, 99, 255, 0.88)",
            pointBackgroundColor: "#6c63ff",
            borderWidth: 2,
          },
        ],
      },
      options: {
        scales: {
          r: {
            angleLines: { color: "rgba(255,255,255,0.12)" },
            grid: { color: "rgba(255,255,255,0.08)" },
            suggestedMin: 0,
            suggestedMax: 100,
            ticks: { backdropColor: "rgba(11, 18, 32, 0.85)", color: "#b5c4e3" },
            pointLabels: { color: "#d7e0f5", font: { size: 12 } },
          },
        },
        plugins: {
          legend: { labels: { color: "#f8fafc" } },
        },
      },
    });

    const riskCanvas = document.getElementById("riskChart");
    if (riskCanvas) {
      const riskScores = [
        Math.max(0, 100 - attendance),
        Math.max(0, 60 - marks),
        Math.max(0, 30 - assignments),
        Math.max(0, 18 - studyHours) * 3,
        backlogs * 12,
      ];
      new Chart(riskCanvas, {
        type: "bar",
        data: {
          labels: ["Attendance", "Marks", "Assignments", "Study Hours", "Backlogs"],
          datasets: [
            {
              label: "Risk indicator",
              data: riskScores,
              backgroundColor: [
                "rgba(231, 76, 60, 0.75)",
                "rgba(241, 196, 15, 0.75)",
                "rgba(52, 152, 219, 0.75)",
                "rgba(46, 204, 113, 0.75)",
                "rgba(155, 89, 182, 0.75)",
              ],
              borderColor: [
                "rgba(231, 76, 60, 1)",
                "rgba(241, 196, 15, 1)",
                "rgba(52, 152, 219, 1)",
                "rgba(46, 204, 113, 1)",
                "rgba(155, 89, 182, 1)",
              ],
              borderWidth: 1,
            },
          ],
        },
        options: {
          scales: {
            x: {
              ticks: { color: "#f8fafc" },
              grid: { display: false },
            },
            y: {
              beginAtZero: true,
              ticks: { color: "#f8fafc" },
              grid: { color: "rgba(255,255,255,0.08)" },
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
