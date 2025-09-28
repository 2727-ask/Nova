import { CommonModule, DecimalPipe } from '@angular/common';
import { Component, AfterViewInit, ViewChild, ElementRef, effect } from '@angular/core';
import Chart from 'chart.js/auto';
import { analyzeResponse } from '../../state/analyze-signal';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-analyze',
  standalone: true,
  imports: [CommonModule, DecimalPipe, RouterModule],
  templateUrl: './analyze.html',
  styleUrls: ['./analyze.scss']
})
export class Analyze implements AfterViewInit {
  // response will be populated from the shared signal
  response: any = null;

  categories: { name: string; amount: number; emission: number }[] = [];
  subcategories: { category: string; name: string; amount: number; emission: number }[] = [];

  // existing charts
  @ViewChild('categoryAmountChart') categoryAmountChartEl!: ElementRef<HTMLCanvasElement>;
  @ViewChild('categoryEmissionChart') categoryEmissionChartEl!: ElementRef<HTMLCanvasElement>;
  @ViewChild('subcategoryAmountChart') subcategoryAmountChartEl!: ElementRef<HTMLCanvasElement>;

  // new charts for totals & budget comparison
  @ViewChild('totalsChart') totalsChartEl!: ElementRef<HTMLCanvasElement>;
  @ViewChild('budgetComparisonChart') budgetComparisonChartEl!: ElementRef<HTMLCanvasElement>;
  @ViewChild('deltaChart') deltaChartEl!: ElementRef<HTMLCanvasElement>;

  private charts: Chart[] = [];
  private viewInitialized = false;

  // prepared arrays for budget comparison visuals
  budgetCategories: string[] = [];
  budgetBudgeted: number[] = [];
  budgetActual: number[] = [];
  budgetDelta: number[] = [];

  // typed budget entries to use in template (fixes 'unknown' errors)
  budgetEntries: { key: string; value: { budgeted_kg: number; actual_kg: number; delta_kg: number; delta_pct?: number; status?: string } }[] = [];

  constructor() {
    // react to signal changes
    effect(() => {
      const val = analyzeResponse();
      if (!val) return;
      // assign and re-prepare data
      this.response = val;
      this.categories = [];
      this.subcategories = [];
      this.budgetCategories = [];
      this.budgetBudgeted = [];
      this.budgetActual = [];
      this.budgetDelta = [];
      this.budgetEntries = []; // clear
      this.prepareData();
      // if view already initialized, recreate charts
      if (this.viewInitialized) {
        this.destroyCharts();
        this.createCategoryAmountChart();
        this.createCategoryEmissionChart();
        this.createSubcategoryAmountChart();
        this.createTotalsChart();
        this.createBudgetComparisonChart();
        this.createDeltaChart();
      }
    });
  }

  private destroyCharts() {
    this.charts.forEach(c => {
      try { c.destroy(); } catch (e) { /* ignore */ }
    });
    this.charts = [];
  }

  prepareData() {
    const summary = this.response?.summary || {};
    for (const [category, subs] of Object.entries(summary)) {
      let catAmount = 0;
      let catEmission = 0;
      for (const [subName, values] of Object.entries(subs as any)) {
        const { amount, emission } = values as { amount: number; emission: number };
        const amt = Number(amount) || 0;
        const emi = Number(emission) || 0;
        catAmount += amt;
        catEmission += emi;
        this.subcategories.push({
          category,
          name: subName,
          amount: amt,
          emission: emi
        });
      }
      this.categories.push({
        name: category,
        amount: catAmount,
        emission: catEmission
      });
    }
    this.categories.sort((a, b) => b.amount - a.amount);
    this.subcategories.sort((a, b) => b.amount - a.amount);

    // prepare budget comparison arrays (if available)
    const bc = this.response?.budget_comparison_by_category || {};
    for (const [cat, vals] of Object.entries(bc)) {
      const budgeted = Number((vals as any).budgeted_kg) || 0;
      const actual = Number((vals as any).actual_kg) || 0;
      const delta = Number((vals as any).delta_kg) || 0;
      const delta_pct = Number((vals as any).delta_pct) || 0;
      const status = String((vals as any).status || '');
      this.budgetCategories.push(cat);
      this.budgetBudgeted.push(budgeted);
      this.budgetActual.push(actual);
      this.budgetDelta.push(delta);

      // build typed entry for the template (fixes unknown type in template)
      this.budgetEntries.push({
        key: cat,
        value: {
          budgeted_kg: budgeted,
          actual_kg: actual,
          delta_kg: delta,
          delta_pct,
          status
        }
      });
    }
  }

