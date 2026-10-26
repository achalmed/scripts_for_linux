// tests/plugin_registro_tiempo.test.mjs — el plugin de Super Productivity contra un PluginAPI simulado (lo corre
// test_registro_tiempo.py). Super Productivity ejecuta plugin.js con `new Function("plugin", "PluginAPI", código)`;
// aquí se hace igual, con temporizadores apagados para que la prueba no espere.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const codigo = readFileSync(fileURLToPath(new URL('../script_registro_tiempo/plugin-sp/plugin.js', import.meta.url)), 'utf8');

function simulador() {
  let n = 0;
  const id = () => `id${++n}`;
  const s = { proyectos: [{ id: 'B', title: 'Bloomberg', isArchived: false, taskIds: ['x'] },
    { id: 'I', title: 'Aprenizaje de idiomas', isArchived: false, taskIds: [] }], etiquetas: [], tareas: [], archivadas: [], llamadas: [] };
  const api = {
    async getAllProjects() { return s.proyectos.map((p) => ({ ...p })); },
    async addProject(p) { const nuevo = { id: id(), isArchived: false, taskIds: [], ...p }; s.proyectos.push(nuevo); return nuevo.id; },
    async updateProject(pid, cambios) { Object.assign(s.proyectos.find((p) => p.id === pid), cambios); s.llamadas.push(['updateProject', pid, cambios]); },
    async getAllTags() { return s.etiquetas.map((t) => ({ ...t })); },
    async addTag(t) { s.etiquetas.push({ id: id(), ...t }); },
    async getTasks() { return s.tareas.map((t) => ({ ...t, timeSpentOnDay: { ...(t.timeSpentOnDay || {}) } })); },
    async getArchivedTasks() { return s.archivadas.map((t) => ({ ...t })); },
    async addTask(t) { const nueva = { id: id(), timeSpentOnDay: {}, ...t }; s.tareas.push(nueva); return nueva.id; },
    async updateTask(tid, cambios) { Object.assign(s.tareas.find((t) => t.id === tid), cambios); s.llamadas.push(['updateTask', tid, cambios]); },
    showSnack() {},
    async persistDataSynced(d) { s.guardado = d; },
    async loadSyncedData() { return s.guardado || null; },
    onMessage(fn) { s.manejador = fn; },
  };
  return { s, api };
}

const { s, api } = simulador();
const [st, si] = [globalThis.setTimeout, globalThis.setInterval];
globalThis.setTimeout = () => 0;
globalThis.setInterval = () => 0;
new Function('plugin', 'PluginAPI', codigo)({}, api);
globalThis.setTimeout = st;
globalThis.setInterval = si;
const enviar = (type) => s.manejador({ type });

// 1. Sin tarea portadora: no escribe y lo dice.
let r = await enviar('importar');
assert.equal(r.ok, false);
const proyecto = s.proyectos.find((p) => p.title === 'Registro automático');
assert.ok(proyecto, 'crea el proyecto aunque aún no haya datos');

// 2. Con portadora en la bandeja: la mueve, crea la tarea y fija el tiempo por día.
const datos = {
  version: 1, generado: '2026-10-25T10:00:00-05:00', proyecto: 'Registro automático',
  tareas: { 'Lectura en KOReader': { '2026-10-20': 600000, '2026-10-24': 1800000 } },
  estructura: { renombrar: { 'Aprenizaje de idiomas': 'Inglés' },
    proyectos: [{ titulo: 'Tesis' }, { titulo: 'Registro automático' }, { titulo: 'Inglés' }],
    etiquetas: [{ titulo: 'lectura' }], archivar: ['Bloomberg', 'No existe'] },
};
s.tareas.push({ id: 'portadora', title: 'Datos del registro de tiempo', notes: 'texto\n```json\n' + JSON.stringify(datos) + '\n```' });
s.archivadas.push({ id: 'vieja', title: 'Lectura en KOReader', projectId: proyecto.id, timeSpentOnDay: { '2026-10-20': 999 } });
r = await enviar('importar');
assert.equal(r.ok, true);
assert.deepEqual([r.creadas, r.actualizadas], [1, 1]);
assert.equal(s.tareas.find((t) => t.id === 'portadora').projectId, proyecto.id);
const lectura = s.tareas.find((t) => t.title === 'Lectura en KOReader');
assert.deepEqual(lectura.timeSpentOnDay, { '2026-10-24': 1800000 }, 'el día ya archivado no se vuelve a escribir');
assert.equal(lectura.timeSpent, 1800000);

