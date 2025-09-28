import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Analyze } from './analyze';

describe('Analyze', () => {
  let component: Analyze;
  let fixture: ComponentFixture<Analyze>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Analyze]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Analyze);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
