const loader = document.getElementById('loader');
const showLoader = () => loader && loader.classList.remove('hidden');
const hideLoader = () => loader && loader.classList.add('hidden');

async function api(url, method = 'GET', body = null) {
  showLoader();
  try {
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : null,
    });
    return await res.json();
  } finally { hideLoader(); }
}

// Students
async function loadStudents() {
  const q = document.getElementById('studentSearch')?.value || '';
  const rows = await api(`/api/students?q=${encodeURIComponent(q)}`);
  const table = document.getElementById('studentsTable');
  if (!table) return;
  table.innerHTML = '<tr><th>ID</th><th>Name</th><th>Class</th><th>Roll</th><th>Phone</th><th>Email</th><th>Parent</th><th>Actions</th></tr>' +
    rows.map(s => `<tr><td>${s.id||''}</td><td>${s.name||''}</td><td>${s.class||''}</td><td>${s.roll||''}</td><td>${s.phone||''}</td><td>${s.email||''}</td><td>${s.parent||''}</td>
      <td><button onclick="editStudent('${s.id}')">Edit</button> <button onclick="deleteStudent('${s.id}')">Delete</button></td></tr>`).join('');
}


async function editStudent(id) {
  const name = prompt('New name:');
  if (!name) return;
  await api(`/api/students/${id}`, 'PUT', { name });
  loadStudents();
}

async function deleteStudent(id) { await api(`/api/students/${id}`, 'DELETE'); loadStudents(); }

const studentForm = document.getElementById('studentForm');
if (studentForm) {
  loadStudents();
  studentForm.addEventListener('submit', async e => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(studentForm).entries());
    await api('/api/students', 'POST', data);
    studentForm.reset();
    loadStudents();
  });
}

// Attendance
async function loadAttendanceStudents() {
  const students = await api('/api/students');
  const wrap = document.getElementById('attendanceList');
  if (!wrap) return;
  wrap.innerHTML = students.map(s => `<div class="toolbar mt-10"><span>${s.name} (${s.id})</span>
    <select data-id="${s.id}"><option value="Present">Present</option><option value="Absent">Absent</option></select></div>`).join('');
}

async function saveAttendance() {
  const selects = document.querySelectorAll('#attendanceList select');
  const date = new Date().toISOString().slice(0, 10);
  const rows = Array.from(selects).map(el => [date, el.getAttribute('data-id'), el.value]);
  await api('/api/attendance', 'POST', { rows });
  alert('Attendance saved');
}

// Videos
const videoForm = document.getElementById('videoForm');
if (videoForm) {
  loadVideos();
  videoForm.addEventListener('submit', async e => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(videoForm).entries());
    await api('/api/videos', 'POST', data);
    videoForm.reset();
    loadVideos();
  });
}

async function loadVideos() {
  const rows = await api('/api/videos');
  const el = document.getElementById('videoList');
  if (!el) return;
  const today = new Date().toISOString().slice(0, 10);
  const html = rows.map(v => `<div class='card mt-10'><b>${v.date || ''}</b> - ${v.subject || ''}<br/><a href='${v.drive_link}' target='_blank'>Open video</a>${v.date===today?' <span class="muted">(Today)</span>':''}</div>`).join('');
  el.innerHTML = html || '<p class="muted">No videos added yet.</p>';
}

// Subjects
async function addSubject() {
  const name = document.getElementById('subjectName').value;
  if (!name) return;
  await api('/api/subjects', 'POST', { subject_name: name });
  document.getElementById('subjectName').value = '';
  loadSubjects();
}

async function loadSubjects() {
  const rows = await api('/api/subjects');
  const el = document.getElementById('subjectList');
  if (!el) return;
  el.innerHTML = rows.map(s => `<div class='toolbar mt-10'><span>${s.subject_name || ''}</span><button onclick="removeSubject('${s.subject_name}')">Delete</button></div>`).join('');
}

async function removeSubject(name) { await api('/api/subjects', 'DELETE', { subject_name: name }); loadSubjects(); }
if (document.getElementById('subjectList')) loadSubjects();

// Announcements
async function saveAnnouncement() {
  const message = document.getElementById('announcementText').value;
  if (!message) return;
  await api('/api/announcements', 'POST', { message });
  document.getElementById('announcementText').value = '';
  loadAnnouncements();
}

async function loadAnnouncements() {
  const rows = await api('/api/announcements');
  const el = document.getElementById('announcementList');
  if (!el) return;
  el.innerHTML = rows.map(a => `<div class='card mt-10'><b>${a.date || ''}</b><p>${a.message || ''}</p></div>`).join('');
}
if (document.getElementById('announcementList')) loadAnnouncements();

async function generateAnnouncement() {
  const topic = document.getElementById('announcementText').value || 'Holiday tomorrow';
  const res = await api('/api/ai/announcement-generator', 'POST', { topic });
  document.getElementById('announcementText').value = res.answer;
}

// AI Tools
async function aiAttendanceAnalysis() {
  const res = await api('/api/ai/attendance-analysis', 'POST', {});
  document.getElementById('attendanceAnalysis').innerText = res.answer;
}
async function aiVideoSummary() {
  const topic = document.getElementById('videoTopic').value;
  const res = await api('/api/ai/video-summary', 'POST', { topic });
  document.getElementById('videoSummary').innerText = res.answer;
}
async function aiQuizGenerator() {
  const subject = document.getElementById('quizSubject').value;
  const topic = document.getElementById('quizTopic').value;
  const res = await api('/api/ai/quiz-generator', 'POST', { subject, topic });
  document.getElementById('quizOutput').innerText = res.answer;
}
async function aiDoubtSolver() {
  const question = document.getElementById('doubtQuestion').value;
  const res = await api('/api/ai/doubt-solver', 'POST', { question });
  document.getElementById('doubtOutput').innerText = res.answer;
}

// Student chatbot
function appendChat(role, text) {
  const win = document.getElementById('chatWindow');
  if (!win) return;
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  div.textContent = text;
  win.appendChild(div);
  win.scrollTop = win.scrollHeight;
}
async function sendChat() {
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text) return;
  appendChat('user', text);
  input.value = '';
  const res = await api('/api/ai/chatbot', 'POST', { message: text });
  appendChat('ai', res.answer);
}

async function loadMyAttendance() {
  const sid = document.getElementById('studentAttendanceId').value;
  const rows = await api(`/api/attendance?student_id=${encodeURIComponent(sid)}`);
  const el = document.getElementById('attendanceTable');
  if (!el) return;
  el.innerHTML = '<table><tr><th>Date</th><th>Student ID</th><th>Status</th></tr>' + rows.map(r => `<tr><td>${r.date||''}</td><td>${r.student_id||''}</td><td>${r.status||''}</td></tr>`).join('') + '</table>';
}

if (document.getElementById('videoList')) loadVideos();
