// plugin-sp/plugin.js — plugin «Registro de tiempo» para Super Productivity (18.10 o posterior).
//
// Qué hace: lee la tarea portadora que deja la suite script_registro_tiempo por la API REST local de SP (sus notas
// llevan un bloque JSON) y escribe, por tarea y por día, el tiempo de lo que pasa fuera de SP (KOReader, Zotero,
// categorías de ActivityWatch) en el proyecto «Registro automático». Desde su panel muestra y aplica la estructura
// propuesta (proyectos y etiquetas que faltan, proyectos que se archivan).
//
// Por qué así: en la 18.10 un plugin subido a mano no puede ejecutar Node (solo los incluidos de fábrica) y la API
// REST no escribe tiempo por día; los dos juntos sí, cada uno con su API oficial. Escribir es idempotente: el tiempo
// de un día se fija (no se suma) y un día que ya está en una tarea archivada no se vuelve a escribir.

const VERSION = '1.1.1';
const PROYECTO = 'Registro automático';
const PORTADORA = 'Datos del registro de tiempo';
const CADA_MS = 10 * 60 * 1000;

const igual = (a, b) => (a || '').trim().toLowerCase() === (b || '').trim().toLowerCase();

function leerPortadora(tarea) {
  const notas = (tarea && tarea.notes) || '';
  const ini = notas.indexOf('{');
  const fin = notas.lastIndexOf('}');
  if (ini < 0 || fin <= ini) throw new Error('la tarea portadora no tiene un bloque JSON');
  const datos = JSON.parse(notas.slice(ini, fin + 1));
  if (datos.version !== 1 || typeof datos.tareas !== 'object') throw new Error('versión de datos no reconocida');
  return datos;
}

async function asegurarProyecto() {
  const proyectos = await PluginAPI.getAllProjects();
  const hallado = proyectos.find((p) => igual(p.title, PROYECTO) && !p.isArchived);
  if (hallado) return hallado.id;
  const creado = await PluginAPI.addProject({ title: PROYECTO });
  if (typeof creado === 'string') return creado;
  if (creado && creado.id) return creado.id;
  const otra = (await PluginAPI.getAllProjects()).find((p) => igual(p.title, PROYECTO));
  if (!otra) throw new Error('no se pudo crear el proyecto ' + PROYECTO);
  return otra.id;
}

// Fija el tiempo por día de cada tarea del proyecto; devuelve un resumen.
async function importar() {
  const proyectoId = await asegurarProyecto();
  const activas = await PluginAPI.getTasks();
  const portadora = activas.find((t) => igual(t.title, PORTADORA));
  if (!portadora) {
    return { ok: false, mensaje: 'aún no hay datos: corre «main.py recoger --aplicar» con Super Productivity abierto' };
  }
  if (portadora.projectId !== proyectoId) {
    await PluginAPI.updateTask(portadora.id, { projectId: proyectoId });
  }
  const datos = leerPortadora(portadora);
  const archivadas = (await PluginAPI.getArchivedTasks()).filter((t) => t.projectId === proyectoId);
  let creadas = 0;
  let actualizadas = 0;
  for (const [titulo, dias] of Object.entries(datos.tareas)) {
    const cerrados = new Set();
    archivadas.filter((t) => igual(t.title, titulo)).forEach((t) => Object.keys(t.timeSpentOnDay || {}).forEach((d) => cerrados.add(d)));
    let tarea = activas.find((t) => igual(t.title, titulo) && t.projectId === proyectoId && !t.parentId);
    if (!tarea) {
      const id = await PluginAPI.addTask({ title: titulo, projectId: proyectoId,
        notes: 'Tiempo medido fuera de Super Productivity; lo escribe el plugin «Registro de tiempo». No lo cronometres.' });
      tarea = { id, timeSpentOnDay: {} };
      creadas += 1;
    }
    const previo = tarea.timeSpentOnDay || {};
    const nuevo = { ...previo };
    for (const [dia, ms] of Object.entries(dias)) {
      if (!cerrados.has(dia) && Number.isFinite(ms) && ms >= 0) nuevo[dia] = Math.round(ms);
    }
    const cambia = Object.keys(nuevo).some((d) => nuevo[d] !== previo[d]);
    if (cambia) {
      const total = Object.values(nuevo).reduce((a, b) => a + b, 0);
      await PluginAPI.updateTask(tarea.id, { timeSpentOnDay: nuevo, timeSpent: total });
      actualizadas += 1;
    }
  }
  const guardado = JSON.parse((await PluginAPI.loadSyncedData()) || '{}');
  let estructura = null;
  if (datos.aplicar_estructura && datos.estructura_id && guardado.estructuraAplicada !== datos.estructura_id) {
    estructura = await aplicarEstructura();   // el autor la pidió con `aplicar: true` en registro-tiempo.yml
  }
  const resumen = { ok: true, generado: datos.generado, tareas: Object.keys(datos.tareas).length, creadas, actualizadas, estructura };
  await PluginAPI.persistDataSynced(JSON.stringify({
    ...guardado, ultimaImportacion: new Date().toISOString(), ...resumen,
    ...(estructura && estructura.ok ? { estructuraAplicada: datos.estructura_id } : {}),
  }));
  return resumen;
}

