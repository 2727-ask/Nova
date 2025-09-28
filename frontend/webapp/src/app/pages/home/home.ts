import { Component, AfterViewInit, Renderer2 } from '@angular/core';

@Component({
  selector: 'app-home',
  imports: [],
  templateUrl: './home.html',
  styleUrl: './home.scss',
})
export class Home implements AfterViewInit {
  constructor(private renderer: Renderer2) {}
  ngAfterViewInit() {
    const script = this.renderer.createElement('script');
    script.src = 'https://3d-parallax-effect.netlify.app/js/app.js';
    script.type = 'text/javascript';
    script.defer = true;
    this.renderer.appendChild(document.body, script);
  }
}
