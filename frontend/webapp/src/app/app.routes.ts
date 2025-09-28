import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/home/home').then((m) => m.Home),
  },
  {
    path: 'getstarted',
    loadComponent: () => import('./pages/getstarted/getstarted').then((m) => m.Getstarted),
  },
  {
    path: 'analyze',
    loadComponent: () => import('./pages/analyze/analyze').then((m) => m.Analyze),
  },
  {
    path: 'optimizing',
    loadComponent: () => import('./pages/optimizing/optimizing').then((m) => m.Optimizing),
  },
  {
    path: 'final',
    loadComponent: () => import('./pages/final/final').then((m) => m.Final),
  }
];