// getAllProjects no devuelve los archivados; el estado completo sí (para poder restaurarlos). En SP 18.10,
// getAppState devuelve {tasks, projects, tags, notes, taskRepeatCfgs, simpleCounters, globalConfig}, cada uno {id: entidad}.
async function todosLosProyectos() {
  try {
    const estado = await PluginAPI.getAppState();
    const entidades = estado && (estado.projects || (estado.project && estado.project.entities));
    if (entidades) return Object.values(entidades);
  } catch (error) {
    // sin getAppState (otra versión de SP): solo los activos
  }
  return PluginAPI.getAllProjects();
}

// Lo que falta crear, lo que se restaura y lo que se archivaría según la estructura propuesta (sin escribir).
async function vistaEstructura() {
  const portadora = (await PluginAPI.getTasks()).find((t) => igual(t.title, PORTADORA));
  if (!portadora) return { ok: false, mensaje: 'aún no hay datos de la suite' };
  const e = leerPortadora(portadora).estructura || {};
  const todos = await todosLosProyectos();
  const restaurar = todos.filter((p) => p.isArchived && (e.restaurar || []).some((r) => igual(r, p.title)))
    .map((p) => ({ id: p.id, titulo: p.title }));
  const proyectos = todos.filter((p) => !p.isArchived);
  const etiquetas = await PluginAPI.getAllTags();
  const renombrar = Object.entries(e.renombrar || {})
    .map(([de, a]) => ({ p: proyectos.find((x) => igual(x.title, de) && !x.isArchived), de, a }))
    .filter((r) => r.p && !proyectos.some((x) => igual(x.title, r.a) && !x.isArchived))
    .map((r) => ({ id: r.p.id, de: r.de, a: r.a }));
  const nombresTrasRenombrar = proyectos.map((x) => renombrar.find((r) => r.id === x.id)?.a || x.title);
  const vivos = [...nombresTrasRenombrar, ...restaurar.map((r) => r.titulo)];
  const sinHallar = (e.restaurar || []).filter((r) => !todos.some((p) => igual(p.title, r)));
  return {
    ok: true,
    version: VERSION,
    sinHallar,
    restaurar,
    renombrar,
    crearProyectos: (e.proyectos || []).filter((p) => !vivos.some((n) => igual(n, p.titulo))),
    crearEtiquetas: (e.etiquetas || []).filter((t) => !etiquetas.some((x) => igual(x.title, t.titulo))),
    archivar: proyectos.filter((p) => !p.isArchived && (e.archivar || []).some((a) => igual(a, p.title)))
      .map((p) => ({ id: p.id, titulo: p.title, tareas: (p.taskIds || []).length })),
    noEncontrados: (e.archivar || []).filter((a) => !proyectos.some((p) => igual(p.title, a))),
  };
}

async function aplicarEstructura() {
  const vista = await vistaEstructura();
  if (!vista.ok) return vista;
  for (const r of vista.restaurar) await PluginAPI.updateProject(r.id, { isArchived: false });
  for (const r of vista.renombrar) await PluginAPI.updateProject(r.id, { title: r.a });
  for (const p of vista.crearProyectos) await PluginAPI.addProject({ title: p.titulo });
  for (const t of vista.crearEtiquetas) await PluginAPI.addTag({ title: t.titulo, ...(t.color ? { color: t.color } : {}) });
  for (const p of vista.archivar) await PluginAPI.updateProject(p.id, { isArchived: true });
  return { ok: true, restaurados: vista.restaurar.length, renombrados: vista.renombrar.length, proyectos: vista.crearProyectos.length,
    etiquetas: vista.crearEtiquetas.length, archivados: vista.archivar.length };
}

async function importarAvisando(silencioso) {
  try {
    const r = await importar();
    if (!r.ok) {
      if (!silencioso) PluginAPI.showSnack({ msg: 'Registro de tiempo: ' + r.mensaje, type: 'CUSTOM' });
    } else if (r.creadas || r.actualizadas || r.estructura || !silencioso) {
      const e = r.estructura && r.estructura.ok
        ? ` · estructura: ${r.estructura.restaurados} restaurados, ${r.estructura.proyectos} proyectos y ${r.estructura.etiquetas} etiquetas creados, ${r.estructura.archivados} archivados`
        : '';
      PluginAPI.showSnack({ msg: `Registro de tiempo: ${r.actualizadas} tareas al día (${r.creadas} nuevas)${e}`, type: 'SUCCESS' });
    }
    return r;
  } catch (error) {
    PluginAPI.showSnack({ msg: 'Registro de tiempo: ' + error.message, type: 'ERROR' });
    return { ok: false, mensaje: error.message };
  }
}

PluginAPI.onMessage(async (mensaje) => {
  switch (mensaje && mensaje.type) {
    case 'importar': return importarAvisando(false);
    case 'vistaEstructura': return vistaEstructura();
    case 'aplicarEstructura': return aplicarEstructura();
    case 'estado': {
      const guardado = await PluginAPI.loadSyncedData();
      return { ok: true, ...(guardado ? JSON.parse(guardado) : {}), version: VERSION };
    }
    default: return { ok: false, mensaje: 'mensaje desconocido' };
  }
});

setTimeout(() => importarAvisando(true), 15000);   // tras el arranque, cuando los datos de SP ya cargaron
setInterval(() => importarAvisando(true), CADA_MS);
