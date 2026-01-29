import React, { useState, useEffect, useCallback } from 'react';
import { Filter, Truck, Tag, Car, Calendar, Gauge, Circle, ChevronDown, X, Package, Droplet, Battery, Check } from 'lucide-react';
import { getFiltros } from '../services/api';
import { cn } from '../lib/utils';

// Departamentos que NO tienen compatibilidad vehicular
const DEPARTAMENTOS_SIN_COMPATIBILIDAD = ['LLANTAS', 'LUBRICACIÓN', 'QUIMICOS/ADITIVOS'];

// Marcas de acumuladores
const MARCAS_ACUMULADORES = ['CHECKER', 'EXTREMA', 'CAMEL'];

// Componente Select estilizado
function SelectField({ label, icon: Icon, value, onChange, options, disabled, placeholder }) {
  return (
    <div className="mb-4">
      <label className="flex items-center gap-2 text-sm font-medium text-notion-text-primary mb-2">
        {Icon && <Icon size={14} className="text-notion-text-secondary" />}
        {label}
      </label>
      <div className="relative">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          className={cn(
            "w-full px-3 py-2.5 bg-white border border-notion-border rounded-lg text-sm appearance-none cursor-pointer transition-all",
            "focus:outline-none focus:border-reluvsa-yellow focus:ring-2 focus:ring-reluvsa-yellow/20",
            "disabled:bg-notion-bg-subtle disabled:cursor-not-allowed disabled:text-notion-text-secondary",
            value && "border-reluvsa-yellow/50 bg-reluvsa-yellow/5"
          )}
        >
          <option value="">{placeholder}</option>
          {options.map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
        <ChevronDown
          size={16}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-notion-text-secondary pointer-events-none"
        />
      </div>
    </div>
  );
}

// Componente Sección colapsable
function FilterSection({ title, icon: Icon, children, defaultOpen = true }) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border-t border-notion-border pt-4 mt-4">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between text-sm font-semibold text-reluvsa-black mb-3 hover:text-reluvsa-red transition-colors"
      >
        <span className="flex items-center gap-2">
          {Icon && <Icon size={16} />}
          {title}
        </span>
        <ChevronDown
          size={16}
          className={cn("transition-transform", isOpen && "rotate-180")}
        />
      </button>
      {isOpen && <div className="space-y-0">{children}</div>}
    </div>
  );
}

