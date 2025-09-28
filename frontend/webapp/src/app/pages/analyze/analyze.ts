import { CommonModule } from '@angular/common';
import { Component, AfterViewInit, ViewChild, ElementRef, effect } from '@angular/core';
import Chart from 'chart.js/auto';
import { analyzeResponse } from '../../state/analyze-signal';

@Component({
  selector: 'app-analyze',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './analyze.html',
  styleUrls: ['./analyze.scss']
})
export class Analyze implements AfterViewInit {
  // response will be populated from the shared signal
  response: any = null;

  categories: { name: string; amount: number; emission: number }[] = [];
  subcategories: { category: string; name: string; amount: number; emission: number }[] = [];

  @ViewChild('categoryAmountChart') categoryAmountChartEl!: ElementRef<HTMLCanvasElement>;
  @ViewChild('categoryEmissionChart') categoryEmissionChartEl!: ElementRef<HTMLCanvasElement>;
  @ViewChild('subcategoryAmountChart') subcategoryAmountChartEl!: ElementRef<HTMLCanvasElement>;

  private charts: Chart[] = [];
  private viewInitialized = false;

  constructor() {
    // react to signal changes
    effect(() => {
      const val = analyzeResponse();
      if (!val) return;
      // assign and re-prepare data
      this.response = val;
      this.categories = [];
      this.subcategories = [];
      this.prepareData();
      // if view already initialized, recreate charts
      if (this.viewInitialized) {
        this.destroyCharts();
        this.createCategoryAmountChart();
        this.createCategoryEmissionChart();
        this.createSubcategoryAmountChart();
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
  }

  ngAfterViewInit(): void {
    this.viewInitialized = true;
    // if response already set, create charts now
    if (this.response) {
      this.createCategoryAmountChart();
      this.createCategoryEmissionChart();
      this.createSubcategoryAmountChart();
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

  private generateColors(n: number) {
    const base = ['#3366cc', '#dc3912', '#ff9900', '#109618', '#990099', '#3b3eac', '#0099c6', '#dd4477', '#66aa00', '#b82e2e'];
    const colors: string[] = [];
    for (let i = 0; i < n; i++) colors.push(base[i % base.length]);
    return colors;
  }
}