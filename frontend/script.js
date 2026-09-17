/* ==========================================================================
   Student Placement Management System - Frontend logic
   Talks to the Flask REST API at API_BASE.
   ========================================================================== */

const API_BASE = "http://127.0.0.1:5000/api";

let state = {
  students: [],
  companies: [],
  placements: [],
};

/* ---------------------------------------------------------------------- */
/* Navigation                                                              */
/* ---------------------------------------------------------------------- */

const views = ["dashboard", "students", "companies", "placements"];

document.querySelectorAll(".nav-item").forEach(btn => {
  btn.addEventListener("click", () => switchView(btn.dataset.view));
});

function switchView(name) {
  views.forEach(v => {
    document.getElementById(`view-${v}`).classList.toggle("hidden", v !== name);
  });
  document.querySelectorAll(".nav-item").forEach(b => {
    b.classList.toggle("active", b.dataset.view === name);
  });
  if (name === "dashboard") loadDashboard();
  if (name === "students") loadStudents();
  if (name === "companies") loadCompanies();
  if (name === "placements") loadPlacements();
}

/* ---------------------------------------------------------------------- */
/* API helper                                                              */
/* ---------------------------------------------------------------------- */

async function api(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  let data = null;
  try { data = await res.json(); } catch (e) { /* no body */ }
  if (!res.ok) {
    const message = (data && data.error) || `Request failed (${res.status})`;
    throw new Error(message);
  }
  return data;
}

async function checkApiStatus() {
  const el = document.getElementById("apiStatus");
  try {
    await api("/dashboard/");
    el.textContent = "API connected";
    el.className = "api-status ok";
  } catch (e) {
    el.textContent = "API unreachable — start the backend";
    el.className = "api-status down";
  }
}

/* ---------------------------------------------------------------------- */
/* Toast notifications                                                     */
/* ---------------------------------------------------------------------- */

