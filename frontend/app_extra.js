// ============================================================
// Toast 通知系统
// ============================================================
(function initToast() {
    if (!document.getElementById("toast-container")) return;
    window.Toast = {
        _container: document.getElementById("toast-container"),
        show: function(title, message, type, duration) {
            type = type || "info"; duration = duration || 4000;
            var el = document.createElement("div");
            el.className = "toast toast-" + type;
            el.innerHTML = '<div class="toast-body"><div class="toast-title">' + escapeHtml(title) + '</div>' +
                (message ? '<div class="text-xs" style="color:var(--text-muted)">' + escapeHtml(message) + '</div>' : '') +
                '</div><button class="toast-close">&times;</button>';
            var close = function() { el.classList.add("toast-out"); setTimeout(function() { el.remove(); }, 300); };
            el.querySelector(".toast-close").addEventListener("click", close);
            this._container.appendChild(el);
            if (duration > 0) setTimeout(close, duration);
            return el;
        },
        success: function(m) { this.show("完成", m, "success", 3000); },
        error: function(m) { this.show("错误", m, "error", 6000); },
        warn: function(m) { this.show("注意", m, "warning", 4000); },
        info: function(m) { this.show("提示", m, "info", 3000); }
    };
    window._origAlert = window.alert;
    window.alert = function(m) { window.Toast.show("提示", String(m), "info", 4000); };
})();

// ============================================================
// 我的课程 Tab — API 集成
// ============================================================
(function initCourses() {
    var addBtn = document.getElementById("courses-add-btn");
    var listEl = document.getElementById("courses-list");
    var courses = [];

    function load() {
        fetch(API + "/courses").then(function(r) { return r.json(); }).then(function(d) {
            courses = (d && d.data && d.data.courses) || [];
            render();
        }).catch(function(e) {
            if (listEl) listEl.innerHTML = '<div class="text-red-500 text-sm col-span-full">加载失败</div>';
        });
    }

    function render() {
        if (!listEl) return;
        if (!courses.length) {
            listEl.innerHTML = '<div class="col-span-full text-center py-16" style="color:var(--text-muted)"><div style="font-size:40px;margin-bottom:12px">📚</div><p>还没有课程</p><p class="text-xs mt-1">点击右上角「+ 添加课程」开始</p></div>';
            return;
        }
        listEl.innerHTML = courses.map(function(c) {
            var badgeCls = c.category === '必修' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700';
            var progressPct = c.progress || 0;
            return '<div class="edu-card p-5"><div class="flex justify-between items-start mb-3"><div><h4 class="font-semibold text-base">' + escapeHtml(c.name) + '</h4><p class="text-xs mt-0.5" style="color:var(--text-muted)">' + escapeHtml(c.college || '') + ' · ' + escapeHtml(c.schedule || '待定') + '</p></div><span class="px-2 py-0.5 text-xs rounded-full ' + badgeCls + '">' + escapeHtml(c.category || '必修') + '</span></div>' +
                '<div class="mb-2"><div class="flex justify-between text-xs mb-1"><span style="color:var(--text-muted)">学习进度</span><span class="font-semibold">' + progressPct + '%</span></div><div class="h-1.5 bg-slate-200 rounded-full overflow-hidden"><div class="h-full rounded-full transition-all" style="width:' + progressPct + '%;background:var(--edu-accent)"></div></div></div>' +
                '<div class="flex items-center gap-4 text-xs mt-3" style="color:var(--text-muted)"><span>📝 作业: ' + (c.assignments_done || 0) + '/' + (c.assignments_total || 0) + '</span><span>🎯 GPA: ' + (c.gpa || '-') + '</span><span>🎓 ' + (c.credits || 3) + '学分</span></div>' +
                '<div class="flex gap-2 mt-3"><button class="btn-cstudy px-3 py-1.5 text-xs text-white rounded-full font-medium" style="background:var(--edu-accent)" data-course="' + escapeHtml(c.name) + '">继续学习</button><button class="btn-cedit px-3 py-1.5 text-xs border rounded-full hover:bg-slate-50" data-id="' + c.id + '" data-name="' + escapeHtml(c.name) + '">编辑</button><button class="btn-cdel px-3 py-1.5 text-xs border rounded-full hover:bg-rose-50 text-rose-500" data-id="' + c.id + '">删除</button></div></div>';
        }).join("");

        listEl.querySelectorAll(".btn-cstudy").forEach(function(b) { b.addEventListener("click", function() {
            document.querySelector('[data-tab="education"]').click();
            var ec = document.getElementById("edu-course");
            if (ec) ec.value = b.dataset.course;
        });});
        listEl.querySelectorAll(".btn-cedit").forEach(function(b) { b.addEventListener("click", function() {
            var nn = prompt("课程名称", b.dataset.name);
            if (!nn) return;
            fetch(API + "/courses/" + b.dataset.id, { method: "PUT", headers: {"Content-Type":"application/json"}, body: JSON.stringify({name: nn}) }).then(load);
        });});
        listEl.querySelectorAll(".btn-cdel").forEach(function(b) { b.addEventListener("click", function() {
            if (!confirm("确定要删除？")) return;
            fetch(API + "/courses/" + b.dataset.id, { method: "DELETE" }).then(load);
        });});
    }

    if (addBtn) addBtn.addEventListener("click", function() {
        var name = prompt("课程名称", "");
        if (!name) return;
        fetch(API + "/courses", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({name: name, college: "计算机学院", schedule: "待定", credits: 3}) }).then(function() { Toast.success("课程已添加"); load(); });
    });
    document.querySelector('[data-tab="courses"]').addEventListener("click", function() { setTimeout(load, 100); });
})();

