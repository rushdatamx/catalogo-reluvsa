import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await api.post('/auth/login', { username, password });
      login(res.data.token, {
        username: res.data.username,
        role: res.data.role
      });
    } catch (err) {
      setError('Usuario o contraseña incorrectos');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-reluvsa-yellow">
      <div className="bg-white p-8 rounded-xl shadow-xl w-full max-w-md border-2 border-reluvsa-black">
        {/* Logo RELUVSA */}
        <div className="text-center mb-8">
          <img
            src="/reluvsa-logo.png"
            alt="RELUVSA Autopartes"
            className="h-16 mx-auto mb-4"
          />
          <p className="text-reluvsa-black font-medium">Catálogo de Autopartes</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-semibold text-reluvsa-black mb-2">
              Usuario
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-reluvsa-yellow focus:border-reluvsa-black transition-all"
              placeholder="Ingresa tu usuario"
              required
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-semibold text-reluvsa-black mb-2">
              Contraseña
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-reluvsa-yellow focus:border-reluvsa-black transition-all"
              placeholder="Ingresa tu contraseña"
              required
            />
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-300 rounded-lg">
              <p className="text-red-600 text-sm text-center font-medium">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-reluvsa-black text-reluvsa-yellow py-3 rounded-lg font-bold text-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Ingresando...' : 'Ingresar'}
          </button>
        </form>

        {/* Footer con Rushdata */}
        <div className="flex items-center justify-center gap-2 mt-8 pt-6 border-t border-gray-200">
          <img
            src="/rushdata-icono-gris.png"
            alt="Rushdata"
            className="h-5 w-5 object-contain opacity-60"
          />
          <p className="text-gray-400 text-xs">
            Desarrollado por Rushdata
          </p>
        </div>
      </div>
    </div>
  );
}
