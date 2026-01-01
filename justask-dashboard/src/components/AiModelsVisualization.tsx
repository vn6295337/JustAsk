import React, { useState, useEffect, useLayoutEffect, useRef, CSSProperties } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { ChevronDown, ChevronRight, Filter, X, Moon, Sun, BarChart3, Search } from 'lucide-react';
import { Link } from 'react-router-dom';

const AiModelsVisualization = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [darkMode, setDarkMode] = useState(true);
  const [columnFilters, setColumnFilters] = useState({
    inferenceProvider: new Set<string>(),
    modelProvider: new Set<string>(), 
    modelName: new Set<string>(),
    modelProviderCountry: new Set<string>(),
    inputModalities: new Set<string>(),
    outputModalities: new Set<string>(),
    license: new Set<string>(),
    rateLimits: new Set<string>(),
    apiAccess: new Set<string>()
  });
  const [openFilter, setOpenFilter] = useState<string | null>(null);
  const [sortConfig, setSortConfig] = useState<{key: string; direction: 'asc' | 'desc'} | null>(null);
  const [bannerText, setBannerText] = useState<string>("🔴 LIVE: JustAsk Dashboard - Loading...");
  const containerRef = useRef<HTMLDivElement>(null);
  const unitRef = useRef<HTMLSpanElement>(null);
  const [spacerWidth, setSpacerWidth] = useState(0);
  const [unitWidth, setUnitWidth] = useState(0);
  const [ready, setReady] = useState(false);

  // Search state for filtering dropdown options
  const [dropdownSearchTerms, setDropdownSearchTerms] = useState({
    inferenceProvider: '',
    modelProvider: '',
    modelName: '',
    modelProviderCountry: '',
    inputModalities: '',
    outputModalities: '',
    license: '',
    rateLimits: '',
    apiAccess: ''
  });
  

  const fetchModelData = async () => {
    try {
      console.log('Fetching model data from ai_models_main...');
      const response = await supabase
        .from('ai_models_main')
        .select('*')
        .order('id', { ascending: true });

      console.log('Supabase response:', response);

      if (response.error) {
        console.error('Supabase error:', response.error);
        throw new Error(`Supabase error: ${response.error.message}`);
      }

      if (!response.data || response.data.length === 0) {
        console.warn('No data returned from Supabase');
        throw new Error('No data available from ai_models_main table');
      }

      console.log(`Successfully fetched ${response.data.length} records`);
      console.log('Sample record:', response.data[0]);
      console.log('Sample record fields:', Object.keys(response.data[0]));
      return response.data;
    } catch (err) {
      console.error('Error fetching data:', err);
      throw err;
    }
  };

  const [models, setModels] = useState<any[]>([]);

  // Get unique values for each column based on current filters (relational filtering)
  const getUniqueValues = (columnKey: keyof typeof columnFilters) => {
    const values = new Set<string>();
    
    // Get data that matches all OTHER filters (excluding the current column being filtered)
    const relevantData = models.filter(model => {
      const inferenceProvider = model.inference_provider || 'Unknown';
      const modelProvider = model.model_provider || 'Unknown';
      const modelName = model.human_readable_name || 'Unknown';
      const modelProviderCountry = model.model_provider_country || 'Unknown';
      const inputModalities = model.input_modalities || 'Unknown';
      const outputModalities = model.output_modalities || 'Unknown';
      const license = model.license_name || 'N/A';
      const rateLimits = model.rate_limits || 'N/A';
      const apiAccess = model.provider_api_access || 'N/A';

      return (
        (columnKey === 'inferenceProvider' || columnFilters.inferenceProvider.size === 0 || columnFilters.inferenceProvider.has(inferenceProvider)) &&
        (columnKey === 'modelProvider' || columnFilters.modelProvider.size === 0 || columnFilters.modelProvider.has(modelProvider)) &&
        (columnKey === 'modelName' || columnFilters.modelName.size === 0 || columnFilters.modelName.has(modelName)) &&
        (columnKey === 'modelProviderCountry' || columnFilters.modelProviderCountry.size === 0 || columnFilters.modelProviderCountry.has(modelProviderCountry)) &&
        (columnKey === 'inputModalities' || columnFilters.inputModalities.size === 0 || columnFilters.inputModalities.has(inputModalities)) &&
        (columnKey === 'outputModalities' || columnFilters.outputModalities.size === 0 || columnFilters.outputModalities.has(outputModalities)) &&
        (columnKey === 'license' || columnFilters.license.size === 0 || columnFilters.license.has(license)) &&
        (columnKey === 'rateLimits' || columnFilters.rateLimits.size === 0 || columnFilters.rateLimits.has(rateLimits)) &&
        (columnKey === 'apiAccess' || columnFilters.apiAccess.size === 0 || columnFilters.apiAccess.has(apiAccess))
      );
    });

    relevantData.forEach(model => {
      let value = '';
      switch(columnKey) {
        case 'inferenceProvider':
          value = model.inference_provider || 'Unknown';
          break;
        case 'modelProvider':
          value = model.model_provider || 'Unknown';
          break;
        case 'modelName':
          value = model.human_readable_name || 'Unknown';
          break;
        case 'modelProviderCountry':
          value = model.model_provider_country || 'Unknown';
          break;
        case 'inputModalities':
          value = model.input_modalities || 'Unknown';
          break;
        case 'outputModalities':
          value = model.output_modalities || 'Unknown';
          break;
        case 'license':
          value = model.license_name || 'N/A';
          break;
        case 'rateLimits':
          value = model.rate_limits || 'N/A';
          break;
        case 'apiAccess':
          value = model.provider_api_access || 'N/A';
          break;
      }
      values.add(value);
    });
    return Array.from(values).sort();
  };

  // Sort function
  const handleSort = (key: string) => {
    let direction: 'asc' | 'desc' = 'asc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  // Get sortable value from model
  const getSortableValue = (model: any, key: string) => {
    switch(key) {
      case 'inferenceProvider':
        return model.inference_provider || 'Unknown';
      case 'modelProvider':
        return model.model_provider || 'Unknown';
      case 'modelName':
        return model.human_readable_name || 'Unknown';
      case 'modelProviderCountry':
        return model.model_provider_country || 'Unknown';
      case 'inputModalities':
        return model.input_modalities || 'Unknown';
      case 'outputModalities':
        return model.output_modalities || 'Unknown';
      case 'license':
        return model.license_name || 'N/A';
      case 'rateLimits':
        return model.rate_limits || 'N/A';
      case 'apiAccess':
        return model.provider_api_access || 'N/A';
      default:
        return '';
    }
  };

  // Filter models based on current filters
  const filteredModels = models.filter(model => {
    const inferenceProvider = model.inference_provider || 'Unknown';
    const modelProvider = model.model_provider || 'Unknown';
    const modelName = model.human_readable_name || 'Unknown';
    const modelProviderCountry = model.model_provider_country || 'Unknown';
    const inputModalities = model.input_modalities || 'Unknown';
    const outputModalities = model.output_modalities || 'Unknown';
    const license = model.license_name || 'N/A';
    const rateLimits = model.rate_limits || 'N/A';
    const apiAccess = model.provider_api_access || 'N/A';

    // Filter out Dolphin models from Cognitive Computations
    if (modelProvider === 'Cognitive Computations' && modelName.toLowerCase().includes('dolphin')) {
      return false;
    }

    // Apply checkbox filters
    return (
      (columnFilters.inferenceProvider.size === 0 || columnFilters.inferenceProvider.has(inferenceProvider)) &&
      (columnFilters.modelProvider.size === 0 || columnFilters.modelProvider.has(modelProvider)) &&
      (columnFilters.modelName.size === 0 || columnFilters.modelName.has(modelName)) &&
      (columnFilters.modelProviderCountry.size === 0 || columnFilters.modelProviderCountry.has(modelProviderCountry)) &&
      (columnFilters.inputModalities.size === 0 || columnFilters.inputModalities.has(inputModalities)) &&
      (columnFilters.outputModalities.size === 0 || columnFilters.outputModalities.has(outputModalities)) &&
      (columnFilters.license.size === 0 || columnFilters.license.has(license)) &&
      (columnFilters.rateLimits.size === 0 || columnFilters.rateLimits.has(rateLimits)) &&
      (columnFilters.apiAccess.size === 0 || columnFilters.apiAccess.has(apiAccess))
    );
  }).sort((a, b) => {
    if (!sortConfig) return 0;
    
    const aValue = getSortableValue(a, sortConfig.key);
    const bValue = getSortableValue(b, sortConfig.key);
    
    if (aValue < bValue) {
      return sortConfig.direction === 'asc' ? -1 : 1;
    }
    if (aValue > bValue) {
      return sortConfig.direction === 'asc' ? 1 : -1;
    }
    return 0;
  });

  // Toggle filter value
  const toggleFilterValue = (columnKey: keyof typeof columnFilters, value: string) => {
    setColumnFilters(prev => {
      const newSet = new Set(prev[columnKey]);
      if (newSet.has(value)) {
        newSet.delete(value);
      } else {
        newSet.add(value);
      }
      return { ...prev, [columnKey]: newSet };
    });
  };

  // Clear all filters for a column
  const clearColumnFilter = (columnKey: keyof typeof columnFilters) => {
    setColumnFilters(prev => ({
      ...prev,
      [columnKey]: new Set<string>()
    }));
  };

  // Handle dropdown search input change
  const handleDropdownSearchChange = (columnKey: keyof typeof dropdownSearchTerms, value: string) => {
    setDropdownSearchTerms(prev => ({
      ...prev,
      [columnKey]: value
    }));
  };

  // Filter dropdown options based on search term
  const getFilteredDropdownOptions = (columnKey: keyof typeof columnFilters) => {
    const allOptions = getUniqueValues(columnKey);
    const searchTerm = dropdownSearchTerms[columnKey].toLowerCase();
    
    if (!searchTerm) return allOptions;
    
    return allOptions.filter(option => 
      option.toLowerCase().includes(searchTerm)
    );
  };


  useEffect(() => {
    const loadData = async () => {
      try {
        const rawData = await fetchModelData();
        console.log('Raw data length:', rawData.length);
        setModels(rawData);
        setLastRefresh(new Date());
      } catch (err: any) {
        console.error('Load data error:', err);
        setError(err.message || 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    loadData();

    // Set up auto-refresh every 5 minutes
    const interval = setInterval(loadData, 5 * 60 * 1000);

    // Cleanup interval on unmount
    return () => clearInterval(interval);
  }, []);

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
  }, [bannerText, loading]);

  // Close filter dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest('.filter-dropdown') && !target.closest('.filter-button')) {
        setOpenFilter(null);
        // Clear dropdown search terms when closing
        setDropdownSearchTerms({
          inferenceProvider: '',
          modelProvider: '',
          modelName: '',
          modelProviderCountry: '',
          inputModalities: '',
          outputModalities: '',
          license: '',
          rateLimits: '',
          apiAccess: ''
        });
      }
    };

    if (openFilter) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [openFilter]);

  if (loading) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${darkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
        <div className={`text-lg ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>Loading AI models data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${darkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
        <div className="text-red-600">Error: {error}</div>
      </div>
    );
  }

  if (!loading && models.length === 0) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${darkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
        <div className={`${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>No data available</div>
      </div>
    );
  }

  // Complex license mapping removed - now using database fields directly

  // Update official URL for Kimi/Moonshot models
  const getOfficialUrl = (model: any) => {
    const modelName = model.human_readable_name || '';
    if (modelName.includes('Moonshot') || modelName.includes('Kimi')) {
      return 'https://www.moonshot.ai/';
    }
    return model.official_url;
  };

  return (
    <div className={`min-h-screen py-4 ${darkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full flex flex-col">
        {/* Header */}
        <div className="text-center mb-4">
          {/* Mobile: Stack vertically */}
          <div className="block md:hidden space-y-4">
            <h1 className={`text-xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              JustAsk <span className="text-base font-normal">Dashboard</span>
            </h1>
            <div className="flex justify-center space-x-4">
              {/* Analytics Link */}
              <Link
                to="/analytics"
                className={`inline-flex items-center px-3 py-2 rounded-lg transition-colors ${
                  darkMode ? 'bg-gray-800 text-blue-400 hover:bg-gray-700' : 'bg-white text-blue-600 hover:bg-gray-100'
                }`}
                title="View Analytics Dashboard"
              >
                <BarChart3 size={18} className="mr-2" />
                Analytics
              </Link>

              {/* Dark Mode Toggle */}
              <button
                onClick={() => setDarkMode(!darkMode)}
                className={`p-2 rounded-lg ${
                  darkMode ? 'bg-gray-800 text-yellow-400 hover:bg-gray-700' : 'bg-white text-gray-600 hover:bg-gray-100'
                } transition-colors`}
              >
                {darkMode ? <Sun size={18} /> : <Moon size={18} />}
              </button>
            </div>
          </div>

          {/* Desktop: Original layout */}
          <div className="hidden md:block relative">
            {/* Analytics Link */}
            <Link
              to="/analytics"
              className={`absolute left-0 top-0 inline-flex items-center px-3 py-2 rounded-lg transition-colors ${
                darkMode ? 'bg-gray-800 text-blue-400 hover:bg-gray-700' : 'bg-white text-blue-600 hover:bg-gray-100'
              }`}
              title="View Analytics Dashboard"
            >
              <BarChart3 size={20} className="mr-2" />
              Analytics
            </Link>

            {/* Dark Mode Toggle */}
            <button
              onClick={() => setDarkMode(!darkMode)}
              className={`absolute right-0 top-0 p-2 rounded-lg ${
                darkMode ? 'bg-gray-800 text-yellow-400 hover:bg-gray-700' : 'bg-white text-gray-600 hover:bg-gray-100'
              } transition-colors`}
            >
              {darkMode ? <Sun size={20} /> : <Moon size={20} />}
            </button>
            
            <h1 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              JustAsk <span className="text-lg font-normal">Dashboard</span>
            </h1>
          </div>
        </div>

        {/* Rolling TV News Banner */}
        <div className={`relative overflow-hidden py-3 ${
          darkMode ? 'bg-red-900 border-red-700' : 'bg-red-600 border-red-400'
        } border-y-2 my-4`}>
          <div ref={containerRef} className="overflow-hidden">
            <div
              className="whitespace-nowrap will-change-transform banner-scroll-pause"
              style={{
                '--d': `${unitWidth}px`,
                animation: ready ? 'scrollX 20s linear infinite' : undefined
              } as CSSProperties}
            >
              <span ref={unitRef} className="inline-flex items-center flex-shrink-0">
                <span className="text-white font-semibold text-lg tracking-wide px-8">{bannerText}</span>
                <span aria-hidden style={{ display: 'inline-block', width: spacerWidth }} />
              </span>
              <span aria-hidden className="inline-flex items-center flex-shrink-0">
                <span className="text-white font-semibold text-lg tracking-wide px-8">{bannerText}</span>
                <span aria-hidden style={{ display: 'inline-block', width: spacerWidth }} />
              </span>
            </div>
          </div>
        </div>

        <div className="flex-1 space-y-4">
          {/* Version Info */}
          <div className={`text-base text-center ${darkMode ? 'text-gray-400' : 'text-gray-500'} space-y-1`}>
            <p className="mt-2">
              Last Refresh: {lastRefresh.toLocaleString('en-US', { 
                timeZone: 'UTC', 
                year: 'numeric', 
                month: 'short', 
                day: '2-digit', 
                hour: '2-digit', 
                minute: '2-digit'
              })} UTC | <strong>Total Models: {filteredModels.length}<sup>*</sup></strong>
            </p>
            <p className={`text-sm ${darkMode ? 'text-gray-500' : 'text-gray-400'} mt-1`}>
              *Exclusions: Experimental, preview, test, and beta models; Models with unknown origins or no/unclear license info; Models requiring payment info.
            </p>
          </div>

          {/* Clear Filters Button */}
          {Object.values(columnFilters).some(set => set.size > 0) && (
            <div className="flex justify-center">
              <button
                onClick={() => setColumnFilters({
                  inferenceProvider: new Set<string>(),
                  modelProvider: new Set<string>(),
                  modelName: new Set<string>(),
                  modelProviderCountry: new Set<string>(),
                  inputModalities: new Set<string>(),
                  outputModalities: new Set<string>(),
                  license: new Set<string>(),
                  rateLimits: new Set<string>(),
                  apiAccess: new Set<string>()
                })}
                className={`px-4 py-2 rounded-md transition-colors font-medium ${
                  darkMode 
                    ? 'bg-red-600 hover:bg-red-500 text-white'
                    : 'bg-red-600 hover:bg-red-700 text-white'
                }`}
              >
                Clear All Filters
              </button>
            </div>
          )}

          {/* Simple Structured Table */}
          <div className={`p-6 rounded-lg shadow-lg ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
            <div className="overflow-x-auto min-h-[400px]">
              <table className="w-full border-collapse" style={{ tableLayout: 'auto' }}>
                <thead>
                  <tr className={`border-b ${darkMode ? 'border-gray-600' : 'border-gray-300'}`}>
                    <th className={`text-left py-3 px-4 font-semibold ${darkMode ? 'text-white' : 'text-gray-900'}`}>#</th>
                    {[
                      { key: 'inferenceProvider', label: 'Inference Provider', className: 'min-w-[100px] max-w-[120px]' },
                      { key: 'modelProvider', label: 'Model Provider', className: 'min-w-[100px] max-w-[120px]' },
                      { key: 'modelName', label: 'Model Name', className: 'min-w-[200px] max-w-[300px]' },
                      { key: 'modelProviderCountry', label: 'Country of Origin', className: 'min-w-[120px] max-w-[150px]' },
                      { key: 'inputModalities', label: 'Input Type', className: 'min-w-[150px] max-w-[200px]' },
                      { key: 'outputModalities', label: 'Output Type', className: 'min-w-[100px] max-w-[130px]' },
                      { key: 'license', label: 'License', className: 'min-w-[80px] max-w-[100px]' },
                      { key: 'rateLimits', label: 'Rate Limits', className: 'min-w-[180px] max-w-[250px]' },
                      { key: 'apiAccess', label: 'API Access', className: 'min-w-[100px] max-w-[120px]' }
                    ].map((column) => (
                      <th key={column.key} className={`text-left py-3 px-4 font-semibold ${darkMode ? 'text-white' : 'text-gray-900'} relative ${column.className || ''}`}>
                        <div className="flex items-center justify-between">
                          <button
                            onClick={() => handleSort(column.key)}
                            className="flex items-center hover:opacity-75 transition-opacity"
                          >
                            <span>{column.label}</span>
                            {sortConfig?.key === column.key && (
                              <span className="ml-1">
                                {sortConfig.direction === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </button>
                          <div className="relative">
                            <button
                              onClick={() => setOpenFilter(openFilter === column.key ? null : column.key)}
                              className={`filter-button ml-2 p-1 rounded hover:bg-opacity-20 ${
                                columnFilters[column.key as keyof typeof columnFilters].size > 0
                                  ? 'text-blue-600'
                                  : darkMode ? 'text-gray-400 hover:text-gray-300' : 'text-gray-500 hover:text-gray-700'
                              }`}
                            >
                              <Filter className="w-4 h-4" />
                            </button>
                            
                            {openFilter === column.key && (
                              <div className={`filter-dropdown absolute top-full ${
                                ['inferenceProvider', 'modelProvider'].includes(column.key) ? 'left-0' : 'right-0'
                              } ${column.key === 'apiAccess' ? 'right-0' : ''} mt-1 w-64 max-h-80 overflow-y-auto ${
                                darkMode ? 'bg-gray-800 border-gray-600' : 'bg-white border-gray-300'
                              } border rounded-lg shadow-lg z-50`}>
                                <div className="p-2">
                                  <div className="flex justify-between items-center mb-2">
                                    <span className={`text-sm font-medium ${darkMode ? 'text-gray-200' : 'text-gray-800'}`}>Filter {column.label}</span>
                                    <button
                                      onClick={() => clearColumnFilter(column.key as keyof typeof columnFilters)}
                                      className={`text-xs px-2 py-1 rounded ${
                                        darkMode 
                                          ? 'bg-red-600 hover:bg-red-500 text-white' 
                                          : 'bg-red-600 hover:bg-red-700 text-white'
                                      }`}
                                    >
                                      Clear
                                    </button>
                                  </div>
                                  
                                  {/* Search input */}
                                  <div className="mb-2 relative">
                                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-gray-400" />
                                    <input
                                      type="text"
                                      placeholder="Search options..."
                                      value={dropdownSearchTerms[column.key as keyof typeof dropdownSearchTerms]}
                                      onChange={(e) => handleDropdownSearchChange(column.key as keyof typeof dropdownSearchTerms, e.target.value)}
                                      className={`w-full pl-8 pr-3 py-2 text-sm border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                                        darkMode 
                                          ? 'bg-gray-700 border-gray-600 text-gray-200 placeholder-gray-400' 
                                          : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                                      }`}
                                    />
                                  </div>
                                  
                                  <div className="space-y-1 max-h-60 overflow-y-auto">
                                    {getFilteredDropdownOptions(column.key as keyof typeof columnFilters).map((value) => (
                                      <label key={value} className="flex items-center space-x-2 cursor-pointer">
                                        <input
                                          type="checkbox"
                                          checked={columnFilters[column.key as keyof typeof columnFilters].has(value)}
                                          onChange={() => toggleFilterValue(column.key as keyof typeof columnFilters, value)}
                                          className="w-4 h-4"
                                        />
                                        <span className={`text-sm truncate ${darkMode ? 'text-gray-300' : 'text-gray-800'}`} title={value}>
                                          {value}
                                        </span>
                                      </label>
                                    ))}
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredModels.map((model, index) => {
                    return (
                      <tr key={index} className={`border-b ${darkMode ? 'border-gray-600' : 'border-gray-200'} ${index % 2 === 0 
                        ? darkMode ? 'bg-gray-800/50' : 'bg-gray-50/50'
                        : darkMode ? 'bg-gray-900' : 'bg-white'
                      } ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-blue-50'} transition-colors`}>
                        <td className={`py-3 px-4 text-sm font-mono ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{index + 1}</td>
                        <td className={`py-3 px-4 text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'} min-w-[100px] max-w-[120px] truncate`}>{model.inference_provider || 'Unknown'}</td>
                        <td className={`py-3 px-4 text-sm min-w-[100px] max-w-[120px] truncate`}>
                          {(() => {
                            const officialUrl = getOfficialUrl(model);
                            const providerName = model.model_provider || 'Unknown';
                            return officialUrl && officialUrl.startsWith('http') ? (
                              <a 
                                href={officialUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className={`${darkMode ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-800'} hover:underline`}
                              >
                                {providerName}
                              </a>
                            ) : (
                              <span className={`${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>{providerName}</span>
                            );
                          })()} 
                        </td>
                        <td className={`py-3 px-4 text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'} min-w-[200px] max-w-[300px]`}>{model.human_readable_name || 'Unknown'}</td>
                        <td className={`py-3 px-4 text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'} min-w-[120px] max-w-[150px] truncate`}>{model.model_provider_country || 'Unknown'}</td>
                        <td className={`py-3 px-4 text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'} min-w-[150px] max-w-[200px]`}>{model.input_modalities || 'Unknown'}</td>
                        <td className={`py-3 px-4 text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'} min-w-[100px] max-w-[130px] truncate`}>{model.output_modalities || 'Unknown'}</td>
                        <td className="py-3 px-4 text-sm min-w-[80px] max-w-[100px]">
                          <div className="text-center">
                            {/* Top line: Info text with URL */}
                            {model.license_info_text && (
                              model.license_info_url ? (
                                <a
                                  href={model.license_info_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className={`${darkMode ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-800'} hover:underline block`}
                                >
                                  {model.license_info_text}
                                </a>
                              ) : (
                                <span className={`${darkMode ? 'text-gray-300' : 'text-gray-700'} block`}>{model.license_info_text}</span>
                              )
                            )}
                            {/* Bottom line: License name with URL */}
                            {model.license_name && (
                              model.license_url ? (
                                <a
                                  href={model.license_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className={`${darkMode ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-800'} hover:underline block`}
                                >
                                  {model.license_name}
                                </a>
                              ) : (
                                <span className={`${darkMode ? 'text-gray-300' : 'text-gray-700'} block`}>{model.license_name}</span>
                              )
                            )}
                          </div>
                        </td>
                        <td className={`py-3 px-4 text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'} min-w-[180px] max-w-[250px]`}>{model.rate_limits || 'N/A'}</td>
                        <td className="py-3 px-4 text-center min-w-[100px] max-w-[120px]">
                          {model.provider_api_access && model.provider_api_access.startsWith('http') ? (
                            <a 
                              href={model.provider_api_access}
                              target="_blank"
                              rel="noopener noreferrer"
                              title="Get API Key"
                              className={`inline-flex items-center justify-center w-8 h-8 rounded-full transition-colors ${
                                darkMode 
                                  ? 'bg-blue-600 hover:bg-blue-500 text-white' 
                                  : 'bg-blue-600 hover:bg-blue-700 text-white'
                              }`}
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m0 0a2 2 0 012 2 2 2 0 01-2 2m-2-2h.01M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                            </a>
                          ) : (
                            <span className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{model.provider_api_access || 'N/A'}</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              
              {filteredModels.length === 0 && models.length > 0 && (
                <div className="flex items-center justify-center py-12 text-gray-600">
                  <div className="text-center">
                    <Filter className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p className="text-lg font-medium">No models match the current filters</p>
                    <p className="text-sm mt-2">Try adjusting or clearing some filters to see results</p>
                  </div>
                </div>
              )}
            </div>
            
            {/* Filter summary */}
            {Object.values(columnFilters).some(set => set.size > 0) && (
              <div className="mt-4 p-3 rounded-lg border-l-4 bg-blue-50 border-blue-500 text-blue-800">
                <span className="text-sm">
                  Showing {filteredModels.length} of {models.length} models with active filters
                </span>
              </div>
            )}
            
          </div>
        </div>


        {/* Legal Disclaimer */}
        <div className={`mt-8 pt-6 border-t rounded-lg p-4 ${
          darkMode 
            ? 'border-gray-600 bg-gray-800' 
            : 'border-gray-300 bg-gray-50'
        }`}>
          <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            <h4 className={`font-semibold mb-3 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>Important Legal Disclaimer</h4>
            <div className="space-y-2">
              <p>
                <strong>For informational purposes only:</strong> This dashboard provides information about AI models and their availability. Model data is sourced from provider APIs and public documentation. Information is updated on a best-effort basis and may not reflect the most current status. All data is provided “as-is,” without warranties of any kind, including but not limited to accuracy, completeness, merchantability, fitness for a particular purpose, or non-infringement.
              </p>
              <p>
                <strong>No liability:</strong> We are not responsible for model accuracy, availability, pricing, rate limits, licensing terms, or any issues arising from the use of these models. We disclaim all liability for direct, indirect, incidental, consequential, or special damages of any kind. Users must independently verify all information before relying on it.
              </p>
              <p>
                <strong>Independence:</strong> This platform is independent and not affiliated with, sponsored by, or endorsed by any model provider.
              </p>
              <p>
                <strong>Terms compliance:</strong> Users are solely responsible for complying with each provider’s terms of service, usage policies, and applicable laws. Some models may have restrictions on commercial use, data processing, or geographic availability.
              </p>
              <p>
                <strong>Rate limits:</strong> Displayed rate limits reflect publicly available or free-tier usage and may change without notice. Actual limits vary by provider, account status, and usage history.
              </p>
              <p>
                <strong>License verification:</strong> License details shown are for reference only. Users must verify current license terms directly with the provider before using any model in production.
              </p>
            </div>
            <p className="font-medium mt-4">
              © 2025 JustAsk - AI Model Discovery Platform
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AiModelsVisualization;