// ============================================================
// 学习日历 Tab — API 集成 (适配新 HTML ID)
// ============================================================
(function initCalendar() {
    var calGrid = document.getElementById("cal-grid");
    var monthLabel = document.getElementById("cal-month-label");
    var prevBtn = document.getElementById("cal-prev");
    var nextBtn = document.getElementById("cal-next");
    var todayEvents = document.getElementById("cal-today-events");
    var eventCount = document.getElementById("cal-event-count");
    var examCount = document.getElementById("cal-exam-count");
    var hoursEl = document.getElementById("cal-hours");
    var currentYear = 2026, currentMonth = 7, events = [];

    if (prevBtn) prevBtn.addEventListener("click", function() { currentMonth--; if (currentMonth < 1) { currentMonth = 12; currentYear--; } loadEv(); });
    if (nextBtn) nextBtn.addEventListener("click", function() { currentMonth++; if (currentMonth > 12) { currentMonth = 1; currentYear++; } loadEv(); });

    function loadEv() {
        fetch(API + "/calendar?year=" + currentYear + "&month=" + currentMonth).then(function(r) { return r.json(); }).then(function(d) {
            events = (d && d.data && d.data.events) || [];
            renderCal();
        }).catch(function() { renderCal(); });
    }

    function renderCal() {
        if (!calGrid || !monthLabel) return;
        monthLabel.textContent = currentYear + "年" + currentMonth + "月";
        var firstDay = new Date(currentYear, currentMonth - 1, 1);
        var totalDays = new Date(currentYear, currentMonth, 0).getDate();
        var startDow = (firstDay.getDay() + 6) % 7;
        var today = new Date();
        var todayStr = today.getFullYear() + "-" + String(today.getMonth() + 1).padStart(2,"0") + "-" + String(today.getDate()).padStart(2,"0");
        var html = "";

        for (var i = 0; i < startDow; i++) html += '<div class="h-16 border rounded p-1.5 text-xs opacity-30" style="background:var(--surface-alt)"></div>';
        for (var d = 1; d <= totalDays; d++) {
            var ds = currentYear + "-" + String(currentMonth).padStart(2,"0") + "-" + String(d).padStart(2,"0");
            var dayEvs = events.filter(function(e) { return e.date === ds; });
            var isToday = ds === todayStr;
            var isWeekend = (startDow + d - 1) % 7 >= 5;
            var bg = isToday ? 'style="background:var(--edu-warm);border:2px solid var(--edu-accent)"' : (isWeekend ? 'style="background:var(--surface-alt)"' : '');
            html += '<div class="h-16 border rounded p-1.5 text-xs cursor-pointer hover:shadow-sm transition" ' + bg + ' data-date="' + ds + '"><div class="font-semibold ' + (isToday ? 'text-rose-500' : '') + '">' + d + '</div>' +
                dayEvs.slice(0, 2).map(function(e) {
                    var dot = e.event_type === 'exam' ? '🔴' : (e.event_type === 'review' ? '🟡' : '🟢');
                    return '<div class="text-[10px] truncate leading-tight">' + dot + ' ' + escapeHtml(e.title).slice(0, 6) + '</div>';
                }).join("") + (dayEvs.length > 2 ? '<div class="text-[10px]" style="color:var(--text-muted)">+' + (dayEvs.length - 2) + '</div>' : '') + '</div>';
        }
        calGrid.innerHTML = html;

        // 统计
        var exams = events.filter(function(e) { return e.event_type === 'exam'; });
        var totalMin = events.reduce(function(s, e) { return s + (e.duration_minutes || 45); }, 0);
        if (eventCount) eventCount.textContent = String(events.length);
        if (examCount) examCount.textContent = String(exams.length);
        if (hoursEl) hoursEl.textContent = (totalMin / 60).toFixed(1) + "h";

        // 今日待办
        var todayEvs = events.filter(function(e) { return e.date === todayStr; });
        if (todayEvents) {
            todayEvents.innerHTML = todayEvs.length ? todayEvs.map(function(e) {
                return '<div class="flex items-center gap-2 p-2 rounded text-xs" style="background:var(--surface-alt)"><span>' + (e.event_type === 'exam' ? '📝' : '📖') + '</span><span>' + escapeHtml(e.title) + '</span><span class="ml-auto" style="color:var(--text-muted)">' + (e.duration_minutes || 45) + 'min</span></div>';
            }).join("") : '<p class="text-xs" style="color:var(--text-muted)">今天没有学习安排</p>';
        }

        // 点击日期添加事件
        calGrid.querySelectorAll("[data-date]").forEach(function(cell) { cell.addEventListener("click", function() {
            var ds = cell.dataset.date;
            var title = prompt("事件名称 (如: 机器学习复习)", "");
            if (!title) return;
            fetch(API + "/calendar", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({title: title, date: ds, event_type: "study", duration_minutes: 45}) }).then(loadEv);
        });});
    }
    document.querySelector('[data-tab="calendar"]').addEventListener("click", function() { setTimeout(loadEv, 100); });
})();

