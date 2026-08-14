// ============================================================
// 学情分析 Tab — 智能诊断学习问题
// ============================================================
(function initAnalysis() {
    var queryEl = document.getElementById("analysis-query");
    var courseEl = document.getElementById("analysis-course");
    var startBtn = document.getElementById("analysis-start");
    var statusEl = document.getElementById("analysis-status");
    var statusText = document.getElementById("analysis-status-text");
    var reportEl = document.getElementById("analysis-report");
    // resultEl 兼容: 如果 HTML 中没有独立的结果容器, 就直接用 reportEl
    var resultEl = document.getElementById("analysis-result") || reportEl;
    if (!startBtn) return;

    // 快捷预设按钮
    document.querySelectorAll(".analysis-preset").forEach(function(btn) {
        btn.addEventListener("click", function() {
            if (queryEl) queryEl.value = btn.dataset.text || "";
            if (queryEl) queryEl.focus();
        });
    });

    startBtn.addEventListener("click", function() {
        var query = (queryEl && queryEl.value || "").trim();
        if (!query) { alert("请描述你的学习困扰"); return; }

        var _resultArea = document.getElementById("analysis-result");
        // 结果区: 优先用 analysis-result, 没有则复用 reportEl
        if (!_resultArea) _resultArea = reportEl;
        _resultArea.innerHTML = "";
        reportEl.innerHTML = '<div class="text-slate-400 italic">多智能体分析中...</div>';
        if (statusEl) statusEl.classList.remove("hidden");
        if (statusText) statusText.textContent = "多智能体分析中...";

        var courseName = (courseEl && courseEl.value || "").trim();
        fetch(API + "/education/learn", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                query: "【学情分析请求】" + query,
                course: courseName,
                mode: "comprehensive"
            })
        }).then(function(resp) {
            var reader = resp.body.getReader();
            var decoder = new TextDecoder();
            var buffer = "";
            function pump() {
                return reader.read().then(function(chunk) {
                    if (chunk.done) { if (statusEl) statusEl.classList.add("hidden"); return; }
                    buffer += decoder.decode(chunk.value, { stream: true });
                    var lines = buffer.split("\n");
                    buffer = lines.pop() || "";
                    lines.forEach(function(line) {
                        if (line.indexOf("data: ") !== 0) return;
                        try {
                            var evt = JSON.parse(line.slice(6));
                            if (evt.type === "status") { if (statusText) statusText.textContent = evt.content; }
                            else if (evt.type === "agent_output") {
                                var card = document.createElement("div");
                                card.className = "edu-agent-output";
                                card.setAttribute("data-agent", evt.agent || "");
                                var formatted = (typeof formatAgentContent === "function")
                                    ? formatAgentContent(evt.content)
                                    : (typeof evt.content === "string" ? evt.content.slice(0, 500) : JSON.stringify(evt.content || {}).slice(0, 500));
                                card.innerHTML = '<div class="agent-label" style="font-weight:600;color:var(--primary);margin-bottom:4px;">' + (evt.label || "") + '</div><div style="font-size:13px;color:var(--text-primary);line-height:1.6;max-height:400px;overflow-y:auto;">' + formatted + '</div>';
                                _resultArea.appendChild(card);
                            } else if (evt.type === "report") {
                                reportEl.innerHTML = (typeof fmtMarkdown === "function") ? fmtMarkdown(evt.content || "") : (evt.content || "").replace(/\\n/g, '<br>');
                            }
                        } catch(e) {}
                    });
                    return pump();
                });
            }
            return pump();
        }).catch(function(e) {
            reportEl.innerHTML = '<div class="text-red-500">分析失败: ' + escapeHtml(e.message) + '</div>';
            if (statusEl) statusEl.classList.add("hidden");
        });
    });
})();

// ============================================================
// 学习记录 Tab — 学习活动时间线
// ============================================================
(function initRecords() {
    var listEl = document.getElementById("rec-list");
    var daysEl = document.getElementById("rec-days");
    var coursesEl = document.getElementById("rec-courses");
    var completedEl = document.getElementById("rec-completed");
    var weeklyEl = document.getElementById("rec-weekly-h");

    function load() {
        // 从课程和日历 API 聚合学习记录
        Promise.all([
            fetch(API + "/courses").then(function(r) { return r.json(); }).catch(function() { return {data:{courses:[]}}; }),
            fetch(API + "/calendar?year=2026").then(function(r) { return r.json(); }).catch(function() { return {data:{events:[]}}; })
        ]).then(function(results) {
            var courses = (results[0] && results[0].data && results[0].data.courses) || [];
            var events = (results[1] && results[1].data && results[1].data.events) || [];

            // 统计
            var completedCourses = courses.filter(function(c) { return (c.progress || 0) >= 100; }).length;
            var totalProgress = courses.reduce(function(s, c) { return s + (c.progress || 0); }, 0);
            var avgProgress = courses.length ? Math.round(totalProgress / courses.length) : 0;
            var studyEvents = events.filter(function(e) { return e.event_type === "study" || e.event_type === "exam" || e.event_type === "review"; });
            var uniqueDays = new Set(events.map(function(e) { return e.date; })).size;
            var weeklyEstimate = studyEvents.reduce(function(s, e) { return s + (e.duration_minutes || 45); }, 0);

            if (daysEl) daysEl.textContent = String(uniqueDays);
            if (coursesEl) coursesEl.textContent = String(courses.length);
            if (completedEl) completedEl.textContent = String(completedCourses);
            if (weeklyEl) weeklyEl.textContent = (weeklyEstimate / 60).toFixed(1) + "h";

            if (!listEl) return;
            if (!courses.length && !events.length) {
                listEl.innerHTML = '<div class="text-slate-400 italic text-center py-8">还没有学习记录<br>去「智能导学」开始你的第一次学习吧！</div>';
                return;
            }

            // 合并课程和事件为学习时间线
            var timeline = [];
            courses.forEach(function(c) {
                timeline.push({ type: "course", title: "📚 " + (c.name || ""), detail: "进度 " + (c.progress || 0) + "% · GPA " + (c.gpa || "-"), time: c.created_at || "", color: "var(--agent-knowledge)" });
            });
            events.forEach(function(e) {
                var icon = e.event_type === "exam" ? "📝" : (e.event_type === "review" ? "🔄" : "📖");
                timeline.push({ type: "event", title: icon + " " + (e.title || ""), detail: (e.date || "") + " · " + (e.duration_minutes || 45) + "分钟", time: e.created_at || "", color: e.event_type === "exam" ? "var(--edu-accent)" : "var(--st-success)" });
            });
            timeline.sort(function(a, b) { return (b.time || "").localeCompare(a.time || ""); });

            listEl.innerHTML = timeline.slice(0, 50).map(function(item) {
                return '<div class="border-l-2 pl-3 py-2" style="border-color:' + item.color + '"><div class="font-medium text-sm">' + escapeHtml(item.title) + '</div><div class="text-xs" style="color:var(--text-muted)">' + escapeHtml(item.detail) + '</div></div>';
            }).join("");
        });
    }

    var refreshBtn = document.getElementById("rec-refresh");
    if (refreshBtn) refreshBtn.addEventListener("click", load);
    document.querySelector('[data-tab="records"]') && document.querySelector('[data-tab="records"]').addEventListener("click", function() { setTimeout(load, 100); });
})();

// fmtMarkdown 复用主 app.js 中的定义 (全局函数), 不重复声明
// formatAgentContent 也来自 app.js