  ngAfterViewInit(): void {
    this.viewInitialized = true;
    // if response already set, create charts now
    if (this.response) {
      this.createCategoryAmountChart();
      this.createCategoryEmissionChart();
      this.createSubcategoryAmountChart();
      this.createTotalsChart();
      this.createBudgetComparisonChart();
      this.createDeltaChart();
    }
  }

  private createCategoryAmountChart() {
    const labels = this.categories.map(c => c.name);
    const data = this.categories.map(c => c.amount);
    const ctx = this.categoryAmountChartEl.nativeElement.getContext('2d')!;
    this.charts.push(new Chart(ctx, {
      type: 'pie',
      data: { labels, datasets: [{ data, backgroundColor: this.generateColors(labels.length) }] },
      options: { plugins: { legend: { position: 'right' } } }
    }));
  }

  private createCategoryEmissionChart() {
    const labels = this.categories.map(c => c.name);
    const data = this.categories.map(c => c.emission);
    const ctx = this.categoryEmissionChartEl.nativeElement.getContext('2d')!;
    this.charts.push(new Chart(ctx, {
      type: 'pie',
      data: { labels, datasets: [{ data, backgroundColor: this.generateColors(labels.length) }] },
      options: { plugins: { legend: { position: 'right' } } }
    }));
  }

  private createSubcategoryAmountChart() {
    const top = this.subcategories.slice(0, 8);
    const labels = top.map(s => `${s.category} — ${s.name}`);
    const data = top.map(s => s.amount);
    const ctx = this.subcategoryAmountChartEl.nativeElement.getContext('2d')!;
    this.charts.push(new Chart(ctx, {
      type: 'pie',
      data: { labels, datasets: [{ data, backgroundColor: this.generateColors(labels.length) }] },
      options: { plugins: { legend: { position: 'right' } } }
    }));
  }

  // New: totals donut (allotted vs actual)
  private createTotalsChart() {
    const totals = this.response?.totals || { total_allotted_emission: 0, total_actual_emission: 0 };
    const labels = ['Allotted (budget)', 'Actual'];
    const data = [Number(totals.total_allotted_emission) || 0, Number(totals.total_actual_emission) || 0];
    const ctx = this.totalsChartEl?.nativeElement.getContext('2d')!;
    if (!ctx) return;
    this.charts.push(new Chart(ctx, {
      type: 'doughnut',
      data: { labels, datasets: [{ data, backgroundColor: ['#109618', '#dc3912'] }] },
      options: { plugins: { legend: { position: 'bottom' } } }
    }));
  }

  // New: budget vs actual per category (bar chart)
  private createBudgetComparisonChart() {
    if (!this.budgetCategories.length) return;
    const ctx = this.budgetComparisonChartEl.nativeElement.getContext('2d')!;
    this.charts.push(new Chart(ctx, {
      type: 'bar',
      data: {
        labels: this.budgetCategories,
        datasets: [
          { label: 'Budgeted (kg)', data: this.budgetBudgeted, backgroundColor: '#3366cc' },
          { label: 'Actual (kg)', data: this.budgetActual, backgroundColor: '#ff9900' }
        ]
      },
      options: {
        plugins: { legend: { position: 'bottom' } },
        responsive: true,
        scales: {
          x: { stacked: false },
          y: { beginAtZero: true }
        }
      }
    }));
  }

  // New: delta per category (colored by over/under)
  private createDeltaChart() {
    if (!this.budgetCategories.length) return;
    const colors = this.budgetDelta.map(d => d > 0 ? '#b82e2e' : '#109618'); // red if over, green if under
    const ctx = this.deltaChartEl.nativeElement.getContext('2d')!;
    this.charts.push(new Chart(ctx, {
      type: 'bar',
      data: { labels: this.budgetCategories, datasets: [{ label: 'Delta (kg)', data: this.budgetDelta, backgroundColor: colors }] },
      options: {
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } }
      }
    }));
  }

  private generateColors(n: number) {
    const base = ['#3366cc', '#dc3912', '#ff9900', '#109618', '#990099', '#3b3eac', '#0099c6', '#dd4477', '#66aa00', '#b82e2e'];
    const colors: string[] = [];
    for (let i = 0; i < n; i++) colors.push(base[i % base.length]);
    return colors;
  }
}