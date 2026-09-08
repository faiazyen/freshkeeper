/* FreshKeeper interface.
 *
 * Single-page Vue 3 application served by the Flask backend off the Raspberry
 * Pi itself. It polls rather than using websockets: the measurement cycle runs
 * every thirty minutes, so a 30-second poll is already far finer-grained than
 * the data changes, and it avoids holding a socket open on a device that
 * spends most of its life idle.
 */
const { createApp, ref, nextTick } = Vue;

// The token is generated on first run and printed to the device console. In a
// browser it lives in localStorage, which is scoped to this origin.
const TOKEN = localStorage.getItem('fk_token') || 'devtoken';
const HEADERS = { 'Authorization': `Bearer ${TOKEN}`, 'Content-Type': 'application/json' };

const STATE_LABELS = { fresh: 'Fresh', marginal: 'Use soon', spoiled: 'Spoiled' };

createApp({
  setup() {
    const items = ref([]);
    const alerts = ref([]);
    const stats = ref({});
    const view = ref('dashboard');
    const selected = ref(null);
    const loading = ref(false);
    const chart = ref(null);
    let chartInstance = null;

    const statLabels = {
      items_tracked: 'Items tracked',
      eaten: 'Eaten in time',
      binned: 'Thrown away',
      waste_rate: 'Waste rate',
      wasted_mass_g: 'Mass wasted',
      mean_alert_lead_time_hours: 'Mean alert lead time'
    };

    async function api(path, options = {}) {
      const res = await fetch(`/api${path}`, { headers: HEADERS, ...options });
      if (!res.ok) throw new Error(`${path} -> ${res.status}`);
      return res.json();
    }

    async function refresh() {
      loading.value = true;
      try {
        [items.value, alerts.value, stats.value] = await Promise.all([
          api('/items'), api('/alerts'), api('/stats')
        ]);
      } catch (err) {
        console.error('refresh failed', err);
      } finally {
        loading.value = false;
      }
    }

    async function open(item) {
      selected.value = await api(`/items/${item.id}`);
      view.value = 'detail';
      await nextTick();
      drawChart();
    }

    function drawChart() {
      if (!chart.value || !selected.value) return;
      if (chartInstance) chartInstance.destroy();
      const history = selected.value.history || [];
      chartInstance = new Chart(chart.value, {
        type: 'line',
        data: {
          labels: history.map(p => new Date(p.t).toLocaleDateString(undefined,
            { month: 'short', day: 'numeric' })),
          datasets: [{
            data: history.map(p => p.score),
            borderColor: '#059669',
            backgroundColor: 'rgba(5,150,105,0.10)',
            fill: true, tension: 0.3, pointRadius: 2
          }]
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: {
            y: { min: 0, max: 100, title: { display: true, text: 'Freshness' } }
          }
        }
      });
    }

    async function snooze(id) {
      await api(`/items/${id}/snooze`, { method: 'POST' });
      await refresh();
    }

    async function consume(id, outcome) {
      await api(`/items/${id}/consume`, {
        method: 'POST', body: JSON.stringify({ outcome })
      });
      view.value = 'dashboard';
      await refresh();
    }

    const stateLabel = s => STATE_LABELS[s] || 'Unknown';

    const badgeClass = s => ({
      fresh: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      marginal: 'bg-amber-50 text-amber-700 border-amber-200',
      spoiled: 'bg-rose-50 text-rose-700 border-rose-200'
    }[s] || 'bg-slate-50 text-slate-600 border-slate-200');

    const barClass = s => ({
      fresh: 'bg-emerald-500', marginal: 'bg-amber-500', spoiled: 'bg-rose-500'
    }[s] || 'bg-slate-400');

    // Scores arrive as float32 round-trips, so 17.6 comes back as
    // 17.600000381469727. Round at the edge rather than in the API, which
    // should keep full precision for anything analysing the data.
    const score = v => (v === null || v === undefined) ? '—' : Math.round(v);

    const ageDays = t =>
      Math.max(0, Math.floor((Date.now() - new Date(t)) / 86400000));

    function formatStat(key) {
      const v = stats.value[key];
      if (v === null || v === undefined) return '—';
      if (key === 'waste_rate') return `${(v * 100).toFixed(0)}%`;
      if (key === 'wasted_mass_g') return `${Math.round(v)} g`;
      if (key === 'mean_alert_lead_time_hours') return `${v.toFixed(1)} h`;
      return v;
    }

    refresh();
    setInterval(refresh, 30000);

    return { items, alerts, stats, view, selected, loading, chart, statLabels,
             refresh, open, snooze, consume, stateLabel, badgeClass, barClass,
             ageDays, formatStat, score };
  }
}).mount('#app');