function FiltrosCascada({ filtros, onFiltrosChange }) {
  const [opciones, setOpciones] = useState({
    departamentos: [],
    marcasProducto: [],
    marcasVehiculo: [],
    modelosVehiculo: [],
    años: [],
    motores: [],
    anchosLlanta: [],
    relacionesLlanta: [],
    diametrosLlanta: [],
    tiposLlanta: [],
    capasLlanta: [],
    viscosidades: [],
    tiposAceite: [],
    presentaciones: [],
    gruposBci: [],
    capacidadesCca: [],
    tamanosAcumulador: [],
    gruposProducto: [],
  });

  const [loading, setLoading] = useState({});

  const esLlantas = filtros.departamento === 'LLANTAS';
  const esAceites = filtros.departamento === 'LUBRICACIÓN' || filtros.departamento === 'QUIMICOS/ADITIVOS';
  const esAcumuladores = MARCAS_ACUMULADORES.includes(filtros.marca);
  const mostrarFiltrosVehiculo = !DEPARTAMENTOS_SIN_COMPATIBILIDAD.includes(filtros.departamento) && !esAcumuladores;

  // Cargar departamentos al inicio
  useEffect(() => {
    getFiltros.departamentos()
      .then(res => setOpciones(prev => ({ ...prev, departamentos: res.data.valores })))
      .catch(console.error);
  }, []);

  // Cargar marcas de producto cuando cambia departamento
  useEffect(() => {
    setLoading(prev => ({ ...prev, marcasProducto: true }));
    getFiltros.marcasProducto({ departamento: filtros.departamento || undefined })
      .then(res => setOpciones(prev => ({ ...prev, marcasProducto: res.data.valores })))
      .catch(console.error)
      .finally(() => setLoading(prev => ({ ...prev, marcasProducto: false })));
  }, [filtros.departamento]);

  // Cargar marcas de vehículo
  useEffect(() => {
    if (DEPARTAMENTOS_SIN_COMPATIBILIDAD.includes(filtros.departamento)) {
      setOpciones(prev => ({ ...prev, marcasVehiculo: [] }));
      return;
    }
    setLoading(prev => ({ ...prev, marcasVehiculo: true }));
    getFiltros.marcasVehiculo({
      departamento: filtros.departamento || undefined,
      marca_producto: filtros.marca || undefined,
    })
      .then(res => setOpciones(prev => ({ ...prev, marcasVehiculo: res.data.valores })))
      .catch(console.error)
      .finally(() => setLoading(prev => ({ ...prev, marcasVehiculo: false })));
  }, [filtros.departamento, filtros.marca]);

  // Cargar modelos cuando hay marca de vehículo
  useEffect(() => {
    if (!filtros.marca_vehiculo) {
      setOpciones(prev => ({ ...prev, modelosVehiculo: [] }));
      return;
    }
    setLoading(prev => ({ ...prev, modelosVehiculo: true }));
    getFiltros.modelosVehiculo({
      marca_vehiculo: filtros.marca_vehiculo,
      departamento: filtros.departamento || undefined,
      marca_producto: filtros.marca || undefined,
    })
      .then(res => setOpciones(prev => ({ ...prev, modelosVehiculo: res.data.valores })))
      .catch(console.error)
      .finally(() => setLoading(prev => ({ ...prev, modelosVehiculo: false })));
  }, [filtros.marca_vehiculo, filtros.departamento, filtros.marca]);

  // Cargar años
  useEffect(() => {
    if (!filtros.marca_vehiculo) {
      setOpciones(prev => ({ ...prev, años: [] }));
      return;
    }
    setLoading(prev => ({ ...prev, años: true }));
    getFiltros.años({
      marca_vehiculo: filtros.marca_vehiculo,
      modelo_vehiculo: filtros.modelo_vehiculo || undefined,
      departamento: filtros.departamento || undefined,
    })
      .then(res => setOpciones(prev => ({ ...prev, años: res.data.valores })))
      .catch(console.error)
      .finally(() => setLoading(prev => ({ ...prev, años: false })));
  }, [filtros.marca_vehiculo, filtros.modelo_vehiculo, filtros.departamento]);

  // Cargar motores
  useEffect(() => {
    if (!filtros.marca_vehiculo) {
      setOpciones(prev => ({ ...prev, motores: [] }));
      return;
    }
    setLoading(prev => ({ ...prev, motores: true }));
    getFiltros.motores({
      marca_vehiculo: filtros.marca_vehiculo,
      modelo_vehiculo: filtros.modelo_vehiculo || undefined,
      año: filtros.año || undefined,
    })
      .then(res => setOpciones(prev => ({ ...prev, motores: res.data.valores })))
      .catch(console.error)
      .finally(() => setLoading(prev => ({ ...prev, motores: false })));
  }, [filtros.marca_vehiculo, filtros.modelo_vehiculo, filtros.año]);

  // Cargar grupos de producto
  useEffect(() => {
    setLoading(prev => ({ ...prev, gruposProducto: true }));
    getFiltros.gruposProducto({
      departamento: filtros.departamento || undefined,
      marca_producto: filtros.marca || undefined,
      marca_vehiculo: filtros.marca_vehiculo || undefined,
      modelo_vehiculo: filtros.modelo_vehiculo || undefined,
      año: filtros.año || undefined,
      motor: filtros.motor || undefined,
    })
      .then(res => setOpciones(prev => ({ ...prev, gruposProducto: res.data.valores })))
      .catch(console.error)
      .finally(() => setLoading(prev => ({ ...prev, gruposProducto: false })));
  }, [filtros.departamento, filtros.marca, filtros.marca_vehiculo, filtros.modelo_vehiculo, filtros.año, filtros.motor]);

  // ========== FILTROS PARA LLANTAS ==========
  useEffect(() => {
    if (!esLlantas) {
      setOpciones(prev => ({
        ...prev,
        anchosLlanta: [],
        relacionesLlanta: [],
        diametrosLlanta: [],
        tiposLlanta: [],
        capasLlanta: [],
      }));
      return;
    }

    setLoading(prev => ({ ...prev, anchosLlanta: true }));
    getFiltros.anchosLlanta({ marca_producto: filtros.marca || undefined })
      .then(res => setOpciones(prev => ({ ...prev, anchosLlanta: res.data.valores })))
      .catch(console.error)
      .finally(() => setLoading(prev => ({ ...prev, anchosLlanta: false })));

    getFiltros.tiposLlanta({ marca_producto: filtros.marca || undefined })
      .then(res => setOpciones(prev => ({ ...prev, tiposLlanta: res.data.valores })))
      .catch(console.error);

    getFiltros.capasLlanta({ marca_producto: filtros.marca || undefined })
      .then(res => setOpciones(prev => ({ ...prev, capasLlanta: res.data.valores })))
      .catch(console.error);
  }, [esLlantas, filtros.marca]);

  useEffect(() => {
    if (!esLlantas) return;
    setLoading(prev => ({ ...prev, relacionesLlanta: true }));
    getFiltros.relacionesLlanta({
      ancho: filtros.ancho_llanta || undefined,
      marca_producto: filtros.marca || undefined,
    })
      .then(res => setOpciones(prev => ({ ...prev, relacionesLlanta: res.data.valores })))
      .catch(console.error)
      .finally(() => setLoading(prev => ({ ...prev, relacionesLlanta: false })));
  }, [esLlantas, filtros.ancho_llanta, filtros.marca]);

  useEffect(() => {
    if (!esLlantas) return;
    setLoading(prev => ({ ...prev, diametrosLlanta: true }));
    getFiltros.diametrosLlanta({
      ancho: filtros.ancho_llanta || undefined,
      relacion: filtros.relacion_llanta || undefined,
      marca_producto: filtros.marca || undefined,
    })
      .then(res => setOpciones(prev => ({ ...prev, diametrosLlanta: res.data.valores })))
      .catch(console.error)
      .finally(() => setLoading(prev => ({ ...prev, diametrosLlanta: false })));
  }, [esLlantas, filtros.ancho_llanta, filtros.relacion_llanta, filtros.marca]);

  // ========== FILTROS PARA ACEITES ==========
  useEffect(() => {
    if (!esAceites) {
      setOpciones(prev => ({
        ...prev,
        viscosidades: [],
        tiposAceite: [],
        presentaciones: [],
      }));
      return;
    }

    getFiltros.tiposAceite({ marca_producto: filtros.marca || undefined })
      .then(res => setOpciones(prev => ({ ...prev, tiposAceite: res.data.valores })))
      .catch(console.error);
  }, [esAceites, filtros.marca]);

  useEffect(() => {
    if (!esAceites) return;
    setLoading(prev => ({ ...prev, viscosidades: true }));
    getFiltros.viscosidades({
      tipo_aceite: filtros.tipo_aceite || undefined,
      marca_producto: filtros.marca || undefined,
    })
      .then(res => setOpciones(prev => ({ ...prev, viscosidades: res.data.valores })))
      .catch(console.error)
      .finally(() => setLoading(prev => ({ ...prev, viscosidades: false })));
  }, [esAceites, filtros.tipo_aceite, filtros.marca]);

  useEffect(() => {
    if (!esAceites) return;
    setLoading(prev => ({ ...prev, presentaciones: true }));
    getFiltros.presentaciones({
      viscosidad: filtros.viscosidad || undefined,
      tipo_aceite: filtros.tipo_aceite || undefined,
      marca_producto: filtros.marca || undefined,
    })
      .then(res => setOpciones(prev => ({ ...prev, presentaciones: res.data.valores })))
      .catch(console.error)
      .finally(() => setLoading(prev => ({ ...prev, presentaciones: false })));
  }, [esAceites, filtros.viscosidad, filtros.tipo_aceite, filtros.marca]);

  // ========== FILTROS PARA ACUMULADORES ==========
  useEffect(() => {
    if (!esAcumuladores) {
      setOpciones(prev => ({
        ...prev,
        gruposBci: [],
        capacidadesCca: [],
        tamanosAcumulador: [],
      }));
      return;
    }

    getFiltros.gruposBci({ marca_producto: filtros.marca || undefined })
      .then(res => setOpciones(prev => ({ ...prev, gruposBci: res.data.valores })))
      .catch(console.error);

    getFiltros.tamanosAcumulador({ marca_producto: filtros.marca || undefined })
      .then(res => setOpciones(prev => ({ ...prev, tamanosAcumulador: res.data.valores })))
      .catch(console.error);
  }, [esAcumuladores, filtros.marca]);

  useEffect(() => {
    if (!esAcumuladores) return;
    setLoading(prev => ({ ...prev, capacidadesCca: true }));
    getFiltros.capacidadesCca({
      grupo_bci: filtros.grupo_bci || undefined,
      marca_producto: filtros.marca || undefined,
    })
      .then(res => setOpciones(prev => ({ ...prev, capacidadesCca: res.data.valores })))
      .catch(console.error)
      .finally(() => setLoading(prev => ({ ...prev, capacidadesCca: false })));
  }, [esAcumuladores, filtros.grupo_bci, filtros.marca]);

  const handleChange = useCallback((field, value) => {
    const newFiltros = { ...filtros, [field]: value || '' };

    // Limpiar filtros dependientes en cascada
    if (field === 'departamento') {
      newFiltros.marca_vehiculo = '';
      newFiltros.modelo_vehiculo = '';
      newFiltros.año = '';
      newFiltros.motor = '';
      newFiltros.grupo_producto = '';
      newFiltros.ancho_llanta = '';
      newFiltros.relacion_llanta = '';
      newFiltros.diametro_llanta = '';
      newFiltros.tipo_llanta = '';
      newFiltros.capas_llanta = '';
      newFiltros.viscosidad = '';
      newFiltros.tipo_aceite = '';
      newFiltros.presentacion = '';
      newFiltros.grupo_bci = '';
      newFiltros.capacidad_cca = '';
      newFiltros.tamano_acumulador = '';
    }
    if (field === 'marca') {
      if (MARCAS_ACUMULADORES.includes(value)) {
        newFiltros.marca_vehiculo = '';
        newFiltros.modelo_vehiculo = '';
        newFiltros.año = '';
        newFiltros.motor = '';
      }
    }
    if (field === 'marca_vehiculo') {
      newFiltros.modelo_vehiculo = '';
      newFiltros.año = '';
      newFiltros.motor = '';
    }
    if (field === 'modelo_vehiculo') {
      newFiltros.año = '';
      newFiltros.motor = '';
    }
    if (field === 'año') {
      newFiltros.motor = '';
    }
    if (field === 'ancho_llanta') {
      newFiltros.relacion_llanta = '';
      newFiltros.diametro_llanta = '';
    }
    if (field === 'relacion_llanta') {
      newFiltros.diametro_llanta = '';
    }
    if (field === 'tipo_aceite') {
      newFiltros.viscosidad = '';
      newFiltros.presentacion = '';
    }
    if (field === 'viscosidad') {
      newFiltros.presentacion = '';
    }
    if (field === 'grupo_bci') {
      newFiltros.capacidad_cca = '';
    }

    onFiltrosChange(newFiltros);
  }, [filtros, onFiltrosChange]);

  const limpiarFiltros = () => {
    onFiltrosChange({
      departamento: '',
      marca: '',
      grupo_producto: '',
      marca_vehiculo: '',
      modelo_vehiculo: '',
      año: '',
      motor: '',
      con_inventario: false,
      ancho_llanta: '',
      relacion_llanta: '',
      diametro_llanta: '',
      tipo_llanta: '',
      capas_llanta: '',
      viscosidad: '',
      tipo_aceite: '',
      presentacion: '',
      grupo_bci: '',
      capacidad_cca: '',
      tamano_acumulador: '',
    });
  };

  const tieneAlgunFiltro = Object.entries(filtros).some(([k, v]) => v && v !== false && k !== 'page');

  return (
    <div className="bg-white rounded-xl p-5 border border-notion-border sticky top-28">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <h2 className="flex items-center gap-2 font-semibold text-notion-text-primary">
          <Filter size={18} />
          Filtros
        </h2>
        {tieneAlgunFiltro && (
          <button
            onClick={limpiarFiltros}
            className="text-xs text-reluvsa-red hover:underline font-medium flex items-center gap-1"
          >
            <X size={12} />
            Limpiar
          </button>
        )}
      </div>

      {/* Filtros básicos */}
      <SelectField
        label="Departamento"
        icon={Truck}
        value={filtros.departamento}
        onChange={(v) => handleChange('departamento', v)}
        options={opciones.departamentos}
        placeholder="Todos los departamentos"
      />

      <SelectField
        label="Marca del Producto"
        icon={Tag}
        value={filtros.marca}
        onChange={(v) => handleChange('marca', v)}
        options={opciones.marcasProducto}
        disabled={loading.marcasProducto}
        placeholder="Todas las marcas"
      />

      {/* Filtros de vehículo */}
      {mostrarFiltrosVehiculo && opciones.marcasVehiculo.length > 0 && (
        <FilterSection title="Compatibilidad Vehicular" icon={Car}>
          <SelectField
            label="Marca del Vehículo"
            value={filtros.marca_vehiculo}
            onChange={(v) => handleChange('marca_vehiculo', v)}
            options={opciones.marcasVehiculo}
            disabled={loading.marcasVehiculo}
            placeholder="Todas las marcas"
          />

          <SelectField
            label="Modelo"
            value={filtros.modelo_vehiculo}
            onChange={(v) => handleChange('modelo_vehiculo', v)}
            options={opciones.modelosVehiculo}
            disabled={!filtros.marca_vehiculo || loading.modelosVehiculo}
            placeholder="Todos los modelos"
          />

          <SelectField
            label="Año"
            icon={Calendar}
            value={filtros.año}
            onChange={(v) => handleChange('año', v)}
            options={opciones.años}
            disabled={!filtros.marca_vehiculo || loading.años}
            placeholder="Todos los años"
          />

          <SelectField
            label="Motor"
            icon={Gauge}
            value={filtros.motor}
            onChange={(v) => handleChange('motor', v)}
            options={opciones.motores}
            disabled={!filtros.marca_vehiculo || loading.motores}
            placeholder="Todos los motores"
          />

          <SelectField
            label="Grupo de Producto"
            icon={Package}
            value={filtros.grupo_producto}
            onChange={(v) => handleChange('grupo_producto', v)}
            options={opciones.gruposProducto}
            disabled={loading.gruposProducto}
            placeholder="Todos los grupos"
          />
        </FilterSection>
      )}

      {/* Filtros de llantas */}
      {esLlantas && (
        <FilterSection title="Medidas de Llanta" icon={Circle}>
          <SelectField
            label="Ancho (mm)"
            value={filtros.ancho_llanta}
            onChange={(v) => handleChange('ancho_llanta', v)}
            options={opciones.anchosLlanta}
            disabled={loading.anchosLlanta}
            placeholder="Todos los anchos"
          />

          <SelectField
            label="Relación/Perfil (%)"
            value={filtros.relacion_llanta}
            onChange={(v) => handleChange('relacion_llanta', v)}
            options={opciones.relacionesLlanta}
            disabled={loading.relacionesLlanta}
            placeholder="Todas las relaciones"
          />

          <SelectField
            label="Diámetro (Rin)"
            value={filtros.diametro_llanta}
            onChange={(v) => handleChange('diametro_llanta', v)}
            options={opciones.diametrosLlanta}
            disabled={loading.diametrosLlanta}
            placeholder="Todos los diámetros"
          />

          <SelectField
            label="Tipo de Llanta"
            value={filtros.tipo_llanta}
            onChange={(v) => handleChange('tipo_llanta', v)}
            options={opciones.tiposLlanta}
            placeholder="Todos los tipos"
          />

          <SelectField
            label="Capas"
            value={filtros.capas_llanta}
            onChange={(v) => handleChange('capas_llanta', v)}
            options={opciones.capasLlanta.map(c => `${c}C`)}
            placeholder="Todas las capas"
          />
        </FilterSection>
      )}

      {/* Filtros de aceites */}
      {esAceites && (
        <FilterSection title="Especificaciones de Aceite" icon={Droplet}>
          <SelectField
            label="Tipo de Aceite"
            value={filtros.tipo_aceite}
            onChange={(v) => handleChange('tipo_aceite', v)}
            options={opciones.tiposAceite}
            placeholder="Todos los tipos"
          />

          <SelectField
            label="Viscosidad SAE"
            value={filtros.viscosidad}
            onChange={(v) => handleChange('viscosidad', v)}
            options={opciones.viscosidades}
            disabled={loading.viscosidades}
            placeholder="Todas las viscosidades"
          />

          <SelectField
            label="Presentación"
            value={filtros.presentacion}
            onChange={(v) => handleChange('presentacion', v)}
            options={opciones.presentaciones}
            disabled={loading.presentaciones}
            placeholder="Todas las presentaciones"
          />
        </FilterSection>
      )}

      {/* Filtros de acumuladores */}
      {esAcumuladores && (
        <FilterSection title="Especificaciones de Acumulador" icon={Battery}>
          <SelectField
            label="Grupo BCI"
            value={filtros.grupo_bci}
            onChange={(v) => handleChange('grupo_bci', v)}
            options={opciones.gruposBci}
            placeholder="Todos los grupos"
          />

          <SelectField
            label="Capacidad (CCA)"
            value={filtros.capacidad_cca}
            onChange={(v) => handleChange('capacidad_cca', v)}
            options={opciones.capacidadesCca}
            disabled={loading.capacidadesCca}
            placeholder="Todas las capacidades"
          />

          <SelectField
            label="Tamaño"
            value={filtros.tamano_acumulador}
            onChange={(v) => handleChange('tamano_acumulador', v)}
            options={opciones.tamanosAcumulador}
            placeholder="Todos los tamaños"
          />
        </FilterSection>
      )}

      {/* Filtro de inventario */}
      <div className="border-t border-notion-border pt-4 mt-4">
        <label className="flex items-center gap-3 cursor-pointer group">
          <input
            type="checkbox"
            checked={filtros.con_inventario || false}
            onChange={(e) => handleChange('con_inventario', e.target.checked)}
            className="hidden"
          />
          <div className={cn(
            "w-5 h-5 rounded border-2 flex items-center justify-center transition-all",
            filtros.con_inventario
              ? "bg-reluvsa-yellow border-reluvsa-black"
              : "border-notion-border group-hover:border-reluvsa-yellow"
          )}>
            {filtros.con_inventario && <Check size={14} className="text-reluvsa-black" />}
          </div>
          <span className="text-sm font-medium text-notion-text-primary flex items-center gap-2">
            <Package size={14} className="text-notion-text-secondary" />
            Solo con inventario
          </span>
        </label>
      </div>
    </div>
  );
}

export default FiltrosCascada;
