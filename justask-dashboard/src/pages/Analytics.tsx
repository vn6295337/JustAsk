import React, { useState, useEffect, useLayoutEffect, useRef, CSSProperties } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { Link } from 'react-router-dom';
import { ArrowLeft, Moon, Sun } from 'lucide-react';
import ModelCountLineGraph from '@/components/ModelCountLineGraph';

const Analytics = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<any[]>([]);
  const [darkMode, setDarkMode] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  // Banner-related state and refs
  const containerRef = useRef<HTMLDivElement>(null);
  const unitRef = useRef<HTMLSpanElement>(null);
  const [bannerText, setBannerText] = useState<string>("🔴 LIVE: JustAsk Dashboard - Loading...");
  const [spacerWidth, setSpacerWidth] = useState(0);
  const [unitWidth, setUnitWidth] = useState(0);
  const [ready, setReady] = useState(false);

  const fetchModelData = async () => {
    try {
      const response = await supabase
        .from('ai_models_main')
        .select('*')
        .order('id', { ascending: true });


      if (response.error) {
        console.error('Supabase error:', response.error);
        throw new Error(`Supabase error: ${response.error.message}`);
      }

      if (!response.data || response.data.length === 0) {
        console.warn('No data returned from Supabase');
        throw new Error('No data available from ai_models_main table');
      }

      return response.data;
    } catch (err) {
      console.error('Error fetching data:', err);
      throw err;
    }
  };

  const hasDataRef = useRef(false);

  useEffect(() => {
    let cancelled = false;
    let requestId = 0;
    const loadData = async () => {
      const myId = ++requestId;
      try {
        const rawData = await fetchModelData();
        if (cancelled || myId !== requestId) return;
        hasDataRef.current = true;
        setError(null);
        // Exclude Dolphin models (Cognitive Computations), same as the main dashboard
        setModels(rawData.filter((m: any) =>
          !(m.model_provider === 'Cognitive Computations' &&
            String(m.human_readable_name || '').toLowerCase().includes('dolphin'))
        ));
        setLastRefresh(new Date());
      } catch (err: any) {
        if (cancelled || myId !== requestId) return;
        console.error('Load data error:', err);
        // Keep showing last good data if a background refresh fails
        if (!hasDataRef.current) setError(err.message || 'Failed to load data');
      } finally {
        if (!cancelled && myId === requestId) setLoading(false);
      }
    };

    loadData();

    // Set up auto-refresh every 5 minutes (same as main dashboard)
    const interval = setInterval(loadData, 5 * 60 * 1000);

    // Cleanup interval on unmount
    return () => { cancelled = true; clearInterval(interval); };
  }, []);

  // Load banner text from file
  useEffect(() => {
    const controller = new AbortController();
    const loadBannerText = async () => {
      try {
        const response = await fetch('/banner-text.txt', { signal: controller.signal });
        if (response.ok) {
          const text = await response.text();
          setBannerText(text.trim() || "🔴 LIVE: JustAsk Dashboard - 50+ free AI models from 3 providers");
        }
      } catch (error) {
        if (controller.signal.aborted) return;
        setBannerText("🔴 LIVE: JustAsk Dashboard - 50+ free AI models from 3 providers");
      }
    };

    loadBannerText();

    // Poll for banner text changes every 30 seconds
    const bannerInterval = setInterval(loadBannerText, 30000);
    return () => { controller.abort(); clearInterval(bannerInterval); };
  }, []);

  // One-time keyframes
  useEffect(() => {
    const id = 'banner-scroll-keyframes-analytics';
    if (document.getElementById(id)) return;
    const style = document.createElement('style');
    style.id = id;
    style.innerHTML = `
      @keyframes scrollXAnalytics {
        from { transform: translate3d(0,0,0); }
        to   { transform: translate3d(calc(-1 * var(--d-analytics, 0px)),0,0); }
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
    let cancelled = false;
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
      fonts.ready.then(() => { if (cancelled) return; fontDone = true; measure(); measureUnit(); });
    }

    // Fallback
    const rAF = requestAnimationFrame(() => { if (!fontDone) { measureUnit(); } });

    return () => {
      cancelled = true;
      window.removeEventListener('resize', onResize);
      cancelAnimationFrame(rAF);
    };
  }, [bannerText, loading]);

  if (loading) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${darkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
        <div className={`text-lg ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>Loading analytics data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${darkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
        <div className="text-center">
          <div className="text-red-600 mb-4">Error: {error}</div>
          <Link 
            to="/" 
            className={`inline-flex items-center px-4 py-2 rounded-md transition-colors ${
              darkMode ? 'bg-blue-600 hover:bg-blue-500 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen py-4 ${darkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full flex flex-col">
        {/* Header */}
        <div className="text-center mb-6">
          {/* Mobile: Stack vertically */}
          <div className="block md:hidden space-y-4">
            <h1 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              AI Models Analytics
            </h1>
            <p className={`text-base ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Daily trends and provider insights
            </p>
            <div className="flex justify-center space-x-4">
              {/* Back Button */}
              <Link 
                to="/"
                className={`inline-flex items-center px-3 py-2 rounded-md transition-colors ${
                  darkMode ? 'bg-gray-800 text-gray-300 hover:bg-gray-700' : 'bg-white text-gray-600 hover:bg-gray-100'
                }`}
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Dashboard
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
            {/* Back Button */}
            <Link 
              to="/"
              className={`absolute left-0 top-0 inline-flex items-center px-3 py-2 rounded-md transition-colors ${
                darkMode ? 'bg-gray-800 text-gray-300 hover:bg-gray-700' : 'bg-white text-gray-600 hover:bg-gray-100'
              }`}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Dashboard
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
            
            <h1 className={`text-3xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              AI Models Analytics
            </h1>
            <p className={`mt-2 text-lg ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Daily trends and provider insights
            </p>
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
                '--d-analytics': `${unitWidth}px`,
                animation: ready ? 'scrollXAnalytics 20s linear infinite' : undefined
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

        <div className="flex-1">
          {/* Analytics Info */}
          <div className={`mb-6 p-4 rounded-lg ${darkMode ? 'bg-blue-900/20 border-blue-600' : 'bg-blue-50 border-blue-200'} border`}>
            <div className={`text-base ${darkMode ? 'text-blue-200' : 'text-blue-800'}`}>
              <p className="mb-2">
                <strong>Analytics Dashboard:</strong> Track model count changes over time with provider-level filtering.
              </p>
              <p className="mb-2">
                <strong>Data Collection:</strong> Snapshots are captured daily when the dashboard loads new data.
              </p>
              <p>
                <strong>Last Refresh:</strong> {lastRefresh.toLocaleString('en-US', { 
                  timeZone: 'UTC', 
                  year: 'numeric', 
                  month: 'short', 
                  day: '2-digit', 
                  hour: '2-digit', 
                  minute: '2-digit'
                })} UTC | <strong>Total Models: {models.length}<sup>*</sup></strong>
              </p>
              <p className={`text-sm ${darkMode ? 'text-blue-300' : 'text-blue-700'} mt-1`}>
                *Does not include experimental, preview, test, beta models. Also excludes models with unknown origins and license info
              </p>
            </div>
          </div>

          {/* Model Count Line Graph */}
          <ModelCountLineGraph currentModels={models} darkMode={darkMode} />
        </div>

        {/* Footer */}
        <div className={`mt-8 pt-6 border-t rounded-lg p-4 ${
          darkMode ? 'border-gray-600 bg-gray-800' : 'border-gray-300 bg-gray-50'
        }`}>
          <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'} text-center`}>
            <p className="font-medium">
              © 2025 JustAsk - Analytics Dashboard
            </p>
            <p className="mt-2">
              Analytics data is stored locally in your browser. Use the export feature to backup your historical snapshots.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;