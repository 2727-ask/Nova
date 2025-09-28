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
];
