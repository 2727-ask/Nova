// ...new file...
import { signal } from '@angular/core';

export const analyzeResponse = signal<any | null>(null);

export function setAnalyzeResponse(payload: any) {
  analyzeResponse.set(payload);
}