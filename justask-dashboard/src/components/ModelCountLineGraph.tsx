import React, { useState, useEffect, useMemo, useLayoutEffect, useRef, CSSProperties } from 'react';
import { Line } from 'react-chartjs-2';
import { supabase } from '@/integrations/supabase/client';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import { ChevronDown, ChevronUp, Download, Calendar } from 'lucide-react';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
);

interface HistoricalDataPoint {
  id?: number;
  timestamp: Date;
  totalCount: number;
  providerCounts: {
    inferenceProviders: { [key: string]: number };
    modelProviders: { [key: string]: number };
  };
}

interface ModelCountLineGraphProps {
  currentModels: any[];
  darkMode: boolean;
}

const ModelCountLineGraph: React.FC<ModelCountLineGraphProps> = ({ currentModels, darkMode }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [historicalData, setHistoricalData] = useState<HistoricalDataPoint[]>([]);
  const [selectedInferenceProviders, setSelectedInferenceProviders] = useState<Set<string>>(new Set());
  const [selectedModelProviders, setSelectedModelProviders] = useState<Set<string>>(new Set());
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | 'all'>('7d');

  // Banner-related state and refs
  const containerRef = useRef<HTMLDivElement>(null);
  const unitRef = useRef<HTMLSpanElement>(null);
  const [bannerText, setBannerText] = useState<string>("🔴 LIVE: JustAsk Dashboard - Loading...");
  const [spacerWidth, setSpacerWidth] = useState(0);
  const [unitWidth, setUnitWidth] = useState(0);
  const [ready, setReady] = useState(false);

  // No longer using localStorage - data persisted in database

  // Load historical data from database
  useEffect(() => {
    const loadHistoricalData = async () => {
      try {
        // Fetch all historical data (limit prevents runaway queries)
        const { data, error } = await supabase
          .from('analytics_history')
          .select('*')
          .order('timestamp', { ascending: true })
          .limit(10000);

        console.log('Raw Supabase response:', {
          recordCount: data?.length || 0,
          error,
          sample: data?.slice(-5).map(d => ({ timestamp: d.timestamp, total: d.total_models }))
        });

        if (error) {
          console.error('Error loading historical data:', error);
          return;
        }

        const formattedData: HistoricalDataPoint[] = (data || []).map((item: any) => ({
          id: item.id,
          timestamp: new Date(item.timestamp),
          totalCount: item.total_models,
          providerCounts: {
            inferenceProviders: item.inference_provider_counts,
            modelProviders: item.model_provider_counts
          }
        }));

        console.log('Loaded historical data from Supabase:', {
          total: formattedData.length,
          dateRange: formattedData.length > 0 ? {
            first: formattedData[0].timestamp.toISOString(),
            last: formattedData[formattedData.length - 1].timestamp.toISOString()
          } : null,
          nov3Plus: formattedData.filter(d => d.timestamp >= new Date('2025-11-03T00:00:00Z')).length
        });

        setHistoricalData(formattedData);
      } catch (error) {
        console.error('Error loading historical data:', error);
      }
    };

    loadHistoricalData();
  }, []);

  // Save analytics snapshot to database
  const saveAnalyticsSnapshot = async (
    totalModels: number,
    inferenceProviders: { [key: string]: number },
    modelProviders: { [key: string]: number }
  ) => {
    try {
      const { error } = await supabase.rpc('insert_analytics_snapshot', {
        p_total_models: totalModels,
        p_inference_provider_counts: inferenceProviders,
        p_model_provider_counts: modelProviders
      });

      if (error) {
        console.error('Error saving analytics snapshot:', error);
        return false;
      }
      return true;
    } catch (error) {
      console.error('Error saving analytics snapshot:', error);
      return false;
    }
  };

  // Track analytics snapshots - save once per day (last update of the day)
  useEffect(() => {
    const collectAnalyticsData = async () => {
      if (currentModels.length === 0) return;

      // Calculate provider counts
      const inferenceProviders: { [key: string]: number } = {};
      const modelProviders: { [key: string]: number } = {};
      
      currentModels.forEach(model => {
        const inferenceProvider = model.inference_provider || 'Unknown';
        const modelProvider = model.model_provider || 'Unknown';
        
        inferenceProviders[inferenceProvider] = (inferenceProviders[inferenceProvider] || 0) + 1;
        modelProviders[modelProvider] = (modelProviders[modelProvider] || 0) + 1;
      });

      // Always save - will overwrite existing data for the current day
      console.log('Saving daily analytics snapshot:', {
        totalModels: currentModels.length,
        inferenceProviderCount: Object.keys(inferenceProviders).length,
        modelProviderCount: Object.keys(modelProviders).length
      });
      
      const success = await saveAnalyticsSnapshot(
        currentModels.length,
        inferenceProviders,
        modelProviders
      );

      if (success) {
        // Reload historical data to get the latest entry
        const { data, error } = await supabase
          .from('analytics_history')
          .select('*')
          .order('timestamp', { ascending: true })
          .limit(10000);

        if (!error && data) {
          const formattedData: HistoricalDataPoint[] = data.map((item: any) => ({
            id: item.id,
            timestamp: new Date(item.timestamp),
            totalCount: item.total_models,
            providerCounts: {
              inferenceProviders: item.inference_provider_counts,
              modelProviders: item.model_provider_counts
            }
          }));
          setHistoricalData(formattedData);
        }
      }
    };

    collectAnalyticsData();
  }, [currentModels]);

  // Load banner text from file
  useEffect(() => {
    const loadBannerText = async () => {
      try {
        const response = await fetch('/banner-text.txt');
        if (response.ok) {
          const text = await response.text();
          setBannerText(text.trim() || "🔴 LIVE: JustAsk Dashboard - 50+ free AI models from 3 providers");
        }
      } catch (error) {
        console.log('Using default banner text');
        setBannerText("🔴 LIVE: JustAsk Dashboard - 50+ free AI models from 3 providers");
      }
    };

    loadBannerText();

    // Poll for banner text changes every 30 seconds
    const bannerInterval = setInterval(loadBannerText, 30000);
    return () => clearInterval(bannerInterval);
  }, []);

  // One-time keyframes
  useEffect(() => {
    const id = 'banner-scroll-keyframes';
    if (document.getElementById(id)) return;
    const style = document.createElement('style');
    style.id = id;
    style.innerHTML = `
      @keyframes scrollX {
        from { transform: translate3d(0,0,0); }
        to   { transform: translate3d(calc(-1 * var(--d, 0px)),0,0); }
      }
    `;
    document.head.appendChild(style);
  }, []);

  // Measure the true unit width after fonts load
  useLayoutEffect(() => {
    const measure = () => {
      const cw = containerRef.current?.getBoundingClientRect().width ?? window.innerWidth;
      setSpacerWidth(Math.ceil(cw));
    };
    measure();

    const onResize = () => { measure(); };
    window.addEventListener('resize', onResize);

    let fontDone = false;
    const measureUnit = () => {
      if (!unitRef.current) return;
      const uw = Math.ceil(unitRef.current.getBoundingClientRect().width);
      setUnitWidth(uw);
      setReady(uw > 0);
    };

    // Wait for fonts if available
    // @ts-ignore
    const fonts = (document as any).fonts;
    if (fonts?.ready && typeof fonts.ready.then === 'function') {
      fonts.ready.then(() => { fontDone = true; measure(); measureUnit(); });
    }

    // Fallback
    const rAF = requestAnimationFrame(() => { if (!fontDone) { measureUnit(); } });

    return () => {
      window.removeEventListener('resize', onResize);
      cancelAnimationFrame(rAF);
    };
  }, [bannerText]);

  // Filter data based on time range and get only last entry per day
  const filteredData = useMemo(() => {
    if (historicalData.length === 0) return [];

    const now = new Date();
    const cutoffTime = (() => {
      switch (timeRange) {
        case '7d': return new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        case '30d': return new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        case 'all': return new Date(0);
        default: return new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      }
    })();

    // Filter by time range first
    const timeFiltered = historicalData.filter(point => point.timestamp >= cutoffTime);
    
    // Group by date (YYYY-MM-DD) and get the latest entry per day
    const dailyData = new Map<string, HistoricalDataPoint>();
    
    timeFiltered.forEach(point => {
      const dateKey = point.timestamp.toISOString().split('T')[0]; // YYYY-MM-DD
      const existing = dailyData.get(dateKey);
      
      // Keep the latest timestamp for each day
      if (!existing || point.timestamp > existing.timestamp) {
        dailyData.set(dateKey, point);
      }
    });
    
    // Convert back to array and sort by date
    const result = Array.from(dailyData.values()).sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());

    console.log(`Time range: ${timeRange}, Total points: ${historicalData.length}, Daily points: ${result.length}`, {
      cutoffTime: cutoffTime.toISOString(),
      timeFiltered: timeFiltered.length,
      nov3Plus: result.filter(d => d.timestamp >= new Date('2025-11-03T00:00:00Z')).length
    });

    return result;
  }, [historicalData, timeRange]);

  // Get providers sorted by latest model count in the selected time range
  const availableProviders = useMemo(() => {
    if (filteredData.length === 0) {
      return { inferenceProviders: [], modelProviders: [] };
    }

    // Get the latest data point
    const latestPoint = filteredData[filteredData.length - 1];

    return {
      inferenceProviders: Object.entries(latestPoint.providerCounts.inferenceProviders)
        .map(([provider, count]) => ({ provider, count }))
        .sort((a, b) => b.count - a.count),
      modelProviders: Object.entries(latestPoint.providerCounts.modelProviders)
        .map(([provider, count]) => ({ provider, count }))
        .sort((a, b) => b.count - a.count)
    };
  }, [filteredData]);

  // Prepare chart data
  const chartData = useMemo(() => {
    const datasets = [];
    const colors = [
      '#3b82f6', '#ef4444', '#22c55e', '#f59e0b', '#8b5cf6', 
      '#ec4899', '#06b6d4', '#f97316', '#84cc16', '#6366f1'
    ];

    // Total count line (only shown when no providers are selected)
    const showTotalLine = selectedInferenceProviders.size === 0 && selectedModelProviders.size === 0;
    
    if (showTotalLine) {
      datasets.push({
        label: 'Total Models',
        data: filteredData.map(point => {
          // Normalize to midnight UTC for proper x-axis alignment
          const dateStr = point.timestamp.toISOString().split('T')[0];
          const normalizedDate = new Date(dateStr + 'T00:00:00.000Z');
          return {
            x: normalizedDate.getTime(), // Use timestamp (milliseconds) instead of Date object
            y: point.totalCount
          };
        }),
        borderColor: colors[0],
        backgroundColor: colors[0] + '20',
        tension: 0.1,
        pointRadius: 4,
        pointHoverRadius: 8,
        borderWidth: 2,
        pointBackgroundColor: colors[0],
        pointBorderColor: '#ffffff',
        pointBorderWidth: 1
      });
    }

    let colorIndex = showTotalLine ? 1 : 0;

    // Add selected inference provider lines
    selectedInferenceProviders.forEach(provider => {
      datasets.push({
        label: `${provider} (Inference Provider)`,
        data: filteredData.map(point => {
          // Normalize to midnight UTC for proper x-axis alignment
          const dateStr = point.timestamp.toISOString().split('T')[0];
          const normalizedDate = new Date(dateStr + 'T00:00:00.000Z');
          return {
            x: normalizedDate.getTime(), // Use timestamp (milliseconds) instead of Date object
            y: point.providerCounts.inferenceProviders[provider] || 0
          };
        }),
        borderColor: colors[colorIndex % colors.length],
        backgroundColor: colors[colorIndex % colors.length] + '20',
        tension: 0.1,
        pointRadius: 3,
        pointHoverRadius: 6,
        borderWidth: 2,
        borderDash: [5, 5],
        pointBackgroundColor: colors[colorIndex % colors.length],
        pointBorderColor: '#ffffff',
        pointBorderWidth: 1
      });
      colorIndex++;
    });

    // Add selected model provider lines
    selectedModelProviders.forEach(provider => {
      datasets.push({
        label: `${provider} (Model Provider)`,
        data: filteredData.map(point => {
          // Normalize to midnight UTC for proper x-axis alignment
          const dateStr = point.timestamp.toISOString().split('T')[0];
          const normalizedDate = new Date(dateStr + 'T00:00:00.000Z');
          return {
            x: normalizedDate.getTime(), // Use timestamp (milliseconds) instead of Date object
            y: point.providerCounts.modelProviders[provider] || 0
          };
        }),
        borderColor: colors[colorIndex % colors.length],
        backgroundColor: colors[colorIndex % colors.length] + '20',
        tension: 0.1,
        pointRadius: 3,
        pointHoverRadius: 6,
        borderWidth: 2,
        borderDash: [2, 2],
        pointBackgroundColor: colors[colorIndex % colors.length],
        pointBorderColor: '#ffffff',
        pointBorderWidth: 1
      });
      colorIndex++;
    });

    console.log('Chart data prepared:', {
      datasets: datasets.length,
      dataPoints: datasets.length > 0 ? datasets[0].data.length : 0,
      firstDate: datasets.length > 0 && datasets[0].data.length > 0 ? datasets[0].data[0].x : null,
      lastDate: datasets.length > 0 && datasets[0].data.length > 0 ? datasets[0].data[datasets[0].data.length - 1].x : null
    });

    return { datasets };
  }, [filteredData, selectedInferenceProviders, selectedModelProviders]);

  // Calculate dynamic y-axis range for better visibility of small changes
  const yAxisConfig = useMemo(() => {
    if (filteredData.length === 0) return { min: 0, max: 100, stepSize: 10 };
    
    // Determine which values to consider based on what's being displayed
    const showTotalLine = selectedInferenceProviders.size === 0 && selectedModelProviders.size === 0;
    
    const allValues = filteredData.flatMap(point => [
      ...(showTotalLine ? [point.totalCount] : []),
      ...selectedInferenceProviders.size > 0 
        ? Array.from(selectedInferenceProviders).map(provider => 
            point.providerCounts.inferenceProviders[provider] || 0
          ) 
        : [],
      ...selectedModelProviders.size > 0 
        ? Array.from(selectedModelProviders).map(provider => 
            point.providerCounts.modelProviders[provider] || 0
          ) 
        : []
    ]);
    
    if (allValues.length === 0) return { min: 0, max: 100, stepSize: 10 };
    
    const minValue = Math.min(...allValues);
    const maxValue = Math.max(...allValues);
    const range = maxValue - minValue;
    
    // If range is very small, add padding to make changes visible
    const padding = range < 5 ? Math.max(2, Math.ceil(range * 0.5)) : Math.ceil(range * 0.1);
    
    const adjustedMin = Math.max(0, minValue - padding);
    const adjustedMax = maxValue + padding;
    const adjustedRange = adjustedMax - adjustedMin;
    
    // Calculate dynamic step size based on the range
    let stepSize;
    if (adjustedRange <= 10) {
      stepSize = 1;
    } else if (adjustedRange <= 50) {
      stepSize = Math.max(1, Math.ceil(adjustedRange / 10));
    } else if (adjustedRange <= 100) {
      stepSize = Math.max(5, Math.ceil(adjustedRange / 15));
    } else {
      stepSize = Math.max(10, Math.ceil(adjustedRange / 10));
    }
    
    return {
      min: adjustedMin,
      max: adjustedMax,
      stepSize: stepSize
    };
  }, [filteredData, selectedInferenceProviders, selectedModelProviders]);

  // Chart options
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: darkMode ? '#e5e7eb' : '#374151',
          font: { size: 12 }
        }
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        backgroundColor: darkMode ? '#1f2937' : '#ffffff',
        titleColor: darkMode ? '#e5e7eb' : '#374151',
        bodyColor: darkMode ? '#d1d5db' : '#6b7280',
        borderColor: darkMode ? '#374151' : '#d1d5db',
        borderWidth: 1,
        titleFont: { size: 12, weight: 'bold' },
        bodyFont: { size: 11 },
        cornerRadius: 6,
        displayColors: true,
        callbacks: {
          title: (context: any) => {
            const date = new Date(context[0].parsed.x);
            return date.toLocaleDateString('en-GB', {
              year: 'numeric',
              month: 'short',
              day: '2-digit',
              timeZone: 'UTC'
            }).replace(/ /g, '-');
          },
          label: (context: any) => {
            return `${context.dataset.label}: ${context.parsed.y} models`;
          }
        }
      },
      // Note: Data labels would require chartjs-plugin-datalabels
      // For now, values are shown in tooltips on hover
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          unit: 'day',
          round: 'day',
          displayFormats: {
            day: 'dd-MMM-yyyy'
          },
          tooltipFormat: 'dd-MMM-yyyy',
          parser: false
        },
        adapters: {
          date: {
            zone: 'utc'
          }
        },
        grid: {
          color: darkMode ? '#374151' : '#e5e7eb'
        },
        ticks: {
          color: darkMode ? '#9ca3af' : '#6b7280',
          source: 'data',
          callback: function(value: any) {
            const date = new Date(value);
            return date.toLocaleDateString('en-GB', {
              day: '2-digit',
              month: 'short',
              year: 'numeric',
              timeZone: 'UTC'
            }).replace(/ /g, '-');
          }
        }
      },
      y: {
        min: yAxisConfig.min,
        max: yAxisConfig.max,
        grid: {
          color: darkMode ? '#374151' : '#e5e7eb'
        },
        ticks: {
          color: darkMode ? '#9ca3af' : '#6b7280',
          precision: 0,
          stepSize: yAxisConfig.stepSize
        }
      }
    },
    interaction: {
      mode: 'nearest' as const,
      axis: 'x' as const,
      intersect: false
    }
  };

  // Toggle provider selection
  const toggleProvider = (provider: string, type: 'inference' | 'model') => {
    if (type === 'inference') {
      const newSet = new Set(selectedInferenceProviders);
      if (newSet.has(provider)) {
        newSet.delete(provider);
      } else {
        newSet.add(provider);
      }
      setSelectedInferenceProviders(newSet);
    } else {
      const newSet = new Set(selectedModelProviders);
      if (newSet.has(provider)) {
        newSet.delete(provider);
      } else {
        newSet.add(provider);
      }
      setSelectedModelProviders(newSet);
    }
  };

  // Export data
  const exportData = () => {
    const exportableData = historicalData.map(point => ({
      timestamp: point.timestamp.toISOString(),
      totalCount: point.totalCount,
      providerCounts: point.providerCounts
    }));
    const dataStr = JSON.stringify(exportableData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `model-count-history-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (historicalData.length === 0) {
    return (
      <div className={`p-6 rounded-lg shadow-lg mb-6 ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
        <h2 className={`text-lg font-semibold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
          Model Count Tracker
        </h2>
        <div className={`text-center py-8 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
          <Calendar className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No historical data available yet.</p>
          <p className="text-sm mt-2">Data is collected automatically when the dashboard refreshes (latest snapshot per day).</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`p-6 rounded-lg shadow-lg mb-6 ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className={`flex items-center space-x-2 text-lg font-semibold ${darkMode ? 'text-white hover:text-gray-300' : 'text-gray-900 hover:text-gray-700'}`}
        >
          {isCollapsed ? <ChevronDown className="w-5 h-5" /> : <ChevronUp className="w-5 h-5" />}
          <span>Model Count Tracker</span>
          <span className={`text-sm font-normal ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            ({historicalData.length} data points)
          </span>
        </button>
        <div className="flex items-center space-x-2">
          <button
            onClick={exportData}
            className={`p-2 rounded-md transition-colors ${
              darkMode ? 'hover:bg-gray-700 text-gray-400' : 'hover:bg-gray-100 text-gray-600'
            }`}
            title="Export Data"
          >
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>

      {!isCollapsed && (
        <>
          {/* Controls */}
          <div className="mb-6 space-y-4">
            {/* Time Range Selector */}
            <div className="flex items-center space-x-4">
              <span className={`text-sm font-medium ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                Time Range:
              </span>
              <div className="flex space-x-2">
                {[
                  { value: '7d', label: '7 Days' },
                  { value: '30d', label: '30 Days' },
                  { value: 'all', label: 'All Time' }
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setTimeRange(option.value as any)}
                    className={`px-3 py-1 text-sm rounded-md transition-colors ${
                      timeRange === option.value
                        ? darkMode ? 'bg-blue-600 text-white' : 'bg-blue-600 text-white'
                        : darkMode ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Clear All Providers Button */}
            {(selectedInferenceProviders.size > 0 || selectedModelProviders.size > 0) && (
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => {
                    setSelectedInferenceProviders(new Set());
                    setSelectedModelProviders(new Set());
                  }}
                  className={`px-4 py-2 text-sm rounded-md font-medium transition-colors ${
                    darkMode ? 'bg-red-600 hover:bg-red-500 text-white' : 'bg-red-600 hover:bg-red-700 text-white'
                  }`}
                >
                  Clear All Providers
                </button>
                <span className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  {selectedInferenceProviders.size + selectedModelProviders.size} provider(s) selected
                </span>
              </div>
            )}

            {/* Provider Filters */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Inference Providers */}
              <div>
                <h3 className={`text-sm font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  Inference Providers (Dashed Lines) - <span className="text-xs font-normal opacity-75">(latest count)</span>
                </h3>
                <div className="flex flex-wrap gap-2">
                  {availableProviders.inferenceProviders.map(item => (
                    <button
                      key={item.provider}
                      onClick={() => toggleProvider(item.provider, 'inference')}
                      className={`px-3 py-1 text-xs rounded-md flex items-center gap-2 transition-colors ${
                        selectedInferenceProviders.has(item.provider)
                          ? 'bg-blue-600 text-white'
                          : darkMode ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      <span>{item.provider}</span>
                      <span className="font-mono text-xs opacity-75">({item.count})</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Model Providers */}
              <div>
                <h3 className={`text-sm font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  Model Providers (Dotted Lines) - <span className="text-xs font-normal opacity-75">(latest count)</span>
                </h3>
                <div className="flex flex-wrap gap-2">
                  {availableProviders.modelProviders.map(item => (
                    <button
                      key={item.provider}
                      onClick={() => toggleProvider(item.provider, 'model')}
                      className={`px-3 py-1 text-xs rounded-md flex items-center gap-2 transition-colors ${
                        selectedModelProviders.has(item.provider)
                          ? 'bg-green-600 text-white'
                          : darkMode ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      <span>{item.provider}</span>
                      <span className="font-mono text-xs opacity-75">({item.count})</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Chart */}
          <div className="h-96 relative">
            <Line data={chartData} options={chartOptions} />
            {selectedInferenceProviders.size === 0 && selectedModelProviders.size === 0 && (
              <div className={`absolute top-4 right-4 px-3 py-2 rounded-md text-xs ${
                darkMode ? 'bg-blue-900/30 text-blue-200 border border-blue-600/30' : 'bg-blue-50 text-blue-700 border border-blue-200'
              }`}>
                💡 Select providers above to compare their model counts
              </div>
            )}
          </div>

          {/* Stats */}
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-700' : 'bg-gray-100'}`}>
              <div className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                {(() => {
                  const showTotalLine = selectedInferenceProviders.size === 0 && selectedModelProviders.size === 0;
                  if (showTotalLine) return currentModels.length;
                  
                  // Sum current counts for selected providers
                  let total = 0;
                  selectedInferenceProviders.forEach(provider => {
                    const counts = {};
                    currentModels.forEach(model => {
                      const inferenceProvider = model.inference_provider || 'Unknown';
                      counts[inferenceProvider] = (counts[inferenceProvider] || 0) + 1;
                    });
                    total += counts[provider] || 0;
                  });
                  selectedModelProviders.forEach(provider => {
                    const counts = {};
                    currentModels.forEach(model => {
                      const modelProvider = model.model_provider || 'Unknown';
                      counts[modelProvider] = (counts[modelProvider] || 0) + 1;
                    });
                    total += counts[provider] || 0;
                  });
                  return total;
                })()}
              </div>
              <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                Current Count
              </div>
            </div>
            <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-700' : 'bg-gray-100'}`}>
              <div className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                {filteredData.length}
              </div>
              <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                Data Points
              </div>
            </div>
            <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-700' : 'bg-gray-100'}`}>
              <div className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                {(() => {
                  const showTotalLine = selectedInferenceProviders.size === 0 && selectedModelProviders.size === 0;
                  if (showTotalLine) {
                    return filteredData.length > 0 ? Math.max(...filteredData.map(d => d.totalCount)) : 0;
                  }
                  
                  // Calculate peak for selected providers
                  const allValues = filteredData.flatMap(point => [
                    ...selectedInferenceProviders.size > 0 
                      ? Array.from(selectedInferenceProviders).map(provider => 
                          point.providerCounts.inferenceProviders[provider] || 0
                        ) 
                      : [],
                    ...selectedModelProviders.size > 0 
                      ? Array.from(selectedModelProviders).map(provider => 
                          point.providerCounts.modelProviders[provider] || 0
                        ) 
                      : []
                  ]);
                  return allValues.length > 0 ? Math.max(...allValues) : 0;
                })()}
              </div>
              <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                Peak Count
              </div>
            </div>
            <div className={`p-3 rounded-lg ${darkMode ? 'bg-gray-700' : 'bg-gray-100'}`}>
              <div className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                {(() => {
                  if (filteredData.length < 2) return '0';
                  
                  const showTotalLine = selectedInferenceProviders.size === 0 && selectedModelProviders.size === 0;
                  if (showTotalLine) {
                    const change = filteredData[filteredData.length - 1].totalCount - filteredData[filteredData.length - 2].totalCount;
                    return (change >= 0 ? '+' : '') + change;
                  }
                  
                  // Calculate daily change for selected providers
                  const latest = filteredData[filteredData.length - 1];
                  const previous = filteredData[filteredData.length - 2];
                  
                  let latestTotal = 0;
                  let previousTotal = 0;
                  
                  selectedInferenceProviders.forEach(provider => {
                    latestTotal += latest.providerCounts.inferenceProviders[provider] || 0;
                    previousTotal += previous.providerCounts.inferenceProviders[provider] || 0;
                  });
                  selectedModelProviders.forEach(provider => {
                    latestTotal += latest.providerCounts.modelProviders[provider] || 0;
                    previousTotal += previous.providerCounts.modelProviders[provider] || 0;
                  });
                  
                  const change = latestTotal - previousTotal;
                  return (change >= 0 ? '+' : '') + change;
                })()}
              </div>
              <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                Daily Change
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ModelCountLineGraph;