// 3. Segunda pasada con los mismos datos: idempotente.
const antes = s.llamadas.length;
r = await enviar('importar');
assert.deepEqual([r.creadas, r.actualizadas], [0, 0]);
assert.equal(s.llamadas.length, antes);

// 4. Estructura: primero la vista, luego aplicar; archiva sin borrar.
const vista = await enviar('vistaEstructura');
assert.deepEqual(vista.renombrar.map((p) => p.a), ['Inglés']);
assert.deepEqual(vista.crearProyectos.map((p) => p.titulo), ['Tesis'], 'lo que se renombra no se crea otra vez');
assert.deepEqual(vista.crearEtiquetas.map((t) => t.titulo), ['lectura']);
assert.deepEqual(vista.archivar.map((p) => p.titulo), ['Bloomberg']);
assert.deepEqual(vista.noEncontrados, ['No existe']);
r = await enviar('aplicarEstructura');
assert.deepEqual([r.renombrados, r.proyectos, r.etiquetas, r.archivados], [1, 1, 1, 1]);
assert.equal(s.proyectos.find((p) => p.id === 'B').isArchived, true);
assert.equal(s.proyectos.find((p) => p.id === 'I').title, 'Inglés');
assert.equal((await enviar('vistaEstructura')).crearProyectos.length, 0);

// 5. El estado guardado lo lee el panel.
assert.ok((await enviar('estado')).ultimaImportacion);

// 6. Con `aplicar_estructura`, la importación aplica la estructura sola, una vez por huella.
const portadora = s.tareas.find((t) => t.id === 'portadora');
const nueva = { ...datos, estructura_id: 'h1', aplicar_estructura: true,
  estructura: { proyectos: [{ titulo: 'Cursos CAF' }], etiquetas: [], archivar: [] } };
portadora.notes = '```json\n' + JSON.stringify(nueva) + '\n```';
r = await enviar('importar');
assert.equal(r.estructura.proyectos, 1);
assert.ok(s.proyectos.some((p) => p.title === 'Cursos CAF'));
r = await enviar('importar');
assert.equal(r.estructura, null, 'la misma huella no se aplica otra vez');

// 7. Restaurar: los archivados no salen en getAllProjects; se encuentran por getAppState y vuelven a activos.
s.proyectos.find((p) => p.id === 'B').isArchived = true;
api.getAllProjects = async () => s.proyectos.filter((p) => !p.isArchived).map((p) => ({ ...p }));
// la forma real de SP 18.10: {tasks, projects, tags, ...}, cada uno {id: entidad}
api.getAppState = async () => ({ tasks: {}, projects: Object.fromEntries(s.proyectos.map((p) => [p.id, { ...p }])), tags: {} });
portadora.notes = '```json\n' + JSON.stringify({ ...nueva, estructura_id: 'h2',
  estructura: { restaurar: ['Bloomberg'], archivar: [], proyectos: [{ titulo: 'Bloomberg' }] } }) + '\n```';
r = await enviar('importar');
assert.equal(r.estructura.restaurados, 1);
assert.equal(r.estructura.proyectos, 0, 'lo que se restaura no se crea de nuevo');
assert.equal(s.proyectos.find((p) => p.id === 'B').isArchived, false);
console.log('plugin: 7 escenarios correctos');
