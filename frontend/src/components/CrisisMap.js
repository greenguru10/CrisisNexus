import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, CircleMarker } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.heat'; // Must be imported after leaflet
import { Activity, Users, MapPin, Layers } from 'lucide-react';

// Fix for default Leaflet icons in Webpack
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Custom colored markers based on urgency
const createCustomIcon = (color) => {
  return new L.Icon({
    iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });
};

const icons = {
  high: createCustomIcon('red'),
  medium: createCustomIcon('orange'),
  low: createCustomIcon('green'),
};

// Extracted Popup Content so it can be reused in both Pins and Heatmap view
const NeedPopupContent = ({ need }) => (
  <div className="p-1 min-w-[200px]">
    <div className="flex items-center gap-2 mb-2">
      <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase
        ${need.urgency === 'high' ? 'bg-red-100 text-red-700' : 
          need.urgency === 'medium' ? 'bg-orange-100 text-orange-700' : 
          'bg-green-100 text-green-700'}`}
      >
        {need.urgency}
      </span>
      <span className="text-xs font-semibold text-gray-500 uppercase">
        {need.category}
      </span>
    </div>
    
    <h4 className="font-semibold text-gray-900 mb-2">Crisis Report #{need.id}</h4>
    
    <div className="space-y-1.5 text-sm">
      <div className="flex items-center gap-2 text-gray-600">
        <Users size={14} className="text-blue-500" />
        <span>{need.people_affected} affected</span>
      </div>
      <div className="flex items-center gap-2 text-gray-600">
        <Activity size={14} className="text-amber-500" />
        <span className="capitalize">{need.status.replace('_', ' ')}</span>
      </div>
    </div>
    
    <a
      href={`/needs#need-${need.id}`}
      className="mt-4 w-full block text-center bg-blue-50 text-blue-600 hover:bg-blue-100 py-1.5 rounded-lg text-sm font-medium transition-colors"
    >
      View Details
    </a>
  </div>
);

// Component to handle Leaflet.heat layer
const HeatmapLayer = ({ points }) => {
  const map = useMap();

  useEffect(() => {
    if (!points || points.length === 0) return;

    // points array: [lat, lng, intensity]
    const heatLayer = L.heatLayer(points, {
      radius: 45,
      blur: 30,
      maxZoom: 10,
      max: 0.5, // Lower max forces colors to appear hotter even with few points
      minOpacity: 0.5, // Ensures the edges of the blur aren't completely washed out
      gradient: { 
        0.1: '#3b82f6', // blue
        0.3: '#10b981', // green
        0.5: '#eab308', // yellow
        0.7: '#f97316', // orange
        1.0: '#ef4444'  // red
      }
    }).addTo(map);

    return () => {
      map.removeLayer(heatLayer);
    };
  }, [map, points]);

  return null;
};

// Component to auto-fit bounds based on markers
const FitBounds = ({ needs }) => {
  const map = useMap();
  
  useEffect(() => {
    const validNeeds = needs.filter(n => n.latitude && n.longitude);
    if (validNeeds.length === 0) return;

    const bounds = L.latLngBounds(validNeeds.map(n => [n.latitude, n.longitude]));
    map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
  }, [map, needs]);

  return null;
};

const CrisisMap = ({ needs, loading }) => {
  const [viewMode, setViewMode] = useState('markers'); // 'markers' or 'heatmap'

  // Filter out needs without coordinates
  const validNeeds = needs?.filter(n => n.latitude && n.longitude) || [];

  // Calculate heatmap points: [lat, lng, intensity]
  // Intensity is based on people affected and urgency
  const heatPoints = validNeeds.map(n => {
    let weight = 0.6; // Base weight increased so points are much more visible
    if (n.urgency === 'high') weight += 0.4;
    else if (n.urgency === 'medium') weight += 0.2;
    
    // Add up to 0.3 weight based on people affected (cap at 500)
    const popWeight = Math.min(n.people_affected / 500, 1) * 0.3;
    weight += popWeight;
    
    return [n.latitude, n.longitude, Math.min(weight, 1.0)];
  });

  return (
    <div className="relative w-full h-[600px] bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden flex flex-col">
      {/* Map Header / Controls */}
      <div className="absolute top-4 right-4 z-[400] flex gap-2">
        <div className="bg-white p-1 rounded-lg shadow-md flex">
          <button
            onClick={() => setViewMode('markers')}
            className={`px-3 py-1.5 rounded-md text-sm font-medium flex items-center gap-2 transition-colors ${
              viewMode === 'markers' ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            <MapPin size={16} /> Pins
          </button>
          <button
            onClick={() => setViewMode('heatmap')}
            className={`px-3 py-1.5 rounded-md text-sm font-medium flex items-center gap-2 transition-colors ${
              viewMode === 'heatmap' ? 'bg-red-50 text-red-700' : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            <Layers size={16} /> Heatmap
          </button>
        </div>
      </div>

      {loading && (
        <div className="absolute inset-0 bg-white/50 backdrop-blur-sm z-[500] flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}

      {/* Map Container */}
      <MapContainer
        center={[20.5937, 78.9629]} // Default to India center
        zoom={5}
        className="flex-1 w-full z-0"
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        />
        
        {/* Adds Zoom Control to bottom right to avoid overlapping our custom buttons */}
        <div className="leaflet-bottom leaflet-right">
          <div className="leaflet-control-zoom leaflet-bar leaflet-control">
            <a className="leaflet-control-zoom-in" href="#" title="Zoom in" role="button" aria-label="Zoom in">+</a>
            <a className="leaflet-control-zoom-out" href="#" title="Zoom out" role="button" aria-label="Zoom out">-</a>
          </div>
        </div>

        {validNeeds.length > 0 && <FitBounds needs={validNeeds} />}

        {viewMode === 'markers' ? (
          <MarkerClusterGroup
            chunkedLoading
            maxClusterRadius={40}
            disableClusteringAtZoom={15}
          >
            {validNeeds.map((need) => (
              <Marker
                key={need.id}
                position={[need.latitude, need.longitude]}
                icon={icons[need.urgency] || icons.low}
              >
                <Popup className="rounded-xl custom-popup">
                  <NeedPopupContent need={need} />
                </Popup>
              </Marker>
            ))}
          </MarkerClusterGroup>
        ) : (
          <>
            <HeatmapLayer points={heatPoints} />
            {/* Invisible markers to allow clicking/hovering in heatmap view */}
            {validNeeds.map((need) => (
              <CircleMarker
                key={`heat-${need.id}`}
                center={[need.latitude, need.longitude]}
                radius={20}
                pathOptions={{ color: 'transparent', fillColor: 'transparent' }}
              >
                <Popup className="rounded-xl custom-popup">
                  <NeedPopupContent need={need} />
                </Popup>
              </CircleMarker>
            ))}
          </>
        )}
      </MapContainer>
    </div>
  );
};

export default CrisisMap;
