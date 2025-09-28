import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Optimizing } from './optimizing';

describe('Optimizing', () => {
  let component: Optimizing;
  let fixture: ComponentFixture<Optimizing>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Optimizing]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Optimizing);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
