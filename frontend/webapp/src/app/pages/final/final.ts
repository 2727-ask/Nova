import { Component, AfterViewInit, ViewChild, ElementRef, OnInit, effect } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { RouterModule } from '@angular/router';
import Chart from 'chart.js/auto';
import { analyzeResponse } from '../../state/analyze-signal';

@Component({
  selector: 'app-final',
  standalone: true,
  imports: [CommonModule, DecimalPipe, RouterModule],
  templateUrl: './final.html',
  styleUrls: ['./final.scss']
})
export class Final implements OnInit, AfterViewInit {
  response: any = null;
  categories: { name: string; amount: number; emission: number; suggestionPct: number; afterEmission: number; tips: string[] }[] = [];
  totals = { allotted: 0, actual: 0, delta: 0, afterActual: 0 };
  compliant = false;

  // new compensation fields
  overallReductionPct = 0;
  offsetKg = 0;
  estimatedCreditCostUsd = 0;
  estimatedTrees = 0;

  @ViewChild('beforeAfterChart') beforeAfterChartEl!: ElementRef<HTMLCanvasElement>;
  @ViewChild('totalsChart') totalsChartEl!: ElementRef<HTMLCanvasElement>;
  @ViewChild('categoryDeltaChart') categoryDeltaChartEl!: ElementRef<HTMLCanvasElement>;

  private charts: Chart[] = [];
  private suggestionsMap: Record<string, { pct: number; tips: string[] }> = {
    Finances: { pct: 0.25, tips: ['Consolidate loans', 'Switch to digital statements', 'Avoid late fees'] },
    Food: { pct: 0.15, tips: ['Choose plant-forward meals', 'Plan grocery trips', 'Buy seasonal/local produce'] },
    Shopping: { pct: 0.35, tips: ['Buy less, choose durable', 'Prefer second-hand', 'Avoid fast-fashion & bulk shipping'] },
    Travel: { pct: 0.4, tips: ['Use public transit / bike', 'Combine errands', 'Choose EV / carpool'] },
    Housing: { pct: 0.2, tips: ['Fix leaks', 'Install low-flow fixtures', 'Reduce hot water use'] },
    Health: { pct: 0.1, tips: ['Telehealth where possible', 'Choose low-packaging products'] },
    Entertainment: { pct: 0.2, tips: ['Stream Smart (lower quality)', 'Share subscriptions'] },
    Charity: { pct: 0.0, tips: ['Keep charitable giving but favour low-overhead options'] },
    default: { pct: 0.15, tips: ['Review subscriptions', 'Reduce single-use purchases'] }
  };

  constructor() {
    effect(() => {
      const val = analyzeResponse();
      if (!val) return;
      this.response = val;
      this.prepareData();
      this.destroyCharts();
      // charts recreated in AfterViewInit if view ready
      try { this.createChartsIfReady(); } catch { /* ignore during tests */ }
    });
  }

  ngOnInit(): void {}

  ngAfterViewInit(): void {
    this.createChartsIfReady();
  }

  private createChartsIfReady() {
    if (!this.response) return;
    this.createBeforeAfterChart();
    this.createTotalsChart();
    this.createCategoryDeltaChart();
  }

  private destroyCharts() {
    this.charts.forEach(c => { try { c.destroy(); } catch { } });
    this.charts = [];
  }

