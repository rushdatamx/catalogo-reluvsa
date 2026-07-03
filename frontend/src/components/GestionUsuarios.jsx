import React, { useState, useEffect, useCallback } from 'react';
import { Users, UserPlus, X, KeyRound, Power, Loader2, ShoppingBag, CheckCircle } from 'lucide-react';
import { getUsuarios, crearUsuario, actualizarUsuario } from '../services/api';
import { cn } from '../lib/utils';

const FORM_VACIO = { username: '', password: '', nombre_empresa: '', contacto: '' };

/**
 * Modal de gestión de usuarios de proveedores (solo admin).
 * Alta de usuarios, activar/desactivar (soft delete) y reset de contraseña.
 * Los usuarios viven en pedidos.db (backend), no en variables de entorno.
 */
export default function GestionUsuarios({ abierto, onClose }) {
  const [usuarios, setUsuarios] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [exito, setExito] = useState('');

  // Formulario de alta
  const [mostrarForm, setMostrarForm] = useState(false);
  const [form, setForm] = useState(FORM_VACIO);
  const [guardando, setGuardando] = useState(false);

  // Reset de contraseña inline (username del row activo)
  const [resetUsername, setResetUsername] = useState(null);
  const [resetPassword, setResetPassword] = useState('');

  const cargarUsuarios = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await getUsuarios();
      setUsuarios(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error cargando usuarios');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (abierto) {
      cargarUsuarios();
      setExito('');
      setError('');
    }
  }, [abierto, cargarUsuarios]);

  // Cerrar con ESC
  useEffect(() => {
    if (!abierto) return;
    const handler = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [abierto, onClose]);

  if (!abierto) return null;

  const handleCrear = async (e) => {
    e.preventDefault();
    setGuardando(true);
    setError('');
    setExito('');
    try {
      await crearUsuario({
        username: form.username.trim(),
        password: form.password,
        nombre_empresa: form.nombre_empresa.trim(),
        contacto: form.contacto.trim() || null,
      });
      setExito(`Usuario "${form.username.trim()}" creado. Compártele sus credenciales al proveedor.`);
      setForm(FORM_VACIO);
      setMostrarForm(false);
      cargarUsuarios();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error creando el usuario');
    } finally {
      setGuardando(false);
    }
  };

  const handleToggleActivo = async (u) => {
    setError('');
    setExito('');
    try {
      await actualizarUsuario(u.username, { activo: !u.activo });
      setExito(u.activo
        ? `"${u.username}" desactivado: ya no puede iniciar sesión.`
        : `"${u.username}" reactivado.`);
      cargarUsuarios();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error actualizando el usuario');
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError('');
    setExito('');
    try {
      await actualizarUsuario(resetUsername, { password: resetPassword });
      setExito(`Contraseña de "${resetUsername}" actualizada. Compártela al proveedor.`);
      setResetUsername(null);
      setResetPassword('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error actualizando la contraseña');
    }
  };

  const inputClase = 'w-full px-3 py-2 border border-notion-border rounded-lg text-sm focus:outline-none focus:border-reluvsa-yellow';

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Gestión de usuarios"
        className="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-notion-border p-6 flex items-center justify-between z-10">
          <div className="flex items-center gap-3">
            <Users size={22} />
            <div>
              <h2 className="text-xl font-semibold text-notion-text-primary">Usuarios de proveedores</h2>
              <p className="text-sm text-notion-text-secondary">
                Acceso al catálogo completo. Los pedidos quedan ligados a cada usuario.
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-notion-bg-subtle rounded-lg transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="p-6 space-y-4">
          {/* Mensajes */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-300 rounded-lg text-red-600 text-sm font-medium">
              {error}
            </div>
          )}
          {exito && (
            <div className="p-3 bg-green-50 border border-green-300 rounded-lg text-green-700 text-sm font-medium flex items-center gap-2">
              <CheckCircle size={16} className="flex-shrink-0" />
              {exito}
            </div>
          )}

          {/* Botón / formulario de alta */}
          {!mostrarForm ? (
            <button
              onClick={() => { setMostrarForm(true); setExito(''); }}
              className="flex items-center gap-2 bg-reluvsa-black text-reluvsa-yellow px-4 py-2.5 rounded-lg font-semibold hover:bg-gray-800 transition-colors"
            >
              <UserPlus size={18} />
              Nuevo usuario
            </button>
          ) : (
            <form onSubmit={handleCrear} className="bg-notion-bg-subtle rounded-xl p-4 space-y-3">
              <h3 className="font-semibold text-notion-text-primary flex items-center gap-2">
                <UserPlus size={18} />
                Nuevo usuario de proveedor
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-notion-text-secondary mb-1 block">Usuario *</label>
                  <input
                    type="text"
                    value={form.username}
                    onChange={(e) => setForm({ ...form, username: e.target.value })}
                    placeholder="ej: refaccionaria-lopez"
                    className={inputClase}
                    required
                    minLength={3}
                  />
                </div>
                <div>
                  <label className="text-xs text-notion-text-secondary mb-1 block">Contraseña * (mín. 6)</label>
                  <input
                    type="text"
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                    placeholder="Asígnala y compártela al proveedor"
                    className={inputClase}
                    required
                    minLength={6}
                  />
                </div>
                <div>
                  <label className="text-xs text-notion-text-secondary mb-1 block">Empresa *</label>
                  <input
                    type="text"
                    value={form.nombre_empresa}
                    onChange={(e) => setForm({ ...form, nombre_empresa: e.target.value })}
                    placeholder="ej: Refaccionaria López SA de CV"
                    className={inputClase}
                    required
                  />
                </div>
                <div>
                  <label className="text-xs text-notion-text-secondary mb-1 block">Contacto (opcional)</label>
                  <input
                    type="text"
                    value={form.contacto}
                    onChange={(e) => setForm({ ...form, contacto: e.target.value })}
                    placeholder="Nombre, teléfono o correo"
                    className={inputClase}
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={guardando}
                  className="flex items-center gap-2 bg-reluvsa-black text-reluvsa-yellow px-4 py-2 rounded-lg font-semibold hover:bg-gray-800 disabled:opacity-50 transition-colors"
                >
                  {guardando ? <Loader2 size={16} className="animate-spin" /> : <UserPlus size={16} />}
                  Crear usuario
                </button>
                <button
                  type="button"
                  onClick={() => { setMostrarForm(false); setForm(FORM_VACIO); }}
                  className="px-4 py-2 rounded-lg font-medium text-notion-text-secondary hover:bg-notion-bg-subtle border border-notion-border transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </form>
          )}

          {/* Lista de usuarios */}
          {loading ? (
            <div className="p-8 text-center">
              <div className="w-8 h-8 border-2 border-reluvsa-yellow border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p className="mt-4 text-notion-text-secondary text-sm">Cargando usuarios...</p>
            </div>
          ) : usuarios.length === 0 ? (
            <div className="p-8 text-center text-notion-text-secondary text-sm">
              Aún no hay usuarios de proveedores. Crea el primero con "Nuevo usuario".
            </div>
          ) : (
            <div className="space-y-2">
              {usuarios.map((u) => (
                <div
                  key={u.username}
                  className={cn(
                    'border border-notion-border rounded-xl p-4',
                    !u.activo && 'opacity-60 bg-notion-bg-subtle'
                  )}
                >
                  <div className="flex items-start justify-between gap-3 flex-wrap">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-semibold text-notion-text-primary">
                          {u.nombre_empresa || u.username}
                        </span>
                        <code className="text-xs bg-notion-bg-subtle px-2 py-0.5 rounded font-mono">
                          {u.username}
                        </code>
                        <span
                          className={cn(
                            'text-xs px-2 py-0.5 rounded-full font-medium',
                            u.activo ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-600'
                          )}
                        >
                          {u.activo ? 'Activo' : 'Desactivado'}
                        </span>
                      </div>
                      <div className="text-xs text-notion-text-secondary mt-1 flex items-center gap-3 flex-wrap">
                        {u.contacto && <span>{u.contacto}</span>}
                        <span className="flex items-center gap-1">
                          <ShoppingBag size={12} />
                          {u.total_pedidos} pedido{u.total_pedidos === 1 ? '' : 's'}
                        </span>
                        {u.last_login && <span>Último acceso: {u.last_login}</span>}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <button
                        onClick={() => {
                          setResetUsername(resetUsername === u.username ? null : u.username);
                          setResetPassword('');
                        }}
                        className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg border border-notion-border hover:bg-notion-bg-subtle font-medium transition-colors"
                        title="Cambiar contraseña"
                      >
                        <KeyRound size={14} />
                        Contraseña
                      </button>
                      <button
                        onClick={() => handleToggleActivo(u)}
                        className={cn(
                          'flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg font-medium transition-colors',
                          u.activo
                            ? 'border border-red-300 text-red-600 hover:bg-red-50'
                            : 'border border-green-300 text-green-700 hover:bg-green-50'
                        )}
                        title={u.activo ? 'Desactivar acceso' : 'Reactivar acceso'}
                      >
                        <Power size={14} />
                        {u.activo ? 'Desactivar' : 'Reactivar'}
                      </button>
                    </div>
                  </div>

                  {/* Reset de contraseña inline */}
                  {resetUsername === u.username && (
                    <form onSubmit={handleResetPassword} className="mt-3 flex gap-2 items-center">
                      <input
                        type="text"
                        value={resetPassword}
                        onChange={(e) => setResetPassword(e.target.value)}
                        placeholder="Nueva contraseña (mín. 6)"
                        className={cn(inputClase, 'max-w-xs')}
                        required
                        minLength={6}
                        autoFocus
                      />
                      <button
                        type="submit"
                        className="bg-reluvsa-black text-reluvsa-yellow px-3 py-2 rounded-lg text-sm font-semibold hover:bg-gray-800 transition-colors"
                      >
                        Guardar
                      </button>
                    </form>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
