import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';

@Component({
  selector: 'app-getstarted',
  standalone: true,
  imports: [],
  templateUrl: './getstarted.html',
  styleUrl: './getstarted.scss',
})
export class Getstarted {
  constructor(private http: HttpClient, private router: Router) {}

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      const file = input.files[0];
      const formData = new FormData();
      formData.append('file', file);

      // Hit the FastAPI endpoint
      this.http.post('http://localhost:8000/statements/categorize', formData).subscribe({
        next: (response) => {
          console.log('File uploaded successfully:', response);
          // Redirect to the analyze route
          this.router.navigate(['/analyze']);
        },
        error: (error) => {
          console.error('Error uploading file:', error);
          alert('Failed to upload file. Please try again.');
        },
      });
    }
  }
}