  private prepareData() {
    this.categories = [];
    const summary = this.response?.summary || {};
    let totalActual = 0;
    for (const [cat, subs] of Object.entries(summary)) {
      let catAmount = 0;
      let catEmission = 0;
      for (const [name, vals] of Object.entries(subs as any)) {
        const amt = Number((vals as any).amount) || 0;
        const emi = Number((vals as any).emission) || 0;
        catAmount += amt;
        catEmission += emi;
      }
      const cfg = this.suggestionsMap[cat] ?? this.suggestionsMap?.['default'];
      const suggestionPct = cfg.pct;
      const afterEmission = +(catEmission * (1 - suggestionPct));
      this.categories.push({
        name: cat,
        amount: catAmount,
        emission: +catEmission,
        suggestionPct,
        afterEmission: +afterEmission,
        tips: cfg.tips
      });
      totalActual += catEmission;
    }

    // Totals from response (use response totals if present)
    const totalsResp = this.response?.totals || {};
    const allotted = Number(totalsResp.total_allotted_emission) || 0;
    const actual = Number(totalsResp.total_actual_emission) || totalActual || 0;
    const afterActual = this.categories.reduce((s, c) => s + c.afterEmission, 0);
    const delta = allotted - actual;
    this.totals = { allotted, actual, delta, afterActual };
    this.compliant = actual <= allotted;

    // overall reduction percent (actual -> projected after)
    this.overallReductionPct = actual > 0 ? ((actual - afterActual) / actual) * 100 : 0;

    // if still not compliant after projected reductions -> estimate offset need
    this.offsetKg = Math.max(0, afterActual - allotted);
    // rough cost estimate for carbon credits: assume $10 / metric tonne = $0.01 / kg
    this.estimatedCreditCostUsd = +(this.offsetKg * 0.01);
    // rough tree planting estimate: assume ~22 kg CO2 absorbed per tree / year (varies)
    this.estimatedTrees = Math.ceil(this.offsetKg > 0 ? (this.offsetKg / 22) : 0);

    // sort categories by impact
    this.categories.sort((a, b) => b.emission - a.emission);
  }

  // charts
  private createBeforeAfterChart() {
    if (!this.beforeAfterChartEl) return;
    const labels = this.categories.map(c => c.name);
    const before = this.categories.map(c => c.emission);
    const after = this.categories.map(c => c.afterEmission);
    const ctx = this.beforeAfterChartEl.nativeElement.getContext('2d')!;
    this.charts.push(new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          { label: 'Before (kg)', data: before, backgroundColor: this.generateColors(before.length, 0.7) },
          { label: 'After (kg)', data: after, backgroundColor: this.generateColors(after.length, 0.25) }
        ]
      },
      options: { responsive: true, plugins: { legend: { position: 'bottom' } }, scales: { y: { beginAtZero: true } } }
    }));
  }

  private createTotalsChart() {
    if (!this.totalsChartEl) return;
    const ctx = this.totalsChartEl.nativeElement.getContext('2d')!;
    const labels = ['Allotted', 'Actual', 'After (projected)'];
    const data = [this.totals.allotted, this.totals.actual, this.totals.afterActual];
    this.charts.push(new Chart(ctx, {
      type: 'doughnut',
      data: { labels, datasets: [{ data, backgroundColor: ['#109618', '#dc3912', '#3366cc'] }] },
      options: { plugins: { legend: { position: 'bottom' } } }
    }));
  }

  private createCategoryDeltaChart() {
    if (!this.categoryDeltaChartEl) return;
    const labels = this.categories.map(c => c.name);
    const delta = this.categories.map(c => +(c.afterEmission - c.emission).toFixed(2));
    const colors = delta.map(d => d < 0 ? '#109618' : '#b82e2e');
    const ctx = this.categoryDeltaChartEl.nativeElement.getContext('2d')!;
    this.charts.push(new Chart(ctx, {
      type: 'bar',
      data: { labels, datasets: [{ label: 'Delta (after - before)', data: delta, backgroundColor: colors }] },
      options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
    }));
  }

  private generateColors(n: number, alpha = 1) {
    const base = ['#3366cc', '#dc3912', '#ff9900', '#109618', '#990099', '#3b3eac', '#0099c6', '#dd4477', '#66aa00', '#b82e2e'];
    return Array.from({ length: n }, (_, i) => {
      const c = base[i % base.length];
      if (alpha === 1) return c;
      return this.hexToRgba(c, alpha);
    });
  }

  private hexToRgba(hex: string, a: number) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r},${g},${b},${a})`;
  }
}
