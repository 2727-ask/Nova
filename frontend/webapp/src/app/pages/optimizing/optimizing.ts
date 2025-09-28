import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-optimizing',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './optimizing.html',
  styleUrls: ['./optimizing.scss']
})
export class Optimizing implements OnInit {
  logs = [
    'Queuing your request',
    'Tokenizing your report',
    'Evaluating your report',
    'Generating Suggestions',
    'Displaying results',
    'Redirecting'
  ];

  visibleLogs: string[] = [];
  currentIndex = -1;
  progress = 0; // 0..100

  constructor(private router: Router) {}

  ngOnInit(): void {
    this.startSequence();
  }

  private randomDelayMs(min = 2000, max = 5000) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  private startSequence() {
    const initialDelay = 200;

    const next = () => {
      this.currentIndex++;
      if (this.currentIndex < this.logs.length) {
        this.visibleLogs.push(this.logs[this.currentIndex]);
        this.progress = Math.round(((this.currentIndex + 1) / this.logs.length) * 100);
        // pick a random delay between 2000ms and 5000ms before showing the next step
        setTimeout(next, this.randomDelayMs());
      } else {
        // final pause then redirect to optimized page
        setTimeout(() => this.router.navigate(['/final']), 700);
      }
    };

    setTimeout(next, initialDelay);
  }
}
