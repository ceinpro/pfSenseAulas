const translations = JSON.parse(document.body.dataset.translations || '{}');
const t = text => translations[text] || text;
const csrf = document.querySelector('meta[name=csrf]').content;
const message = document.getElementById('message');
const refreshButton = document.getElementById('refresh');
let busy = false;
const states = new Map();
const labels = {allowed:t('Internet permitido'),blocked:t('Internet bloqueado'),pending:t('Pendiente de aplicar'),error:t('Revisar regla'),unconfigured:t('Sin configurar')};
function disableButtons() {
  document.querySelectorAll('[data-action]').forEach(button => { button.disabled = true; });
}
async function api(url, options = {}) {
  const response = await fetch(url, options);
  if (response.status === 401) { window.location.assign('/login'); throw new Error(t('Sesión caducada.')); }
  let data;
  try { data = await response.json(); } catch { throw new Error(t('Respuesta inesperada del panel.')); }
  if (!response.ok) throw new Error(data.error || t('No se pudo completar la operación.'));
  return data;
}
async function refresh() {
  disableButtons();
  try {
    const data = await api('/api/status');
    states.clear();
    for (const classroom of data.classrooms) {
      const card = document.querySelector(`[data-id="${classroom.id}"]`);
      const status = card.querySelector('.status');
      status.textContent = labels[classroom.state];
      status.className = `status ${classroom.state}`;
      status.title = classroom.error || '';
      states.set(classroom.id, classroom.state);
      const button = card.querySelector('[data-action]');
      if (button) {
        const confirmed = ['allowed', 'blocked'].includes(classroom.state);
        button.hidden = !confirmed;
        button.disabled = !confirmed;
        if (confirmed) {
          const block = classroom.state === 'allowed';
          button.dataset.action = block ? 'block' : 'allow';
          button.className = block ? 'block' : 'allow';
          button.textContent = block ? t('Bloquear') : t('Permitir');
          button.setAttribute('aria-label', t('{action} Internet en {classroom}').replace('{action}', button.textContent).replace('{classroom}', card.querySelector('h2').textContent));
        }
      }
    }
    message.hidden = data.applied;
    message.textContent = data.applied ? '' : t('Hay cambios pendientes en pfSense. Revísalos y aplícalos desde su interfaz.');
    message.classList.toggle('error', !data.applied);
  } catch (error) {
    states.clear();
    document.querySelectorAll('[data-action]').forEach(button => { button.hidden = true; });
    document.querySelectorAll('[data-configured=yes] .status').forEach(status => {
      status.textContent = t('Sin confirmar'); status.className = 'status error';
    });
    throw error;
  }
}
function showError(error) {
  message.hidden = false;
  message.textContent = error.message;
  message.classList.add('error');
}
async function updateStatus() {
  if (busy) return;
  busy = true; refreshButton.disabled = true;
  try { await refresh(); } catch (error) { showError(error); }
  finally { busy = false; refreshButton.disabled = false; }
}
document.querySelectorAll('[data-action]').forEach(button => button.addEventListener('click', async () => {
  if (busy) return;
  const card = button.closest('.card');
  const id = Number(card.dataset.id);
  const blocked = button.dataset.action === 'block';
  const previous = states.get(id);
  if (!['allowed', 'blocked'].includes(previous)) return;
  busy = true; disableButtons(); refreshButton.disabled = true;
  message.hidden = false;
  message.textContent = t('Aplicando el cambio en pfSense…'); message.classList.remove('error');
  try {
    await api(`/api/classrooms/${id}`, {method:'POST', headers:{'Content-Type':'application/json','X-CSRF-Token':csrf}, body:JSON.stringify({blocked,expected_blocked:previous === 'blocked'})});
    await refresh();
  } catch (error) {
    states.clear();
    document.querySelectorAll('[data-action]').forEach(button => { button.hidden = true; });
    card.querySelector('.status').textContent = t('Sin confirmar');
    card.querySelector('.status').className = 'status error'; showError(error);
  } finally { busy = false; refreshButton.disabled = false; }
}));
refreshButton.addEventListener('click', updateStatus);
updateStatus();
setInterval(() => { if (!document.hidden) updateStatus(); }, 30000);