// ============================================================
// 同学协作 Tab — API 集成 (适配新 HTML ID)
// ============================================================
(function initCollab() {
    var discContainer = document.getElementById("disc-list");
    var postBtn = document.getElementById("collab-post-btn");

    function loadDisc() {
        fetch(API + "/collaboration/discussions").then(function(r) { return r.json(); }).then(function(d) {
            var discs = (d && d.data && d.data.discussions) || [];
            if (!discContainer) return;
            if (!discs.length) {
                discContainer.innerHTML = '<div class="text-center py-16" style="color:var(--text-muted)"><div style="font-size:40px;margin-bottom:12px">💬</div><p>暂无讨论</p><p class="text-xs mt-1">点击「+ 发起讨论」发布第一条</p></div>';
                return;
            }
            discContainer.innerHTML = discs.map(function(dd) {
                return '<div class="edu-card p-4"><div class="flex items-center gap-2 mb-2"><div class="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-xs font-bold text-white">' + escapeHtml((dd.author || "匿")[0]) + '</div><span class="text-sm font-medium">' + escapeHtml(dd.author) + '</span><span class="text-xs" style="color:var(--text-muted)">' + (dd.created_at || "").slice(0, 16) + '</span>' + (dd.topic_tag ? '<span class="text-xs px-2 py-0.5 rounded-full" style="background:var(--edu-warm);color:var(--edu-accent)">' + escapeHtml(dd.topic_tag) + '</span>' : '') + '</div><p class="text-sm leading-relaxed">' + escapeHtml(dd.content) + '</p><div class="flex gap-3 mt-2 text-xs" style="color:var(--text-muted)"><button>💬 ' + (dd.replies || 0) + '</button><button>👍 ' + (dd.likes || 0) + '</button></div></div>';
            }).join("");
        }).catch(function() {});
    }

    if (postBtn) postBtn.addEventListener("click", function() {
        var content = prompt("讨论内容", "");
        if (!content) return;
        fetch(API + "/collaboration/discussions", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({author: "同学", content: content, topic_tag: "学习讨论"}) }).then(function() { Toast.success("已发布"); loadDisc(); });
    });
    document.querySelector('[data-tab="collab"]').addEventListener("click", function() { setTimeout(loadDisc, 100); });
})();
