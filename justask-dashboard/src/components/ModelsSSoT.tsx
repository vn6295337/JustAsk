import React, { useState, useEffect, useMemo } from 'react';
import { 
  Search, 
  Filter, 
  Download, 
  Moon, 
  Sun, 
  ChevronDown, 
  ChevronRight, 
  X, 
  Menu,
  Eye,
  Calendar,
  Zap,
  ArrowLeft
} from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';

export interface ModelRecord {
  provider: string;
  modelName: string;
  accessType: string;
  license: string;
  pricing: string;
  providerApiAccess: string;
  lastUpdated: string;
  modelOriginator: string;
  rateLimits: string;
  taskType: string;
}

interface Filters {
  providers: string[];
  licenses: string[];
  pricing: string;
  taskTypes: string[];
  freeOnly: boolean;
}

interface QuickView {
  id: string;
  label: string;
  filter: (models: ModelRecord[]) => ModelRecord[];
  icon: React.ReactNode;
}

const ModelsSSoT: React.FC<{ csvData?: string }> = ({ csvData }) => {
  // State management
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<keyof ModelRecord>('lastUpdated');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [activeQuickView, setActiveQuickView] = useState<string>('all');
  const [showFilters, setShowFilters] = useState(false);
  const [showMobileFilters, setShowMobileFilters] = useState(false);
  const [selectedModel, setSelectedModel] = useState<ModelRecord | null>(null);
  const [isMobile, setIsMobile] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rawData, setRawData] = useState<any[]>([]);
  
  const [filters, setFilters] = useState<Filters>({
    providers: [],
    licenses: [],
    pricing: '',
    taskTypes: [],
    freeOnly: false
  });

  // Fetch data from Supabase
  const fetchModelData = async () => {
    try {
      setLoading(true);
      const response = await supabase
        .from('ai_models_discovery')
        .select('*')
        .order('id', { ascending: false });

      if (response.error) {
        throw response.error;
      }

      if (!response.data || response.data.length === 0) {
        setError('No data available');
        return [];
      }

      setRawData(response.data);
      return response.data;
    } catch (err: any) {
      setError(err.message || 'Failed to load data');
      return [];
    } finally {
      setLoading(false);
    }
  };

  // Transform Supabase data to ModelRecord format
  const transformSupabaseData = (data: any[]): ModelRecord[] => {
    return data.map(item => ({
      provider: item.provider || '',
      modelName: item.model_name || '',
      accessType: item.access_type || 'public',
      license: item.license || '',
      pricing: item.pricing || '',
      providerApiAccess: item.provider_api_access || '',
      lastUpdated: item.last_updated || item.updated_at || '',
      modelOriginator: item.model_originator || item.provider || '',
      rateLimits: item.rate_limits || '',
      taskType: item.task_type || ''
    }));
  };

  // Load models from Supabase or fallback data
  const loadModels = (csv: string): ModelRecord[] => {
    if (rawData.length > 0) {
      return transformSupabaseData(rawData);
    }

    if (!csv) {
      // Fallback dataset
      return [
        {
          provider: 'openrouter',
          modelName: 'mistralai/mistral-7b-instruct:free',
          accessType: 'public',
          license: 'apache-2.0',
          pricing: 'free',
          providerApiAccess: '🔑 API Key Required',
          lastUpdated: '2024',
          modelOriginator: 'Mistral AI',
          rateLimits: '20/min, 50/day',
          taskType: 'conversational'
        },
        {
          provider: 'google',
          modelName: 'gemini-1.5-flash',
          accessType: 'public',
          license: 'proprietary',
          pricing: 'free',
          providerApiAccess: '🔑 API Key Required',
          lastUpdated: 'May 2024',
          modelOriginator: 'Google',
          rateLimits: '15/min, 1M tokens/min',
          taskType: 'conversational'
        },
        {
          provider: 'mistral',
          modelName: 'codestral-latest',
          accessType: 'public',
          license: 'mistral-non-production',
          pricing: 'free',
          providerApiAccess: '🔑 API Key Required',
          lastUpdated: 'Jan 2025',
          modelOriginator: 'Mistral AI',
          rateLimits: '1 req/sec, 500K tokens/min',
          taskType: 'code_generation'
        }
      ];
    }

    const lines = csv.trim().split('\n');
    const headers = lines[0].split(',').map(h => h.trim());
    
    return lines.slice(1).map(line => {
      const values = line.split(',').map(v => v.trim());
      const record: any = {};
      
      headers.forEach((header, index) => {
        const key = header.toLowerCase().replace(/\s+/g, '');
        const mappedKey = {
          'provider': 'provider',
          'modelname': 'modelName',
          'accesstype': 'accessType',
          'license': 'license',
          'pricing': 'pricing',
          'providerapiaccess': 'providerApiAccess',
          'lastupdated': 'lastUpdated',
          'modeloriginator': 'modelOriginator',
          'ratelimits': 'rateLimits',
          'tasktype': 'taskType'
        }[key] || key;
        
        record[mappedKey] = values[index] || '';
      });
      
      return record as ModelRecord;
    }).filter(record => record.modelName && record.provider);
  };

  const models = useMemo(() => loadModels(csvData || ''), [csvData, rawData]);

  // Fetch data on mount
  useEffect(() => {
    fetchModelData();
  }, []);

  // Responsive detection
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Dark mode persistence
  useEffect(() => {
    const saved = localStorage.getItem('darkMode');
    if (saved) {
      setIsDarkMode(JSON.parse(saved));
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(isDarkMode));
    document.documentElement.classList.toggle('dark', isDarkMode);
  }, [isDarkMode]);

  // URL state management
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('search')) setSearchQuery(params.get('search') || '');
    if (params.get('sort')) setSortBy(params.get('sort') as keyof ModelRecord);
    if (params.get('order')) setSortOrder(params.get('order') as 'asc' | 'desc');
  }, []);

  useEffect(() => {
    const params = new URLSearchParams();
    if (searchQuery) params.set('search', searchQuery);
    if (sortBy !== 'lastUpdated') params.set('sort', sortBy);
    if (sortOrder !== 'desc') params.set('order', sortOrder);
    
    const newUrl = `${window.location.pathname}${params.toString() ? '?' + params.toString() : ''}`;
    window.history.replaceState({}, '', newUrl);
  }, [searchQuery, sortBy, sortOrder]);

  // Get unique values for filters
  const uniqueProviders = useMemo(() => [...new Set(models.map(m => m.provider))].sort(), [models]);
  const uniqueLicenses = useMemo(() => [...new Set(models.map(m => m.license))].sort(), [models]);
  const uniqueTaskTypes = useMemo(() => [...new Set(models.map(m => m.taskType))].sort(), [models]);

  // Quick views
  const quickViews: QuickView[] = [
    {
      id: 'all',
      label: 'All Models',
      filter: (models) => models,
      icon: <Eye className="w-4 h-4" />
    },
    {
      id: 'api-required',
      label: 'API Key Required',
      filter: (models) => models.filter(m => m.providerApiAccess.includes('API Key')),
      icon: <Zap className="w-4 h-4" />
    },
    {
      id: 'no-api',
      label: 'No API Key',
      filter: (models) => models.filter(m => !m.providerApiAccess.includes('API Key')),
      icon: <Eye className="w-4 h-4" />
    },
    {
      id: 'recent',
      label: 'Recently Updated',
      filter: (models) => models.filter(m => m.lastUpdated.includes('2024') || m.lastUpdated.includes('2025')),
      icon: <Calendar className="w-4 h-4" />
    }
  ];

  // Filtered and sorted models
  const filteredModels = useMemo(() => {
    let filtered = models;

    // Apply quick view
    const quickView = quickViews.find(qv => qv.id === activeQuickView);
    if (quickView) {
      filtered = quickView.filter(filtered);
    }

    // Apply search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(model =>
        model.modelName.toLowerCase().includes(query) ||
        model.provider.toLowerCase().includes(query) ||
        model.modelOriginator.toLowerCase().includes(query)
      );
    }

    // Apply filters
    if (filters.providers.length > 0) {
      filtered = filtered.filter(m => filters.providers.includes(m.provider));
    }
    if (filters.licenses.length > 0) {
      filtered = filtered.filter(m => filters.licenses.includes(m.license));
    }
    if (filters.taskTypes.length > 0) {
      filtered = filtered.filter(m => filters.taskTypes.includes(m.taskType));
    }
    if (filters.freeOnly) {
      filtered = filtered.filter(m => m.pricing.toLowerCase().includes('free'));
    }

    // Apply sort
    filtered.sort((a, b) => {
      const aVal = a[sortBy];
      const bVal = b[sortBy];
      const comparison = aVal.localeCompare(bVal);
      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return filtered;
  }, [models, searchQuery, filters, sortBy, sortOrder, activeQuickView, quickViews]);

  // Export CSV
  const exportCSV = () => {
    const headers = Object.keys(filteredModels[0] || {});
    const csv = [
      headers.join(','),
      ...filteredModels.map(model =>
        headers.map(header => `"${model[header as keyof ModelRecord]}"`).join(',')
      )
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'free-to-use-models.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  // KPI calculations
  const totalModels = models.length;
  const selectedProviderCount = filters.providers.length > 0 
    ? models.filter(m => filters.providers.includes(m.provider)).length 
    : totalModels;
  const recentlyUpdatedCount = models.filter(m => 
    m.lastUpdated.includes('2024') || m.lastUpdated.includes('2025')
  ).length;

  const baseClasses = {
    bg: isDarkMode ? 'bg-[#0A0A0A]' : 'bg-gray-50',
    surface: isDarkMode ? 'bg-[#111111]' : 'bg-white',
    surfaceHover: isDarkMode ? 'hover:bg-[#1A1A1A]' : 'hover:bg-gray-50',
    border: isDarkMode ? 'border-[#222222]' : 'border-gray-200',
    text: isDarkMode ? 'text-[#E5E5E5]' : 'text-gray-900',
    textMuted: isDarkMode ? 'text-gray-400' : 'text-gray-600',
    accent: isDarkMode ? 'text-[#38BDF8]' : 'text-blue-600',
    accentBg: isDarkMode ? 'bg-[#38BDF8]' : 'bg-blue-600',
    input: isDarkMode ? 'bg-[#111111] border-[#222222] text-[#E5E5E5]' : 'bg-white border-gray-300 text-gray-900',
    button: isDarkMode ? 'bg-[#222222] hover:bg-[#333333] text-[#E5E5E5] border-[#222222]' : 'bg-white hover:bg-gray-50 text-gray-700 border-gray-300',
    buttonPrimary: isDarkMode ? 'bg-[#38BDF8] hover:bg-[#0EA5E9] text-black' : 'bg-blue-600 hover:bg-blue-700 text-white'
  };

  if (loading) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${baseClasses.bg}`}>
        <div className={`text-lg ${baseClasses.text}`}>Loading AI models data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${baseClasses.bg}`}>
        <div className="text-red-600">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen transition-colors duration-200 ${baseClasses.bg}`}>
      {/* Header */}
      <header className={`sticky top-0 z-50 ${baseClasses.surface} ${baseClasses.border} border-b`}>
        <div className="px-4 py-4">
          <div className="text-center mb-4">
            <h1 className={`text-2xl font-bold ${baseClasses.text}`}>
              Free to use models
            </h1>
            <p className={`text-lg mt-2 ${baseClasses.textMuted}`}>
              Interactive tracker of API-accessible and publicly available models
            </p>
            <div className="mt-4">
              <a 
                href="/"
                className={`inline-flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-md transition-colors ${baseClasses.button} border`}
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Dashboard
              </a>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {!isMobile && (
                <div className="flex items-center gap-4 text-sm">
                  <span className={`${baseClasses.textMuted}`}>
                    {filteredModels.length} of {totalModels} models
                  </span>
                </div>
              )}
            </div>
            
            <div className="flex items-center gap-2">
              {!isMobile && (
                <button
                  onClick={exportCSV}
                  className={`inline-flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-md ${baseClasses.button} border transition-colors`}
                >
                  <Download className="w-4 h-4" />
                  Export CSV
                </button>
              )}
              
              <button
                onClick={() => setIsDarkMode(!isDarkMode)}
                className={`p-2 rounded-md ${baseClasses.button} border transition-colors`}
                aria-label="Toggle dark mode"
              >
                {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </button>

              {isMobile && (
                <button
                  onClick={() => setShowMobileFilters(true)}
                  className={`p-2 rounded-md ${baseClasses.button} border transition-colors`}
                >
                  <Menu className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* Search Bar */}
          <div className="mt-4 relative">
            <div className="relative">
              <Search className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 ${baseClasses.textMuted}`} />
              <input
                type="text"
                placeholder="Search models, providers, or originators..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={`w-full pl-10 pr-4 py-2 rounded-md border transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${baseClasses.input}`}
              />
            </div>
          </div>

          {/* KPI Bar */}
          <div className="mt-4 grid grid-cols-3 gap-4 text-center">
            <div>
              <div className={`text-2xl font-bold ${baseClasses.accent}`}>{totalModels}</div>
              <div className={`text-xs ${baseClasses.textMuted}`}>Total Models</div>
            </div>
            <div>
              <div className={`text-2xl font-bold ${baseClasses.accent}`}>{selectedProviderCount}</div>
              <div className={`text-xs ${baseClasses.textMuted}`}>In Selection</div>
            </div>
            <div>
              <div className={`text-2xl font-bold ${baseClasses.accent}`}>{recentlyUpdatedCount}</div>
              <div className={`text-xs ${baseClasses.textMuted}`}>Recent Updates</div>
            </div>
          </div>

          {/* Quick Views */}
          <div className="mt-4 flex gap-2 overflow-x-auto">
            {quickViews.map((view) => (
              <button
                key={view.id}
                onClick={() => setActiveQuickView(view.id)}
                className={`inline-flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-md whitespace-nowrap transition-colors ${
                  activeQuickView === view.id
                    ? baseClasses.buttonPrimary
                    : baseClasses.button + ' border'
                }`}
              >
                {view.icon}
                {view.label}
              </button>
            ))}
          </div>

          {/* Desktop Filters */}
          {!isMobile && (
            <div className="mt-4">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`inline-flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-md ${baseClasses.button} border transition-colors`}
              >
                <Filter className="w-4 h-4" />
                Filters
                {showFilters ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              </button>

              {showFilters && (
                <div className={`mt-4 p-4 rounded-md ${baseClasses.surface} ${baseClasses.border} border`}>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {/* Provider Filter */}
                    <div>
                      <label className={`block text-sm font-medium ${baseClasses.text} mb-2`}>
                        Providers
                      </label>
                      <div className="space-y-2 max-h-32 overflow-y-auto">
                        {uniqueProviders.map((provider) => (
                          <label key={provider} className="flex items-center">
                            <input
                              type="checkbox"
                              checked={filters.providers.includes(provider)}
                              onChange={(e) => {
                                setFilters(prev => ({
                                  ...prev,
                                  providers: e.target.checked
                                    ? [...prev.providers, provider]
                                    : prev.providers.filter(p => p !== provider)
                                }));
                              }}
                              className="mr-2"
                            />
                            <span className={`text-sm ${baseClasses.text}`}>{provider}</span>
                          </label>
                        ))}
                      </div>
                    </div>

                    {/* License Filter */}
                    <div>
                      <label className={`block text-sm font-medium ${baseClasses.text} mb-2`}>
                        Licenses
                      </label>
                      <div className="space-y-2 max-h-32 overflow-y-auto">
                        {uniqueLicenses.map((license) => (
                          <label key={license} className="flex items-center">
                            <input
                              type="checkbox"
                              checked={filters.licenses.includes(license)}
                              onChange={(e) => {
                                setFilters(prev => ({
                                  ...prev,
                                  licenses: e.target.checked
                                    ? [...prev.licenses, license]
                                    : prev.licenses.filter(l => l !== license)
                                }));
                              }}
                              className="mr-2"
                            />
                            <span className={`text-sm ${baseClasses.text}`}>{license}</span>
                          </label>
                        ))}
                      </div>
                    </div>

                    {/* Task Type Filter */}
                    <div>
                      <label className={`block text-sm font-medium ${baseClasses.text} mb-2`}>
                        Task Types
                      </label>
                      <div className="space-y-2 max-h-32 overflow-y-auto">
                        {uniqueTaskTypes.map((taskType) => (
                          <label key={taskType} className="flex items-center">
                            <input
                              type="checkbox"
                              checked={filters.taskTypes.includes(taskType)}
                              onChange={(e) => {
                                setFilters(prev => ({
                                  ...prev,
                                  taskTypes: e.target.checked
                                    ? [...prev.taskTypes, taskType]
                                    : prev.taskTypes.filter(t => t !== taskType)
                                }));
                              }}
                              className="mr-2"
                            />
                            <span className={`text-sm ${baseClasses.text}`}>{taskType}</span>
                          </label>
                        ))}
                      </div>
                    </div>

                    {/* Other Filters */}
                    <div>
                      <label className={`block text-sm font-medium ${baseClasses.text} mb-2`}>
                        Options
                      </label>
                      <div className="space-y-2">
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={filters.freeOnly}
                            onChange={(e) => setFilters(prev => ({ ...prev, freeOnly: e.target.checked }))}
                            className="mr-2"
                          />
                          <span className={`text-sm ${baseClasses.text}`}>Free only</span>
                        </label>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="px-4 py-6">
        {isMobile ? (
          /* Mobile Cards */
          <div className="space-y-4">
            {filteredModels.map((model, index) => (
              <div
                key={index}
                onClick={() => setSelectedModel(model)}
                className={`p-4 rounded-md ${baseClasses.surface} ${baseClasses.border} border ${baseClasses.surfaceHover} cursor-pointer transition-colors`}
              >
                <div className="flex justify-between items-start mb-2">
                  <h3 className={`font-semibold ${baseClasses.text} text-sm`}>
                    {model.modelName}
                  </h3>
                  <span className={`px-2 py-1 rounded text-xs ${baseClasses.accent} bg-opacity-10`}>
                    {model.taskType}
                  </span>
                </div>
                <div className={`text-sm ${baseClasses.textMuted} space-y-1`}>
                  <div>Provider: {model.provider}</div>
                  <div>Originator: {model.modelOriginator}</div>
                  <div>License: {model.license}</div>
                  <div>Updated: {model.lastUpdated}</div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          /* Desktop Table */
          <div className={`rounded-md ${baseClasses.surface} ${baseClasses.border} border overflow-hidden`}>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className={`${baseClasses.surface} ${baseClasses.border} border-b`}>
                  <tr>
                    {[
                      { key: 'modelName', label: 'Model Name' },
                      { key: 'provider', label: 'Provider' },
                      { key: 'modelOriginator', label: 'Originator' },
                      { key: 'taskType', label: 'Task Type' },
                      { key: 'license', label: 'License' },
                      { key: 'pricing', label: 'Pricing' },
                      { key: 'lastUpdated', label: 'Updated' }
                    ].map((column) => (
                      <th
                        key={column.key}
                        className={`px-4 py-3 text-left text-sm font-medium ${baseClasses.text} cursor-pointer ${baseClasses.surfaceHover}`}
                        onClick={() => {
                          if (sortBy === column.key) {
                            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                          } else {
                            setSortBy(column.key as keyof ModelRecord);
                            setSortOrder('asc');
                          }
                        }}
                      >
                        <div className="flex items-center gap-2">
                          {column.label}
                          {sortBy === column.key && (
                            sortOrder === 'asc' ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4 rotate-90" />
                          )}
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredModels.map((model, index) => (
                    <tr
                      key={index}
                      onClick={() => setSelectedModel(model)}
                      className={`${baseClasses.border} border-b last:border-b-0 ${baseClasses.surfaceHover} cursor-pointer transition-colors`}
                    >
                      <td className={`px-4 py-3 text-sm ${baseClasses.text} font-medium`}>
                        {model.modelName}
                      </td>
                      <td className={`px-4 py-3 text-sm ${baseClasses.textMuted}`}>
                        {model.provider}
                      </td>
                      <td className={`px-4 py-3 text-sm ${baseClasses.textMuted}`}>
                        {model.modelOriginator}
                      </td>
                      <td className={`px-4 py-3 text-sm`}>
                        <span className={`px-2 py-1 rounded-full text-xs ${baseClasses.accent} bg-opacity-10`}>
                          {model.taskType}
                        </span>
                      </td>
                      <td className={`px-4 py-3 text-sm ${baseClasses.textMuted}`}>
                        {model.license}
                      </td>
                      <td className={`px-4 py-3 text-sm`}>
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          model.pricing.toLowerCase().includes('free') 
                            ? 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900' 
                            : baseClasses.textMuted
                        }`}>
                          {model.pricing}
                        </span>
                      </td>
                      <td className={`px-4 py-3 text-sm ${baseClasses.textMuted}`}>
                        {model.lastUpdated}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {filteredModels.length === 0 && (
          <div className={`text-center py-12 ${baseClasses.textMuted}`}>
            No models found matching your criteria.
          </div>
        )}
      </main>

      {/* Mobile Filter Drawer */}
      {showMobileFilters && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setShowMobileFilters(false)} />
          <div className={`fixed bottom-0 left-0 right-0 ${baseClasses.surface} rounded-t-lg p-4 max-h-[80vh] overflow-y-auto`}>
            <div className="flex justify-between items-center mb-4">
              <h3 className={`text-lg font-semibold ${baseClasses.text}`}>Filters</h3>
              <button
                onClick={() => setShowMobileFilters(false)}
                className={`p-2 rounded-md ${baseClasses.button}`}
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            
            <div className="space-y-6">
              {/* Mobile filters content - simplified */}
              <div>
                <label className={`block text-sm font-medium ${baseClasses.text} mb-2`}>
                  Free Models Only
                </label>
                <input
                  type="checkbox"
                  checked={filters.freeOnly}
                  onChange={(e) => setFilters(prev => ({ ...prev, freeOnly: e.target.checked }))}
                  className="mr-2"
                />
              </div>

              <button
                onClick={exportCSV}
                className={`w-full inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-md ${baseClasses.buttonPrimary} transition-colors`}
              >
                <Download className="w-4 h-4" />
                Export CSV
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Model Details Modal */}
      {selectedModel && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setSelectedModel(null)} />
          <div className={`relative ${baseClasses.surface} rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto`}>
            <div className="flex justify-between items-start mb-4">
              <h3 className={`text-lg font-semibold ${baseClasses.text}`}>
                {selectedModel.modelName}
              </h3>
              <button
                onClick={() => setSelectedModel(null)}
                className={`p-2 rounded-md ${baseClasses.button} transition-colors`}
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(selectedModel).map(([key, value]) => (
                <div key={key}>
                  <dt className={`text-sm font-medium ${baseClasses.textMuted} mb-1`}>
                    {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                  </dt>
                  <dd className={`text-sm ${baseClasses.text}`}>
                    {value || 'N/A'}
                  </dd>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Status Notice */}
      <div className={`mt-6 mx-4 p-3 rounded-lg ${
        isDarkMode ? 'bg-blue-900 border-blue-700' : 'bg-blue-50 border-blue-200'
      } border`}>
        <p className={`text-sm ${
          isDarkMode ? 'text-blue-200' : 'text-blue-800'
        }`}>
          ℹ️ <strong>Filter Applied:</strong> Only stable models from North American and European companies are displayed. 
          Beta, deprecated, and active status models are filtered out to ensure production-ready options.
        </p>
      </div>

      {/* Legal Disclaimer & Licensing - Footer */}
      <div className={`mt-8 mx-4 pt-6 border-t rounded-lg p-4 ${
        isDarkMode 
          ? 'border-gray-700 bg-gray-800' 
          : 'border-gray-300 bg-gray-50'
      }`}>
        <div className={`text-xs ${
          isDarkMode ? 'text-gray-400' : 'text-gray-500'
        }`}>
          <h4 className={`font-semibold mb-3 ${
            isDarkMode ? 'text-gray-300' : 'text-gray-700'
          }`}>Legal Disclaimer & Licensing</h4>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <p>
                <strong>Educational Purpose:</strong> This dashboard is provided for educational and research purposes only. 
                Model information is aggregated from publicly available APIs and sources.
              </p>
              <p>
                <strong>Model Attribution:</strong> All model names, descriptions, and metadata remain property of their respective creators and providers. 
                This project does not claim ownership of any listed models or their intellectual property.
              </p>
              <p>
                <strong>Dashboard Attribution:</strong> If you use, reference, or derive from this dashboard, you must provide attribution: 
                "Data visualization powered by AI Models Discovery Dashboard - Deployed on Vercel"
              </p>
            </div>
            <div className="space-y-2">
              <p>
                <strong>Accuracy Disclaimer:</strong> While we strive for accuracy, model availability, pricing, and specifications may change. 
                Users should verify current information directly with providers before making decisions.
              </p>
              <p>
                <strong>No Warranty:</strong> This information is provided "as-is" without warranties of any kind. 
                Use of this information is at your own risk.
              </p>
              <p className="font-medium">
                © 2025 AI Models Discovery Dashboard - Licensed under MIT License for educational use only
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModelsSSoT;