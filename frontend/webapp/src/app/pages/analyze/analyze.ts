// ...existing code...
import { CommonModule } from '@angular/common';
import { Component, AfterViewInit, ViewChild, ElementRef } from '@angular/core';
import Chart from 'chart.js/auto';

@Component({
  selector: 'app-analyze',
  // ...existing code...
  imports: [CommonModule],
  templateUrl: './analyze.html',
  styleUrls: ['./analyze.scss']
})
export class Analyze implements AfterViewInit {
  // sample response (use real response when you have it)
  response = {
    summary: {
      Finances: {
        'Loan / credit card payments': { amount: 1166.43, emission: '20' },
        'Bank fees': { amount: 1166.43, emission: '20' }
      },
      Housing: {
        'Water & waste services': { amount: 116.43, emission: '10' }
      },
      Food: {
        Groceries: { amount: 11.43, emission: '2' }
      },
      Shopping: {
        'General e-commerce (Amazon, Walmart, etc.)': { amount: 1166.43, emission: '20' }
      },
      Travel: {
        'Ride-hailing (Uber, Lyft)': { amount: 1166.43, emission: '20' },
        'Car-related (fuel, parking, tolls, EV charging)': { amount: 1166.43, emission: '20' }
      }
    },
    uncategorized: 206.97,
    transactions_count: 56
  };

  categories: { name: string; amount: number; emission: number }[] = [];
  subcategories: { category: string; name: string; amount: number; emission: number }[] = [];

  @ViewChild('categoryAmountChart') categoryAmountChartEl!: ElementRef<HTMLCanvasElement>;
  @ViewChild('categoryEmissionChart') categoryEmissionChartEl!: ElementRef<HTMLCanvasElement>;
  @ViewChild('subcategoryAmountChart') subcategoryAmountChartEl!: ElementRef<HTMLCanvasElement>;

  private charts: Chart[] = [];

  constructor() {
    this.prepareData();
  }

  prepareData() {
    const summary = this.response.summary;
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
    // sort descending by amount for nicer visuals
    this.categories.sort((a, b) => b.amount - a.amount);
    this.subcategories.sort((a, b) => b.amount - a.amount);
  }

  ngAfterViewInit(): void {
    this.createCategoryAmountChart();
    this.createCategoryEmissionChart();
    this.createSubcategoryAmountChart();
  }

  private createCategoryAmountChart() {
    const labels = this.categories.map(c => c.name);
    const data = this.categories.map(c => c.amount);
    const ctx = this.categoryAmountChartEl.nativeElement.getContext('2d')!;
    this.charts.push(new Chart(ctx, {
      type: 'pie',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: this.generateColors(labels.length)
        }]
      },
      options: {
        plugins: { legend: { position: 'right' } }
      }
    }));
  }

  private createCategoryEmissionChart() {
    const labels = this.categories.map(c => c.name);
    const data = this.categories.map(c => c.emission);
    const ctx = this.categoryEmissionChartEl.nativeElement.getContext('2d')!;
    this.charts.push(new Chart(ctx, {
      type: 'pie',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: this.generateColors(labels.length)
        }]
      },
      options: {
        plugins: { legend: { position: 'right' } }
      }
    }));
  }

  private createSubcategoryAmountChart() {
    // show top 8 subcategories by amount
    const top = this.subcategories.slice(0, 8);
    const labels = top.map(s => `${s.category} — ${s.name}`);
    const data = top.map(s => s.amount);
    const ctx = this.subcategoryAmountChartEl.nativeElement.getContext('2d')!;
    this.charts.push(new Chart(ctx, {
      type: 'pie',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: this.generateColors(labels.length)
        }]
      },
      options: {
        plugins: { legend: { position: 'right' } }
      }
    }));
  }

  private generateColors(n: number) {
    const base = [
      '#3366cc', '#dc3912', '#ff9900', '#109618', '#990099',
      '#3b3eac', '#0099c6', '#dd4477', '#66aa00', '#b82e2e'
    ];
    const colors: string[] = [];
    for (let i = 0; i < n; i++) {
      colors.push(base[i % base.length]);
    }
    return colors;
  }
}