let toastTimer;
function showToast(message, type = "") {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.className = `toast ${type}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.add("hidden"), 3200);
}

/* ---------------------------------------------------------------------- */
/* Modal helper                                                            */
/* ---------------------------------------------------------------------- */

const modalOverlay = document.getElementById("modalOverlay");
const modalTitle = document.getElementById("modalTitle");
const modalForm = document.getElementById("modalForm");

document.getElementById("modalClose").addEventListener("click", closeModal);
modalOverlay.addEventListener("click", (e) => { if (e.target === modalOverlay) closeModal(); });

function openModal(title, fieldsHtml, onSubmit) {
  modalTitle.textContent = title;
  modalForm.innerHTML = fieldsHtml + `
    <p class="form-error" id="formError"></p>
    <div class="form-actions">
      <button type="button" class="btn-secondary" id="formCancel">Cancel</button>
      <button type="submit" class="btn-primary" style="margin-top:0;">Save</button>
    </div>
  `;
  modalOverlay.classList.remove("hidden");
  document.getElementById("formCancel").addEventListener("click", closeModal);

  modalForm.onsubmit = async (e) => {
    e.preventDefault();
    const errorEl = document.getElementById("formError");
    errorEl.classList.remove("show");
    try {
      await onSubmit(new FormData(modalForm));
      closeModal();
    } catch (err) {
      errorEl.textContent = err.message;
      errorEl.classList.add("show");
    }
  };

  const firstInput = modalForm.querySelector("input, select");
  if (firstInput) firstInput.focus();
}

function closeModal() {
  modalOverlay.classList.add("hidden");
  modalForm.onsubmit = null;
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !modalOverlay.classList.contains("hidden")) closeModal();
});

/* ---------------------------------------------------------------------- */
/* DASHBOARD                                                                */
/* ---------------------------------------------------------------------- */

async function loadDashboard() {
  try {
    const stats = await api("/dashboard/");
    document.getElementById("statStudents").textContent = stats.total_students;
    document.getElementById("statCompanies").textContent = stats.total_companies;
    document.getElementById("statSelected").textContent = stats.students_selected;
    document.getElementById("statPercent").textContent = `${stats.placement_percentage}%`;
    document.getElementById("statAvgPkg").textContent = stats.average_package_lpa;
    document.getElementById("statHighPkg").textContent = stats.highest_package_lpa;

    const placements = await api("/placements/");
    const tbody = document.querySelector("#recentTable tbody");
    tbody.innerHTML = placements.slice(0, 8).map(p => `
      <tr>
        <td>${escapeHtml(p.student_name || "—")}</td>
        <td>${escapeHtml(p.company_name || "—")}</td>
        <td><span class="pill ${p.status}">${p.status}</span></td>
        <td>${p.package_offered ?? "—"}</td>
        <td>${p.placement_date ?? "—"}</td>
      </tr>
    `).join("") || `<tr><td colspan="5" style="text-align:center;color:var(--text-mute);">No activity yet</td></tr>`;
  } catch (e) {
    showToast(e.message, "error");
  }
}

/* ---------------------------------------------------------------------- */
/* STUDENTS                                                                 */
/* ---------------------------------------------------------------------- */

async function loadStudents() {
  const search = document.getElementById("studentSearch").value.trim();
  const branch = document.getElementById("studentBranchFilter").value;
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (branch) params.set("branch", branch);

  try {
    const students = await api(`/students/?${params.toString()}`);
    state.students = students;
    renderStudentBranchFilter(students);
    renderStudentsTable(students);
  } catch (e) {
    showToast(e.message, "error");
  }
}

function renderStudentBranchFilter(students) {
  const select = document.getElementById("studentBranchFilter");
  const current = select.value;
  const branches = [...new Set(state.students.map(s => s.branch))].sort();
  // Only rebuild options if this is the first load (avoid wiping user selection unexpectedly)
  if (select.dataset.built !== "1") {
    select.innerHTML = `<option value="">All branches</option>` +
      branches.map(b => `<option value="${escapeHtml(b)}">${escapeHtml(b)}</option>`).join("");
    select.dataset.built = "1";
    select.value = current;
  }
}

function renderStudentsTable(students) {
  const tbody = document.querySelector("#studentsTable tbody");
  document.getElementById("studentsEmpty").classList.toggle("hidden", students.length !== 0);
  tbody.innerHTML = students.map(s => `
    <tr>
      <td>${escapeHtml(s.roll_number)}</td>
      <td>${escapeHtml(s.name)}</td>
      <td>${escapeHtml(s.email)}</td>
      <td>${escapeHtml(s.phone || "—")}</td>
      <td>${escapeHtml(s.branch)}</td>
      <td>${s.cgpa}</td>
      <td>
        <div class="cell-actions">
          <button class="btn-link" onclick="editStudent(${s.id})">Edit</button>
          <button class="btn-danger" onclick="deleteStudent(${s.id})">Delete</button>
        </div>
      </td>
    </tr>
  `).join("");
}

document.getElementById("studentSearch").addEventListener("input", debounce(loadStudents, 300));
document.getElementById("studentBranchFilter").addEventListener("change", loadStudents);

document.getElementById("btnAddStudent").addEventListener("click", () => {
  openModal("Add student", studentFormFields(), async (formData) => {
    const payload = Object.fromEntries(formData.entries());
    await api("/students/", { method: "POST", body: JSON.stringify(payload) });
    showToast("Student added", "success");
    loadStudents();
  });
});

function editStudent(id) {
  const student = state.students.find(s => s.id === id);
  if (!student) return;
  openModal("Edit student", studentFormFields(student), async (formData) => {
    const payload = Object.fromEntries(formData.entries());
    await api(`/students/${id}/`, { method: "PUT", body: JSON.stringify(payload) });
    showToast("Student updated", "success");
    loadStudents();
  });
}

async function deleteStudent(id) {
  const student = state.students.find(s => s.id === id);
  if (!confirm(`Delete ${student ? student.name : "this student"}? This also removes their placement records.`)) return;
  try {
    await api(`/students/${id}/`, { method: "DELETE" });
    showToast("Student deleted", "success");
    loadStudents();
  } catch (e) {
    showToast(e.message, "error");
  }
}

function studentFormFields(s = {}) {
  return `
    <div class="field-row">
      <div class="field">
        <label for="f_roll">Roll number</label>
        <input id="f_roll" name="roll_number" value="${escapeHtml(s.roll_number || "")}" required>
      </div>
      <div class="field">
        <label for="f_branch">Branch</label>
        <input id="f_branch" name="branch" value="${escapeHtml(s.branch || "")}" required>
      </div>
    </div>
    <div class="field">
      <label for="f_name">Full name</label>
      <input id="f_name" name="name" value="${escapeHtml(s.name || "")}" required>
    </div>
    <div class="field">
      <label for="f_email">Email</label>
      <input id="f_email" name="email" type="email" value="${escapeHtml(s.email || "")}" required>
    </div>
    <div class="field-row">
      <div class="field">
        <label for="f_phone">Phone</label>
        <input id="f_phone" name="phone" value="${escapeHtml(s.phone || "")}">
      </div>
      <div class="field">
        <label for="f_cgpa">CGPA</label>
        <input id="f_cgpa" name="cgpa" type="number" step="0.01" min="0" max="10" value="${s.cgpa ?? ""}" required>
      </div>
    </div>
  `;
}

/* ---------------------------------------------------------------------- */
/* COMPANIES                                                                */
/* ---------------------------------------------------------------------- */

async function loadCompanies() {
  const search = document.getElementById("companySearch").value.trim();
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  try {
    const companies = await api(`/companies/?${params.toString()}`);
    state.companies = companies;
    renderCompaniesTable(companies);
  } catch (e) {
    showToast(e.message, "error");
  }
}

function renderCompaniesTable(companies) {
  const tbody = document.querySelector("#companiesTable tbody");
  document.getElementById("companiesEmpty").classList.toggle("hidden", companies.length !== 0);
  tbody.innerHTML = companies.map(c => `
    <tr>
      <td>${escapeHtml(c.name)}</td>
      <td>${escapeHtml(c.role)}</td>
      <td>${c.package_lpa}</td>
      <td>${c.eligibility_cgpa}</td>
      <td>${c.drive_date || "—"}</td>
      <td>
        <div class="cell-actions">
          <button class="btn-link" onclick="editCompany(${c.id})">Edit</button>
          <button class="btn-danger" onclick="deleteCompany(${c.id})">Delete</button>
        </div>
      </td>
    </tr>
  `).join("");
}

document.getElementById("companySearch").addEventListener("input", debounce(loadCompanies, 300));

document.getElementById("btnAddCompany").addEventListener("click", () => {
  openModal("Add company", companyFormFields(), async (formData) => {
    const payload = Object.fromEntries(formData.entries());
    await api("/companies/", { method: "POST", body: JSON.stringify(payload) });
    showToast("Company added", "success");
    loadCompanies();
  });
});

function editCompany(id) {
  const company = state.companies.find(c => c.id === id);
  if (!company) return;
  openModal("Edit company", companyFormFields(company), async (formData) => {
    const payload = Object.fromEntries(formData.entries());
    await api(`/companies/${id}/`, { method: "PUT", body: JSON.stringify(payload) });
    showToast("Company updated", "success");
    loadCompanies();
  });
}

async function deleteCompany(id) {
  const company = state.companies.find(c => c.id === id);
  if (!confirm(`Delete ${company ? company.name : "this company"}? This also removes related placement records.`)) return;
  try {
    await api(`/companies/${id}/`, { method: "DELETE" });
    showToast("Company deleted", "success");
    loadCompanies();
  } catch (e) {
    showToast(e.message, "error");
  }
}

function companyFormFields(c = {}) {
  return `
    <div class="field">
      <label for="f_cname">Company name</label>
      <input id="f_cname" name="name" value="${escapeHtml(c.name || "")}" required>
    </div>
    <div class="field">
      <label for="f_crole">Role offered</label>
      <input id="f_crole" name="role" value="${escapeHtml(c.role || "")}" required>
    </div>
    <div class="field-row">
      <div class="field">
        <label for="f_cpkg">Package (LPA)</label>
        <input id="f_cpkg" name="package_lpa" type="number" step="0.1" min="0" value="${c.package_lpa ?? ""}" required>
      </div>
      <div class="field">
        <label for="f_ccgpa">Minimum CGPA</label>
        <input id="f_ccgpa" name="eligibility_cgpa" type="number" step="0.01" min="0" max="10" value="${c.eligibility_cgpa ?? ""}">
      </div>
    </div>
    <div class="field">
      <label for="f_cdate">Drive date</label>
      <input id="f_cdate" name="drive_date" type="date" value="${c.drive_date || ""}">
    </div>
  `;
}

/* ---------------------------------------------------------------------- */
/* PLACEMENTS                                                               */
/* ---------------------------------------------------------------------- */

async function loadPlacements() {
  const status = document.getElementById("placementStatusFilter").value;
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  try {
    const [placements, students, companies] = await Promise.all([
      api(`/placements/?${params.toString()}`),
      state.students.length ? Promise.resolve(state.students) : api("/students/"),
      state.companies.length ? Promise.resolve(state.companies) : api("/companies/"),
    ]);
    state.placements = placements;
    state.students = students;
    state.companies = companies;
    renderPlacementsTable(placements);
  } catch (e) {
    showToast(e.message, "error");
  }
}

function renderPlacementsTable(placements) {
  const tbody = document.querySelector("#placementsTable tbody");
  document.getElementById("placementsEmpty").classList.toggle("hidden", placements.length !== 0);
  tbody.innerHTML = placements.map(p => `
    <tr>
      <td>${escapeHtml(p.student_name || "—")}</td>
      <td>${escapeHtml(p.company_name || "—")}</td>
      <td><span class="pill ${p.status}">${p.status}</span></td>
      <td>${p.package_offered ?? "—"}</td>
      <td>${p.placement_date ?? "—"}</td>
      <td>
        <div class="cell-actions">
          <button class="btn-link" onclick="editPlacement(${p.id})">Edit</button>
          <button class="btn-danger" onclick="deletePlacement(${p.id})">Delete</button>
        </div>
      </td>
    </tr>
  `).join("");
}

document.getElementById("placementStatusFilter").addEventListener("change", loadPlacements);

document.getElementById("btnAddPlacement").addEventListener("click", async () => {
  if (!state.students.length) state.students = await api("/students/");
  if (!state.companies.length) state.companies = await api("/companies/");
  openModal("Log application", placementFormFields(), async (formData) => {
    const payload = Object.fromEntries(formData.entries());
    await api("/placements/", { method: "POST", body: JSON.stringify(payload) });
    showToast("Application logged", "success");
    loadPlacements();
  });
});

function editPlacement(id) {
  const placement = state.placements.find(p => p.id === id);
  if (!placement) return;
  openModal("Edit application", placementFormFields(placement), async (formData) => {
    const payload = Object.fromEntries(formData.entries());
    await api(`/placements/${id}/`, { method: "PUT", body: JSON.stringify(payload) });
    showToast("Application updated", "success");
    loadPlacements();
  });
}

async function deletePlacement(id) {
  if (!confirm("Delete this placement record?")) return;
  try {
    await api(`/placements/${id}/`, { method: "DELETE" });
    showToast("Record deleted", "success");
    loadPlacements();
  } catch (e) {
    showToast(e.message, "error");
  }
}

function placementFormFields(p = {}) {
  const studentOptions = state.students.map(s =>
    `<option value="${s.id}" ${p.student_id === s.id ? "selected" : ""}>${escapeHtml(s.name)} (${escapeHtml(s.roll_number)})</option>`
  ).join("");
  const companyOptions = state.companies.map(c =>
    `<option value="${c.id}" ${p.company_id === c.id ? "selected" : ""}>${escapeHtml(c.name)}</option>`
  ).join("");
  const statuses = ["Applied", "Shortlisted", "Selected", "Rejected"];
  const statusOptions = statuses.map(s =>
    `<option value="${s}" ${p.status === s ? "selected" : ""}>${s}</option>`
  ).join("");

  return `
    <div class="field">
      <label for="f_pstudent">Student</label>
      <select id="f_pstudent" name="student_id" required>
        <option value="" disabled ${!p.student_id ? "selected" : ""}>Select a student</option>
        ${studentOptions}
      </select>
    </div>
    <div class="field">
      <label for="f_pcompany">Company</label>
      <select id="f_pcompany" name="company_id" required>
        <option value="" disabled ${!p.company_id ? "selected" : ""}>Select a company</option>
        ${companyOptions}
      </select>
    </div>
    <div class="field">
      <label for="f_pstatus">Status</label>
      <select id="f_pstatus" name="status">${statusOptions}</select>
    </div>
    <div class="field-row">
      <div class="field">
        <label for="f_ppkg">Package offered (LPA)</label>
        <input id="f_ppkg" name="package_offered" type="number" step="0.1" min="0" value="${p.package_offered ?? ""}">
      </div>
      <div class="field">
        <label for="f_pdate">Placement date</label>
        <input id="f_pdate" name="placement_date" type="date" value="${p.placement_date || ""}">
      </div>
    </div>
  `;
}

/* ---------------------------------------------------------------------- */
/* Utilities                                                                */
/* ---------------------------------------------------------------------- */

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function debounce(fn, delay) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

/* ---------------------------------------------------------------------- */
/* Init                                                                     */
/* ---------------------------------------------------------------------- */

checkApiStatus();
loadDashboard();
